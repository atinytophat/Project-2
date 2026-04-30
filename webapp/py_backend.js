(function () {
  "use strict";

  const PYODIDE_VERSION = "0.27.2";
  const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  const PYODIDE_SCRIPT_URL = `${PYODIDE_INDEX_URL}pyodide.js`;
  const SERVER_SOURCE_PATH = "./server.py";
  const CSV_CANDIDATE_PATHS = ["../Abaqus/verificationdata.csv", "../verificationdata.csv"];

  let backendReadyPromise = null;
  let backendFailed = false;

  function loadExternalScript(src) {
    return new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[data-src="${src}"]`);
      if (existing) {
        if (existing.dataset.loaded === "true") {
          resolve();
          return;
        }
        existing.addEventListener("load", () => resolve(), { once: true });
        existing.addEventListener("error", () => reject(new Error(`Unable to load script: ${src}`)), { once: true });
        return;
      }

      const script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.dataset.src = src;
      script.addEventListener("load", () => {
        script.dataset.loaded = "true";
        resolve();
      }, { once: true });
      script.addEventListener("error", () => {
        reject(new Error(`Unable to load script: ${src}`));
      }, { once: true });
      document.head.appendChild(script);
    });
  }

  async function fetchTextFromCandidates(paths) {
    for (const path of paths) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (response.ok) {
          return {
            path,
            text: await response.text(),
          };
        }
      } catch (error) {
        console.warn(`Unable to fetch ${path}`, error);
      }
    }
    throw new Error(`Unable to fetch any candidate file: ${paths.join(", ")}`);
  }

  function buildPythonApiBridge() {
    return `
from urllib.parse import parse_qs, urlparse
import json
import numpy as np

def api_request(path):
    parsed = urlparse(path)
    params = parse_qs(parsed.query)

    if parsed.path == "/api/atlas":
        kappa = float(params.get("kappa", [backend.INTERACTIVE_DEFAULT_K])[0])
        phi_deg = float(params.get("phi_deg", [backend.INTERACTIVE_DEFAULT_PHI_DEG])[0])
        beam = backend.read_beam_parameters(params)
        theta0_values, a_l, b_l = backend.generate_locus_for_case(np.deg2rad(phi_deg), kappa, backend.INTERACTIVE_NUM_POINTS)
        limits = backend.atlas_limits(phi_deg, kappa, beam)
        allowable_theta = np.linspace(0.0, float(limits["theta0_limit_rad"]), 220)
        allowable_a, allowable_b = backend.sampled_trajectory(allowable_theta, phi_deg, kappa)
        payload = {
            "phi_deg": float(phi_deg),
            "kappa": float(kappa),
            "geometric_theta0_values": [float(value) for value in theta0_values],
            "geometric_a_over_l": [float(value) for value in a_l],
            "geometric_b_over_l": [float(value) for value in b_l],
            "allowable_theta0_values": [float(value) for value in allowable_theta],
            "allowable_a_over_l": [float(value) for value in allowable_a],
            "allowable_b_over_l": [float(value) for value in allowable_b],
            "theta0_max_rad": float(limits["theta0_limit_rad"]),
            "theta0_max_deg": float(limits["theta0_limit_deg"]),
            "start_point": [float(allowable_a[0]), float(allowable_b[0])],
            "end_point": [float(allowable_a[-1]), float(allowable_b[-1])],
        }
        return json.dumps(payload)

    if parsed.path == "/api/section4-workspace":
        return json.dumps(backend.get_section4_workspace_payload())

    if parsed.path in {"/api/medical-experiment", "/api/section700-vertical-line"}:
        tip_amplitude = float(params.get("tip_amplitude", [backend.SECTION701_TIP_AMPLITUDE])[0])
        core_motion_time = float(params.get("core_motion_time", [backend.SECTION701_CORE_MOTION_TIME])[0])
        beam = backend.read_beam_parameters(params)
        if tip_amplitude <= 0.0:
            raise ValueError("tip_amplitude must be positive.")
        if core_motion_time <= 0.0:
            raise ValueError("core_motion_time must be positive.")
        payload = backend.get_section701_sinusoid_payload(
            tip_amplitude=tip_amplitude,
            core_motion_time=core_motion_time,
            beam=beam,
        )
        return json.dumps(payload)

    if parsed.path == "/api/atlas-report":
        panels = []
        for k_value in backend.REPORT_K_VALUES:
            curves = []
            for angle_deg in backend.REPORT_FORCE_ANGLES_DEG:
                theta0_values, a_l, b_l = backend.generate_locus_for_case(np.deg2rad(angle_deg), float(k_value), backend.NUM_POINTS)
                curves.append(
                    {
                        "phi_deg": float(angle_deg),
                        "theta0_values": [float(value) for value in theta0_values],
                        "a_over_l": [float(value) for value in a_l],
                        "b_over_l": [float(value) for value in b_l],
                    }
                )
            panels.append({"kappa": float(k_value), "curves": curves})
        return json.dumps({"panels": panels})

    if parsed.path == "/api/atlas-loads":
        kappa = float(params.get("kappa", [backend.INTERACTIVE_DEFAULT_K])[0])
        phi_deg = float(params.get("phi_deg", [backend.INTERACTIVE_DEFAULT_PHI_DEG])[0])
        theta0_deg = float(params.get("theta0_deg", [0.0])[0])
        beam = backend.read_beam_parameters(params)
        limits = backend.atlas_limits(phi_deg, kappa, beam)
        theta0_rad = np.deg2rad(min(theta0_deg, float(limits["theta0_limit_deg"])))
        state = backend.selected_state(
            theta0_rad,
            phi_deg,
            kappa,
            beam["beam_length"],
            beam["youngs_modulus"],
            float(limits["inertia"]),
        )
        return json.dumps({"limits": limits, "state": state})

    if parsed.path == "/api/section520-overlay":
        return json.dumps(backend.get_section520_overlay_payload())

    raise ValueError(f"Unsupported in-browser API path: {parsed.path}")
`;
  }

  async function initializeBackend() {
    if (backendReadyPromise) {
      return backendReadyPromise;
    }

    backendReadyPromise = (async () => {
      await loadExternalScript(PYODIDE_SCRIPT_URL);
      const pyodide = await globalThis.loadPyodide({ indexURL: PYODIDE_INDEX_URL });
      await pyodide.loadPackage(["numpy", "scipy"]);

      const [serverSource, csvSource] = await Promise.all([
        fetchTextFromCandidates([SERVER_SOURCE_PATH]),
        fetchTextFromCandidates(CSV_CANDIDATE_PATHS),
      ]);

      pyodide.FS.writeFile("/server.py", serverSource.text);
      try {
        pyodide.FS.mkdir("/Abaqus");
      } catch (error) {
        // Directory already exists.
      }
      pyodide.FS.writeFile("/verificationdata.csv", csvSource.text);
      pyodide.FS.writeFile("/Abaqus/verificationdata.csv", csvSource.text);

      await pyodide.runPythonAsync(`
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("webapp_server", "/server.py")
backend = importlib.util.module_from_spec(spec)
sys.modules["webapp_server"] = backend
spec.loader.exec_module(backend)
`);
      await pyodide.runPythonAsync(buildPythonApiBridge());
      return pyodide;
    })().catch((error) => {
      backendFailed = true;
      backendReadyPromise = null;
      throw error;
    });

    return backendReadyPromise;
  }

  async function request(path, options = {}) {
    const signal = options.signal || null;
    if (signal?.aborted) {
      throw new DOMException("The operation was aborted.", "AbortError");
    }

    const pyodide = await initializeBackend();
    if (signal?.aborted) {
      throw new DOMException("The operation was aborted.", "AbortError");
    }

    pyodide.globals.set("request_path", path);
    try {
      const payloadText = await pyodide.runPythonAsync("api_request(request_path)");
      if (signal?.aborted) {
        throw new DOMException("The operation was aborted.", "AbortError");
      }
      return JSON.parse(payloadText);
    } finally {
      pyodide.globals.delete("request_path");
    }
  }

  globalThis.StaticPyBackend = {
    request,
    prime() {
      return initializeBackend();
    },
    hasFailed() {
      return backendFailed;
    },
  };
}());
