(function () {
  "use strict";

  const TAB_METADATA = {
    atlas: "Section 2 Atlas",
    prb: "Section 4 PRB",
    mechanism: "Section 5 Mechanism",
    materials: "Material Library",
  };
  const ATLAS_CONFIG = {
    xMin: -0.7,
    xMax: 1.05,
    yMin: 0.0,
    yMax: 1.05,
    marginLeft: 38,
    marginRight: 8,
    marginTop: 18,
    marginBottom: 34,
    gridStep: 0.2,
    endpoint: "/api/atlas",
    reportEndpoint: "/api/atlas-report",
  };
  const MECHANISM_CONFIG = {
    endpoint: "/api/section520-overlay",
    marginLeft: 42,
    marginRight: 12,
    marginTop: 18,
    marginBottom: 36,
    gridStep: 0.2,
  };
  const PRB_CONFIG = {
    endpoint: "/api/section4-workspace",
    marginLeft: 48,
    marginRight: 18,
    marginTop: 18,
    marginBottom: 40,
  };
  const MATERIALS_CONFIG = {
    endpoint: "/api/medical-experiment?mode=sinusoid",
    marginLeft: 48,
    marginRight: 14,
    marginTop: 18,
    marginBottom: 36,
    gridStep: 0.1,
  };
  const REPORT_COLORS = [
    "#0c8aa4", "#ef8c54", "#1f5c99", "#2f8f6d", "#b15d85",
    "#c17c1f", "#6a5acd", "#0f766e", "#d45d5d", "#43536e",
  ];
  const PRB_SERIES_COLORS = ["#0c8aa4", "#ef8c54", "#2f8f6d"];
  const MATERIAL_PRESETS = {
    pebax: {
      displayName: "PEBAX",
      elasticModulusMpa: 513.0,
      strengthMpa: 56.0,
    },
    medical_grade_tpu: {
      displayName: "Med. TPU",
      elasticModulusMpa: 22.1,
      strengthMpa: 53.1,
    },
  };
  const STATIC_DATA_PATHS = {
    atlasDefault: "./data/atlas-default.json",
    atlasLoadsDefault: "./data/atlas-loads-default.json",
    atlasReport: "./data/atlas-report.json",
    section4Workspace: "./data/section4-workspace.json",
    section520Overlay: "./data/section520-overlay.json",
    medicalDefault: "./data/medical-default.json",
    medicalPebax: "./data/medical-pebax.json",
    medicalTpu: "./data/medical-tpu.json",
  };

  const tabButtons = Array.from(document.querySelectorAll("[data-tab-target]"));
  const tabPanels = Array.from(document.querySelectorAll("[data-tab-panel]"));
  const atlasModeTabs = Array.from(document.querySelectorAll("[data-atlas-mode]"));
  const atlasModePanels = Array.from(document.querySelectorAll("[data-atlas-mode-panel]"));
  const atlasViewPanels = Array.from(document.querySelectorAll("[data-atlas-view]"));
  const atlasDetailTabs = Array.from(document.querySelectorAll("[data-detail-mode]"));
  const atlasDetailPanels = Array.from(document.querySelectorAll("[data-detail-panel]"));
  const kappaSlider = document.getElementById("kappaSlider");
  const phiSlider = document.getElementById("phiSlider");
  const kappaInput = document.getElementById("kappaInput");
  const phiInput = document.getElementById("phiInput");
  const beamLengthInput = document.getElementById("beamLengthInput");
  const beamWidthInput = document.getElementById("beamWidthInput");
  const thicknessInput = document.getElementById("thicknessInput");
  const youngsModulusInput = document.getElementById("youngsModulusInput");
  const sigmaMaxInput = document.getElementById("sigmaMaxInput");
  const thetaAllowableSlider = document.getElementById("thetaAllowableSlider");
  const thetaAllowableInput = document.getElementById("thetaAllowableInput");
  const thetaMaxRad = document.getElementById("thetaMaxRad");
  const thetaSelectedDeg = document.getElementById("thetaSelectedDeg");
  const startPoint = document.getElementById("startPoint");
  const endPoint = document.getElementById("endPoint");
  const allowableForce = document.getElementById("allowableForce");
  const allowableMoment = document.getElementById("allowableMoment");
  const allowableAOverL = document.getElementById("allowableAOverL");
  const allowableBOverL = document.getElementById("allowableBOverL");
  const atlasGrid = document.getElementById("atlasGrid");
  const atlasAxes = document.getElementById("atlasAxes");
  const atlasFullCurve = document.getElementById("atlasFullCurve");
  const atlasAllowableCurve = document.getElementById("atlasAllowableCurve");
  const atlasSelectedPoint = document.getElementById("atlasSelectedPoint");
  const atlasPlot = document.getElementById("atlasPlot");
  const atlasReportGrid = document.getElementById("atlasReportGrid");
  const prbStageTabs = Array.from(document.querySelectorAll("[data-prb-mode]"));
  const prbPlot = document.getElementById("prbPlot");
  const prbGrid = document.getElementById("prbGrid");
  const prbAxes = document.getElementById("prbAxes");
  const prbSeries = document.getElementById("prbSeries");
  const prbAnnotations = document.getElementById("prbAnnotations");
  const prbLegend = document.getElementById("prbLegend");
  const prbStageKicker = document.getElementById("prbStageKicker");
  const prbStageTitle = document.getElementById("prbStageTitle");
  const prbStageLead = document.getElementById("prbStageLead");
  const prbStageSummary = document.getElementById("prbStageSummary");
  const prbParameterSource = document.getElementById("prbParameterSource");
  const prbFinalGammas = document.getElementById("prbFinalGammas");
  const prbFinalKbar = document.getElementById("prbFinalKbar");
  const prbKappaGrid = document.getElementById("prbKappaGrid");
  const prbStiffnessLabel = document.getElementById("prbStiffnessLabel");
  const prbOutputTabs = Array.from(document.querySelectorAll("[data-prb-output-mode]"));
  const prbOutputPlot = document.getElementById("prbOutputPlot");
  const prbOutputGrid = document.getElementById("prbOutputGrid");
  const prbOutputAxes = document.getElementById("prbOutputAxes");
  const prbOutputSeries = document.getElementById("prbOutputSeries");
  const prbOutputLabels = document.getElementById("prbOutputLabels");
  const prbOutputSummary = document.getElementById("prbOutputSummary");
  const mechanismPlot = document.getElementById("mechanismPlot");
  const mechanismGrid = document.getElementById("mechanismGrid");
  const mechanismAxes = document.getElementById("mechanismAxes");
  const mechanismYTrendPlot = document.getElementById("mechanismYTrendPlot");
  const mechanismYTrendGrid = document.getElementById("mechanismYTrendGrid");
  const mechanismYTrendAxes = document.getElementById("mechanismYTrendAxes");
  const mechanismYTrendFEA = document.getElementById("mechanismYTrendFEA");
  const mechanismYTrendPRB = document.getElementById("mechanismYTrendPRB");
  const mechanismYTrendCursor = document.getElementById("mechanismYTrendCursor");
  const mechanismYTrendPointFEA = document.getElementById("mechanismYTrendPointFEA");
  const mechanismYTrendPointPRB = document.getElementById("mechanismYTrendPointPRB");
  const mechanismXTrendPlot = document.getElementById("mechanismXTrendPlot");
  const mechanismXTrendGrid = document.getElementById("mechanismXTrendGrid");
  const mechanismXTrendAxes = document.getElementById("mechanismXTrendAxes");
  const mechanismXTrendFEA = document.getElementById("mechanismXTrendFEA");
  const mechanismXTrendPRB = document.getElementById("mechanismXTrendPRB");
  const mechanismXTrendCursor = document.getElementById("mechanismXTrendCursor");
  const mechanismXTrendPointFEA = document.getElementById("mechanismXTrendPointFEA");
  const mechanismXTrendPointPRB = document.getElementById("mechanismXTrendPointPRB");
  const mechanismFEACrank = document.getElementById("mechanismFEACrank");
  const mechanismFEACoupler = document.getElementById("mechanismFEACoupler");
  const mechanismFEAFlex = document.getElementById("mechanismFEAFlex");
  const mechanismPRBChain = document.getElementById("mechanismPRBChain");
  const mechanismBALink = document.getElementById("mechanismBALink");
  const mechanismAQLink = document.getElementById("mechanismAQLink");
  const mechanismOrigin = document.getElementById("mechanismOrigin");
  const mechanismBAnchor = document.getElementById("mechanismBAnchor");
  const mechanismFEAFlexNodes = document.getElementById("mechanismFEAFlexNodes");
  const mechanismJointPoints = document.getElementById("mechanismJointPoints");
  const mechanismQPoint = document.getElementById("mechanismQPoint");
  const mechanismAPoint = document.getElementById("mechanismAPoint");
  const mechanismCrankPoint = document.getElementById("mechanismCrankPoint");
  const mechanismAngleSlider = document.getElementById("mechanismAngleSlider");
  const mechanismAngleInput = document.getElementById("mechanismAngleInput");
  const mechanismShowFEA = document.getElementById("mechanismShowFEA");
  const mechanismShowPRB = document.getElementById("mechanismShowPRB");
  const mechanismAnimateButton = document.getElementById("mechanismAnimateButton");
  const mechanismParameterSource = document.getElementById("mechanismParameterSource");
  const mechanismGammas = document.getElementById("mechanismGammas");
  const mechanismKbar = document.getElementById("mechanismKbar");
  const mechanismFrameAngles = document.getElementById("mechanismFrameAngles");
  const mechanismThetas = document.getElementById("mechanismThetas");
  const mechanismTipSlope = document.getElementById("mechanismTipSlope");
  const mechanismQValue = document.getElementById("mechanismQValue");
  const mechanismAValue = document.getElementById("mechanismAValue");
  const mechanismErrors = document.getElementById("mechanismErrors");
  const mechanismLoadValue = document.getElementById("mechanismLoadValue");
  const materialsPlot = document.getElementById("materialsPlot");
  const materialsGrid = document.getElementById("materialsGrid");
  const materialsAxes = document.getElementById("materialsAxes");
  const materialsStatic = document.getElementById("materialsStatic");
  const materialsDynamic = document.getElementById("materialsDynamic");
  const materialsYTrendPlot = document.getElementById("materialsYTrendPlot");
  const materialsYTrendGrid = document.getElementById("materialsYTrendGrid");
  const materialsYTrendAxes = document.getElementById("materialsYTrendAxes");
  const materialsYTrendTarget = document.getElementById("materialsYTrendTarget");
  const materialsYTrendActual = document.getElementById("materialsYTrendActual");
  const materialsYTrendCursor = document.getElementById("materialsYTrendCursor");
  const materialsYTrendPointTarget = document.getElementById("materialsYTrendPointTarget");
  const materialsYTrendPointActual = document.getElementById("materialsYTrendPointActual");
  const materialsThetaTrendPlot = document.getElementById("materialsThetaTrendPlot");
  const materialsThetaTrendGrid = document.getElementById("materialsThetaTrendGrid");
  const materialsThetaTrendAxes = document.getElementById("materialsThetaTrendAxes");
  const materialsThetaTrendTarget = document.getElementById("materialsThetaTrendTarget");
  const materialsThetaTrendActual = document.getElementById("materialsThetaTrendActual");
  const materialsThetaTrendCursor = document.getElementById("materialsThetaTrendCursor");
  const materialsThetaTrendPointTarget = document.getElementById("materialsThetaTrendPointTarget");
  const materialsThetaTrendPointActual = document.getElementById("materialsThetaTrendPointActual");
  const materialsMomentTrendPlot = document.getElementById("materialsMomentTrendPlot");
  const materialsMomentTrendGrid = document.getElementById("materialsMomentTrendGrid");
  const materialsMomentTrendAxes = document.getElementById("materialsMomentTrendAxes");
  const materialsMomentTrendLine = document.getElementById("materialsMomentTrendLine");
  const materialsMomentTrendCursor = document.getElementById("materialsMomentTrendCursor");
  const materialsMomentTrendPoint = document.getElementById("materialsMomentTrendPoint");
  const materialsMomentValue = document.getElementById("materialsMomentValue");
  const materialsExperimentTitle = document.getElementById("materialsExperimentTitle");
  const materialsSliderLabel = document.getElementById("materialsSliderLabel");
  const materialsFrameSlider = document.getElementById("materialsFrameSlider");
  const materialsFrameValue = document.getElementById("materialsFrameValue");
  const materialsAnimateButton = document.getElementById("materialsAnimateButton");
  const materialsMotionTimeInput = document.getElementById("materialsMotionTimeInput");
  const materialsAmplitudeInput = document.getElementById("materialsAmplitudeInput");
  const materialsLengthInput = document.getElementById("materialsLengthInput");
  const materialsThicknessInput = document.getElementById("materialsThicknessInput");
  const materialsWidthInput = document.getElementById("materialsWidthInput");
  const materialsYoungsModulusInput = document.getElementById("materialsYoungsModulusInput");
  const materialsYieldStrengthInput = document.getElementById("materialsYieldStrengthInput");
  const materialsPresetButtons = Array.from(document.querySelectorAll("[data-material-preset]"));
  const materialsPresetNote = document.getElementById("materialsPresetNote");
  const materialsGammas = document.getElementById("materialsGammas");
  const materialsKbar = document.getElementById("materialsKbar");
  const materialsTargetXY = document.getElementById("materialsTargetXY");
  const materialsThetaTip = document.getElementById("materialsThetaTip");
  const materialsThetas = document.getElementById("materialsThetas");
  const materialsTau = document.getElementById("materialsTau");
  const materialsForceMoment = document.getElementById("materialsForceMoment");
  const materialsTrackingError = document.getElementById("materialsTrackingError");
  const materialsTraceSpan = document.getElementById("materialsTraceSpan");
  let atlasRequestController = null;
  let atlasRequestTimer = null;
  let allowableLoadRequestTimer = null;
  let activeAtlasMode = "interactive";
  let reportAtlasCache = null;
  let allowableLoadRequestController = null;
  let activeDetailMode = "theta";
  let activePrbMode = "search";
  let activePrbOutputMode = "figure12";
  let activePrbViewMode = "stage";
  let prbWorkspaceData = null;
  let prbLoaded = false;
  let mechanismOverlayData = null;
  let mechanismLoaded = false;
  let mechanismBounds = null;
  let mechanismCurrentFrameIndex = 0;
  let mechanismAnimationTimer = null;
  let mechanismTrendBounds = null;
  let mechanismFEAFlexNodePool = [];
  let mechanismJointPointPool = [];
  let materialsPanelInitialized = false;
  let materialsExperimentCache = null;
  let materialsExperimentCacheKey = "";
  let materialsMotionData = null;
  let materialsBounds = null;
  let materialsCurrentFrameIndex = 0;
  let materialsAnimationTimer = null;
  let materialsTrendBounds = null;
  let materialsReloadTimer = null;
  let materialsRequestSequence = 0;
  let activeMaterialPresetKey = "";
  let materialsTargetTracePath = null;
  let materialsActualTracePath = null;
  let materialsChainPath = null;
  let materialsJointPool = [];
  let materialsTargetPoint = null;
  let materialsTipPoint = null;
  let activeZoomTarget = null;

  function createSvgNode(tagName, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tagName);
    Object.entries(attrs).forEach(([key, value]) => {
      node.setAttribute(key, String(value));
    });
    return node;
  }

  function ensureCirclePool(container, pool, count, attrsFactory) {
    while (pool.length < count) {
      const node = createSvgNode("circle", attrsFactory());
      container.appendChild(node);
      pool.push(node);
    }
    pool.forEach((node, index) => {
      node.style.display = index < count ? "" : "none";
    });
  }

  function clamp(value, minValue, maxValue) {
    return Math.min(maxValue, Math.max(minValue, value));
  }

  function snapToStep(value, minValue, step) {
    return minValue + Math.round((value - minValue) / step) * step;
  }

  function formatControlValue(controlKey, value) {
    return controlKey === "kappa" ? value.toFixed(2) : value.toFixed(1);
  }

  function formatThetaValue(value) {
    return value.toFixed(1);
  }

  function radiansToDegrees(value) {
    return Number(value) * 180 / Math.PI;
  }

  function formatDegrees(value, digits = 2) {
    return `${Number(value).toFixed(digits)}\u00b0`;
  }

  function wrapAngleDegrees(value) {
    const wrappedValue = Number(value) % 360;
    return wrappedValue < 0 ? wrappedValue + 360 : wrappedValue;
  }

  function computePositionMagnitude(point) {
    return Math.hypot(Number(point[0]), Number(point[1]));
  }

  function computeFeaTipAngleDegrees(flexPoints) {
    if (!Array.isArray(flexPoints) || flexPoints.length < 2) {
      return 0;
    }
    const previousPoint = flexPoints[flexPoints.length - 2];
    const tipPoint = flexPoints[flexPoints.length - 1];
    return radiansToDegrees(
      Math.atan2(
        Number(tipPoint[1]) - Number(previousPoint[1]),
        Number(tipPoint[0]) - Number(previousPoint[0]),
      ),
    );
  }

  function angleDistanceDegrees(leftValue, rightValue) {
    const wrappedDelta = Math.abs(wrapAngleDegrees(leftValue) - wrapAngleDegrees(rightValue));
    return Math.min(wrappedDelta, 360 - wrappedDelta);
  }

  function applyUiNotationLabels() {
    const setText = (selector, text) => {
      const node = document.querySelector(selector);
      if (node) {
        node.textContent = text;
      }
    };

    setText('label[for="phiSlider"] .control-label-row span:first-child', 'Phi (°)');
    setText('#panel-atlas [data-detail-panel="theta"] .summary-row:nth-of-type(1) dt', 'θ0 max');
    setText('#panel-atlas [data-detail-panel="theta"] .summary-row:nth-of-type(2) dt', 'θ0 selected');
    setText('label[for="thetaAllowableSlider"] .control-label-row span:first-child', 'θ0 (°)');
    setText('#atlasReportView .summary-row:nth-of-type(2) dd', '9° to 171°');
    setText('#panel-mechanism .mechanism-trend-card:nth-of-type(2) h3', 'θ0 vs crank angle');
    setText('#panel-mechanism .mechanism-summary-list .summary-row:nth-of-type(3) dt', 'θ1 / θ2 / θ3');
    setText('#panel-materials .summary-row:nth-of-type(4) dt', 'θ0 desired / actual');
    setText('#panel-materials .summary-row:nth-of-type(5) dt', 'θ1 / θ2 / θ3');
    setText('#panel-materials .summary-row:nth-of-type(6) dt', 'τ1 / τ2 / τ3');

    if (mechanismXTrendPlot) {
      mechanismXTrendPlot.setAttribute('aria-label', 'Tip angle θ0 over crank angle for FEA and PRB');
    }
    if (materialsThetaTrendPlot) {
      materialsThetaTrendPlot.setAttribute('aria-label', 'Medical θ0 over time');
    }
  }

  function setPlotZoomState(target, isZoomed) {
    if (!target) {
      return;
    }
    target.classList.toggle("plot-zoomed", isZoomed);
    const button = target.querySelector(".plot-zoom-button");
    if (button) {
      const label = target.dataset.zoomLabel || "graph";
      button.textContent = isZoomed ? "Close" : "Zoom";
      button.setAttribute("aria-label", `${isZoomed ? "Close" : "Zoom"} ${label}`);
    }
  }

  function closeActivePlotZoom() {
    if (!activeZoomTarget) {
      return;
    }
    setPlotZoomState(activeZoomTarget, false);
    activeZoomTarget = null;
    document.body.classList.remove("plot-zoom-open");
  }

  function togglePlotZoom(target) {
    if (!target) {
      return;
    }
    const shouldOpen = !target.classList.contains("plot-zoomed");
    if (activeZoomTarget && activeZoomTarget !== target) {
      setPlotZoomState(activeZoomTarget, false);
    }
    activeZoomTarget = shouldOpen ? target : null;
    setPlotZoomState(target, shouldOpen);
    document.body.classList.toggle("plot-zoom-open", shouldOpen);
  }

  function ensurePlotZoomControls(root = document) {
    const zoomTargets = root.querySelectorAll(
      ".atlas-svg-wrap, .prb-svg-wrap, .mechanism-svg-wrap, .mechanism-trend-wrap, .materials-svg-wrap, .materials-trend-wrap, .report-panel",
    );

    zoomTargets.forEach((target) => {
      if (target.dataset.zoomReady === "true") {
        return;
      }

      const labelSource = target.querySelector("svg[aria-label]") || target.querySelector(".report-panel-title");
      const zoomLabel = labelSource?.getAttribute?.("aria-label") || labelSource?.textContent?.trim() || "graph";

      target.dataset.zoomReady = "true";
      target.dataset.zoomLabel = zoomLabel;
      target.classList.add("plot-zoom-target");

      const button = document.createElement("button");
      button.type = "button";
      button.className = "plot-zoom-button";
      button.textContent = "Zoom";
      button.setAttribute("aria-label", `Zoom ${zoomLabel}`);
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        togglePlotZoom(target);
      });
      target.appendChild(button);
    });
  }

  function getPositiveNumber(inputElement, fallbackValue) {
    if (!inputElement) {
      return fallbackValue;
    }
    const value = Number(inputElement.value);
    return Number.isFinite(value) && value > 0 ? value : fallbackValue;
  }

  function getBeamParameters() {
    return {
      beam_length: getPositiveNumber(beamLengthInput, 0.1),
      beam_width: getPositiveNumber(beamWidthInput, 0.02),
      thickness: getPositiveNumber(thicknessInput, 0.001),
      youngs_modulus_mpa: getPositiveNumber(youngsModulusInput, 69000),
      sigma_max_mpa: getPositiveNumber(sigmaMaxInput, 276),
    };
  }

  function getMedicalMotionParameters() {
    return {
      core_motion_time: getPositiveNumber(materialsMotionTimeInput, 8.0),
      tip_amplitude: getPositiveNumber(materialsAmplitudeInput, 0.10),
    };
  }

  function getMedicalBeamParameters() {
    return {
      beam_length: getPositiveNumber(materialsLengthInput, 0.1),
      beam_width: getPositiveNumber(materialsWidthInput, 0.02),
      thickness: getPositiveNumber(materialsThicknessInput, 0.001),
      youngs_modulus_mpa: getPositiveNumber(materialsYoungsModulusInput, 69000),
      sigma_max_mpa: getPositiveNumber(materialsYieldStrengthInput, 276),
    };
  }

  function buildBeamQuery() {
    const beam = getBeamParameters();
    return [
      `beam_length=${encodeURIComponent(beam.beam_length)}`,
      `beam_width=${encodeURIComponent(beam.beam_width)}`,
      `thickness=${encodeURIComponent(beam.thickness)}`,
      `youngs_modulus=${encodeURIComponent(beam.youngs_modulus_mpa * 1e6)}`,
      `sigma_max=${encodeURIComponent(beam.sigma_max_mpa * 1e6)}`,
    ].join("&");
  }

  function buildMedicalExperimentEndpoint() {
    const motion = getMedicalMotionParameters();
    const beam = getMedicalBeamParameters();
    const params = [
      `tip_amplitude=${encodeURIComponent(motion.tip_amplitude)}`,
      `core_motion_time=${encodeURIComponent(motion.core_motion_time)}`,
      `beam_length=${encodeURIComponent(beam.beam_length)}`,
      `beam_width=${encodeURIComponent(beam.beam_width)}`,
      `thickness=${encodeURIComponent(beam.thickness)}`,
      `youngs_modulus=${encodeURIComponent(beam.youngs_modulus_mpa * 1e6)}`,
      `sigma_max=${encodeURIComponent(beam.sigma_max_mpa * 1e6)}`,
    ].join("&");
    return `${MATERIALS_CONFIG.endpoint}&${params}`;
  }

  function setMaterialsPresetNote(message) {
    if (materialsPresetNote) {
      materialsPresetNote.textContent = message;
    }
  }

  function getMaterialsPresetStatus(presetKey, options = {}) {
    const preset = MATERIAL_PRESETS[presetKey];
    const suffix = options.loading ? " (loading...)" : "";
    if (preset) {
      return `Preset active: ${preset.displayName}${suffix}`;
    }
    return options.loading ? "No preset active (loading...)" : "No preset active.";
  }

  function updateMaterialsPresetButtons() {
    materialsPresetButtons.forEach((button) => {
      const isActive = button.dataset.materialPreset === activeMaterialPresetKey;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function applyMaterialPreset(presetKey) {
    const preset = MATERIAL_PRESETS[presetKey];
    if (!preset) {
      return;
    }

    activeMaterialPresetKey = presetKey;
    updateMaterialsPresetButtons();

    if (materialsYoungsModulusInput && Number.isFinite(preset.elasticModulusMpa)) {
      materialsYoungsModulusInput.value = Number(preset.elasticModulusMpa).toFixed(1);
    }
    if (materialsYieldStrengthInput && Number.isFinite(preset.strengthMpa)) {
      materialsYieldStrengthInput.value = Number(preset.strengthMpa).toFixed(1);
    }

    setMaterialsPresetNote(getMaterialsPresetStatus(presetKey));
    stopMaterialsAnimation();
    scheduleMaterialsReload();
  }

  function scheduleAtlasUpdate() {
    clearTimeout(atlasRequestTimer);
    atlasRequestTimer = window.setTimeout(updateAtlasPanel, 100);
  }

  function setControlValue(controlKey, value, options = {}) {
    const emitUpdate = options.emitUpdate !== false;
    const slider = controlKey === "kappa" ? kappaSlider : phiSlider;
    const input = controlKey === "kappa" ? kappaInput : phiInput;
    if (!slider || !input) return;

    const minValue = Number(slider.min);
    const maxValue = Number(slider.max);
    const stepValue = Number(slider.step || 1);
    const normalizedValue = snapToStep(clamp(value, minValue, maxValue), minValue, stepValue);

    slider.value = String(normalizedValue);
    input.value = formatControlValue(controlKey, normalizedValue);

    if (emitUpdate) {
      scheduleAtlasUpdate();
    }
  }

  function bindSliderAndInput(controlKey) {
    const slider = controlKey === "kappa" ? kappaSlider : phiSlider;
    const input = controlKey === "kappa" ? kappaInput : phiInput;
    if (!slider || !input) return;

    slider.addEventListener("input", () => {
      setControlValue(controlKey, Number(slider.value));
    });

    input.addEventListener("input", () => {
      const typedValue = Number(input.value);
      if (!Number.isFinite(typedValue)) {
        return;
      }
      setControlValue(controlKey, typedValue);
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        input.blur();
      }
    });

    input.addEventListener("blur", () => {
      const typedValue = Number(input.value);
      const fallbackValue = Number(slider.value);
      setControlValue(controlKey, Number.isFinite(typedValue) ? typedValue : fallbackValue, { emitUpdate: false });
    });
  }

  function bindAllowableThetaControls() {
    if (!thetaAllowableSlider || !thetaAllowableInput) return;

    thetaAllowableSlider.addEventListener("input", () => {
      thetaAllowableInput.value = formatThetaValue(Number(thetaAllowableSlider.value));
      scheduleAllowableLoadsUpdate();
    });

    thetaAllowableInput.addEventListener("input", () => {
      const typedValue = Number(thetaAllowableInput.value);
      if (!Number.isFinite(typedValue)) {
        return;
      }
      const minValue = Number(thetaAllowableSlider.min);
      const maxValue = Number(thetaAllowableSlider.max);
      const stepValue = Number(thetaAllowableSlider.step || 0.1);
      const normalizedValue = snapToStep(clamp(typedValue, minValue, maxValue), minValue, stepValue);
      thetaAllowableSlider.value = String(normalizedValue);
      thetaAllowableInput.value = formatThetaValue(normalizedValue);
      scheduleAllowableLoadsUpdate();
    });
  }

  function bindBeamInputs() {
    [
      beamLengthInput,
      beamWidthInput,
      thicknessInput,
      youngsModulusInput,
      sigmaMaxInput,
    ].forEach((inputElement) => {
      if (!inputElement) {
        return;
      }
      inputElement.addEventListener("input", () => {
        scheduleAtlasUpdate();
      });
    });
  }

  function scheduleAllowableLoadsUpdate() {
    if (activeAtlasMode !== "interactive") {
      return;
    }
    clearTimeout(allowableLoadRequestTimer);
    allowableLoadRequestTimer = window.setTimeout(updateAllowableLoadsPanel, 100);
  }

  function mapPlotX(value) {
    const width = atlasPlot.viewBox.baseVal.width;
    const usableWidth = width - ATLAS_CONFIG.marginLeft - ATLAS_CONFIG.marginRight;
    const ratio = (value - ATLAS_CONFIG.xMin) / (ATLAS_CONFIG.xMax - ATLAS_CONFIG.xMin);
    return ATLAS_CONFIG.marginLeft + ratio * usableWidth;
  }

  function mapPlotY(value) {
    const height = atlasPlot.viewBox.baseVal.height;
    const usableHeight = height - ATLAS_CONFIG.marginTop - ATLAS_CONFIG.marginBottom;
    const ratio = (value - ATLAS_CONFIG.yMin) / (ATLAS_CONFIG.yMax - ATLAS_CONFIG.yMin);
    return height - ATLAS_CONFIG.marginBottom - ratio * usableHeight;
  }

  function buildTickValues(minValue, maxValue, step) {
    const ticks = [];
    const start = Math.ceil(minValue / step) * step;
    const count = Math.round((maxValue - start) / step);

    for (let i = 0; i <= count; i += 1) {
      const value = start + i * step;
      if (value >= minValue - 1e-9 && value <= maxValue + 1e-9) {
        ticks.push(Number(value.toFixed(10)));
      }
    }

    return ticks;
  }

  function chooseNiceStep(spanValue) {
    if (!(spanValue > 0)) {
      return 0.2;
    }
    const roughStep = spanValue / 6;
    const magnitude = 10 ** Math.floor(Math.log10(roughStep));
    const normalizedStep = roughStep / magnitude;
    let niceNormalizedStep = 1;
    if (normalizedStep > 5) {
      niceNormalizedStep = 10;
    } else if (normalizedStep > 2) {
      niceNormalizedStep = 5;
    } else if (normalizedStep > 1) {
      niceNormalizedStep = 2;
    }
    return niceNormalizedStep * magnitude;
  }

  function isAbortError(error) {
    return error && (error.name === "AbortError" || error.message === "The operation was aborted.");
  }

  function getStaticSnapshotPath(endpoint) {
    try {
      const url = new URL(endpoint, window.location.href);
      const path = url.pathname;
      const params = url.searchParams;

      if (path === "/api/section4-workspace") {
        return STATIC_DATA_PATHS.section4Workspace;
      }
      if (path === "/api/section520-overlay") {
        return STATIC_DATA_PATHS.section520Overlay;
      }
      if (path === "/api/atlas-report") {
        return STATIC_DATA_PATHS.atlasReport;
      }
      if (path === "/api/atlas") {
        const isDefault =
          Number(params.get("kappa")) === 0
          && Number(params.get("phi_deg")) === 90
          && Number(params.get("beam_length")) === 0.1
          && Number(params.get("beam_width")) === 0.02
          && Number(params.get("thickness")) === 0.001
          && Number(params.get("youngs_modulus")) === 69000000000
          && Number(params.get("sigma_max")) === 276000000;
        if (isDefault) {
          return STATIC_DATA_PATHS.atlasDefault;
        }
      }
      if (path === "/api/atlas-loads") {
        const isDefault =
          Number(params.get("kappa")) === 0
          && Number(params.get("phi_deg")) === 90
          && Number(params.get("theta0_deg")) === 0
          && Number(params.get("beam_length")) === 0.1
          && Number(params.get("beam_width")) === 0.02
          && Number(params.get("thickness")) === 0.001
          && Number(params.get("youngs_modulus")) === 69000000000
          && Number(params.get("sigma_max")) === 276000000;
        if (isDefault) {
          return STATIC_DATA_PATHS.atlasLoadsDefault;
        }
      }
      if (path === "/api/medical-experiment") {
        const isDefault =
          params.get("mode") === "sinusoid"
          && Number(params.get("tip_amplitude")) === 0.1
          && Number(params.get("core_motion_time")) === 8
          && Number(params.get("beam_length")) === 0.1
          && Number(params.get("beam_width")) === 0.02
          && Number(params.get("thickness")) === 0.001
          && Number(params.get("youngs_modulus")) === 69000000000
          && Number(params.get("sigma_max")) === 276000000;
        if (isDefault) {
          return STATIC_DATA_PATHS.medicalDefault;
        }
        const isPebax =
          params.get("mode") === "sinusoid"
          && Number(params.get("tip_amplitude")) === 0.1
          && Number(params.get("core_motion_time")) === 8
          && Number(params.get("beam_length")) === 0.1
          && Number(params.get("beam_width")) === 0.02
          && Number(params.get("thickness")) === 0.001
          && Number(params.get("youngs_modulus")) === 513000000
          && Number(params.get("sigma_max")) === 56000000;
        if (isPebax) {
          return STATIC_DATA_PATHS.medicalPebax;
        }
        const isTpu =
          params.get("mode") === "sinusoid"
          && Number(params.get("tip_amplitude")) === 0.1
          && Number(params.get("core_motion_time")) === 8
          && Number(params.get("beam_length")) === 0.1
          && Number(params.get("beam_width")) === 0.02
          && Number(params.get("thickness")) === 0.001
          && Number(params.get("youngs_modulus")) === 22100000
          && Number(params.get("sigma_max")) === 53100000;
        if (isTpu) {
          return STATIC_DATA_PATHS.medicalTpu;
        }
      }
    } catch (error) {
      console.warn("Unable to parse endpoint for static snapshot lookup.", endpoint, error);
    }

    return null;
  }

  async function requestJson(endpoint, options = {}) {
    const staticSnapshotPath = getStaticSnapshotPath(endpoint);
    if (staticSnapshotPath) {
      const response = await fetch(staticSnapshotPath, options);
      if (!response.ok) {
        throw new Error(`Unable to load static snapshot: ${staticSnapshotPath}`);
      }
      return response.json();
    }

    if (window.StaticPyBackend && typeof window.StaticPyBackend.request === "function") {
      try {
        return await window.StaticPyBackend.request(endpoint, options);
      } catch (error) {
        if (isAbortError(error)) {
          throw error;
        }
        console.warn("Falling back to HTTP fetch for endpoint", endpoint, error);
      }
    }

    const response = await fetch(endpoint, options);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `Request failed for ${endpoint}`);
    }
    return data;
  }

  function renderSummaryRows(container, rows) {
    if (!container) {
      return;
    }
    container.replaceChildren();
    rows.forEach(([label, value]) => {
      const row = document.createElement("div");
      row.className = "summary-row";
      const term = document.createElement("dt");
      term.textContent = label;
      const detail = document.createElement("dd");
      detail.textContent = value;
      row.append(term, detail);
      container.appendChild(row);
    });
  }

  function drawAtlasFrame() {
    if (!atlasGrid || !atlasAxes || !atlasPlot) return;

    atlasGrid.replaceChildren();
    atlasAxes.replaceChildren();

    const xTicks = buildTickValues(ATLAS_CONFIG.xMin, ATLAS_CONFIG.xMax, ATLAS_CONFIG.gridStep);
    const yTicks = buildTickValues(ATLAS_CONFIG.yMin, ATLAS_CONFIG.yMax, ATLAS_CONFIG.gridStep);
    const width = atlasPlot.viewBox.baseVal.width;
    const height = atlasPlot.viewBox.baseVal.height;
    const left = ATLAS_CONFIG.marginLeft;
    const right = width - ATLAS_CONFIG.marginRight;
    const top = ATLAS_CONFIG.marginTop;
    const bottom = height - ATLAS_CONFIG.marginBottom;
    const axisX = mapPlotX(0);
    const axisY = mapPlotY(0);

    xTicks.forEach((tick) => {
      const x = mapPlotX(tick);
      atlasGrid.appendChild(createSvgNode("line", {
        x1: x, y1: top, x2: x, y2: bottom, class: "atlas-grid-line",
      }));
      atlasAxes.appendChild(createSvgNode("text", {
        x, y: bottom + 24, "text-anchor": "middle", class: "atlas-tick-label",
      })).textContent = tick.toFixed(1);
    });

    yTicks.forEach((tick) => {
      const y = mapPlotY(tick);
      atlasGrid.appendChild(createSvgNode("line", {
        x1: left, y1: y, x2: right, y2: y, class: "atlas-grid-line",
      }));
      atlasAxes.appendChild(createSvgNode("text", {
        x: left - 14, y: y + 4, "text-anchor": "end", class: "atlas-tick-label",
      })).textContent = tick.toFixed(2);
    });

    atlasAxes.appendChild(createSvgNode("line", {
      x1: left, y1: axisY, x2: right, y2: axisY, class: "atlas-axis-line",
    }));
    atlasAxes.appendChild(createSvgNode("line", {
      x1: axisX, y1: top, x2: axisX, y2: bottom, class: "atlas-axis-line",
    }));

    atlasAxes.appendChild(createSvgNode("text", {
      x: right - 8, y: axisY - 10, "text-anchor": "end", class: "atlas-axis-label",
    })).textContent = "a / L";

    const yLabel = createSvgNode("text", {
      x: axisX + 18, y: top + 18, class: "atlas-axis-label",
      transform: `rotate(-90 ${axisX + 18} ${top + 18})`,
      "text-anchor": "middle",
    });
    yLabel.textContent = "b / L";
    atlasAxes.appendChild(yLabel);
  }

  function buildPath(aValues, bValues) {
    return aValues.map((value, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${mapPlotX(value).toFixed(2)} ${mapPlotY(bValues[index]).toFixed(2)}`;
    }).join(" ");
  }

  function buildReportPanelSvg(panelData) {
    const width = 320;
    const height = 220;
    const marginLeft = 22;
    const marginRight = 6;
    const marginTop = 10;
    const marginBottom = 22;
    const xMin = -0.55;
    const xMax = 1.05;
    const yMin = 0.0;
    const yMax = 1.05;
    const xTicks = [-0.5, 0.0, 0.5, 1.0];
    const yTicks = [0.0, 0.5, 1.0];
    const usableWidth = width - marginLeft - marginRight;
    const usableHeight = height - marginTop - marginBottom;
    const mapX = (value) => marginLeft + ((value - xMin) / (xMax - xMin)) * usableWidth;
    const mapY = (value) => height - marginBottom - ((value - yMin) / (yMax - yMin)) * usableHeight;
    const axisX = mapX(0);
    const axisY = mapY(0);

    const wrapper = document.createElement("article");
    wrapper.className = "report-panel";

    const title = document.createElement("p");
    title.className = "report-panel-title";
    title.textContent = `kappa = ${Number(panelData.kappa).toString()}`;
    wrapper.appendChild(title);

    const svg = createSvgNode("svg", {
      class: "report-panel-svg",
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-label": `Report atlas panel for kappa ${panelData.kappa}`,
    });

    xTicks.forEach((tick) => {
      const x = mapX(tick);
      svg.appendChild(createSvgNode("line", {
        x1: x, y1: marginTop, x2: x, y2: height - marginBottom, class: "report-grid-line",
      }));
      const label = createSvgNode("text", {
        x, y: height - 6, "text-anchor": "middle", class: "report-tick-label",
      });
      label.textContent = tick.toFixed(1);
      svg.appendChild(label);
    });

    yTicks.forEach((tick) => {
      const y = mapY(tick);
      svg.appendChild(createSvgNode("line", {
        x1: marginLeft, y1: y, x2: width - marginRight, y2: y, class: "report-grid-line",
      }));
      const label = createSvgNode("text", {
        x: marginLeft - 8, y: y + 3, "text-anchor": "end", class: "report-tick-label",
      });
      label.textContent = tick.toFixed(1);
      svg.appendChild(label);
    });

    svg.appendChild(createSvgNode("line", {
      x1: marginLeft, y1: axisY, x2: width - marginRight, y2: axisY, class: "report-axis-line",
    }));
    svg.appendChild(createSvgNode("line", {
      x1: axisX, y1: marginTop, x2: axisX, y2: height - marginBottom, class: "report-axis-line",
    }));

    panelData.curves.forEach((curveData, index) => {
      const d = curveData.a_over_l.map((value, pointIndex) => {
        const command = pointIndex === 0 ? "M" : "L";
        return `${command} ${mapX(value).toFixed(2)} ${mapY(curveData.b_over_l[pointIndex]).toFixed(2)}`;
      }).join(" ");
      svg.appendChild(createSvgNode("path", {
        d,
        class: "report-curve",
        stroke: REPORT_COLORS[index % REPORT_COLORS.length],
      }));
    });

    const xLabel = createSvgNode("text", {
      x: width - 14,
      y: axisY - 6,
      "text-anchor": "end",
      class: "report-axis-label",
    });
    xLabel.textContent = "a / L";
    svg.appendChild(xLabel);

    const yLabel = createSvgNode("text", {
      x: axisX + 12,
      y: marginTop + 12,
      "text-anchor": "middle",
      class: "report-axis-label",
      transform: `rotate(-90 ${axisX + 12} ${marginTop + 12})`,
    });
    yLabel.textContent = "b / L";
    svg.appendChild(yLabel);

    wrapper.appendChild(svg);
    return wrapper;
  }

  function renderReportAtlas(reportData) {
    if (!atlasReportGrid) return;
    atlasReportGrid.replaceChildren();
    reportData.panels.forEach((panelData) => {
      atlasReportGrid.appendChild(buildReportPanelSvg(panelData));
    });
    ensurePlotZoomControls(atlasReportGrid);
  }

  function setDetailMode(modeKey) {
    activeDetailMode = modeKey;
    atlasDetailTabs.forEach((button) => {
      const isActive = button.dataset.detailMode === modeKey;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    atlasDetailPanels.forEach((panel) => {
      panel.classList.toggle("active", panel.dataset.detailPanel === modeKey);
    });
  }

  function loadReportAtlas() {
    if (reportAtlasCache) {
      renderReportAtlas(reportAtlasCache);
      return Promise.resolve();
    }

    return requestJson(ATLAS_CONFIG.reportEndpoint)
      .then((data) => {
        reportAtlasCache = data;
        renderReportAtlas(reportAtlasCache);
      })
      .catch((error) => {
        if (atlasReportGrid) {
          atlasReportGrid.replaceChildren();
          const errorCard = document.createElement("article");
          errorCard.className = "report-panel";
          errorCard.textContent = "Unable to load report atlas.";
          atlasReportGrid.appendChild(errorCard);
          ensurePlotZoomControls(atlasReportGrid);
        }
        console.error(error);
      });
  }

  function setAtlasMode(modeKey) {
    activeAtlasMode = modeKey;

    atlasModeTabs.forEach((button) => {
      const isActive = button.dataset.atlasMode === modeKey;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    atlasModePanels.forEach((panel) => {
      panel.classList.toggle("active", panel.dataset.atlasModePanel === modeKey);
    });

    atlasViewPanels.forEach((panel) => {
      panel.classList.toggle("active", panel.dataset.atlasView === modeKey);
    });

    if (modeKey === "report") {
      loadReportAtlas();
    }
  }

  function updateAtlasPanel() {
    if (!kappaSlider || !phiSlider || !atlasAllowableCurve || !atlasFullCurve || activeAtlasMode !== "interactive") return;

    const kappa = Number(kappaSlider.value);
    const phiDeg = Number(phiSlider.value);
    if (kappaInput) {
      kappaInput.value = formatControlValue("kappa", kappa);
    }
    if (phiInput) {
      phiInput.value = formatControlValue("phi", phiDeg);
    }

    if (atlasRequestController) {
      atlasRequestController.abort();
    }
    atlasRequestController = new AbortController();

    const endpoint =
      `${ATLAS_CONFIG.endpoint}?kappa=${encodeURIComponent(kappa)}&phi_deg=${encodeURIComponent(phiDeg)}`
      + `&${buildBeamQuery()}`;

    requestJson(endpoint, { signal: atlasRequestController.signal })
      .then((data) => {
        const fullAValues = data.geometric_a_over_l;
        const fullBValues = data.geometric_b_over_l;
        const allowableAValues = data.allowable_a_over_l;
        const allowableBValues = data.allowable_b_over_l;
        const startA = data.start_point[0];
        const startB = data.start_point[1];
        const endA = data.end_point[0];
        const endB = data.end_point[1];

        const thetaMaxDeg = Number(
          data.theta0_max_deg !== undefined ? data.theta0_max_deg : radiansToDegrees(data.theta0_max_rad),
        );
        thetaMaxRad.textContent = formatDegrees(thetaMaxDeg);
        startPoint.textContent = `(${startA.toFixed(3)}, ${startB.toFixed(3)})`;
        endPoint.textContent = `(${endA.toFixed(3)}, ${endB.toFixed(3)})`;

        atlasFullCurve.setAttribute("d", buildPath(fullAValues, fullBValues));
        atlasAllowableCurve.setAttribute("d", buildPath(allowableAValues, allowableBValues));
        updateAllowableLoadsPanel();
      })
      .catch((error) => {
        if (isAbortError(error)) {
          return;
        }
        thetaMaxRad.textContent = "Unavailable";
        if (thetaSelectedDeg) {
          thetaSelectedDeg.textContent = "Unavailable";
        }
        startPoint.textContent = "(error)";
        endPoint.textContent = "(error)";
        atlasFullCurve.setAttribute("d", "");
        atlasAllowableCurve.setAttribute("d", "");
        console.error(error);
      });
  }

  function updateAllowableLoadsPanel() {
    if (
      !thetaAllowableSlider || !thetaAllowableInput || !allowableForce || !allowableMoment
      || activeAtlasMode !== "interactive"
    ) {
      return;
    }

    const kappa = Number(kappaSlider.value);
    const phiDeg = Number(phiSlider.value);
    const theta0Deg = Number(thetaAllowableSlider.value);

    if (allowableLoadRequestController) {
      allowableLoadRequestController.abort();
    }
    allowableLoadRequestController = new AbortController();

    const endpoint =
      `/api/atlas-loads?kappa=${encodeURIComponent(kappa)}&phi_deg=${encodeURIComponent(phiDeg)}`
      + `&theta0_deg=${encodeURIComponent(theta0Deg)}&${buildBeamQuery()}`;

    requestJson(endpoint, { signal: allowableLoadRequestController.signal })
      .then((data) => {
        const thetaMax = Number(data.limits.theta0_limit_deg);
        thetaAllowableSlider.max = thetaMax.toFixed(1);
        thetaAllowableInput.max = thetaMax.toFixed(1);

        const currentTheta = Math.min(Number(data.state.theta0_deg), thetaMax);
        thetaAllowableSlider.value = currentTheta.toFixed(1);
        thetaAllowableInput.value = currentTheta.toFixed(1);

        allowableForce.textContent = `${Number(data.state.force).toFixed(3)} N`;
        allowableMoment.textContent = `${Number(data.state.moment).toFixed(4)} N*m`;
        allowableAOverL.textContent = Number(data.state.a_over_l).toFixed(3);
        allowableBOverL.textContent = Number(data.state.b_over_l).toFixed(3);
        if (thetaSelectedDeg) {
          thetaSelectedDeg.textContent = formatDegrees(Number(data.state.theta0_deg));
        }
        endPoint.textContent = `(${Number(data.state.a_over_l).toFixed(3)}, ${Number(data.state.b_over_l).toFixed(3)})`;
        if (atlasSelectedPoint) {
          atlasSelectedPoint.setAttribute("cx", mapPlotX(Number(data.state.a_over_l)));
          atlasSelectedPoint.setAttribute("cy", mapPlotY(Number(data.state.b_over_l)));
        }
      })
      .catch((error) => {
        if (isAbortError(error)) {
          return;
        }
        allowableForce.textContent = "Unavailable";
        allowableMoment.textContent = "Unavailable";
        if (thetaSelectedDeg) {
          thetaSelectedDeg.textContent = "Unavailable";
        }
        endPoint.textContent = "(error)";
        if (atlasSelectedPoint) {
          atlasSelectedPoint.setAttribute("cx", "-100");
          atlasSelectedPoint.setAttribute("cy", "-100");
        }
        console.error(error);
      });
  }

  function formatPair(point) {
    return `(${Number(point[0]).toFixed(3)}, ${Number(point[1]).toFixed(3)})`;
  }

  function prbMapX(value, bounds) {
    const width = prbPlot.viewBox.baseVal.width;
    const usableWidth = width - PRB_CONFIG.marginLeft - PRB_CONFIG.marginRight;
    const ratio = (value - bounds.xMin) / (bounds.xMax - bounds.xMin);
    return PRB_CONFIG.marginLeft + ratio * usableWidth;
  }

  function prbMapY(value, bounds) {
    const height = prbPlot.viewBox.baseVal.height;
    const usableHeight = height - PRB_CONFIG.marginTop - PRB_CONFIG.marginBottom;
    const ratio = (value - bounds.yMin) / (bounds.yMax - bounds.yMin);
    return height - PRB_CONFIG.marginBottom - ratio * usableHeight;
  }

  function buildPrbPath(xValues, yValues, bounds) {
    return xValues.map((value, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${prbMapX(Number(value), bounds).toFixed(2)} ${prbMapY(Number(yValues[index]), bounds).toFixed(2)}`;
    }).join(" ");
  }

  function buildPrbBounds(xValues, seriesValues) {
    const flattenedValues = seriesValues.flat().map((value) => Number(value));
    const xMinValue = Math.min(...xValues);
    const xMaxValue = Math.max(...xValues);
    const yMinValue = Math.min(...flattenedValues);
    const yMaxValue = Math.max(...flattenedValues);
    const xSpan = Math.max(xMaxValue - xMinValue, 1e-6);
    const ySpan = Math.max(yMaxValue - yMinValue, 1e-6);
    return {
      xMin: xMinValue,
      xMax: xMaxValue,
      yMin: yMinValue - 0.08 * ySpan,
      yMax: yMaxValue + 0.12 * ySpan,
      xStep: chooseNiceStep(xSpan),
      yStep: chooseNiceStep(ySpan),
    };
  }

  function drawPrbChartFrame(bounds, xLabel, yLabel) {
    if (!prbGrid || !prbAxes || !prbPlot) {
      return;
    }

    prbGrid.replaceChildren();
    prbAxes.replaceChildren();

    const xTicks = buildTickValues(bounds.xMin, bounds.xMax, bounds.xStep);
    const yTicks = buildTickValues(bounds.yMin, bounds.yMax, bounds.yStep);
    const width = prbPlot.viewBox.baseVal.width;
    const height = prbPlot.viewBox.baseVal.height;
    const left = PRB_CONFIG.marginLeft;
    const right = width - PRB_CONFIG.marginRight;
    const top = PRB_CONFIG.marginTop;
    const bottom = height - PRB_CONFIG.marginBottom;
    const axisX = prbMapX(bounds.xMin <= 0 && bounds.xMax >= 0 ? 0 : bounds.xMin, bounds);
    const axisY = prbMapY(bounds.yMin <= 0 && bounds.yMax >= 0 ? 0 : bounds.yMin, bounds);

    xTicks.forEach((tick) => {
      const x = prbMapX(tick, bounds);
      prbGrid.appendChild(createSvgNode("line", {
        x1: x, y1: top, x2: x, y2: bottom, class: "prb-grid-line",
      }));
      prbAxes.appendChild(createSvgNode("text", {
        x, y: bottom + 24, "text-anchor": "middle", class: "prb-tick-label",
      })).textContent = Number(tick).toFixed(Math.abs(tick) < 1 ? 2 : 1);
    });

    yTicks.forEach((tick) => {
      const y = prbMapY(tick, bounds);
      prbGrid.appendChild(createSvgNode("line", {
        x1: left, y1: y, x2: right, y2: y, class: "prb-grid-line",
      }));
      prbAxes.appendChild(createSvgNode("text", {
        x: left - 14, y: y + 4, "text-anchor": "end", class: "prb-tick-label",
      })).textContent = Number(tick).toFixed(1);
    });

    prbAxes.appendChild(createSvgNode("line", {
      x1: left, y1: axisY, x2: right, y2: axisY, class: "prb-axis-line",
    }));
    prbAxes.appendChild(createSvgNode("line", {
      x1: axisX, y1: top, x2: axisX, y2: bottom, class: "prb-axis-line",
    }));

    prbAxes.appendChild(createSvgNode("text", {
      x: right - 8, y: axisY - 10, "text-anchor": "end", class: "prb-axis-label",
    })).textContent = xLabel;

    const yAxisLabel = createSvgNode("text", {
      x: axisX + 22, y: top + 18, class: "prb-axis-label",
      transform: `rotate(-90 ${axisX + 22} ${top + 18})`,
      "text-anchor": "middle",
    });
    yAxisLabel.textContent = yLabel;
    prbAxes.appendChild(yAxisLabel);
  }

  function buildPrbLegend(items) {
    if (!prbLegend) {
      return;
    }
    prbLegend.replaceChildren();
    items.forEach((item) => {
      const wrapper = document.createElement("div");
      wrapper.className = "prb-legend-item";
      const swatch = document.createElement("span");
      swatch.className = "prb-swatch";
      swatch.style.borderTopColor = item.color;
      if (item.dashed) {
        swatch.style.borderTopStyle = "dashed";
      }
      const label = document.createElement("span");
      label.textContent = item.label;
      wrapper.append(swatch, label);
      prbLegend.appendChild(wrapper);
    });
  }

  function renderPrbSearchPlot() {
    if (!prbWorkspaceData || !prbGrid || !prbAxes || !prbSeries || !prbAnnotations) {
      return;
    }
    prbGrid.replaceChildren();
    prbAxes.replaceChildren();
    prbSeries.replaceChildren();
    prbAnnotations.replaceChildren();

    const bounds = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };
    const width = prbPlot.viewBox.baseVal.width;
    const height = prbPlot.viewBox.baseVal.height;
    const top = PRB_CONFIG.marginTop;
    const bottom = height - PRB_CONFIG.marginBottom;
    const baselineYValue = 0.56;
    const baselineY = prbMapY(baselineYValue, bounds);
    const xTicks = buildTickValues(0, 1, 0.2);
    const segmentStops = [0, ...prbWorkspaceData.search.gamma_cumulative];
    const segmentLabels = ["gamma0", "gamma1", "gamma2", "gamma3"];

    xTicks.forEach((tick) => {
      const x = prbMapX(tick, bounds);
      prbGrid.appendChild(createSvgNode("line", {
        x1: x, y1: top + 56, x2: x, y2: bottom - 34, class: "prb-grid-line",
      }));
      prbAxes.appendChild(createSvgNode("text", {
        x, y: bottom + 24, "text-anchor": "middle", class: "prb-tick-label",
      })).textContent = tick.toFixed(1);
    });

    prbAxes.appendChild(createSvgNode("line", {
      x1: prbMapX(0, bounds),
      y1: baselineY + 28,
      x2: prbMapX(1, bounds),
      y2: baselineY + 28,
      class: "prb-axis-line",
    }));
    prbAxes.appendChild(createSvgNode("text", {
      x: width - PRB_CONFIG.marginRight - 8,
      y: baselineY + 18,
      "text-anchor": "end",
      class: "prb-axis-label",
    })).textContent = "normalized beam coordinate";

    for (let index = 0; index < 4; index += 1) {
      const x1 = prbMapX(segmentStops[index], bounds);
      const x2 = prbMapX(segmentStops[index + 1], bounds);
      prbSeries.appendChild(createSvgNode("line", {
        x1,
        y1: baselineY,
        x2,
        y2: baselineY,
        class: "prb-line",
        stroke: PRB_SERIES_COLORS[index % PRB_SERIES_COLORS.length],
        "stroke-width": index === 0 || index === 3 ? 7 : 9,
      }));
      const label = createSvgNode("text", {
        x: 0.5 * (x1 + x2),
        y: baselineY - 18,
        "text-anchor": "middle",
        class: "prb-text-label",
      });
      label.textContent = `${segmentLabels[index]} = ${(segmentStops[index + 1] - segmentStops[index]).toFixed(2)}`;
      prbAnnotations.appendChild(label);
    }

    segmentStops.forEach((value, index) => {
      prbSeries.appendChild(createSvgNode("circle", {
        cx: prbMapX(value, bounds),
        cy: baselineY,
        r: 6,
        class: "prb-marker",
        fill: index === segmentStops.length - 1 ? "#ef8c54" : "#ffffff",
      }));
    });

    buildPrbLegend([
      { label: "Characteristic radius segments", color: PRB_SERIES_COLORS[0] },
      { label: "Search result used downstream", color: "#ef8c54" },
    ]);
  }

  function renderPrbLinePlot(modeKey) {
    if (!prbWorkspaceData || !prbSeries || !prbAnnotations) {
      return;
    }
    prbSeries.replaceChildren();
    prbAnnotations.replaceChildren();

    const isAverageMode = modeKey === "average";
    const data = isAverageMode ? prbWorkspaceData.average : prbWorkspaceData[`${modeKey}_fit`];
    if (modeKey === "moment") {
      const theta0Rad = data.theta0_rad || [];
      const thetaPrb = data.theta_prb || [];
      const fitK = data.fit_k || [];
      const xValues = thetaPrb.flat().concat(
        thetaPrb.flatMap((series, index) => theta0Rad.map((value) => Number(value) / Number(fitK[index]))),
      );
      const yValues = [theta0Rad, theta0Rad, theta0Rad];
      const bounds = buildPrbBounds(xValues, yValues);
      drawPrbChartFrame(bounds, "Θi (rad)", "θ0 (rad)");

      thetaPrb.forEach((series, index) => {
        const pointNodes = series.map((value, pointIndex) => createSvgNode("circle", {
          cx: prbMapX(Number(value), bounds),
          cy: prbMapY(Number(theta0Rad[pointIndex]), bounds),
          r: 2.3,
          class: "prb-marker",
          fill: PRB_SERIES_COLORS[index],
          opacity: "0.78",
        }));
        pointNodes.forEach((node) => prbSeries.appendChild(node));

        const fitX = theta0Rad.map((value) => Number(value) / Number(fitK[index]));
        prbSeries.appendChild(createSvgNode("path", {
          d: buildPrbPath(fitX, theta0Rad, bounds),
          class: "prb-line",
          stroke: PRB_SERIES_COLORS[index],
        }));
      });

      buildPrbLegend([
        { label: "actual Θ1 / fit θ0-k1", color: PRB_SERIES_COLORS[0] },
        { label: "actual Θ2 / fit θ0-k2", color: PRB_SERIES_COLORS[1] },
        { label: "actual Θ3 / fit θ0-k3", color: PRB_SERIES_COLORS[2] },
      ]);
      return;
    }

    if (modeKey === "force") {
      const thetaPrb = data.theta_prb || [];
      const torque = data.torque || [];
      const fitK = data.fit_k || [];
      const xValues = thetaPrb.flat();
      const yValues = torque;
      const bounds = buildPrbBounds(xValues, yValues);
      drawPrbChartFrame(bounds, "Θi (rad)", "τi");

      thetaPrb.forEach((series, index) => {
        const torqueSeries = torque[index] || [];
        const pointNodes = series.map((value, pointIndex) => createSvgNode("circle", {
          cx: prbMapX(Number(value), bounds),
          cy: prbMapY(Number(torqueSeries[pointIndex]), bounds),
          r: 2.3,
          class: "prb-marker",
          fill: PRB_SERIES_COLORS[index],
          opacity: "0.78",
        }));
        pointNodes.forEach((node) => prbSeries.appendChild(node));

        const thetaSorted = [...series].map(Number).sort((leftValue, rightValue) => leftValue - rightValue);
        const thetaMin = thetaSorted[0];
        const thetaMax = thetaSorted[thetaSorted.length - 1];
        const fitX = Array.from({ length: 200 }, (_, pointIndex) => (
          thetaMin + ((thetaMax - thetaMin) * pointIndex) / 199
        ));
        const fitY = fitX.map((value) => Number(fitK[index]) * Number(value));
        prbSeries.appendChild(createSvgNode("path", {
          d: buildPrbPath(fitX, fitY, bounds),
          class: "prb-line",
          stroke: PRB_SERIES_COLORS[index],
        }));
      });

      buildPrbLegend([
        { label: "actual Θ1 / fit τ1", color: PRB_SERIES_COLORS[0] },
        { label: "actual Θ2 / fit τ2", color: PRB_SERIES_COLORS[1] },
        { label: "actual Θ3 / fit τ3", color: PRB_SERIES_COLORS[2] },
      ]);
      return;
    }

    const xValues = data.kappa_values;
    const seriesValues = [data.k1, data.k2, data.k3];
    const bounds = buildPrbBounds(xValues, seriesValues);
    drawPrbChartFrame(bounds, "kappa", "k_i");
    seriesValues.forEach((series, index) => {
      prbSeries.appendChild(createSvgNode("path", {
        d: buildPrbPath(xValues, series, bounds),
        class: "prb-line",
        stroke: PRB_SERIES_COLORS[index],
      }));
    });

    data.kbar.forEach((value, index) => {
      prbSeries.appendChild(createSvgNode("line", {
        x1: prbMapX(bounds.xMin, bounds),
        y1: prbMapY(Number(value), bounds),
        x2: prbMapX(bounds.xMax, bounds),
        y2: prbMapY(Number(value), bounds),
        class: "prb-line prb-dashed-line",
        stroke: PRB_SERIES_COLORS[index],
        "stroke-width": 1.8,
        opacity: "0.9",
      }));
    });
    buildPrbLegend([
      { label: "k1(kappa)", color: PRB_SERIES_COLORS[0] },
      { label: "k2(kappa)", color: PRB_SERIES_COLORS[1] },
      { label: "k3(kappa)", color: PRB_SERIES_COLORS[2] },
      { label: "dashed = final kbar", color: "#43536e", dashed: true },
    ]);
  }

  function renderPrbStageSummary() {
    if (!prbWorkspaceData) {
      return;
    }

    if (activePrbMode === "search") {
      prbStageKicker.textContent = "Section400";
      prbStageTitle.textContent = "Characteristic radius search";
      if (prbStageLead) {
        prbStageLead.textContent = "";
      }
      renderSummaryRows(prbStageSummary, [
        ["gamma step", prbWorkspaceData.search.gamma_step.toFixed(2)],
        ["moment samples", String(prbWorkspaceData.search.moment_samples)],
        ["force samples", String(prbWorkspaceData.search.force_samples)],
        ["force fit fraction", prbWorkspaceData.search.force_fit_fraction.toFixed(2)],
        ["θ stress limit", formatDegrees(prbWorkspaceData.search.theta_stress_limit_deg)],
        ["objective", prbWorkspaceData.search.objective.toExponential(3)],
      ]);
      renderPrbSearchPlot();
      return;
    }

    if (activePrbMode === "moment") {
      prbStageKicker.textContent = "Section450";
      prbStageTitle.textContent = "Pure-moment fit";
      if (prbStageLead) {
        prbStageLead.textContent = "";
      }
      renderSummaryRows(prbStageSummary, [
        ["sample count", String(prbWorkspaceData.moment_fit.theta_deg.length)],
        ["θ max", formatDegrees(Math.max(...prbWorkspaceData.moment_fit.theta_deg))],
        ["k1", prbWorkspaceData.moment_fit.fit_k[0].toFixed(3)],
        ["k2", prbWorkspaceData.moment_fit.fit_k[1].toFixed(3)],
        ["k3", prbWorkspaceData.moment_fit.fit_k[2].toFixed(3)],
      ]);
      renderPrbLinePlot("moment");
      return;
    }

    if (activePrbMode === "force") {
      prbStageKicker.textContent = "Section460";
      prbStageTitle.textContent = "Pure-force fit";
      if (prbStageLead) {
        prbStageLead.textContent = "";
      }
      renderSummaryRows(prbStageSummary, [
        ["sample count", String(prbWorkspaceData.force_fit.theta_deg.length)],
        ["θ max", formatDegrees(Math.max(...prbWorkspaceData.force_fit.theta_deg))],
        ["k1", prbWorkspaceData.force_fit.fit_k[0].toFixed(3)],
        ["k2", prbWorkspaceData.force_fit.fit_k[1].toFixed(3)],
        ["k3", prbWorkspaceData.force_fit.fit_k[2].toFixed(3)],
      ]);
      renderPrbLinePlot("force");
      return;
    }

    prbStageKicker.textContent = "Section500 + Section510";
    prbStageTitle.textContent = "Load-independent kappa average";
    if (prbStageLead) {
      prbStageLead.textContent = "";
    }
    renderSummaryRows(prbStageSummary, [
      ["kappa count", String(prbWorkspaceData.average.kappa_values.length)],
      ["kappa range", `${Math.min(...prbWorkspaceData.average.kappa_values).toFixed(1)} to ${Math.max(...prbWorkspaceData.average.kappa_values).toFixed(1)}`],
      ["kbar1", prbWorkspaceData.average.kbar[0].toFixed(3)],
      ["kbar2", prbWorkspaceData.average.kbar[1].toFixed(3)],
      ["kbar3", prbWorkspaceData.average.kbar[2].toFixed(3)],
    ]);
    renderPrbLinePlot("average");
  }

  function renderPrbOutputIntoMainPlot() {
    if (!prbWorkspaceData || !prbGrid || !prbAxes || !prbSeries || !prbAnnotations || !prbPlot) {
      return;
    }

    const previewGroup = prbWorkspaceData.section5_preview?.[activePrbOutputMode];
    if (!previewGroup) {
      return;
    }

    prbGrid.replaceChildren();
    prbAxes.replaceChildren();
    prbSeries.replaceChildren();
    prbAnnotations.replaceChildren();

    const width = prbPlot.viewBox.baseVal.width;
    const height = prbPlot.viewBox.baseVal.height;
    const cols = 3;
    const rows = 2;
    const outerLeft = 18;
    const outerRight = 12;
    const outerTop = 16;
    const outerBottom = 18;
    const gutterX = 14;
    const gutterY = 18;
    const panelWidth = (width - outerLeft - outerRight - gutterX * (cols - 1)) / cols;
    const panelHeight = (height - outerTop - outerBottom - gutterY * (rows - 1)) / rows;
    const xMin = -0.1;
    const xMax = 1.05;
    const yMin = 0.0;
    const yMax = 1.05;
    const xTicks = buildTickValues(0, 1.0, 0.2);
    const yTicks = buildTickValues(0, 1.0, 0.2);

    previewGroup.cases.forEach((caseData, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      const panelLeft = outerLeft + col * (panelWidth + gutterX);
      const panelTop = outerTop + row * (panelHeight + gutterY);
      const panelRight = panelLeft + panelWidth;
      const panelBottom = panelTop + panelHeight;
      const innerLeft = panelLeft + 30;
      const innerRight = panelRight - 8;
      const innerTop = panelTop + 24;
      const innerBottom = panelBottom - 22;
      const mapX = (value) => innerLeft + ((Number(value) - xMin) / (xMax - xMin)) * (innerRight - innerLeft);
      const mapY = (value) => innerBottom - ((Number(value) - yMin) / (yMax - yMin)) * (innerBottom - innerTop);

      prbAxes.appendChild(createSvgNode("rect", {
        x: panelLeft, y: panelTop, width: panelWidth, height: panelHeight,
        fill: "transparent", stroke: "rgba(34, 52, 78, 0.14)", "stroke-width": "1",
        rx: "10",
      }));

      xTicks.forEach((tick) => {
        const x = mapX(tick);
        prbGrid.appendChild(createSvgNode("line", {
          x1: x, y1: innerTop, x2: x, y2: innerBottom, class: "prb-output-grid-line",
        }));
      });
      yTicks.forEach((tick) => {
        const y = mapY(tick);
        prbGrid.appendChild(createSvgNode("line", {
          x1: innerLeft, y1: y, x2: innerRight, y2: y, class: "prb-output-grid-line",
        }));
      });

      prbAxes.appendChild(createSvgNode("line", {
        x1: innerLeft, y1: mapY(0), x2: innerRight, y2: mapY(0), class: "prb-output-axis-line",
      }));
      prbAxes.appendChild(createSvgNode("line", {
        x1: mapX(0), y1: innerTop, x2: mapX(0), y2: innerBottom, class: "prb-output-axis-line",
      }));

      const prbPath = caseData.prb_x.map((value, pointIndex) => {
        const command = pointIndex === 0 ? "M" : "L";
        return `${command} ${mapX(value).toFixed(2)} ${mapY(caseData.prb_y[pointIndex]).toFixed(2)}`;
      }).join(" ");
      prbSeries.appendChild(createSvgNode("path", {
        d: prbPath,
        fill: "none",
        stroke: "#0c8aa4",
        "stroke-width": "2.0",
      }));

      caseData.actual_x.forEach((value, pointIndex) => {
        prbSeries.appendChild(createSvgNode("circle", {
          cx: mapX(value),
          cy: mapY(caseData.actual_y[pointIndex]),
          r: "1.9",
          fill: "#1f2c40",
          opacity: "0.82",
        }));
      });

      prbAnnotations.appendChild(createSvgNode("text", {
        x: panelLeft + 10, y: panelTop + 14, class: "prb-output-title",
      })).textContent = previewGroup.labels[index];
      prbAnnotations.appendChild(createSvgNode("text", {
        x: panelLeft + 10, y: panelTop + 28, class: "prb-output-label",
      })).textContent = `tip ${Number(caseData.max_tip_error_pct).toFixed(2)}% | slope ${formatDegrees(Number(caseData.max_slope_error_deg))}`;

      if (col === 0) {
        prbAnnotations.appendChild(createSvgNode("text", {
          x: panelLeft + 8, y: innerTop + 10, class: "prb-output-label",
        })).textContent = "b / l";
      }
      if (row === rows - 1) {
        prbAnnotations.appendChild(createSvgNode("text", {
          x: panelRight - 14, y: panelBottom - 6, class: "prb-output-label", "text-anchor": "end",
        })).textContent = "a / l";
      }
    });

    buildPrbLegend([
      { label: "PRB model", color: "#0c8aa4" },
      { label: "Numerical integration", color: "#1f2c40" },
    ]);
  }

  function renderPrbMainPlot() {
    if (activePrbViewMode === "output") {
      renderPrbOutputIntoMainPlot();
      return;
    }
    if (activePrbMode === "search") {
      renderPrbSearchPlot();
      return;
    }
    if (activePrbMode === "moment") {
      renderPrbLinePlot("moment");
      return;
    }
    if (activePrbMode === "force") {
      renderPrbLinePlot("force");
      return;
    }
    renderPrbLinePlot("average");
  }

  function setPrbMode(modeKey) {
    activePrbMode = modeKey;
    activePrbViewMode = "stage";
    prbStageTabs.forEach((button) => {
      const isActive = button.dataset.prbMode === modeKey;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    renderPrbStageSummary();
  }

  function renderPrbOutputPreview() {
    if (!prbWorkspaceData || !prbOutputSummary) {
      return;
    }

    const previewGroup = prbWorkspaceData.section5_preview?.[activePrbOutputMode];
    if (!previewGroup) {
      return;
    }

    const worstCase = previewGroup.cases.reduce((best, current, currentIndex) => (
      Number(current.max_tip_error_pct) > Number(best.case.max_tip_error_pct)
        ? { case: current, label: previewGroup.labels[currentIndex] }
        : best
    ), { case: previewGroup.cases[0], label: previewGroup.labels[0] });

    renderSummaryRows(prbOutputSummary, [
      ["view", previewGroup.subtitle],
      ["case count", String(previewGroup.cases.length)],
      ["worst tip error", `${Number(worstCase.case.max_tip_error_pct).toFixed(2)}%`],
      ["worst slope error", formatDegrees(Number(worstCase.case.max_slope_error_deg))],
      ["worst case", worstCase.label],
      ["θ0 at worst tip", formatDegrees(Number(worstCase.case.theta0_at_max_tip_error_deg))],
    ]);
  }

  function setPrbOutputMode(modeKey, activateMainPlot = true) {
    activePrbOutputMode = modeKey;
    prbOutputTabs.forEach((button) => {
      const isActive = button.dataset.prbOutputMode === modeKey;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    if (activateMainPlot) {
      activePrbViewMode = "output";
      renderPrbMainPlot();
    }
    renderPrbOutputPreview();
  }

  function initializePrbPanel() {
    if (!prbPlot || prbLoaded) {
      return;
    }

    requestJson(PRB_CONFIG.endpoint)
      .then((data) => {
        prbWorkspaceData = data;
        if (prbParameterSource) {
          prbParameterSource.textContent = String(data.parameter_source);
        }
        prbFinalGammas.textContent = data.search.gammas.map((value) => Number(value).toFixed(2)).join(", ");
        prbFinalKbar.textContent = data.average.kbar.map((value) => Number(value).toFixed(3)).join(", ");
        prbKappaGrid.textContent = data.average.kappa_values.map((value) => Number(value).toFixed(value < 1 ? 1 : 0)).join(", ");
        if (prbStiffnessLabel) {
          prbStiffnessLabel.textContent = String(data.average.stiffness_label);
        }
        prbStageTabs.forEach((button) => {
          button.addEventListener("click", () => {
            setPrbMode(button.dataset.prbMode);
          });
        });
        prbOutputTabs.forEach((button) => {
          button.addEventListener("click", () => {
            setPrbOutputMode(button.dataset.prbOutputMode);
          });
        });
        setPrbMode("search");
        setPrbOutputMode("figure12", false);
        prbLoaded = true;
      })
      .catch((error) => {
        console.error(error);
        if (prbParameterSource) {
          prbParameterSource.textContent = "Unavailable";
        }
        renderSummaryRows(prbStageSummary, [["Status", "Unavailable"]]);
      });
  }

  function buildMechanismBounds(overlayData) {
    const allPoints = [];
    const feaScale = 1 / Number(overlayData.prb_scale_to_fea || 1);
    overlayData.fea_frames.forEach((frame) => {
      Object.values(frame.parts).forEach((part) => {
        part.base_xy.forEach((point) => allPoints.push(point.map((value) => Number(value) * feaScale)));
        part.deformed_xy.forEach((point) => allPoints.push(point.map((value) => Number(value) * feaScale)));
      });
    });
    overlayData.prb_motion.A.forEach((point) => allPoints.push(point));
    overlayData.prb_motion.Q.forEach((point) => allPoints.push(point));
    overlayData.prb_motion.crank_tip.forEach((point) => allPoints.push(point));
    overlayData.prb_motion.chain.forEach((chain) => {
      chain.forEach((point) => allPoints.push(point));
    });
    allPoints.push([0, 0], overlayData.prb_motion.B);

    const xs = allPoints.map((point) => Number(point[0]));
    const ys = allPoints.map((point) => Number(point[1]));
    const rawXMin = Math.min(...xs);
    const rawXMax = Math.max(...xs);
    const rawYMin = Math.min(...ys);
    const rawYMax = Math.max(...ys);
    let xMin = rawXMin;
    let xMax = rawXMax;
    let yMin = rawYMin;
    let yMax = rawYMax;
    let xSpan = xMax - xMin;
    let ySpan = yMax - yMin;
    const padding = 0.12;
    const usableWidth = 860 - MECHANISM_CONFIG.marginLeft - MECHANISM_CONFIG.marginRight;
    const usableHeight = 520 - MECHANISM_CONFIG.marginTop - MECHANISM_CONFIG.marginBottom;
    const targetAspect = usableWidth / usableHeight;

    xMin -= padding;
    xMax += padding;
    yMin -= padding;
    yMax += padding;
    xSpan = xMax - xMin;
    ySpan = yMax - yMin;

    xMin = -0.5;
    xMax = 1.3;
    xSpan = xMax - xMin;
    yMax = 1.1;
    yMin = -0.3;
    ySpan = yMax - yMin;

    const dataAspect = xSpan / ySpan;
    let plotLeft = MECHANISM_CONFIG.marginLeft;
    let plotRight = 860 - MECHANISM_CONFIG.marginRight;
    let plotTop = MECHANISM_CONFIG.marginTop;
    let plotBottom = 520 - MECHANISM_CONFIG.marginBottom;

    if (dataAspect < targetAspect) {
      const effectiveWidth = usableHeight * dataAspect;
      const sidePadding = 0.5 * (usableWidth - effectiveWidth);
      plotLeft += sidePadding;
      plotRight -= sidePadding;
    } else if (dataAspect > targetAspect) {
      const effectiveHeight = usableWidth / dataAspect;
      const verticalPadding = 0.5 * (usableHeight - effectiveHeight);
      plotTop += verticalPadding;
      plotBottom -= verticalPadding;
    }

    return {
      xMin: Math.floor(xMin / 0.1) * 0.1,
      xMax: Math.ceil(xMax / 0.1) * 0.1,
      yMin: Math.floor(yMin / 0.1) * 0.1,
      yMax: Math.ceil(yMax / 0.1) * 0.1,
      xSpan,
      ySpan,
      plotLeft,
      plotRight,
      plotTop,
      plotBottom,
    };
  }

  function computeMaterialsBounds(data) {
    const xValues = [0.0, 1.0];
    const yValues = [0.0];

    data.target_path.forEach((point) => {
      xValues.push(Number(point[0]));
      yValues.push(Number(point[1]));
    });
    data.frames.forEach((frame) => {
      frame.chain.forEach((point) => {
        xValues.push(Number(point[0]));
        yValues.push(Number(point[1]));
      });
    });

    let xMin = Math.min(...xValues) - 0.06;
    let xMax = Math.max(...xValues) + 0.06;
    let yMin = Math.min(...yValues) - 0.08;
    let yMax = Math.max(...yValues) + 0.08;
    let xSpan = xMax - xMin;
    let ySpan = yMax - yMin;

    const usableWidth = 860 - MATERIALS_CONFIG.marginLeft - MATERIALS_CONFIG.marginRight;
    const usableHeight = 520 - MATERIALS_CONFIG.marginTop - MATERIALS_CONFIG.marginBottom;
    const targetAspect = usableWidth / usableHeight;
    const dataAspect = xSpan / ySpan;

    let plotLeft = MATERIALS_CONFIG.marginLeft;
    let plotRight = 860 - MATERIALS_CONFIG.marginRight;
    let plotTop = MATERIALS_CONFIG.marginTop;
    let plotBottom = 520 - MATERIALS_CONFIG.marginBottom;

    if (dataAspect < targetAspect) {
      const effectiveWidth = usableHeight * dataAspect;
      const sidePadding = 0.5 * (usableWidth - effectiveWidth);
      plotLeft += sidePadding;
      plotRight -= sidePadding;
    } else if (dataAspect > targetAspect) {
      const effectiveHeight = usableWidth / dataAspect;
      const verticalPadding = 0.5 * (usableHeight - effectiveHeight);
      plotTop += verticalPadding;
      plotBottom -= verticalPadding;
    }

    return {
      xMin: Math.floor(xMin / 0.1) * 0.1,
      xMax: Math.ceil(xMax / 0.1) * 0.1,
      yMin: Math.floor(yMin / 0.1) * 0.1,
      yMax: Math.ceil(yMax / 0.1) * 0.1,
      xSpan,
      ySpan,
      plotLeft,
      plotRight,
      plotTop,
      plotBottom,
    };
  }

  function computeRangeBounds(values, options = {}) {
    const numericValues = values
      .map((value) => Number(value))
      .filter((value) => Number.isFinite(value));
    const includeZero = Boolean(options.includeZero);
    if (includeZero) {
      numericValues.push(0);
    }
    if (numericValues.length === 0) {
      return { min: -1, max: 1 };
    }

    let minValue = Math.min(...numericValues);
    let maxValue = Math.max(...numericValues);
    if (minValue === maxValue) {
      const padding = Math.max(Math.abs(minValue) * 0.15, 0.1);
      minValue -= padding;
      maxValue += padding;
    } else {
      const padding = (maxValue - minValue) * 0.12;
      minValue -= padding;
      maxValue += padding;
    }

    return {
      min: Math.floor(minValue / 0.05) * 0.05,
      max: Math.ceil(maxValue / 0.05) * 0.05,
    };
  }

  function computeMaterialsTrendBounds(data) {
    if (!data || !Array.isArray(data.frames) || data.frames.length === 0) {
      return null;
    }

    const timeValues = data.frames.map((frame) => Number(frame.time));
    const yDesired = data.frames.map((frame) => Number(frame.target_y));
    const yActual = data.frames.map((frame) => Number(frame.tip_y));
    const thetaDesired = data.frames.map((frame) => Number(frame.theta0_desired_deg ?? frame.theta_tip_deg));
    const thetaActual = data.frames.map((frame) => Number(frame.theta_tip_deg));
    const momentValues = data.frames.map((frame) => Number(frame.base_net_moment || 0));

    return {
      time: {
        min: Math.min(...timeValues),
        max: Math.max(...timeValues),
      },
      y: computeRangeBounds([...yDesired, ...yActual], { includeZero: true }),
      theta: computeRangeBounds([...thetaDesired, ...thetaActual], { includeZero: true }),
      moment: computeRangeBounds(momentValues, { includeZero: true }),
    };
  }

  function buildMaterialsTrendPath(points, xBounds, yBounds, plotElement) {
    const width = plotElement.viewBox.baseVal.width;
    const height = plotElement.viewBox.baseVal.height;
    const marginLeft = 42;
    const marginRight = 10;
    const marginTop = 16;
    const marginBottom = 30;
    const usableWidth = width - marginLeft - marginRight;
    const usableHeight = height - marginTop - marginBottom;
    const mapX = (value) => marginLeft + ((value - xBounds.min) / (xBounds.max - xBounds.min)) * usableWidth;
    const mapY = (value) => height - marginBottom - ((value - yBounds.min) / (yBounds.max - yBounds.min)) * usableHeight;

    return points.map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${mapX(point.x).toFixed(2)} ${mapY(point.y).toFixed(2)}`;
    }).join(" ");
  }

  function drawMaterialsTrendFrame(gridNode, axesNode, plotElement, xBounds, yBounds, yLabel) {
    if (!gridNode || !axesNode || !plotElement) {
      return;
    }

    gridNode.replaceChildren();
    axesNode.replaceChildren();

    const width = plotElement.viewBox.baseVal.width;
    const height = plotElement.viewBox.baseVal.height;
    const marginLeft = 42;
    const marginRight = 10;
    const marginTop = 16;
    const marginBottom = 30;
    const left = marginLeft;
    const right = width - marginRight;
    const top = marginTop;
    const bottom = height - marginBottom;
    const usableWidth = width - marginLeft - marginRight;
    const usableHeight = height - marginTop - marginBottom;
    const xStep = chooseNiceStep(xBounds.max - xBounds.min);
    const yStep = chooseNiceStep(yBounds.max - yBounds.min);
    const xTicks = buildTickValues(xBounds.min, xBounds.max, xStep);
    const yTicks = buildTickValues(yBounds.min, yBounds.max, yStep);
    const mapX = (value) => marginLeft + ((value - xBounds.min) / (xBounds.max - xBounds.min)) * usableWidth;
    const mapY = (value) => height - marginBottom - ((value - yBounds.min) / (yBounds.max - yBounds.min)) * usableHeight;
    const axisY = mapY(yBounds.min <= 0 && yBounds.max >= 0 ? 0 : yBounds.min);

    xTicks.forEach((tick) => {
      const x = mapX(tick);
      gridNode.appendChild(createSvgNode("line", {
        x1: x, y1: top, x2: x, y2: bottom, class: "materials-trend-grid-line",
      }));
      axesNode.appendChild(createSvgNode("text", {
        x, y: bottom + 22, "text-anchor": "middle", class: "materials-trend-tick-label",
      })).textContent = Number(tick).toFixed(1);
    });

    yTicks.forEach((tick) => {
      const y = mapY(tick);
      gridNode.appendChild(createSvgNode("line", {
        x1: left, y1: y, x2: right, y2: y, class: "materials-trend-grid-line",
      }));
      axesNode.appendChild(createSvgNode("text", {
        x: left - 12, y: y + 4, "text-anchor": "end", class: "materials-trend-tick-label",
      })).textContent = Number(tick).toFixed(2);
    });

    axesNode.appendChild(createSvgNode("line", {
      x1: left, y1: axisY, x2: right, y2: axisY, class: "materials-trend-axis-line",
    }));
    axesNode.appendChild(createSvgNode("line", {
      x1: left, y1: top, x2: left, y2: bottom, class: "materials-trend-axis-line",
    }));

    axesNode.appendChild(createSvgNode("text", {
      x: right - 6, y: bottom - 8, "text-anchor": "end", class: "materials-trend-axis-label",
    })).textContent = "time (s)";

    const yAxisLabel = createSvgNode("text", {
      x: left + 18, y: top + 16, class: "materials-trend-axis-label",
      transform: `rotate(-90 ${left + 18} ${top + 16})`,
      "text-anchor": "middle",
    });
    yAxisLabel.textContent = yLabel;
    axesNode.appendChild(yAxisLabel);
  }

  function renderMaterialsTrendPlots() {
    if (!materialsMotionData || !materialsTrendBounds) {
      return;
    }

    const timePoints = materialsMotionData.frames.map((frame) => Number(frame.time));
    const yTargetPoints = timePoints.map((time, index) => ({ x: time, y: Number(materialsMotionData.frames[index].target_y) }));
    const yActualPoints = timePoints.map((time, index) => ({ x: time, y: Number(materialsMotionData.frames[index].tip_y) }));
    const thetaTargetPoints = timePoints.map((time, index) => ({ x: time, y: Number(materialsMotionData.frames[index].theta0_desired_deg ?? materialsMotionData.frames[index].theta_tip_deg) }));
    const thetaActualPoints = timePoints.map((time, index) => ({ x: time, y: Number(materialsMotionData.frames[index].theta_tip_deg) }));
    const momentPoints = timePoints.map((time, index) => ({ x: time, y: Number(materialsMotionData.frames[index].base_net_moment || 0) }));

    drawMaterialsTrendFrame(materialsYTrendGrid, materialsYTrendAxes, materialsYTrendPlot, materialsTrendBounds.time, materialsTrendBounds.y, "y / L");
    drawMaterialsTrendFrame(materialsThetaTrendGrid, materialsThetaTrendAxes, materialsThetaTrendPlot, materialsTrendBounds.time, materialsTrendBounds.theta, "\u03b80 (\u00b0)");
    drawMaterialsTrendFrame(materialsMomentTrendGrid, materialsMomentTrendAxes, materialsMomentTrendPlot, materialsTrendBounds.time, materialsTrendBounds.moment, "M_net (N\u00b7m)");

    if (materialsYTrendTarget) {
      materialsYTrendTarget.setAttribute("d", buildMaterialsTrendPath(yTargetPoints, materialsTrendBounds.time, materialsTrendBounds.y, materialsYTrendPlot));
    }
    if (materialsYTrendActual) {
      materialsYTrendActual.setAttribute("d", buildMaterialsTrendPath(yActualPoints, materialsTrendBounds.time, materialsTrendBounds.y, materialsYTrendPlot));
    }
    if (materialsThetaTrendTarget) {
      materialsThetaTrendTarget.setAttribute("d", buildMaterialsTrendPath(thetaTargetPoints, materialsTrendBounds.time, materialsTrendBounds.theta, materialsThetaTrendPlot));
    }
    if (materialsThetaTrendActual) {
      materialsThetaTrendActual.setAttribute("d", buildMaterialsTrendPath(thetaActualPoints, materialsTrendBounds.time, materialsTrendBounds.theta, materialsThetaTrendPlot));
    }
    if (materialsMomentTrendLine) {
      materialsMomentTrendLine.setAttribute("d", buildMaterialsTrendPath(momentPoints, materialsTrendBounds.time, materialsTrendBounds.moment, materialsMomentTrendPlot));
    }
  }

  function updateMaterialsTrendSelection(frame) {
    if (!materialsTrendBounds || !frame) {
      return;
    }

    const updateSelection = (plotElement, xBounds, yBounds, cursorNode, targetNode, actualNode, xValue, targetValue, actualValue) => {
      if (!plotElement || !xBounds || !yBounds) {
        return;
      }
      const width = plotElement.viewBox.baseVal.width;
      const height = plotElement.viewBox.baseVal.height;
      const marginLeft = 42;
      const marginRight = 10;
      const marginTop = 16;
      const marginBottom = 30;
      const usableWidth = width - marginLeft - marginRight;
      const usableHeight = height - marginTop - marginBottom;
      const mapX = (value) => marginLeft + ((value - xBounds.min) / (xBounds.max - xBounds.min)) * usableWidth;
      const mapY = (value) => height - marginBottom - ((value - yBounds.min) / (yBounds.max - yBounds.min)) * usableHeight;
      const cursorX = mapX(xValue);

      if (cursorNode) {
        cursorNode.setAttribute("x1", cursorX);
        cursorNode.setAttribute("x2", cursorX);
        cursorNode.setAttribute("y1", marginTop);
        cursorNode.setAttribute("y2", height - marginBottom);
      }
      if (targetNode) {
        targetNode.setAttribute("cx", cursorX);
        targetNode.setAttribute("cy", mapY(targetValue));
      }
      if (actualNode) {
        actualNode.setAttribute("cx", cursorX);
        actualNode.setAttribute("cy", mapY(actualValue));
      }
    };

    const timeValue = Number(frame.time);
    updateSelection(
      materialsYTrendPlot,
      materialsTrendBounds.time,
      materialsTrendBounds.y,
      materialsYTrendCursor,
      materialsYTrendPointTarget,
      materialsYTrendPointActual,
      timeValue,
      Number(frame.target_y),
      Number(frame.tip_y),
    );
    updateSelection(
      materialsThetaTrendPlot,
      materialsTrendBounds.time,
      materialsTrendBounds.theta,
      materialsThetaTrendCursor,
      materialsThetaTrendPointTarget,
      materialsThetaTrendPointActual,
      timeValue,
      Number(frame.theta0_desired_deg ?? frame.theta_tip_deg),
      Number(frame.theta_tip_deg),
    );
    updateSelection(
      materialsMomentTrendPlot,
      materialsTrendBounds.time,
      materialsTrendBounds.moment,
      materialsMomentTrendCursor,
      materialsMomentTrendPoint,
      null,
      timeValue,
      Number(frame.base_net_moment || 0),
      Number(frame.base_net_moment || 0),
    );
    if (materialsMomentValue) {
      materialsMomentValue.textContent = `M_net = ${Number(frame.base_net_moment || 0).toFixed(5)} N·m`;
    }
  }

  function materialsMapX(value, bounds) {
    const ratio = (value - bounds.xMin) / (bounds.xMax - bounds.xMin);
    return bounds.plotLeft + ratio * (bounds.plotRight - bounds.plotLeft);
  }

  function materialsMapY(value, bounds) {
    const ratio = (value - bounds.yMin) / (bounds.yMax - bounds.yMin);
    return bounds.plotBottom - ratio * (bounds.plotBottom - bounds.plotTop);
  }

  function buildMaterialsPath(points, bounds) {
    return points.map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${materialsMapX(Number(point[0]), bounds).toFixed(2)} ${materialsMapY(Number(point[1]), bounds).toFixed(2)}`;
    }).join(" ");
  }

  function drawMaterialsFrame(bounds) {
    if (!materialsPlot || !materialsGrid || !materialsAxes) {
      return;
    }

    materialsGrid.replaceChildren();
    materialsAxes.replaceChildren();

    const xTicks = buildTickValues(bounds.xMin, bounds.xMax, MATERIALS_CONFIG.gridStep);
    const yTicks = buildTickValues(bounds.yMin, bounds.yMax, MATERIALS_CONFIG.gridStep);
    const left = bounds.plotLeft;
    const right = bounds.plotRight;
    const top = bounds.plotTop;
    const bottom = bounds.plotBottom;
    const axisX = materialsMapX(clamp(0, bounds.xMin, bounds.xMax), bounds);
    const axisY = materialsMapY(clamp(0, bounds.yMin, bounds.yMax), bounds);

    xTicks.forEach((tick) => {
      const x = materialsMapX(tick, bounds);
      materialsGrid.appendChild(createSvgNode("line", {
        x1: x, y1: top, x2: x, y2: bottom, class: "materials-grid-line",
      }));
      materialsAxes.appendChild(createSvgNode("text", {
        x, y: bottom + 24, "text-anchor": "middle", class: "materials-tick-label",
      })).textContent = tick.toFixed(1);
    });

    yTicks.forEach((tick) => {
      const y = materialsMapY(tick, bounds);
      materialsGrid.appendChild(createSvgNode("line", {
        x1: left, y1: y, x2: right, y2: y, class: "materials-grid-line",
      }));
      materialsAxes.appendChild(createSvgNode("text", {
        x: left - 14, y: y + 4, "text-anchor": "end", class: "materials-tick-label",
      })).textContent = tick.toFixed(1);
    });

    materialsAxes.appendChild(createSvgNode("line", {
      x1: left, y1: axisY, x2: right, y2: axisY, class: "materials-axis-line",
    }));
    materialsAxes.appendChild(createSvgNode("line", {
      x1: axisX, y1: top, x2: axisX, y2: bottom, class: "materials-axis-line",
    }));

    materialsAxes.appendChild(createSvgNode("text", {
      x: right - 8, y: axisY - 10, "text-anchor": "end", class: "materials-axis-label",
    })).textContent = "x / L";

    const yAxisLabel = createSvgNode("text", {
      x: axisX + 20, y: top + 18, class: "materials-axis-label",
      transform: `rotate(-90 ${axisX + 20} ${top + 18})`,
      "text-anchor": "middle",
    });
    yAxisLabel.textContent = "y / L";
    materialsAxes.appendChild(yAxisLabel);
  }

  function drawMaterialsStaticScene() {
    if (!materialsStatic || !materialsMotionData || !materialsBounds) {
      return;
    }

    materialsStatic.replaceChildren();

    const undeformedPoints = [
      [0.0, 0.0],
      [materialsMotionData.gammas[0], 0.0],
      [materialsMotionData.gammas[0] + materialsMotionData.gammas[1], 0.0],
      [materialsMotionData.gammas[0] + materialsMotionData.gammas[1] + materialsMotionData.gammas[2], 0.0],
      [1.0, 0.0],
    ];
    materialsStatic.appendChild(createSvgNode("path", {
      d: buildMaterialsPath(undeformedPoints, materialsBounds),
      class: "materials-line",
      stroke: "#8a96a7",
      "stroke-dasharray": "9 8",
      "stroke-width": "1.8",
    }));

    materialsStatic.appendChild(createSvgNode("path", {
      d: buildMaterialsPath(materialsMotionData.target_path, materialsBounds),
      class: "materials-line",
      stroke: "#ef8c54",
      "stroke-dasharray": "8 7",
      "stroke-width": "2.0",
      opacity: "0.9",
    }));

    if (Array.isArray(materialsMotionData.actual_path) && materialsMotionData.actual_path.length > 1) {
      materialsStatic.appendChild(createSvgNode("path", {
        d: buildMaterialsPath(materialsMotionData.actual_path, materialsBounds),
        class: "materials-line",
        stroke: "rgba(12, 138, 164, 0.34)",
        "stroke-width": "1.8",
      }));
    }
  }

  function initializeMaterialsDynamicScene() {
    if (!materialsDynamic) {
      return;
    }
    materialsDynamic.replaceChildren();
    materialsJointPool = [];

    materialsTargetTracePath = createSvgNode("path", {
      class: "materials-line",
      stroke: "#ef8c54",
      "stroke-width": "2.4",
      opacity: "0.28",
      d: "",
    });
    materialsActualTracePath = createSvgNode("path", {
      class: "materials-line",
      stroke: "rgba(12, 138, 164, 0.45)",
      "stroke-width": "2.2",
      d: "",
    });
    materialsChainPath = createSvgNode("path", {
      class: "materials-line",
      stroke: "#0c8aa4",
      "stroke-width": "2.8",
      d: "",
    });

    materialsDynamic.appendChild(materialsTargetTracePath);
    materialsDynamic.appendChild(materialsActualTracePath);
    materialsDynamic.appendChild(materialsChainPath);

    materialsTargetPoint = createSvgNode("circle", {
      r: 5.2,
      fill: "rgba(239, 140, 84, 0.18)",
      stroke: "#ef8c54",
      "stroke-width": "1.8",
    });
    materialsTipPoint = createSvgNode("circle", {
      r: 3.4,
      fill: "#ef8c54",
    });
    materialsDynamic.appendChild(materialsTargetPoint);
    materialsDynamic.appendChild(materialsTipPoint);
  }

  function renderMaterialsState(frameIndex) {
    if (!materialsMotionData || !materialsBounds || !materialsDynamic) {
      return;
    }

    materialsCurrentFrameIndex = clamp(frameIndex, 0, materialsMotionData.frames.length - 1);
    const frame = materialsMotionData.frames[materialsCurrentFrameIndex];

    if (!materialsChainPath) {
      initializeMaterialsDynamicScene();
    }

    const targetTracePoints = materialsMotionData.target_path.slice(0, materialsCurrentFrameIndex + 1);
    materialsTargetTracePath.setAttribute(
      "d",
      targetTracePoints.length > 1 ? buildMaterialsPath(targetTracePoints, materialsBounds) : "",
    );

    const actualTracePoints = Array.isArray(materialsMotionData.actual_path)
      ? materialsMotionData.actual_path.slice(0, materialsCurrentFrameIndex + 1)
      : [];
    materialsActualTracePath.setAttribute(
      "d",
      actualTracePoints.length > 1 ? buildMaterialsPath(actualTracePoints, materialsBounds) : "",
    );
    materialsChainPath.setAttribute("d", buildMaterialsPath(frame.chain, materialsBounds));

    const jointPoints = frame.chain.slice(1);
    ensureCirclePool(materialsDynamic, materialsJointPool, jointPoints.length, () => ({
      r: 3.4,
      class: "materials-joint",
      fill: "#0c8aa4",
    }));
    jointPoints.forEach((point, pointIndex) => {
      const node = materialsJointPool[pointIndex];
      node.setAttribute("cx", materialsMapX(Number(point[0]), materialsBounds));
      node.setAttribute("cy", materialsMapY(Number(point[1]), materialsBounds));
    });
    materialsTargetPoint.setAttribute("cx", materialsMapX(Number(frame.target_x), materialsBounds));
    materialsTargetPoint.setAttribute("cy", materialsMapY(Number(frame.target_y), materialsBounds));
    materialsTipPoint.setAttribute("cx", materialsMapX(Number(frame.tip_x), materialsBounds));
    materialsTipPoint.setAttribute("cy", materialsMapY(Number(frame.tip_y), materialsBounds));
    materialsDynamic.appendChild(materialsTargetPoint);
    materialsDynamic.appendChild(materialsTipPoint);

    if (materialsFrameSlider) {
      materialsFrameSlider.value = String(materialsCurrentFrameIndex);
    }
    if (materialsFrameValue) {
      materialsFrameValue.textContent = `${Number(frame.frame_value_display).toFixed(1)}`;
    }
    if (materialsTargetXY) {
      materialsTargetXY.textContent = `x ${Number(frame.tip_x).toFixed(3)}, y* ${Number(frame.target_y).toFixed(3)}`;
    }
    if (materialsThetaTip) {
      if (Number.isFinite(Number(frame.theta0_desired_deg))) {
        materialsThetaTip.textContent = `${formatDegrees(Number(frame.theta0_desired_deg))} / ${formatDegrees(Number(frame.theta_tip_deg))}`;
      } else {
        materialsThetaTip.textContent = formatDegrees(Number(frame.theta_tip_deg));
      }
    }
    if (materialsThetas) {
      materialsThetas.textContent = frame.theta.map((value) => formatDegrees(Number(value) * 180 / Math.PI, 1)).join(" / ");
    }
    if (materialsTau) {
      const tauValues = Array.isArray(frame.tau) ? frame.tau : [0, 0, 0];
      materialsTau.textContent = tauValues.map((value) => `${Number(value).toFixed(4)} N*m`).join(" / ");
    }
    if (materialsForceMoment) {
      if (frame.exact_force_moment_solved) {
        materialsForceMoment.textContent = `|F_tip| ${Number(frame.force_magnitude || 0).toFixed(4)} N / |M_tip| ${Number(frame.tip_moment_magnitude || 0).toFixed(5)} N*m`;
      } else {
        materialsForceMoment.textContent = "Force/moment solve pending";
      }
    }
    if (materialsTrackingError) {
      materialsTrackingError.textContent = Number(frame.tracking_error || 0).toFixed(5);
    }
    updateMaterialsTrendSelection(frame);
  }

  function stopMaterialsAnimation() {
    if (materialsAnimationTimer !== null) {
      window.clearInterval(materialsAnimationTimer);
      materialsAnimationTimer = null;
    }
    if (materialsAnimateButton) {
      materialsAnimateButton.classList.remove("active");
      materialsAnimateButton.textContent = "Animate";
    }
  }

  function toggleMaterialsAnimation() {
    if (!materialsMotionData) {
      return;
    }
    if (materialsAnimationTimer !== null) {
      stopMaterialsAnimation();
      return;
    }
    if (materialsAnimateButton) {
      materialsAnimateButton.classList.add("active");
      materialsAnimateButton.textContent = "Pause";
    }
    materialsAnimationTimer = window.setInterval(() => {
      const nextIndex = (materialsCurrentFrameIndex + 1) % materialsMotionData.frames.length;
      renderMaterialsState(nextIndex);
    }, 90);
  }

  function loadMaterialsMode() {
    stopMaterialsAnimation();
    const endpoint = buildMedicalExperimentEndpoint();
    const requestSequence = ++materialsRequestSequence;

    if (materialsExperimentCache && materialsExperimentCacheKey === endpoint) {
      const data = materialsExperimentCache;
      materialsMotionData = data;
      materialsBounds = computeMaterialsBounds(data);
      materialsTrendBounds = computeMaterialsTrendBounds(data);
      drawMaterialsFrame(materialsBounds);
      drawMaterialsStaticScene();
      initializeMaterialsDynamicScene();
      renderMaterialsTrendPlots();
      renderMaterialsState(0);
      if (materialsExperimentTitle) {
        materialsExperimentTitle.textContent = String(data.experiment_title || "Medical experiment");
      }
      if (materialsSliderLabel) {
        materialsSliderLabel.textContent = String(data.slider_label || "Motion phase");
      }
      if (materialsGammas) {
        materialsGammas.textContent = data.gammas.map((value) => Number(value).toFixed(2)).join(", ");
      }
      if (materialsKbar) {
        materialsKbar.textContent = data.kbar.map((value) => Number(value).toFixed(3)).join(", ");
      }
      if (materialsMotionTimeInput && Number.isFinite(Number(data.core_motion_time))) {
        materialsMotionTimeInput.value = Number(data.core_motion_time).toFixed(1);
      }
      if (materialsAmplitudeInput && Number.isFinite(Number(data.tip_amplitude))) {
        materialsAmplitudeInput.value = Number(data.tip_amplitude).toFixed(2);
      }
      if (materialsTraceSpan) {
        materialsTraceSpan.textContent = `x ${Number(data.x_min).toFixed(2)} to ${Number(data.x_max).toFixed(2)}, y ${Number(data.y_min).toFixed(2)} to ${Number(data.y_max).toFixed(2)}`;
      }
      if (materialsFrameSlider) {
        materialsFrameSlider.min = "0";
        materialsFrameSlider.max = String(data.frames.length - 1);
        materialsFrameSlider.step = "1";
        materialsFrameSlider.value = "0";
      }
      if (activeMaterialPresetKey && MATERIAL_PRESETS[activeMaterialPresetKey]) {
        setMaterialsPresetNote(getMaterialsPresetStatus(activeMaterialPresetKey));
      } else {
        setMaterialsPresetNote(getMaterialsPresetStatus(""));
      }
      return;
    }

    requestJson(endpoint)
      .then((data) => {
        if (requestSequence !== materialsRequestSequence) {
          return;
        }

        materialsExperimentCache = data;
        materialsExperimentCacheKey = endpoint;
        materialsMotionData = data;
        materialsBounds = computeMaterialsBounds(data);
        materialsTrendBounds = computeMaterialsTrendBounds(data);
        drawMaterialsFrame(materialsBounds);
        drawMaterialsStaticScene();
        initializeMaterialsDynamicScene();
        renderMaterialsTrendPlots();

        if (materialsExperimentTitle) {
          materialsExperimentTitle.textContent = String(data.experiment_title || "Medical experiment");
        }
        if (materialsSliderLabel) {
          materialsSliderLabel.textContent = String(data.slider_label || "Motion phase");
        }
        if (materialsGammas) {
          materialsGammas.textContent = data.gammas.map((value) => Number(value).toFixed(2)).join(", ");
        }
        if (materialsKbar) {
          materialsKbar.textContent = data.kbar.map((value) => Number(value).toFixed(3)).join(", ");
        }
        if (materialsMotionTimeInput && Number.isFinite(Number(data.core_motion_time))) {
          materialsMotionTimeInput.value = Number(data.core_motion_time).toFixed(1);
        }
        if (materialsAmplitudeInput && Number.isFinite(Number(data.tip_amplitude))) {
          materialsAmplitudeInput.value = Number(data.tip_amplitude).toFixed(2);
        }
        if (materialsTraceSpan) {
          materialsTraceSpan.textContent = `x ${Number(data.x_min).toFixed(2)} to ${Number(data.x_max).toFixed(2)}, y ${Number(data.y_min).toFixed(2)} to ${Number(data.y_max).toFixed(2)}`;
        }
        if (materialsFrameSlider) {
          materialsFrameSlider.min = "0";
          materialsFrameSlider.max = String(data.frames.length - 1);
          materialsFrameSlider.step = "1";
          materialsFrameSlider.value = "0";
        }
        if (activeMaterialPresetKey && MATERIAL_PRESETS[activeMaterialPresetKey]) {
          setMaterialsPresetNote(getMaterialsPresetStatus(activeMaterialPresetKey));
        } else {
          setMaterialsPresetNote(getMaterialsPresetStatus(""));
        }

        renderMaterialsState(0);
      })
      .catch((error) => {
        if (requestSequence !== materialsRequestSequence) {
          return;
        }
        console.error(error);
        if (materialsExperimentTitle) {
          materialsExperimentTitle.textContent = "Unavailable";
        }
        if (materialsFrameValue) {
          materialsFrameValue.textContent = "Unavailable";
        }
        if (materialsTargetXY) {
          materialsTargetXY.textContent = "Unavailable";
        }
        if (materialsThetaTip) {
          materialsThetaTip.textContent = "Unavailable";
        }
        if (materialsThetas) {
          materialsThetas.textContent = "Unavailable";
        }
        if (materialsTau) {
          materialsTau.textContent = "Unavailable";
        }
        if (materialsForceMoment) {
          materialsForceMoment.textContent = "Unavailable";
        }
        if (materialsMomentValue) {
          materialsMomentValue.textContent = "M_net = Unavailable";
        }
        if (materialsTrackingError) {
          materialsTrackingError.textContent = "Unavailable";
        }
        if (materialsTraceSpan) {
          materialsTraceSpan.textContent = "Unavailable";
        }
      });
  }

  function scheduleMaterialsReload() {
    if (materialsReloadTimer !== null) {
      window.clearTimeout(materialsReloadTimer);
    }
    setMaterialsPresetNote(
      getMaterialsPresetStatus(activeMaterialPresetKey, { loading: true }),
    );
    materialsReloadTimer = window.setTimeout(() => {
      materialsReloadTimer = null;
      materialsExperimentCache = null;
      materialsExperimentCacheKey = "";
      loadMaterialsMode();
    }, 220);
  }

  function initializeMaterialsPanel() {
    if (!materialsPlot) {
      return;
    }

    if (!materialsPanelInitialized) {
      if (materialsFrameSlider) {
        materialsFrameSlider.addEventListener("input", () => {
          stopMaterialsAnimation();
          renderMaterialsState(Number(materialsFrameSlider.value));
        });
      }
      if (materialsAnimateButton) {
        materialsAnimateButton.addEventListener("click", toggleMaterialsAnimation);
      }
      materialsPresetButtons.forEach((button) => {
        button.addEventListener("click", () => {
          applyMaterialPreset(button.dataset.materialPreset);
        });
      });
      [
        materialsMotionTimeInput,
        materialsAmplitudeInput,
        materialsLengthInput,
        materialsThicknessInput,
        materialsWidthInput,
        materialsYoungsModulusInput,
        materialsYieldStrengthInput,
      ].forEach((inputElement) => {
        if (!inputElement) {
          return;
        }
        inputElement.addEventListener("input", () => {
          if (inputElement !== materialsMotionTimeInput && inputElement !== materialsAmplitudeInput) {
            activeMaterialPresetKey = "";
            updateMaterialsPresetButtons();
            setMaterialsPresetNote(getMaterialsPresetStatus(""));
          }
          stopMaterialsAnimation();
          scheduleMaterialsReload();
        });
      });
      materialsPanelInitialized = true;
    }

    if (!activeMaterialPresetKey && materialsPresetButtons.length > 0) {
      setMaterialsPresetNote(getMaterialsPresetStatus(""));
    }
    loadMaterialsMode();
  }

  function mechanismMapX(value) {
    const ratio = (value - mechanismBounds.xMin) / (mechanismBounds.xMax - mechanismBounds.xMin);
    return mechanismBounds.plotLeft + ratio * (mechanismBounds.plotRight - mechanismBounds.plotLeft);
  }

  function mechanismMapY(value) {
    const ratio = (value - mechanismBounds.yMin) / (mechanismBounds.yMax - mechanismBounds.yMin);
    return mechanismBounds.plotBottom - ratio * (mechanismBounds.plotBottom - mechanismBounds.plotTop);
  }

  function buildMechanismPath(points) {
    return points.map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${mechanismMapX(Number(point[0])).toFixed(2)} ${mechanismMapY(Number(point[1])).toFixed(2)}`;
    }).join(" ");
  }

  function buildMechanismTrendBounds(overlayData) {
    const feaScale = 1 / Number(overlayData.prb_scale_to_fea || 1);
    const feaFrames = overlayData.fea_frames.map((frame) => ({
      angle: wrapAngleDegrees(Number(frame.crank_angle_deg)),
      qx: Number(frame.parts["FLEX-1"].deformed_xy.at(-1)[0]) * feaScale,
      qy: Number(frame.parts["FLEX-1"].deformed_xy.at(-1)[1]) * feaScale,
      positionMagnitude: Math.hypot(
        Number(frame.parts["FLEX-1"].deformed_xy.at(-1)[0]) * feaScale,
        Number(frame.parts["FLEX-1"].deformed_xy.at(-1)[1]) * feaScale,
      ),
      theta0Deg: computeFeaTipAngleDegrees(
        frame.parts["FLEX-1"].deformed_xy.map((point) => [
          Number(point[0]) * feaScale,
          Number(point[1]) * feaScale,
        ]),
      ),
    })).sort((leftFrame, rightFrame) => leftFrame.angle - rightFrame.angle);
    const prbFrames = overlayData.prb_motion.angle_deg.map((angleDeg, index) => ({
      angle: wrapAngleDegrees(Number(angleDeg)),
      qx: Number(overlayData.prb_motion.Q[index][0]),
      qy: Number(overlayData.prb_motion.Q[index][1]),
      positionMagnitude: Math.hypot(
        Number(overlayData.prb_motion.Q[index][0]),
        Number(overlayData.prb_motion.Q[index][1]),
      ),
      theta0Deg: radiansToDegrees(
        overlayData.prb_motion.theta[index].reduce((sum, value) => sum + Number(value), 0),
      ),
    })).sort((leftFrame, rightFrame) => leftFrame.angle - rightFrame.angle);

    const positionValues = [
      ...feaFrames.map((frame) => frame.positionMagnitude),
      ...prbFrames.map((frame) => frame.positionMagnitude),
    ];
    const thetaValues = [
      ...feaFrames.map((frame) => frame.theta0Deg),
      ...prbFrames.map((frame) => frame.theta0Deg),
    ];
    const computeBounds = (values) => {
      const minValue = Math.min(...values);
      const maxValue = Math.max(...values);
      const span = Math.max(maxValue - minValue, 1e-6);
      return {
        min: minValue - 0.08 * span,
        max: maxValue + 0.12 * span,
      };
    };

    return {
      feaFrames,
      prbFrames,
      positionBounds: computeBounds(positionValues),
      thetaBounds: computeBounds(thetaValues),
    };
  }

  function buildTrendPath(points, bounds, plotElement) {
    const width = plotElement.viewBox.baseVal.width;
    const height = plotElement.viewBox.baseVal.height;
    const marginLeft = 42;
    const marginRight = 10;
    const marginTop = 16;
    const marginBottom = 30;
    const usableWidth = width - marginLeft - marginRight;
    const usableHeight = height - marginTop - marginBottom;
    const mapX = (angleValue) => marginLeft + (wrapAngleDegrees(angleValue) / 360) * usableWidth;
    const mapY = (value) => height - marginBottom - ((value - bounds.min) / (bounds.max - bounds.min)) * usableHeight;

    return points.map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${mapX(point.angle).toFixed(2)} ${mapY(point.value).toFixed(2)}`;
    }).join(" ");
  }

  function drawMechanismTrendFrame(gridNode, axesNode, plotElement, yBounds, yLabel) {
    if (!gridNode || !axesNode || !plotElement) {
      return;
    }

    gridNode.replaceChildren();
    axesNode.replaceChildren();

    const width = plotElement.viewBox.baseVal.width;
    const height = plotElement.viewBox.baseVal.height;
    const marginLeft = 42;
    const marginRight = 10;
    const marginTop = 16;
    const marginBottom = 30;
    const left = marginLeft;
    const right = width - marginRight;
    const top = marginTop;
    const bottom = height - marginBottom;
    const usableWidth = width - marginLeft - marginRight;
    const usableHeight = height - marginTop - marginBottom;
    const xTicks = buildTickValues(0, 360, 60);
    const yStep = chooseNiceStep(yBounds.max - yBounds.min);
    const yTicks = buildTickValues(yBounds.min, yBounds.max, yStep);
    const mapX = (angleValue) => marginLeft + (wrapAngleDegrees(angleValue) / 360) * usableWidth;
    const mapY = (value) => height - marginBottom - ((value - yBounds.min) / (yBounds.max - yBounds.min)) * usableHeight;
    const axisY = mapY(yBounds.min <= 0 && yBounds.max >= 0 ? 0 : yBounds.min);

    xTicks.forEach((tick) => {
      const x = mapX(tick);
      gridNode.appendChild(createSvgNode("line", {
        x1: x, y1: top, x2: x, y2: bottom, class: "mechanism-trend-grid-line",
      }));
      axesNode.appendChild(createSvgNode("text", {
        x, y: bottom + 22, "text-anchor": "middle", class: "mechanism-trend-tick-label",
      })).textContent = tick.toFixed(0);
    });

    yTicks.forEach((tick) => {
      const y = mapY(tick);
      gridNode.appendChild(createSvgNode("line", {
        x1: left, y1: y, x2: right, y2: y, class: "mechanism-trend-grid-line",
      }));
      axesNode.appendChild(createSvgNode("text", {
        x: left - 12, y: y + 4, "text-anchor": "end", class: "mechanism-trend-tick-label",
      })).textContent = Number(tick).toFixed(1);
    });

    axesNode.appendChild(createSvgNode("line", {
      x1: left, y1: axisY, x2: right, y2: axisY, class: "mechanism-trend-axis-line",
    }));
    axesNode.appendChild(createSvgNode("line", {
      x1: left, y1: top, x2: left, y2: bottom, class: "mechanism-trend-axis-line",
    }));

    axesNode.appendChild(createSvgNode("text", {
      x: right - 6, y: bottom - 8, "text-anchor": "end", class: "mechanism-trend-axis-label",
    })).textContent = "crank angle (°)";

    const yAxisLabel = createSvgNode("text", {
      x: left + 18, y: top + 16, class: "mechanism-trend-axis-label",
      transform: `rotate(-90 ${left + 18} ${top + 16})`,
      "text-anchor": "middle",
    });
    yAxisLabel.textContent = yLabel;
    axesNode.appendChild(yAxisLabel);
  }

  function renderMechanismTrendPlots() {
    if (!mechanismOverlayData || !mechanismTrendBounds) {
      return;
    }

    const feaPositionPoints = mechanismTrendBounds.feaFrames.map((frame) => ({
      angle: frame.angle,
      value: frame.positionMagnitude,
    }));
    const prbPositionPoints = mechanismTrendBounds.prbFrames.map((frame) => ({
      angle: frame.angle,
      value: frame.positionMagnitude,
    }));
    const feaThetaPoints = mechanismTrendBounds.feaFrames.map((frame) => ({
      angle: frame.angle,
      value: frame.theta0Deg,
    }));
    const prbThetaPoints = mechanismTrendBounds.prbFrames.map((frame) => ({
      angle: frame.angle,
      value: frame.theta0Deg,
    }));

    drawMechanismTrendFrame(
      mechanismYTrendGrid,
      mechanismYTrendAxes,
      mechanismYTrendPlot,
      mechanismTrendBounds.positionBounds,
      "|Q| / l",
    );
    drawMechanismTrendFrame(
      mechanismXTrendGrid,
      mechanismXTrendAxes,
      mechanismXTrendPlot,
      mechanismTrendBounds.thetaBounds,
      "\u03b80 (\u00b0)",
    );

    if (mechanismYTrendFEA) {
      mechanismYTrendFEA.setAttribute("d", buildTrendPath(feaPositionPoints, mechanismTrendBounds.positionBounds, mechanismYTrendPlot));
    }
    if (mechanismYTrendPRB) {
      mechanismYTrendPRB.setAttribute("d", buildTrendPath(prbPositionPoints, mechanismTrendBounds.positionBounds, mechanismYTrendPlot));
    }
    if (mechanismXTrendFEA) {
      mechanismXTrendFEA.setAttribute("d", buildTrendPath(feaThetaPoints, mechanismTrendBounds.thetaBounds, mechanismXTrendPlot));
    }
    if (mechanismXTrendPRB) {
      mechanismXTrendPRB.setAttribute("d", buildTrendPath(prbThetaPoints, mechanismTrendBounds.thetaBounds, mechanismXTrendPlot));
    }
  }

  function updateMechanismTrendSelection(feaAngleDeg, prbAngleDeg, feaPositionMagnitude, prbPositionMagnitude, feaTheta0Deg, prbTheta0Deg) {
    const updatePlotSelection = (plotElement, bounds, cursorNode, feaPointNode, prbPointNode, feaValue, prbValue) => {
      if (!plotElement || !bounds) {
        return;
      }
      const width = plotElement.viewBox.baseVal.width;
      const height = plotElement.viewBox.baseVal.height;
      const marginLeft = 42;
      const marginRight = 10;
      const marginTop = 16;
      const marginBottom = 30;
      const usableWidth = width - marginLeft - marginRight;
      const usableHeight = height - marginTop - marginBottom;
      const mapX = (angleValue) => marginLeft + (wrapAngleDegrees(angleValue) / 360) * usableWidth;
      const mapY = (value) => height - marginBottom - ((value - bounds.min) / (bounds.max - bounds.min)) * usableHeight;
      const cursorX = mapX(feaAngleDeg);

      if (cursorNode) {
        cursorNode.setAttribute("x1", cursorX);
        cursorNode.setAttribute("x2", cursorX);
        cursorNode.setAttribute("y1", marginTop);
        cursorNode.setAttribute("y2", height - marginBottom);
      }
      if (feaPointNode) {
        feaPointNode.setAttribute("cx", mapX(feaAngleDeg));
        feaPointNode.setAttribute("cy", mapY(feaValue));
      }
      if (prbPointNode) {
        prbPointNode.setAttribute("cx", mapX(prbAngleDeg));
        prbPointNode.setAttribute("cy", mapY(prbValue));
      }
    };

    updatePlotSelection(
      mechanismYTrendPlot,
      mechanismTrendBounds?.positionBounds,
      mechanismYTrendCursor,
      mechanismYTrendPointFEA,
      mechanismYTrendPointPRB,
      Number(feaPositionMagnitude),
      Number(prbPositionMagnitude),
    );
    updatePlotSelection(
      mechanismXTrendPlot,
      mechanismTrendBounds?.thetaBounds,
      mechanismXTrendCursor,
      mechanismXTrendPointFEA,
      mechanismXTrendPointPRB,
      Number(feaTheta0Deg),
      Number(prbTheta0Deg),
    );
  }

  function drawMechanismFrame() {
    if (!mechanismPlot || !mechanismGrid || !mechanismAxes || !mechanismBounds) {
      return;
    }

    mechanismGrid.replaceChildren();
    mechanismAxes.replaceChildren();

    const xTicks = buildTickValues(mechanismBounds.xMin, mechanismBounds.xMax, MECHANISM_CONFIG.gridStep);
    const yTicks = buildTickValues(mechanismBounds.yMin, mechanismBounds.yMax, MECHANISM_CONFIG.gridStep);
    const right = mechanismBounds.plotRight;
    const top = mechanismBounds.plotTop;
    const left = mechanismBounds.plotLeft;
    const bottom = mechanismBounds.plotBottom;
    const axisX = mechanismMapX(0);
    const axisY = mechanismMapY(0);

    xTicks.forEach((tick) => {
      const x = mechanismMapX(tick);
      mechanismGrid.appendChild(createSvgNode("line", {
        x1: x, y1: top, x2: x, y2: bottom, class: "mechanism-grid-line",
      }));
      mechanismAxes.appendChild(createSvgNode("text", {
        x, y: bottom + 24, "text-anchor": "middle", class: "mechanism-tick-label",
      })).textContent = tick.toFixed(1);
    });

    yTicks.forEach((tick) => {
      const y = mechanismMapY(tick);
      mechanismGrid.appendChild(createSvgNode("line", {
        x1: left, y1: y, x2: right, y2: y, class: "mechanism-grid-line",
      }));
      mechanismAxes.appendChild(createSvgNode("text", {
        x: left - 14, y: y + 4, "text-anchor": "end", class: "mechanism-tick-label",
      })).textContent = tick.toFixed(1);
    });

    mechanismAxes.appendChild(createSvgNode("line", {
      x1: left, y1: axisY, x2: right, y2: axisY, class: "mechanism-axis-line",
    }));
    mechanismAxes.appendChild(createSvgNode("line", {
      x1: axisX, y1: top, x2: axisX, y2: bottom, class: "mechanism-axis-line",
    }));

    mechanismAxes.appendChild(createSvgNode("text", {
      x: right - 8, y: axisY - 10, "text-anchor": "end", class: "mechanism-axis-label",
    })).textContent = "x / l";

    const yLabel = createSvgNode("text", {
      x: axisX + 20, y: top + 18, class: "mechanism-axis-label",
      transform: `rotate(-90 ${axisX + 20} ${top + 18})`,
      "text-anchor": "middle",
    });
    yLabel.textContent = "y / l";
    mechanismAxes.appendChild(yLabel);
  }

  function buildMechanismPath(points, scale = 1) {
    return points.map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${mechanismMapX(Number(point[0]) * scale).toFixed(2)} ${mechanismMapY(Number(point[1]) * scale).toFixed(2)}`;
    }).join(" ");
  }

  function setSvgVisibility(node, isVisible) {
    if (!node) {
      return;
    }
    node.style.display = isVisible ? "" : "none";
  }

  function applyMechanismVisibility() {
    const showFEA = !mechanismShowFEA || mechanismShowFEA.checked;
    const showPRB = !mechanismShowPRB || mechanismShowPRB.checked;

    [
      mechanismFEACrank,
      mechanismFEACoupler,
      mechanismFEAFlex,
      mechanismFEAFlexNodes,
      mechanismYTrendFEA,
      mechanismXTrendFEA,
      mechanismYTrendPointFEA,
      mechanismXTrendPointFEA,
    ].forEach((node) => setSvgVisibility(node, showFEA));

    [
      mechanismPRBChain,
      mechanismBALink,
      mechanismAQLink,
      mechanismJointPoints,
      mechanismQPoint,
      mechanismAPoint,
      mechanismCrankPoint,
      mechanismOrigin,
      mechanismBAnchor,
      mechanismYTrendPRB,
      mechanismXTrendPRB,
      mechanismYTrendPointPRB,
      mechanismXTrendPointPRB,
    ].forEach((node) => setSvgVisibility(node, showPRB));

    [
      mechanismYTrendCursor,
      mechanismXTrendCursor,
    ].forEach((node) => setSvgVisibility(node, showFEA || showPRB));
  }

  function findNearestMechanismFrameIndex(angleDeg) {
    if (!mechanismOverlayData) {
      return 0;
    }
    const targetAngle = wrapAngleDegrees(angleDeg);
    let bestIndex = 0;
    let bestDistance = Number.POSITIVE_INFINITY;

    mechanismOverlayData.fea_frames.forEach((frame, index) => {
      const currentDistance = angleDistanceDegrees(targetAngle, Number(frame.crank_angle_deg));
      if (currentDistance < bestDistance) {
        bestDistance = currentDistance;
        bestIndex = index;
      }
    });

    return bestIndex;
  }

  function renderMechanismState(index) {
    if (!mechanismOverlayData || !mechanismBounds) {
      return;
    }

    const frameIndex = clamp(index, 0, mechanismOverlayData.fea_frames.length - 1);
    const frame = mechanismOverlayData.fea_frames[frameIndex];
    const feaScale = 1 / Number(mechanismOverlayData.prb_scale_to_fea || 1);
    const prbIndex = Number(frame.matched_prb_index);
    const prbMotion = mechanismOverlayData.prb_motion;
    const chain = prbMotion.chain[prbIndex];
    const qPoint = prbMotion.Q[prbIndex];
    const aPoint = prbMotion.A[prbIndex];
    const crankPoint = prbMotion.crank_tip[prbIndex];
    const thetaRow = prbMotion.theta[prbIndex];
    const loadRow = prbMotion.load[prbIndex];
    const prbAngleDeg = Number(prbMotion.angle_deg[prbIndex]);
    const feaAngleDeg = Number(frame.crank_angle_deg);
    const feaCrank = frame.parts["CRANK-1"].deformed_xy.map((point) => point.map((value) => Number(value) * feaScale));
    const feaCoupler = frame.parts["COUP-1"].deformed_xy.map((point) => point.map((value) => Number(value) * feaScale));
    const feaFlex = frame.parts["FLEX-1"].deformed_xy.map((point) => point.map((value) => Number(value) * feaScale));
    const feaA = feaCrank[feaCrank.length - 1];
    const feaQ = feaFlex[feaFlex.length - 1];
    const feaTipDeg = computeFeaTipAngleDegrees(feaFlex);
    const prbTipDeg = radiansToDegrees(thetaRow.reduce((sum, value) => sum + Number(value), 0));
    const feaPositionMagnitude = computePositionMagnitude(feaQ);
    const prbPositionMagnitude = computePositionMagnitude(qPoint);
    const aError = Math.hypot(Number(aPoint[0]) - Number(feaA[0]), Number(aPoint[1]) - Number(feaA[1]));
    const qError = Math.hypot(Number(qPoint[0]) - Number(feaQ[0]), Number(qPoint[1]) - Number(feaQ[1]));

    mechanismCurrentFrameIndex = frameIndex;

    mechanismFEACrank.setAttribute("d", buildMechanismPath(feaCrank));
    mechanismFEACoupler.setAttribute("d", buildMechanismPath(feaCoupler));
    mechanismFEAFlex.setAttribute("d", buildMechanismPath(feaFlex));

    if (mechanismFEAFlexNodes) {
      ensureCirclePool(mechanismFEAFlexNodes, mechanismFEAFlexNodePool, feaFlex.length, () => ({
        r: 2.8,
        class: "mechanism-flex-node",
      }));
      feaFlex.forEach((point, pointIndex) => {
        const node = mechanismFEAFlexNodePool[pointIndex];
        node.setAttribute("cx", mechanismMapX(Number(point[0])));
        node.setAttribute("cy", mechanismMapY(Number(point[1])));
      });
    }

    mechanismPRBChain.setAttribute("d", buildMechanismPath(chain));
    mechanismBALink.setAttribute("d", buildMechanismPath([prbMotion.B, crankPoint]));
    mechanismAQLink.setAttribute("d", buildMechanismPath([aPoint, qPoint]));

    if (mechanismJointPoints) {
      ensureCirclePool(mechanismJointPoints, mechanismJointPointPool, chain.length, () => ({
        r: 2.8,
        class: "mechanism-joint",
      }));
      chain.forEach((point, pointIndex) => {
        const node = mechanismJointPointPool[pointIndex];
        node.setAttribute("cx", mechanismMapX(Number(point[0])));
        node.setAttribute("cy", mechanismMapY(Number(point[1])));
      });
    }

    mechanismOrigin.setAttribute("cx", mechanismMapX(0));
    mechanismOrigin.setAttribute("cy", mechanismMapY(0));
    mechanismBAnchor.setAttribute("cx", mechanismMapX(Number(prbMotion.B[0])));
    mechanismBAnchor.setAttribute("cy", mechanismMapY(Number(prbMotion.B[1])));
    mechanismQPoint.setAttribute("cx", mechanismMapX(Number(qPoint[0])));
    mechanismQPoint.setAttribute("cy", mechanismMapY(Number(qPoint[1])));
    mechanismAPoint.setAttribute("cx", mechanismMapX(Number(aPoint[0])));
    mechanismAPoint.setAttribute("cy", mechanismMapY(Number(aPoint[1])));
    mechanismCrankPoint.setAttribute("cx", mechanismMapX(Number(crankPoint[0])));
    mechanismCrankPoint.setAttribute("cy", mechanismMapY(Number(crankPoint[1])));

    const displayAngle = wrapAngleDegrees(feaAngleDeg);
    mechanismAngleSlider.value = displayAngle.toFixed(1);
    mechanismAngleInput.value = displayAngle.toFixed(1);
    if (mechanismFrameAngles) {
      mechanismFrameAngles.textContent = `${formatDegrees(feaAngleDeg)} / ${formatDegrees(prbAngleDeg)}`;
    }
    mechanismThetas.textContent = thetaRow.map((value) => formatDegrees(Number(value) * 180 / Math.PI, 1)).join(" / ");
    mechanismTipSlope.textContent = `${formatDegrees(feaTipDeg)} / ${formatDegrees(prbTipDeg)}`;
    mechanismQValue.textContent = `${formatPair(feaQ)} / ${formatPair(qPoint)}`;
    mechanismAValue.textContent = `${formatPair(feaA)} / ${formatPair(aPoint)}`;
    mechanismErrors.textContent = `${(100 * aError).toFixed(2)} / ${(100 * qError).toFixed(2)}`;
    mechanismLoadValue.textContent = `${Number(loadRow[0]).toFixed(3)} / ${Number(loadRow[1]).toFixed(3)} / ${Number(loadRow[2]).toFixed(3)}`;
    updateMechanismTrendSelection(
      feaAngleDeg,
      prbAngleDeg,
      feaPositionMagnitude,
      prbPositionMagnitude,
      feaTipDeg,
      prbTipDeg,
    );
    applyMechanismVisibility();
  }

  function setMechanismFrame(value) {
    if (!mechanismOverlayData || !mechanismAngleSlider || !mechanismAngleInput) {
      return;
    }
    const minValue = Number(mechanismAngleSlider.min);
    const maxValue = Number(mechanismAngleSlider.max);
    const stepValue = Number(mechanismAngleSlider.step || 0.5);
    const normalizedValue = snapToStep(clamp(value, minValue, maxValue), minValue, stepValue);
    renderMechanismState(findNearestMechanismFrameIndex(normalizedValue));
  }

  function stopMechanismAnimation() {
    if (mechanismAnimationTimer !== null) {
      window.clearInterval(mechanismAnimationTimer);
      mechanismAnimationTimer = null;
    }
    if (mechanismAnimateButton) {
      mechanismAnimateButton.classList.remove("active");
      mechanismAnimateButton.textContent = "Animate";
    }
  }

  function toggleMechanismAnimation() {
    if (!mechanismOverlayData) {
      return;
    }
    if (mechanismAnimationTimer !== null) {
      stopMechanismAnimation();
      return;
    }

    if (mechanismAnimateButton) {
      mechanismAnimateButton.classList.add("active");
      mechanismAnimateButton.textContent = "Pause";
    }

    mechanismAnimationTimer = window.setInterval(() => {
      const nextIndex = (mechanismCurrentFrameIndex + 1) % mechanismOverlayData.fea_frames.length;
      renderMechanismState(nextIndex);
    }, 80);
  }

  function initializeMechanismPanel() {
    if (!mechanismPlot || mechanismLoaded) {
      return;
    }

    requestJson(MECHANISM_CONFIG.endpoint)
      .then((data) => {
        mechanismOverlayData = data;
        mechanismBounds = buildMechanismBounds(data);
        mechanismTrendBounds = buildMechanismTrendBounds(data);
        drawMechanismFrame();
        renderMechanismTrendPlots();
        if (mechanismParameterSource) {
          mechanismParameterSource.textContent = String(data.parameter_source);
        }
        mechanismGammas.textContent = data.gammas.map((value) => Number(value).toFixed(2)).join(", ");
        mechanismKbar.textContent = data.kbar.map((value) => Number(value).toFixed(3)).join(", ");

        if (mechanismAngleSlider && mechanismAngleInput) {
          mechanismAngleSlider.min = "0";
          mechanismAngleSlider.max = "360";
          mechanismAngleSlider.step = "0.5";
          mechanismAngleInput.min = mechanismAngleSlider.min;
          mechanismAngleInput.max = mechanismAngleSlider.max;
          mechanismAngleInput.step = "0.5";

          mechanismAngleSlider.addEventListener("input", () => {
            setMechanismFrame(Number(mechanismAngleSlider.value));
          });
          mechanismAngleInput.addEventListener("input", () => {
            const typedValue = Number(mechanismAngleInput.value);
            if (Number.isFinite(typedValue)) {
              setMechanismFrame(typedValue);
            }
          });
          mechanismAngleInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
              mechanismAngleInput.blur();
            }
          });
        }

        if (mechanismShowFEA) {
          mechanismShowFEA.addEventListener("change", applyMechanismVisibility);
        }
        if (mechanismShowPRB) {
          mechanismShowPRB.addEventListener("change", applyMechanismVisibility);
        }
        if (mechanismAnimateButton) {
          mechanismAnimateButton.addEventListener("click", toggleMechanismAnimation);
        }

        renderMechanismState(0);
        mechanismLoaded = true;
      })
      .catch((error) => {
        stopMechanismAnimation();
        console.error(error);
        if (mechanismParameterSource) {
          mechanismParameterSource.textContent = "Unavailable";
        }
      });
  }

  function initializeAtlasPanel() {
    if (!atlasPlot) return;
    drawAtlasFrame();
    bindSliderAndInput("kappa");
    bindSliderAndInput("phi");
    bindAllowableThetaControls();
    bindBeamInputs();
    atlasModeTabs.forEach((button) => {
      button.addEventListener("click", () => {
        setAtlasMode(button.dataset.atlasMode);
      });
    });
    atlasDetailTabs.forEach((button) => {
      button.addEventListener("click", () => {
        setDetailMode(button.dataset.detailMode);
      });
    });
    setDetailMode("theta");
    setAtlasMode("interactive");
    updateAtlasPanel();
  }

  function setActiveTab(tabKey) {
    const title = TAB_METADATA[tabKey];
    if (!title) return;

    for (const button of tabButtons) {
      const isActive = button.dataset.tabTarget === tabKey;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
      button.tabIndex = isActive ? 0 : -1;
    }

    for (const panel of tabPanels) {
      const isActive = panel.dataset.tabPanel === tabKey;
      panel.classList.toggle("active", isActive);
    }

    document.title = `${title} | Compliant Design Workspace`;

    if (tabKey === "prb") {
      initializePrbPanel();
    }

    if (tabKey === "mechanism") {
      initializeMechanismPanel();
    }

    if (tabKey === "materials") {
      initializeMaterialsPanel();
    }
  }

  for (const button of tabButtons) {
    button.addEventListener("click", () => {
      setActiveTab(button.dataset.tabTarget);
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeActivePlotZoom();
    }
  });

  applyUiNotationLabels();
  ensurePlotZoomControls();
  initializeAtlasPanel();
  setActiveTab("atlas");
}());
