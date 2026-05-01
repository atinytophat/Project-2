from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


WEBAPP_DIR = Path(__file__).resolve().parent
DATA_DIR = WEBAPP_DIR / "data"
SERVER_PATH = WEBAPP_DIR / "server.py"


def load_server_module():
    spec = importlib.util.spec_from_file_location("webapp_server_static", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build() -> None:
    server = load_server_module()

    default_beam = {
        "beam_length": server.DEFAULT_BEAM_LENGTH,
        "beam_width": server.DEFAULT_BEAM_WIDTH,
        "thickness": server.DEFAULT_THICKNESS,
        "youngs_modulus": server.DEFAULT_YOUNGS_MODULUS,
        "sigma_max": server.DEFAULT_SIGMA_MAX,
    }
    pebax_beam = {
        "beam_length": server.DEFAULT_BEAM_LENGTH,
        "beam_width": server.DEFAULT_BEAM_WIDTH,
        "thickness": server.DEFAULT_THICKNESS,
        "youngs_modulus": 513.0e6,
        "sigma_max": 56.0e6,
    }
    tpu_beam = {
        "beam_length": server.DEFAULT_BEAM_LENGTH,
        "beam_width": server.DEFAULT_BEAM_WIDTH,
        "thickness": server.DEFAULT_THICKNESS,
        "youngs_modulus": 22.1e6,
        "sigma_max": 53.1e6,
    }

    default_kappa = float(server.INTERACTIVE_DEFAULT_K)
    default_phi_deg = float(server.INTERACTIVE_DEFAULT_PHI_DEG)
    theta0_values, a_l, b_l = server.generate_locus_for_case(
        server.np.deg2rad(default_phi_deg),
        default_kappa,
        server.INTERACTIVE_NUM_POINTS,
    )
    limits = server.atlas_limits(default_phi_deg, default_kappa, default_beam)
    allowable_theta = server.np.linspace(0.0, float(limits["theta0_limit_rad"]), 220)
    allowable_a, allowable_b = server.sampled_trajectory(allowable_theta, default_phi_deg, default_kappa)
    atlas_default = {
        "phi_deg": default_phi_deg,
        "kappa": default_kappa,
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
    atlas_loads_default = {
        "limits": limits,
        "state": server.selected_state(
            0.0,
            default_phi_deg,
            default_kappa,
            default_beam["beam_length"],
            default_beam["youngs_modulus"],
            float(limits["inertia"]),
        ),
    }

    report_panels = []
    for k_value in server.REPORT_K_VALUES:
        curves = []
        for angle_deg in server.REPORT_FORCE_ANGLES_DEG:
            theta_values, curve_a, curve_b = server.generate_locus_for_case(
                server.np.deg2rad(angle_deg),
                float(k_value),
                server.NUM_POINTS,
            )
            curves.append(
                {
                    "phi_deg": float(angle_deg),
                    "theta0_values": [float(value) for value in theta_values],
                    "a_over_l": [float(value) for value in curve_a],
                    "b_over_l": [float(value) for value in curve_b],
                }
            )
        report_panels.append({"kappa": float(k_value), "curves": curves})

    medical_default = server.get_section701_sinusoid_payload(
        tip_amplitude=server.SECTION701_TIP_AMPLITUDE,
        core_motion_time=server.SECTION701_CORE_MOTION_TIME,
        beam=default_beam,
    )
    medical_default_report = server.get_section701_sinusoid_payload(
        tip_amplitude=server.SECTION701_TIP_AMPLITUDE,
        core_motion_time=server.SECTION701_CORE_MOTION_TIME,
        beam=default_beam,
        stiffness_source="report",
    )
    medical_pebax = server.get_section701_sinusoid_payload(
        tip_amplitude=server.SECTION701_TIP_AMPLITUDE,
        core_motion_time=server.SECTION701_CORE_MOTION_TIME,
        beam=pebax_beam,
    )
    medical_pebax_report = server.get_section701_sinusoid_payload(
        tip_amplitude=server.SECTION701_TIP_AMPLITUDE,
        core_motion_time=server.SECTION701_CORE_MOTION_TIME,
        beam=pebax_beam,
        stiffness_source="report",
    )
    medical_tpu = server.get_section701_sinusoid_payload(
        tip_amplitude=server.SECTION701_TIP_AMPLITUDE,
        core_motion_time=server.SECTION701_CORE_MOTION_TIME,
        beam=tpu_beam,
    )
    medical_tpu_report = server.get_section701_sinusoid_payload(
        tip_amplitude=server.SECTION701_TIP_AMPLITUDE,
        core_motion_time=server.SECTION701_CORE_MOTION_TIME,
        beam=tpu_beam,
        stiffness_source="report",
    )

    write_json(DATA_DIR / "atlas-default.json", atlas_default)
    write_json(DATA_DIR / "atlas-loads-default.json", atlas_loads_default)
    write_json(DATA_DIR / "atlas-report.json", {"panels": report_panels})
    write_json(DATA_DIR / "section4-workspace.json", server.get_section4_workspace_payload())
    write_json(DATA_DIR / "section520-overlay.json", server.get_section520_overlay_payload())
    write_json(DATA_DIR / "section520-overlay-report.json", server.get_section520_overlay_payload("report"))
    write_json(DATA_DIR / "medical-default.json", medical_default)
    write_json(DATA_DIR / "medical-default-report.json", medical_default_report)
    write_json(DATA_DIR / "medical-pebax.json", medical_pebax)
    write_json(DATA_DIR / "medical-pebax-report.json", medical_pebax_report)
    write_json(DATA_DIR / "medical-tpu.json", medical_tpu)
    write_json(DATA_DIR / "medical-tpu-report.json", medical_tpu_report)


if __name__ == "__main__":
    build()
