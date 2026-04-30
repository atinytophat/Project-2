from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np
from scipy.integrate import quad
from scipy.optimize import least_squares


HOST = "127.0.0.1"
PORT = 8123
WEBAPP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = WEBAPP_DIR.parent
VERIFICATION_CSV_CANDIDATES = (
    PROJECT_DIR / "verificationdata.csv",
    PROJECT_DIR / "Abaqus" / "verificationdata.csv",
)

NUM_POINTS = 150
INTERACTIVE_DEFAULT_K = 0.0
INTERACTIVE_DEFAULT_PHI_DEG = 90.0
INTERACTIVE_NUM_POINTS = 120
REPORT_K_VALUES = [0, 0.1, 1, 1.5, 2, 2.5, 5, 50]
REPORT_FORCE_ANGLES_DEG = [9, 27, 45, 63, 81, 99, 117, 135, 153, 171]

DEFAULT_BEAM_LENGTH = 0.100
DEFAULT_BEAM_WIDTH = 0.020
DEFAULT_THICKNESS = 0.001
DEFAULT_YOUNGS_MODULUS = 69.0e9
DEFAULT_SIGMA_MAX = 276.0e6

SECTION4_L_OVER_T = 100.0
SECTION4_SIGMA_OVER_E = 0.03
SECTION4_GAMMA_STEP = 0.05
SECTION4_NUM_MOMENT_SAMPLES = 80
SECTION4_NUM_FORCE_SAMPLES = 80
SECTION4_FORCE_FIT_FRACTION = 0.35

SECTION500_KAPPA_VALUES = np.array([0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0], dtype=float)
SECTION510_NUM_KAPPA_FIT_THETA_SAMPLES = 80
SECTION510_FIGURE12_LOAD_RATIOS = [0.0, 0.1, 1.0, 2.0, 5.0, 25.0]
SECTION510_FIGURE12_FORCE_ANGLE_DEG = 90.0
SECTION510_FIGURE13_FORCE_ANGLES_DEG = [30.0, 60.0, 120.0, 135.0, 150.0, 175.0]
SECTION510_FIGURE13_LOAD_RATIO = 0.0
SECTION510_NUM_LOCUS_POINTS = 90

SECTION520_CRANK_START_DEG = 0.0
SECTION520_CRANK_END_DEG = 360.0
SECTION520_NUM_SAMPLES = 361
SECTION520_AU = -1.0 / math.sqrt(2.0)
SECTION520_AV = 1.0 / math.sqrt(2.0)
SECTION520_R = 1.0 - math.sqrt(2.0) / 2.0
SECTION520_B = np.array([0.0, 1.0 / math.sqrt(2.0)], dtype=float)
SECTION520_INITIAL_GUESS_SCALE = np.array([0.35, 0.40, 0.25], dtype=float)
SECTION520_PARAMETER_SOURCE = "Computed locally from Section 4.4 search + Section 5.0/5.1 load-independent averaging"
SECTION520_TO_FEA_SCALE = 100.0

FEA_PART_NAMES = ("CRANK-1", "COUP-1", "FLEX-1")

SECTION520_PARAMETER_CACHE: dict[str, object] | None = None
SECTION520_MOTION_CACHE: dict[str, object] | None = None
SECTION520_OVERLAY_CACHE: dict[str, object] | None = None
SECTION4_WORKSPACE_CACHE: dict[str, object] | None = None
SECTION700_EXPERIMENT_CACHE: dict[str, dict[str, object]] = {}
SECTION700_NUM_FRAMES = 81
SECTION700_CIRCLE_CENTER_X = 0.8
SECTION700_CIRCLE_CENTER_Y = 0.0
SECTION700_CIRCLE_RADIUS = 0.2
SECTION700_START_ANGLE_DEG = 0.0
SECTION700_END_ANGLE_DEG = 360.0
SECTION701_TIP_AMPLITUDE = 0.10
SECTION701_CORE_MOTION_TIME = 8.0
SECTION701_END_HOLD_TIME = 1.0
SECTION701_MAX_HEADING_DEG = 25.0
SECTION701_CONTINUITY_WEIGHT = 1.0e-3


@dataclass(frozen=True)
class ExtremeLoadFit:
    gammas: np.ndarray
    objective: float


@dataclass
class VerificationPartFrame:
    node_labels: np.ndarray
    base_xy: np.ndarray
    deformed_xy: np.ndarray


@dataclass
class VerificationFrame:
    frame_label: str
    step_time: float
    parts: dict[str, VerificationPartFrame]


def mad(values: np.ndarray) -> float:
    median = np.median(values)
    return float(np.median(np.abs(values - median)))


def compute_state_with_alpha(th0: float, phi: float, k_value: float) -> tuple[float, float, float]:
    if th0 == 0.0:
        return 0.0, 1.0, 0.0

    def denom(t: float) -> float:
        return max(np.cos(th0 - phi) - np.cos(t - phi) + k_value, 1.0e-12)

    sqralp = quad(
        lambda t: 0.5 * (1.0 / np.sqrt(denom(t))),
        0.0,
        th0,
        limit=300,
    )[0]

    alpha_value = sqralp * sqralp
    a_l = quad(
        lambda t: (1.0 / (2.0 * sqralp)) * (np.cos(t) / np.sqrt(denom(t))),
        0.0,
        th0,
        limit=300,
    )[0]
    b_l = quad(
        lambda t: (1.0 / (2.0 * sqralp)) * (np.sin(t) / np.sqrt(denom(t))),
        0.0,
        th0,
        limit=300,
    )[0]

    return float(alpha_value), float(a_l), float(b_l)


def compute_single_state(th0: float, phi: float, k_value: float) -> tuple[float, float]:
    _, a_l, b_l = compute_state_with_alpha(th0, phi, k_value)
    return a_l, b_l


def current_curve_cutoff(a_l: np.ndarray, b_l: np.ndarray, ths: np.ndarray, k_value: float) -> int:
    kl = len(a_l)
    idx = kl

    if 0 < k_value < 2:
        d2x = np.gradient(np.gradient(a_l, ths), ths)
        thresh_x = np.median(np.abs(d2x)) + 4.0 * mad(d2x)
        idx_x = next((i + 1 for i, val in enumerate(np.abs(d2x)) if val > thresh_x), kl)

        d2y = np.gradient(np.gradient(b_l, ths), ths)
        thresh_y = np.median(np.abs(d2y)) + 4.0 * mad(d2y)
        idx_y = next((i + 1 for i, val in enumerate(np.abs(d2y)) if val > thresh_y), kl)
        idx = min(idx_x, idx_y)
    elif k_value == 0:
        idx = kl - 1

    return idx


def theta0_max_for_case(phi: float, k_value: float, eps_th: float = 1.0e-6) -> float:
    if k_value <= 2:
        return min(np.pi, phi + np.arccos(1.0 - k_value)) - eps_th
    return np.pi - eps_th


def generate_locus_for_case(
    phi: float,
    k_value: float,
    num_points_local: int = NUM_POINTS,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    th_max = theta0_max_for_case(phi, k_value)
    ths = np.linspace(0.0, th_max, num_points_local)
    a_l = np.zeros_like(ths)
    b_l = np.zeros_like(ths)

    for j, th0 in enumerate(ths):
        a_l[j], b_l[j] = compute_single_state(float(th0), float(phi), float(k_value))

    cutoff = current_curve_cutoff(a_l, b_l, ths, float(k_value))
    return ths[:cutoff], a_l[:cutoff], b_l[:cutoff]


def sampled_trajectory(theta_values: np.ndarray, phi_deg_value: float, kappa: float) -> tuple[np.ndarray, np.ndarray]:
    a_values = np.zeros_like(theta_values, dtype=float)
    b_values = np.zeros_like(theta_values, dtype=float)
    phi_rad = np.deg2rad(phi_deg_value)

    for idx, theta0 in enumerate(theta_values):
        _, a_l, b_l = compute_state_with_alpha(float(theta0), phi_rad, float(kappa))
        a_values[idx] = float(a_l)
        b_values[idx] = float(b_l)

    return a_values, b_values


def rectangular_second_moment(width: float, thickness_value: float) -> float:
    return float(width * thickness_value**3 / 12.0)


def stress_limited_theta_max_from_section22(l_over_t_value: float, sigma_over_e_value: float) -> float:
    return float(2.0 * l_over_t_value * sigma_over_e_value)


def effective_theta0_limit(theta_stress_max: float, theta_geometric_max: float) -> tuple[float, str]:
    if theta_stress_max <= theta_geometric_max:
        return float(theta_stress_max), "stress"
    return float(theta_geometric_max), "geometric"


def selected_state(
    theta0_rad: float,
    phi_deg_value: float,
    kappa: float,
    length: float,
    e_modulus: float,
    inertia: float,
) -> dict[str, float]:
    theta0_rad = float(max(0.0, theta0_rad))
    alpha_value, a_l, b_l = compute_state_with_alpha(
        theta0_rad,
        np.deg2rad(phi_deg_value),
        float(kappa),
    )
    beta_value = 0.0 if kappa == 0.0 else 2.0 * np.sqrt(float(kappa) * float(alpha_value))
    force_value = 2.0 * e_modulus * inertia * float(alpha_value) / (length * length)
    moment_value = e_modulus * inertia * float(beta_value) / length
    return {
        "theta0_rad": float(theta0_rad),
        "theta0_deg": float(np.rad2deg(theta0_rad)),
        "a_over_l": float(a_l),
        "b_over_l": float(b_l),
        "alpha": float(alpha_value),
        "beta": float(beta_value),
        "force": float(force_value),
        "moment": float(moment_value),
    }


def read_beam_parameters(params: dict[str, list[str]]) -> dict[str, float]:
    beam_length = float(params.get("beam_length", [DEFAULT_BEAM_LENGTH])[0])
    beam_width = float(params.get("beam_width", [DEFAULT_BEAM_WIDTH])[0])
    thickness = float(params.get("thickness", [DEFAULT_THICKNESS])[0])
    youngs_modulus = float(params.get("youngs_modulus", [DEFAULT_YOUNGS_MODULUS])[0])
    sigma_max = float(params.get("sigma_max", [DEFAULT_SIGMA_MAX])[0])

    if beam_length <= 0.0 or beam_width <= 0.0 or thickness <= 0.0:
        raise ValueError("Beam dimensions must be positive.")
    if youngs_modulus <= 0.0 or sigma_max <= 0.0:
        raise ValueError("Material properties must be positive.")

    return {
        "beam_length": beam_length,
        "beam_width": beam_width,
        "thickness": thickness,
        "youngs_modulus": youngs_modulus,
        "sigma_max": sigma_max,
    }


def atlas_limits(phi_deg_value: float, kappa: float, beam: dict[str, float]) -> dict[str, float | str]:
    inertia = rectangular_second_moment(beam["beam_width"], beam["thickness"])
    theta_stress_max = stress_limited_theta_max_from_section22(
        beam["beam_length"] / beam["thickness"],
        beam["sigma_max"] / beam["youngs_modulus"],
    )
    theta_geometric_max = theta0_max_for_case(np.deg2rad(phi_deg_value), kappa)
    theta0_limit, governing_limit = effective_theta0_limit(theta_stress_max, theta_geometric_max)
    endpoint = selected_state(
        theta0_limit,
        phi_deg_value,
        kappa,
        beam["beam_length"],
        beam["youngs_modulus"],
        inertia,
    )

    return {
        "beam_length": float(beam["beam_length"]),
        "beam_width": float(beam["beam_width"]),
        "thickness": float(beam["thickness"]),
        "youngs_modulus": float(beam["youngs_modulus"]),
        "sigma_max": float(beam["sigma_max"]),
        "inertia": float(inertia),
        "theta0_stress_max_rad": float(theta_stress_max),
        "theta0_stress_max_deg": float(np.rad2deg(theta_stress_max)),
        "theta0_geometric_max_rad": float(theta_geometric_max),
        "theta0_geometric_max_deg": float(np.rad2deg(theta_geometric_max)),
        "theta0_limit_rad": float(theta0_limit),
        "theta0_limit_deg": float(np.rad2deg(theta0_limit)),
        "governing_limit": str(governing_limit),
        "endpoint_force": float(endpoint["force"]),
        "endpoint_moment": float(endpoint["moment"]),
    }


def precompute_state_samples(
    theta_values: np.ndarray,
    load_case: str,
) -> list[tuple[float, float, float, float, float, float]]:
    state_samples: list[tuple[float, float, float, float, float, float]] = []
    for theta0 in theta_values:
        if load_case == "pure_moment":
            if theta0 == 0.0:
                qx, qy = 1.0, 0.0
            else:
                qx = math.sin(theta0) / theta0
                qy = (1.0 - math.cos(theta0)) / theta0
            alpha_value = 0.0
            beta_value = float(theta0)
        else:
            alpha_value, qx, qy = compute_state_with_alpha(float(theta0), math.pi / 2.0, 0.0)
            beta_value = 0.0
        state_samples.append(
            (
                float(theta0),
                float(qx),
                float(qy),
                float(alpha_value),
                float(beta_value),
                math.pi / 2.0,
            )
        )
    return state_samples


def prb3r_forward_kinematics(theta: np.ndarray, gammas: np.ndarray) -> tuple[float, float, float]:
    theta1, theta2, theta3 = theta
    theta12 = theta1 + theta2
    theta123 = theta12 + theta3
    qx = (
        gammas[0]
        + gammas[1] * math.cos(theta1)
        + gammas[2] * math.cos(theta12)
        + gammas[3] * math.cos(theta123)
    )
    qy = (
        gammas[1] * math.sin(theta1)
        + gammas[2] * math.sin(theta12)
        + gammas[3] * math.sin(theta123)
    )
    return qx, qy, theta123


def prb3r_inverse_kinematics_candidates(
    qx: float,
    qy: float,
    theta0: float,
    gammas: np.ndarray,
) -> list[np.ndarray]:
    px = qx - gammas[0] - gammas[3] * math.cos(theta0)
    py = qy - gammas[3] * math.sin(theta0)

    denom = 2.0 * gammas[1] * gammas[2]
    cos_theta2 = (px * px + py * py - gammas[1] ** 2 - gammas[2] ** 2) / denom
    if cos_theta2 < -1.0 - 1.0e-10 or cos_theta2 > 1.0 + 1.0e-10:
        return []

    cos_theta2 = max(-1.0, min(1.0, cos_theta2))
    theta2_candidates = [math.acos(cos_theta2), -math.acos(cos_theta2)]
    solutions: list[np.ndarray] = []

    for theta2 in theta2_candidates:
        base = gammas[1] ** 2 + gammas[2] ** 2 + 2.0 * gammas[1] * gammas[2] * math.cos(theta2)
        cos_theta1 = (
            px * (gammas[1] + gammas[2] * math.cos(theta2))
            + py * gammas[2] * math.sin(theta2)
        ) / base
        sin_theta1 = (
            py * (gammas[1] + gammas[2] * math.cos(theta2))
            - px * gammas[2] * math.sin(theta2)
        ) / base
        theta1 = math.atan2(sin_theta1, cos_theta1)
        theta3 = theta0 - theta1 - theta2
        candidate = np.array([theta1, theta2, theta3], dtype=float)
        qx_check, qy_check, theta0_check = prb3r_forward_kinematics(candidate, gammas)
        if (
            abs(qx_check - qx) < 1.0e-8
            and abs(qy_check - qy) < 1.0e-8
            and abs(theta0_check - theta0) < 1.0e-8
        ):
            solutions.append(candidate)

    return solutions


def prb3r_inverse_kinematics(qx: float, qy: float, theta0: float, gammas: np.ndarray) -> np.ndarray | None:
    solutions = prb3r_inverse_kinematics_candidates(qx, qy, theta0, gammas)
    if not solutions:
        return None

    if theta0 >= 0.0:
        solutions.sort(key=lambda vec: (np.sum(np.maximum(0.0, -vec) ** 2), np.linalg.norm(vec)))
    else:
        solutions.sort(key=lambda vec: (np.sum(np.maximum(0.0, vec) ** 2), np.linalg.norm(vec)))
    return solutions[0]


def prb3r_jacobian(theta: np.ndarray, gammas: np.ndarray) -> np.ndarray:
    theta1, theta2, theta3 = theta
    theta12 = theta1 + theta2
    theta123 = theta12 + theta3
    return np.array(
        [
            [
                -(
                    gammas[1] * math.sin(theta1)
                    + gammas[2] * math.sin(theta12)
                    + gammas[3] * math.sin(theta123)
                ),
                -(gammas[2] * math.sin(theta12) + gammas[3] * math.sin(theta123)),
                -gammas[3] * math.sin(theta123),
            ],
            [
                gammas[1] * math.cos(theta1)
                + gammas[2] * math.cos(theta12)
                + gammas[3] * math.cos(theta123),
                gammas[2] * math.cos(theta12) + gammas[3] * math.cos(theta123),
                gammas[3] * math.cos(theta123),
            ],
            [1.0, 1.0, 1.0],
        ],
        dtype=float,
    )


def stiffness_samples_from_eq23(
    gammas: np.ndarray,
    state_samples: list[tuple[float, float, float, float, float, float]],
) -> tuple[np.ndarray, np.ndarray] | None:
    theta_prb_samples: list[np.ndarray] = []
    kbar_samples: list[np.ndarray] = []

    for theta0, qx, qy, alpha_value, beta_value, phi in state_samples:
        theta = prb3r_inverse_kinematics(qx, qy, float(theta0), gammas)
        if theta is None:
            break

        load_vector = np.array(
            [
                2.0 * alpha_value * math.cos(phi),
                2.0 * alpha_value * math.sin(phi),
                beta_value,
            ],
            dtype=float,
        )
        torque_vector = prb3r_jacobian(theta, gammas).T @ load_vector

        if np.any(np.abs(theta) <= 1.0e-12):
            continue

        theta_prb_samples.append(theta)
        kbar_samples.append(torque_vector / theta)

    if not theta_prb_samples:
        return None

    return np.column_stack(theta_prb_samples), np.column_stack(kbar_samples)


def zero_intercept_stiffness_fit(theta_samples: np.ndarray, torque_samples: np.ndarray) -> np.ndarray:
    kbar = np.zeros(3, dtype=float)
    for idx in range(3):
        denom = float(np.dot(theta_samples[idx], theta_samples[idx]))
        if denom <= 1.0e-14:
            raise RuntimeError("Could not fit the PRB stiffness because the theta samples were degenerate.")
        kbar[idx] = float(np.dot(theta_samples[idx], torque_samples[idx]) / denom)
    return kbar


def common_theta_range_for_extreme_load_comparison(
    l_over_t_value: float,
    sigma_over_e_value: float,
    sample_count: int,
    force_fit_fraction_value: float,
) -> tuple[np.ndarray, float]:
    theta_stress_limit = stress_limited_theta_max_from_section22(l_over_t_value, sigma_over_e_value)
    theta_common_max = force_fit_fraction_value * min(theta_stress_limit, 0.5 * math.pi)
    return np.linspace(1.0e-4, theta_common_max, sample_count), theta_stress_limit


def section45_pure_moment_theta_range(sample_count: int) -> np.ndarray:
    return np.linspace(1.0e-4, 1.5 * math.pi - 1.0e-6, sample_count)


def section46_pure_force_theta_range(sample_count: int) -> np.ndarray:
    theta_force_max = SECTION4_FORCE_FIT_FRACTION * (0.5 * math.pi)
    return np.linspace(1.0e-4, theta_force_max, sample_count)


def search_characteristic_radius_factors_eq23(
    l_over_t_value: float,
    sigma_over_e_value: float,
    gamma_step_value: float,
    moment_samples: int,
    force_samples: int,
    force_fit_fraction_value: float,
) -> tuple[ExtremeLoadFit, float]:
    theta_common_values, theta_stress_limit = common_theta_range_for_extreme_load_comparison(
        l_over_t_value,
        sigma_over_e_value,
        max(moment_samples, force_samples),
        force_fit_fraction_value,
    )
    moment_state_samples = precompute_state_samples(theta_common_values, "pure_moment")
    force_state_samples = precompute_state_samples(theta_common_values, "pure_force")

    gamma_values = np.arange(0.05, 0.50 + 0.5 * gamma_step_value, gamma_step_value)
    gamma_start = float(gamma_values[0])
    best_result: ExtremeLoadFit | None = None

    for gamma0 in gamma_values:
        for gamma1 in gamma_values:
            for gamma2 in gamma_values:
                gamma3 = 1.0 - gamma0 - gamma1 - gamma2
                if gamma3 < 0.05 - 1.0e-12 or gamma3 > 0.50 + 1.0e-12:
                    continue
                gamma3 = gamma_start + round((gamma3 - gamma_start) / gamma_step_value) * gamma_step_value
                gammas = np.array([gamma0, gamma1, gamma2, gamma3], dtype=float)
                if abs(float(np.sum(gammas)) - 1.0) > 1.0e-12:
                    continue

                moment_sample_data = stiffness_samples_from_eq23(gammas, moment_state_samples)
                if moment_sample_data is None:
                    continue
                force_sample_data = stiffness_samples_from_eq23(gammas, force_state_samples)
                if force_sample_data is None:
                    continue

                _, moment_kbar_samples = moment_sample_data
                _, force_kbar_samples = force_sample_data
                sample_count = min(moment_kbar_samples.shape[1], force_kbar_samples.shape[1])
                if sample_count == 0:
                    continue

                moment_kbar_samples = moment_kbar_samples[:, :sample_count]
                force_kbar_samples = force_kbar_samples[:, :sample_count]
                objective = float(np.mean(np.sum((moment_kbar_samples - force_kbar_samples) ** 2, axis=0)))
                candidate = ExtremeLoadFit(gammas.copy(), objective)
                if best_result is None or candidate.objective < best_result.objective:
                    best_result = candidate

    if best_result is None:
        raise RuntimeError("No valid gamma set was found.")

    return best_result, theta_stress_limit


def generalized_theta_range(kappa: float, phi_rad: float, sample_count: int) -> np.ndarray:
    theta_upper = theta0_max_for_case(phi_rad, kappa)
    if theta_upper <= 1.0e-4:
        raise RuntimeError("The requested load family does not have a usable theta0 range.")
    return np.linspace(1.0e-4, theta_upper, sample_count)


def generalized_state_samples(
    theta_values: np.ndarray,
    phi_rad: float,
    kappa: float,
) -> list[tuple[float, float, float, float, float, float]]:
    state_samples: list[tuple[float, float, float, float, float, float]] = []
    for theta0 in theta_values:
        alpha_value, qx, qy = compute_state_with_alpha(float(theta0), float(phi_rad), float(kappa))
        beta_value = 0.0 if kappa == 0.0 else 2.0 * math.sqrt(float(alpha_value) * float(kappa))
        state_samples.append(
            (
                float(theta0),
                float(qx),
                float(qy),
                float(alpha_value),
                float(beta_value),
                float(phi_rad),
            )
        )
    return state_samples


def fit_stiffness_for_load_family(gammas: np.ndarray, kappa: float, phi_rad: float, sample_count: int) -> np.ndarray:
    theta_values = generalized_theta_range(kappa, phi_rad, sample_count)
    state_samples = generalized_state_samples(theta_values, phi_rad, kappa)
    sample_data = stiffness_samples_from_eq23(gammas, state_samples)
    if sample_data is None:
        raise RuntimeError("Could not compute stiffness samples for the requested load family.")
    _, kbar_samples = sample_data
    return np.median(kbar_samples, axis=1)


def compute_load_independent_stiffness(
    gammas: np.ndarray,
    kappa_values: np.ndarray,
    phi_rad: float,
    sample_count: int,
) -> tuple[np.ndarray, list[tuple[float, np.ndarray]]]:
    stiffness_rows: list[np.ndarray] = []
    stiffness_by_kappa: list[tuple[float, np.ndarray]] = []

    for kappa in np.asarray(kappa_values, dtype=float):
        kbar = fit_stiffness_for_load_family(gammas, float(kappa), phi_rad, sample_count)
        stiffness_rows.append(kbar)
        stiffness_by_kappa.append((float(kappa), kbar))

    return np.mean(np.vstack(stiffness_rows), axis=0), stiffness_by_kappa


def section510_equilibrium_residual(
    theta: np.ndarray, load_vector: np.ndarray, gammas: np.ndarray, kbar: np.ndarray
) -> np.ndarray:
    return kbar * theta - prb3r_jacobian(theta, gammas).T @ load_vector


def section510_solve_prb3r_equilibrium(
    alpha_value: float,
    beta_value: float,
    phi_rad: float,
    gammas: np.ndarray,
    kbar: np.ndarray,
    previous_guess: np.ndarray | None = None,
    atlas_guess: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    load_vector = np.array(
        [
            2.0 * alpha_value * math.cos(phi_rad),
            2.0 * alpha_value * math.sin(phi_rad),
            beta_value,
        ],
        dtype=float,
    )

    guess_pool: list[np.ndarray] = []
    for guess in (previous_guess, atlas_guess, np.zeros(3, dtype=float)):
        if guess is None:
            continue
        if not any(np.allclose(guess, existing) for existing in guess_pool):
            guess_pool.append(np.array(guess, dtype=float))

    for initial_guess in guess_pool:
        theta = initial_guess.copy()
        converged = False

        for _ in range(80):
            residual = section510_equilibrium_residual(theta, load_vector, gammas, kbar)
            if np.linalg.norm(residual, ord=2) < 1.0e-10:
                converged = True
                break

            tangent = np.zeros((3, 3), dtype=float)
            step = 1.0e-7
            try:
                for idx in range(3):
                    theta_shift = theta.copy()
                    theta_shift[idx] += step
                    residual_shift = section510_equilibrium_residual(
                        theta_shift, load_vector, gammas, kbar
                    )
                    tangent[:, idx] = (residual_shift - residual) / step
                delta = np.linalg.solve(tangent, -residual)
            except np.linalg.LinAlgError:
                break

            theta += delta
            if np.linalg.norm(delta, ord=2) < 1.0e-10:
                residual = section510_equilibrium_residual(theta, load_vector, gammas, kbar)
                if np.linalg.norm(residual, ord=2) < 1.0e-8:
                    converged = True
                    break

        if converged:
            qx, qy, theta0 = prb3r_forward_kinematics(theta, gammas)
            return theta, np.array([qx, qy, theta0], dtype=float)

    raise RuntimeError("Could not solve the PRB 3R static equilibrium for this load case.")


def section510_evaluate_load_family(
    gammas: np.ndarray,
    kbar: np.ndarray,
    phi_deg: float,
    kappa: float,
    point_count: int,
) -> dict[str, object]:
    phi_rad = math.radians(phi_deg)
    theta0_values, actual_x, actual_y = generate_locus_for_case(phi_rad, kappa, point_count)

    prb_x: list[float] = []
    prb_y: list[float] = []
    tip_error: list[float] = []
    slope_error: list[float] = []
    theta_guess: np.ndarray | None = None

    for theta0_actual, qx_actual, qy_actual in zip(theta0_values, actual_x, actual_y):
        alpha_value, _, _ = compute_state_with_alpha(float(theta0_actual), phi_rad, kappa)
        beta_value = 0.0 if kappa == 0.0 else 2.0 * math.sqrt(float(alpha_value) * float(kappa))
        atlas_guess = prb3r_inverse_kinematics(
            float(qx_actual), float(qy_actual), float(theta0_actual), gammas
        )
        theta_guess, prb_state = section510_solve_prb3r_equilibrium(
            float(alpha_value),
            float(beta_value),
            phi_rad,
            gammas,
            kbar,
            previous_guess=theta_guess,
            atlas_guess=atlas_guess,
        )

        prb_x.append(float(prb_state[0]))
        prb_y.append(float(prb_state[1]))
        tip_error.append(math.hypot(float(prb_state[0]) - float(qx_actual), float(prb_state[1]) - float(qy_actual)))
        slope_error.append(abs(float(prb_state[2]) - float(theta0_actual)))

    tip_error_array = np.asarray(tip_error, dtype=float)
    slope_error_array = np.asarray(slope_error, dtype=float)
    max_tip_index = int(np.argmax(tip_error_array))

    return {
        "actual_x": [float(value) for value in actual_x],
        "actual_y": [float(value) for value in actual_y],
        "prb_x": [float(value) for value in prb_x],
        "prb_y": [float(value) for value in prb_y],
        "max_tip_error": float(np.max(tip_error_array)),
        "max_tip_error_pct": float(100.0 * np.max(tip_error_array)),
        "max_slope_error_deg": float(np.rad2deg(np.max(slope_error_array))),
        "theta0_at_max_tip_error_deg": float(np.rad2deg(theta0_values[max_tip_index])),
    }


def get_section520_parameters() -> tuple[np.ndarray, np.ndarray, str]:
    global SECTION520_PARAMETER_CACHE
    if SECTION520_PARAMETER_CACHE is None:
        result, _ = search_characteristic_radius_factors_eq23(
            SECTION4_L_OVER_T,
            SECTION4_SIGMA_OVER_E,
            SECTION4_GAMMA_STEP,
            SECTION4_NUM_MOMENT_SAMPLES,
            SECTION4_NUM_FORCE_SAMPLES,
            SECTION4_FORCE_FIT_FRACTION,
        )
        gammas = result.gammas.copy()
        kbar, stiffness_by_kappa = compute_load_independent_stiffness(
            gammas,
            SECTION500_KAPPA_VALUES,
            math.pi / 2.0,
            SECTION510_NUM_KAPPA_FIT_THETA_SAMPLES,
        )
        SECTION520_PARAMETER_CACHE = {
            "gammas": gammas,
            "kbar": kbar,
            "stiffness_label": "computed load-independent average",
            "stiffness_by_kappa": stiffness_by_kappa,
        }

    return (
        np.array(SECTION520_PARAMETER_CACHE["gammas"], dtype=float),
        np.array(SECTION520_PARAMETER_CACHE["kbar"], dtype=float),
        str(SECTION520_PARAMETER_CACHE["stiffness_label"]),
    )


def get_section4_workspace_payload() -> dict[str, object]:
    global SECTION4_WORKSPACE_CACHE
    global SECTION520_PARAMETER_CACHE
    if SECTION4_WORKSPACE_CACHE is not None:
        return SECTION4_WORKSPACE_CACHE

    result, theta_stress_limit = search_characteristic_radius_factors_eq23(
        SECTION4_L_OVER_T,
        SECTION4_SIGMA_OVER_E,
        SECTION4_GAMMA_STEP,
        SECTION4_NUM_MOMENT_SAMPLES,
        SECTION4_NUM_FORCE_SAMPLES,
        SECTION4_FORCE_FIT_FRACTION,
    )
    gammas = result.gammas.copy()
    moment_theta_values = section45_pure_moment_theta_range(SECTION4_NUM_MOMENT_SAMPLES)
    force_theta_values = section46_pure_force_theta_range(SECTION4_NUM_FORCE_SAMPLES)
    moment_state_samples = precompute_state_samples(moment_theta_values, "pure_moment")
    force_state_samples = precompute_state_samples(force_theta_values, "pure_force")
    moment_sample_data = stiffness_samples_from_eq23(gammas, moment_state_samples)
    force_sample_data = stiffness_samples_from_eq23(gammas, force_state_samples)
    if moment_sample_data is None or force_sample_data is None:
        raise RuntimeError("Unable to build the Section 4 fit workspace from the local procedure.")

    moment_theta_prb_samples, moment_kbar_samples = moment_sample_data
    force_theta_prb_samples, force_kbar_samples = force_sample_data
    moment_sample_count = int(moment_kbar_samples.shape[1])
    force_sample_count = int(force_kbar_samples.shape[1])
    moment_theta0_values = moment_theta_values[:moment_sample_count]
    force_theta0_values = force_theta_values[:force_sample_count]
    moment_theta_deg = np.rad2deg(moment_theta0_values)
    force_theta_deg = np.rad2deg(force_theta0_values)
    moment_fit_values = zero_intercept_stiffness_fit(
        moment_theta_prb_samples[:, :moment_sample_count],
        np.vstack([moment_theta0_values, moment_theta0_values, moment_theta0_values]),
    )
    force_fit_values = np.median(force_kbar_samples[:, :force_sample_count], axis=1)

    kbar, stiffness_by_kappa = compute_load_independent_stiffness(
        gammas,
        SECTION500_KAPPA_VALUES,
        math.pi / 2.0,
        SECTION510_NUM_KAPPA_FIT_THETA_SAMPLES,
    )
    figure12_cases = [
        section510_evaluate_load_family(
            gammas,
            kbar,
            SECTION510_FIGURE12_FORCE_ANGLE_DEG,
            float(kappa),
            SECTION510_NUM_LOCUS_POINTS,
        )
        for kappa in SECTION510_FIGURE12_LOAD_RATIOS
    ]
    figure13_cases = [
        section510_evaluate_load_family(
            gammas,
            kbar,
            float(phi_deg),
            SECTION510_FIGURE13_LOAD_RATIO,
            SECTION510_NUM_LOCUS_POINTS,
        )
        for phi_deg in SECTION510_FIGURE13_FORCE_ANGLES_DEG
    ]
    stiffness_label = "computed load-independent average"

    if SECTION520_PARAMETER_CACHE is None:
        SECTION520_PARAMETER_CACHE = {
            "gammas": gammas.copy(),
            "kbar": kbar.copy(),
            "stiffness_label": stiffness_label,
            "stiffness_by_kappa": stiffness_by_kappa,
        }

    SECTION4_WORKSPACE_CACHE = {
        "parameter_source": SECTION520_PARAMETER_SOURCE,
        "search": {
            "l_over_t": float(SECTION4_L_OVER_T),
            "sigma_over_e": float(SECTION4_SIGMA_OVER_E),
            "gamma_step": float(SECTION4_GAMMA_STEP),
            "moment_samples": int(SECTION4_NUM_MOMENT_SAMPLES),
            "force_samples": int(SECTION4_NUM_FORCE_SAMPLES),
            "force_fit_fraction": float(SECTION4_FORCE_FIT_FRACTION),
            "theta_stress_limit_rad": float(theta_stress_limit),
            "theta_stress_limit_deg": float(np.rad2deg(theta_stress_limit)),
            "objective": float(result.objective),
            "gammas": [float(value) for value in gammas],
            "gamma_cumulative": [
                float(gammas[0]),
                float(gammas[0] + gammas[1]),
                float(gammas[0] + gammas[1] + gammas[2]),
                float(np.sum(gammas)),
            ],
        },
        "moment_fit": {
            "theta0_rad": [float(value) for value in moment_theta0_values],
            "theta_deg": [float(value) for value in moment_theta_deg],
            "theta_prb": [
                [float(value) for value in moment_theta_prb_samples[row_index, :moment_sample_count]]
                for row_index in range(3)
            ],
            "k1": [float(value) for value in moment_kbar_samples[0, :moment_sample_count]],
            "k2": [float(value) for value in moment_kbar_samples[1, :moment_sample_count]],
            "k3": [float(value) for value in moment_kbar_samples[2, :moment_sample_count]],
            "fit_k": [float(value) for value in moment_fit_values],
            "median": [float(value) for value in np.median(moment_kbar_samples[:, :moment_sample_count], axis=1)],
        },
        "force_fit": {
            "theta0_rad": [float(value) for value in force_theta0_values],
            "theta_deg": [float(value) for value in force_theta_deg],
            "theta_prb": [
                [float(value) for value in force_theta_prb_samples[row_index, :force_sample_count]]
                for row_index in range(3)
            ],
            "torque": [
                [
                    float(value)
                    for value in (
                        force_theta_prb_samples[row_index, :force_sample_count]
                        * force_kbar_samples[row_index, :force_sample_count]
                    )
                ]
                for row_index in range(3)
            ],
            "k1": [float(value) for value in force_kbar_samples[0, :force_sample_count]],
            "k2": [float(value) for value in force_kbar_samples[1, :force_sample_count]],
            "k3": [float(value) for value in force_kbar_samples[2, :force_sample_count]],
            "fit_k": [float(value) for value in force_fit_values],
            "median": [float(value) for value in np.median(force_kbar_samples[:, :force_sample_count], axis=1)],
        },
        "average": {
            "kappa_values": [float(value) for value in SECTION500_KAPPA_VALUES],
            "k1": [float(row[1][0]) for row in stiffness_by_kappa],
            "k2": [float(row[1][1]) for row in stiffness_by_kappa],
            "k3": [float(row[1][2]) for row in stiffness_by_kappa],
            "kbar": [float(value) for value in kbar],
            "stiffness_label": stiffness_label,
        },
        "section5_preview": {
            "figure12": {
                "title": "Figure 12",
                "subtitle": f"Varying kappa with phi = {SECTION510_FIGURE12_FORCE_ANGLE_DEG:g} deg",
                "labels": [f"kappa = {kappa:g}" for kappa in SECTION510_FIGURE12_LOAD_RATIOS],
                "cases": figure12_cases,
            },
            "figure13": {
                "title": "Figure 13",
                "subtitle": f"Varying phi with kappa = {SECTION510_FIGURE13_LOAD_RATIO:g}",
                "labels": [f"phi = {phi_deg:g} deg" for phi_deg in SECTION510_FIGURE13_FORCE_ANGLES_DEG],
                "cases": figure13_cases,
            },
        },
    }
    return SECTION4_WORKSPACE_CACHE


def section700_joint_positions(theta: np.ndarray, gammas: np.ndarray) -> np.ndarray:
    theta1, theta2, theta3 = np.asarray(theta, dtype=float)
    theta12 = theta1 + theta2
    theta123 = theta12 + theta3
    origin = np.array([0.0, 0.0], dtype=float)
    p1 = np.array([gammas[0], 0.0], dtype=float)
    p2 = p1 + gammas[1] * np.array([math.cos(theta1), math.sin(theta1)], dtype=float)
    p3 = p2 + gammas[2] * np.array([math.cos(theta12), math.sin(theta12)], dtype=float)
    p4 = p3 + gammas[3] * np.array([math.cos(theta123), math.sin(theta123)], dtype=float)
    return np.vstack([origin, p1, p2, p3, p4])


def get_section700_parameters() -> tuple[np.ndarray, np.ndarray]:
    """Reuse the computed project PRB parameters for medical experiments."""
    gammas, kbar, _ = get_section520_parameters()
    return np.asarray(gammas, dtype=float), np.asarray(kbar, dtype=float)


def section700_target_pose(circle_angle_deg: float) -> tuple[float, float]:
    circle_angle_rad = math.radians(circle_angle_deg)
    x_target_value = SECTION700_CIRCLE_CENTER_X + SECTION700_CIRCLE_RADIUS * math.cos(circle_angle_rad)
    y_target_value = SECTION700_CIRCLE_CENTER_Y + SECTION700_CIRCLE_RADIUS * math.sin(circle_angle_rad)
    return float(x_target_value), float(y_target_value)


def section700_solve_tip_pose(
    x_target_value: float,
    y_target_value: float,
    theta_tip_target: float,
    gammas: np.ndarray,
    initial_guess: np.ndarray | None,
) -> np.ndarray:
    initial_guess_array = None if initial_guess is None else np.asarray(initial_guess, dtype=float)
    angle_offsets = [0.0]
    angle_offsets.extend(
        offset
        for magnitude_deg in np.linspace(1.0, 60.0, 60)
        for offset in (math.radians(magnitude_deg), -math.radians(magnitude_deg))
    )

    best_theta: np.ndarray | None = None
    best_score = math.inf

    for angle_offset in angle_offsets:
        theta_tip_candidate = float(theta_tip_target + angle_offset)
        solutions = prb3r_inverse_kinematics_candidates(
            float(x_target_value),
            float(y_target_value),
            theta_tip_candidate,
            gammas,
        )
        if not solutions:
            continue

        for theta_candidate in solutions:
            continuity_cost = (
                float(np.linalg.norm(theta_candidate, ord=2))
                if initial_guess_array is None
                else float(np.linalg.norm(theta_candidate - initial_guess_array, ord=2))
            )
            score = continuity_cost + 0.35 * abs(angle_offset)
            if score < best_score:
                best_theta = np.asarray(theta_candidate, dtype=float)
                best_score = score

        if best_theta is not None and angle_offset == 0.0:
            break

    if best_theta is None:
        raise RuntimeError(
            f"Could not find a PRB pose at x = {x_target_value:.4f}, y = {y_target_value:.4f}."
        )

    return best_theta


def section700_solve_tip_to_target(
    x_target_value: float,
    y_target_value: float,
    gammas: np.ndarray,
    initial_guess: np.ndarray | None,
) -> np.ndarray:
    initial_guess_array = None if initial_guess is None else np.asarray(initial_guess, dtype=float)
    reference_theta_tip = 0.0 if initial_guess_array is None else float(np.sum(initial_guess_array))

    search_grids: list[np.ndarray] = []
    if initial_guess_array is not None:
        search_grids.append(np.linspace(reference_theta_tip - 1.25, reference_theta_tip + 1.25, 1801))
    search_grids.append(np.linspace(-math.pi, math.pi, 3601))

    best_theta: np.ndarray | None = None
    best_score = math.inf

    for theta_tip_grid in search_grids:
        for theta_tip in theta_tip_grid:
            theta_candidate = prb3r_inverse_kinematics(
                float(x_target_value),
                float(y_target_value),
                float(theta_tip),
                gammas,
            )
            if theta_candidate is None:
                continue

            if initial_guess_array is None:
                score = float(np.linalg.norm(theta_candidate, ord=2))
            else:
                score = float(np.linalg.norm(theta_candidate - initial_guess_array, ord=2))

            if score < best_score:
                best_theta = np.asarray(theta_candidate, dtype=float)
                best_score = score

        if best_theta is not None:
            break

    if best_theta is None:
        raise RuntimeError(
            f"Could not find a PRB configuration at x = {x_target_value:.4f}, y = {y_target_value:.4f}."
        )

    return best_theta


def section701_desired_tip_motion(
    time_values: np.ndarray,
    tip_amplitude: float,
    core_motion_time: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the prescribed sinusoidal y motion and matched heading history.

    The PRB base remains fixed at (0, 0) and the undeformed tip at (1, 0).
    This medical steering test only prescribes y_tip(t) and theta0(t), while
    x_tip is intentionally left free.
    """
    normalized_motion_time = np.clip(
        np.asarray(time_values, dtype=float) - float(SECTION701_END_HOLD_TIME),
        0.0,
        float(core_motion_time),
    )
    normalized_time = normalized_motion_time / float(core_motion_time)
    eased_phase = 2.0 * math.pi * (3.0 * normalized_time**2 - 2.0 * normalized_time**3)
    eased_phase_rate = (
        2.0
        * math.pi
        * (6.0 * normalized_time - 6.0 * normalized_time**2)
        / float(core_motion_time)
    )
    active_motion_mask = (
        (np.asarray(time_values, dtype=float) >= float(SECTION701_END_HOLD_TIME))
        & (np.asarray(time_values, dtype=float) <= float(SECTION701_END_HOLD_TIME + core_motion_time))
    )
    eased_phase_rate = np.where(active_motion_mask, eased_phase_rate, 0.0)

    y_desired = -tip_amplitude * np.sin(eased_phase)
    dy_dt = -tip_amplitude * np.cos(eased_phase) * eased_phase_rate

    max_heading_rad = math.radians(SECTION701_MAX_HEADING_DEG)
    peak_vertical_speed = max(float(np.max(np.abs(dy_dt))), 1.0e-12)
    nominal_forward_rate = peak_vertical_speed / math.tan(max_heading_rad)

    theta0_desired = np.zeros_like(time_values, dtype=float)
    for idx, y_rate in enumerate(dy_dt):
        if abs(float(y_rate)) <= 1.0e-12:
            theta0_desired[idx] = 0.0
        else:
            theta0_desired[idx] = math.atan2(float(y_rate), nominal_forward_rate)

    return y_desired, theta0_desired


def section701_equivalent_moment_demand(tau: np.ndarray) -> float:
    """Return a simple equivalent PRB actuation metric for the steering test."""
    return float(np.sum(np.abs(np.asarray(tau, dtype=float))))


def section701_dimensional_load_response(
    theta: np.ndarray,
    gammas: np.ndarray,
    kbar: np.ndarray,
    beam: dict[str, float],
) -> dict[str, object]:
    """Recover dimensional PRB spring torques, tip loads, and base net moment."""
    inertia = rectangular_second_moment(float(beam["beam_width"]), float(beam["thickness"]))
    bending_stiffness = float(beam["youngs_modulus"]) * inertia
    beam_length = float(beam["beam_length"])
    tau_normalized = kbar * theta
    tau_dimensional = tau_normalized * bending_stiffness / beam_length
    load_vector_normalized = section520_tip_load(theta, gammas, kbar)
    force_x = float(load_vector_normalized[0] * bending_stiffness / (beam_length * beam_length))
    force_y = float(load_vector_normalized[1] * bending_stiffness / (beam_length * beam_length))
    tip_moment = float(load_vector_normalized[2] * bending_stiffness / beam_length)
    qx_normalized, qy_normalized, _ = prb3r_forward_kinematics(theta, gammas)
    tip_x = float(qx_normalized * beam_length)
    tip_y = float(qy_normalized * beam_length)
    base_net_moment = float(tip_x * force_y - tip_y * force_x + tip_moment)
    return {
        "inertia": float(inertia),
        "bending_stiffness": float(bending_stiffness),
        "tau_dimensional": np.asarray(tau_dimensional, dtype=float),
        "load_vector_normalized": np.asarray(load_vector_normalized, dtype=float),
        "force_x": force_x,
        "force_y": force_y,
        "force_magnitude": float(math.hypot(force_x, force_y)),
        "tip_moment": tip_moment,
        "tip_moment_magnitude": float(abs(tip_moment)),
        "base_net_moment": base_net_moment,
        "base_net_moment_magnitude": float(abs(base_net_moment)),
    }


def section701_solve_frame(
    y_target_value: float,
    theta_tip_target: float,
    gammas: np.ndarray,
    initial_guess: np.ndarray | None,
) -> np.ndarray:
    """Solve one sinusoidal-motion frame with y and theta0 prescribed and x free."""
    if initial_guess is None:
        seed = np.zeros(3, dtype=float)
    else:
        seed = np.asarray(initial_guess, dtype=float)

    def residual(theta: np.ndarray) -> np.ndarray:
        _, y_value, theta_value = prb3r_forward_kinematics(theta, gammas)
        return np.array(
            [
                y_value - float(y_target_value),
                theta_value - float(theta_tip_target),
                SECTION701_CONTINUITY_WEIGHT * (theta[0] - seed[0]),
                SECTION701_CONTINUITY_WEIGHT * (theta[1] - seed[1]),
                SECTION701_CONTINUITY_WEIGHT * (theta[2] - seed[2]),
            ],
            dtype=float,
        )

    result = least_squares(
        residual,
        seed,
        xtol=1.0e-12,
        ftol=1.0e-12,
        gtol=1.0e-12,
        max_nfev=500,
    )
    if not result.success:
        raise RuntimeError(
            f"Could not solve the Section 701 frame at y = {y_target_value:.5f}, theta0 = {theta_tip_target:.5f}."
        )
    return np.asarray(result.x, dtype=float)


def get_section700_circle_payload() -> dict[str, object]:
    if "circle" in SECTION700_EXPERIMENT_CACHE:
        return SECTION700_EXPERIMENT_CACHE["circle"]

    gammas, kbar = get_section700_parameters()
    circle_angle_values_deg = np.linspace(
        SECTION700_START_ANGLE_DEG,
        SECTION700_END_ANGLE_DEG,
        SECTION700_NUM_FRAMES,
    )
    frames_payload: list[dict[str, object]] = []
    target_path: list[list[float]] = []
    previous_theta = np.zeros(3, dtype=float)

    for frame_index, circle_angle_deg in enumerate(circle_angle_values_deg):
        x_target_value, y_target_value = section700_target_pose(float(circle_angle_deg))
        theta_array = section700_solve_tip_to_target(
            x_target_value,
            y_target_value,
            gammas,
            previous_theta if frame_index > 0 else None,
        )
        tip_x, tip_y, theta_tip = prb3r_forward_kinematics(theta_array, gammas)
        target_path.append([float(x_target_value), float(y_target_value)])
        frames_payload.append(
            {
                "time": float(frame_index / max(1, SECTION700_NUM_FRAMES - 1)),
                "frame_value": float(circle_angle_deg),
                "frame_value_display": float(circle_angle_deg),
                "target_x": float(x_target_value),
                "target_y": float(y_target_value),
                "theta": [float(value) for value in theta_array],
                "theta_tip": float(theta_tip),
                "theta_tip_deg": float(np.degrees(theta_tip)),
                "tip_x": float(tip_x),
                "tip_y": float(tip_y),
                "tau": [float(value) for value in (kbar * theta_array)],
                "spring_energy": float(0.5 * np.dot(kbar, theta_array * theta_array)),
                "equivalent_moment_demand": float(section701_equivalent_moment_demand(kbar * theta_array)),
                "tracking_error": float(math.hypot(tip_x - x_target_value, tip_y - y_target_value)),
                "chain": [[float(x), float(y)] for x, y in section700_joint_positions(theta_array, gammas)],
            }
        )
        previous_theta = theta_array

    target_x_values = [point[0] for point in target_path]
    target_y_values = [point[1] for point in target_path]
    actual_path = [[float(frame["tip_x"]), float(frame["tip_y"])] for frame in frames_payload]
    payload = {
        "experiment_key": "circle",
        "experiment_title": "Circle tip tracking",
        "slider_label": "Circle angle (deg)",
        "time_start": 0.0,
        "time_end": 1.0,
        "circle_center": [float(SECTION700_CIRCLE_CENTER_X), float(SECTION700_CIRCLE_CENTER_Y)],
        "circle_radius": float(SECTION700_CIRCLE_RADIUS),
        "angle_start_deg": float(SECTION700_START_ANGLE_DEG),
        "angle_end_deg": float(SECTION700_END_ANGLE_DEG),
        "gammas": [float(value) for value in gammas],
        "kbar": [float(value) for value in kbar],
        "target_path": target_path,
        "actual_path": actual_path,
        "x_min": float(min(target_x_values)),
        "x_max": float(max(target_x_values)),
        "y_min": float(min(target_y_values)),
        "y_max": float(max(target_y_values)),
        "frames": frames_payload,
    }
    SECTION700_EXPERIMENT_CACHE["circle"] = payload
    return payload


def get_section701_sinusoid_payload(
    tip_amplitude: float = SECTION701_TIP_AMPLITUDE,
    core_motion_time: float = SECTION701_CORE_MOTION_TIME,
    beam: dict[str, float] | None = None,
) -> dict[str, object]:
    beam_parameters = beam or {
        "beam_length": DEFAULT_BEAM_LENGTH,
        "beam_width": DEFAULT_BEAM_WIDTH,
        "thickness": DEFAULT_THICKNESS,
        "youngs_modulus": DEFAULT_YOUNGS_MODULUS,
        "sigma_max": DEFAULT_SIGMA_MAX,
    }
    cache_key = (
        f"sinusoid:{tip_amplitude:.6f}:{core_motion_time:.6f}:"
        f"{beam_parameters['beam_length']:.6f}:{beam_parameters['beam_width']:.6f}:"
        f"{beam_parameters['thickness']:.6f}:{beam_parameters['youngs_modulus']:.6f}:"
        f"{beam_parameters['sigma_max']:.6f}"
    )
    if cache_key in SECTION700_EXPERIMENT_CACHE:
        return SECTION700_EXPERIMENT_CACHE[cache_key]

    gammas, kbar = get_section700_parameters()
    total_motion_time = float(core_motion_time) + 2.0 * float(SECTION701_END_HOLD_TIME)
    time_values = np.linspace(0.0, total_motion_time, SECTION700_NUM_FRAMES)
    y_desired_values, theta0_desired_values = section701_desired_tip_motion(
        time_values,
        float(tip_amplitude),
        float(core_motion_time),
    )
    frames_payload: list[dict[str, object]] = []
    actual_path: list[list[float]] = []
    previous_theta = np.zeros(3, dtype=float)

    for frame_index, (time_value, y_target_value, theta0_desired) in enumerate(
        zip(time_values, y_desired_values, theta0_desired_values)
    ):
        initial_guess = np.zeros(3, dtype=float) if frame_index == 0 else previous_theta
        theta_array = section701_solve_frame(
            float(y_target_value),
            float(theta0_desired),
            gammas,
            initial_guess,
        )

        tip_x, tip_y, theta_tip = prb3r_forward_kinematics(theta_array, gammas)
        load_response = section701_dimensional_load_response(theta_array, gammas, kbar, beam_parameters)
        tau_dimensional = np.asarray(load_response["tau_dimensional"], dtype=float)
        spring_energy = float(0.5 * np.dot(tau_dimensional, theta_array))
        chain = section700_joint_positions(theta_array, gammas)
        actual_path.append([float(tip_x), float(tip_y)])
        frames_payload.append(
            {
                "time": float(time_value),
                "frame_value": float(time_value),
                "frame_value_display": float(time_value),
                "target_x": float(tip_x),
                "target_y": float(y_target_value),
                "theta0_desired": float(theta0_desired),
                "theta0_desired_deg": float(np.degrees(theta0_desired)),
                "theta": [float(value) for value in theta_array],
                "theta_tip": float(theta_tip),
                "theta_tip_deg": float(np.degrees(theta_tip)),
                "tip_x": float(tip_x),
                "tip_y": float(tip_y),
                "tracking_error": float(abs(float(tip_y) - float(y_target_value))),
                "tau": [float(value) for value in tau_dimensional],
                "spring_energy": spring_energy,
                "equivalent_moment_demand": float(section701_equivalent_moment_demand(tau_dimensional)),
                "force_x": float(load_response["force_x"]),
                "force_y": float(load_response["force_y"]),
                "force_magnitude": float(load_response["force_magnitude"]),
                "tip_moment": float(load_response["tip_moment"]),
                "tip_moment_magnitude": float(load_response["tip_moment_magnitude"]),
                "base_net_moment": float(load_response["base_net_moment"]),
                "base_net_moment_magnitude": float(load_response["base_net_moment_magnitude"]),
                "exact_force_moment_solved": True,
                "chain": [[float(x), float(y)] for x, y in chain],
            }
        )
        previous_theta = theta_array

    target_path = [[float(frame["target_x"]), float(frame["target_y"])] for frame in frames_payload]
    all_x_values = [point[0] for point in actual_path]
    all_y_values = [point[1] for point in target_path] + [point[1] for point in actual_path]
    payload = {
        "experiment_key": "sinusoid",
        "experiment_title": "Sinusoidal tip motion",
        "slider_label": "time",
        "time_start": 0.0,
        "time_end": total_motion_time,
        "tip_amplitude": float(tip_amplitude),
        "core_motion_time": float(core_motion_time),
        "end_hold_time": float(SECTION701_END_HOLD_TIME),
        "max_heading_deg": float(SECTION701_MAX_HEADING_DEG),
        "exact_force_moment_solved": True,
        "beam_length": float(beam_parameters["beam_length"]),
        "beam_width": float(beam_parameters["beam_width"]),
        "thickness": float(beam_parameters["thickness"]),
        "youngs_modulus": float(beam_parameters["youngs_modulus"]),
        "sigma_max": float(beam_parameters["sigma_max"]),
        "gammas": [float(value) for value in gammas],
        "kbar": [float(value) for value in kbar],
        "target_path": target_path,
        "actual_path": actual_path,
        "x_min": float(min(all_x_values)),
        "x_max": float(max(all_x_values)),
        "y_min": float(min(all_y_values)),
        "y_max": float(max(all_y_values)),
        "frames": frames_payload,
    }
    SECTION700_EXPERIMENT_CACHE[cache_key] = payload
    return payload


def section520_rotation_matrix(angle: float) -> np.ndarray:
    cval = math.cos(angle)
    sval = math.sin(angle)
    return np.array([[cval, -sval], [sval, cval]], dtype=float)


def section520_prb_joint_positions(theta: np.ndarray, gammas: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    theta1, theta2, theta3 = theta
    theta12 = theta1 + theta2
    theta123 = theta12 + theta3
    origin = np.array([0.0, 0.0], dtype=float)
    p1 = np.array([gammas[0], 0.0], dtype=float)
    p2 = p1 + gammas[1] * np.array([math.cos(theta1), math.sin(theta1)], dtype=float)
    p3 = p2 + gammas[2] * np.array([math.cos(theta12), math.sin(theta12)], dtype=float)
    q_point = p3 + gammas[3] * np.array([math.cos(theta123), math.sin(theta123)], dtype=float)
    return np.vstack([origin, p1, p2, p3, q_point]), q_point


def section520_point_a_from_tip(q_point: np.ndarray, phi_value: float) -> np.ndarray:
    return q_point + section520_rotation_matrix(phi_value) @ np.array([SECTION520_AU, SECTION520_AV], dtype=float)


def section520_crank_endpoint(crank_angle_rad: float) -> np.ndarray:
    return SECTION520_B + SECTION520_R * np.array([math.cos(crank_angle_rad), math.sin(crank_angle_rad)], dtype=float)


def section520_tip_load(theta: np.ndarray, gammas: np.ndarray, kbar: np.ndarray) -> np.ndarray:
    tau = kbar * theta
    jacobian_t = prb3r_jacobian(theta, gammas).T
    load_vector, *_ = np.linalg.lstsq(jacobian_t, tau, rcond=None)
    return load_vector


def section520_residual(theta: np.ndarray, crank_angle_rad: float, gammas: np.ndarray, kbar: np.ndarray) -> np.ndarray:
    _, q_point = section520_prb_joint_positions(theta, gammas)
    phi_value = float(np.sum(theta))
    a_point = section520_point_a_from_tip(q_point, phi_value)
    aq_vector = q_point - a_point
    load_vector = section520_tip_load(theta, gammas, kbar)
    crank_tip = section520_crank_endpoint(crank_angle_rad)
    return np.array(
        [
            a_point[0] - crank_tip[0],
            a_point[1] - crank_tip[1],
            aq_vector[0] * load_vector[1] - aq_vector[1] * load_vector[0] + load_vector[2],
        ],
        dtype=float,
    )


def section520_initial_guess(crank_angle_rad: float) -> np.ndarray:
    return crank_angle_rad * SECTION520_INITIAL_GUESS_SCALE


def section520_solve_configuration(
    crank_angle_rad: float,
    gammas: np.ndarray,
    kbar: np.ndarray,
    previous_theta: np.ndarray | None,
) -> np.ndarray:
    guess_pool: list[np.ndarray] = []
    for guess in (previous_theta, section520_initial_guess(crank_angle_rad), np.zeros(3, dtype=float)):
        if guess is None:
            continue
        guess_array = np.array(guess, dtype=float)
        if not any(np.allclose(guess_array, existing) for existing in guess_pool):
            guess_pool.append(guess_array)

    best_result = None
    best_norm = math.inf
    for guess in guess_pool:
        result = least_squares(
            section520_residual,
            guess,
            args=(crank_angle_rad, gammas, kbar),
            xtol=1.0e-12,
            ftol=1.0e-12,
            gtol=1.0e-12,
            max_nfev=500,
        )
        residual_norm = float(np.linalg.norm(result.fun, ord=2))
        if residual_norm < best_norm:
            best_result = result
            best_norm = residual_norm
        if result.success and residual_norm < 1.0e-9:
            return np.array(result.x, dtype=float)

    if best_result is None or best_norm > 1.0e-7:
        raise RuntimeError(
            f"Could not solve the compliant four-bar configuration at BA angle = {math.degrees(crank_angle_rad):.3f} deg."
        )
    return np.array(best_result.x, dtype=float)


def section520_solve_motion() -> dict[str, object]:
    global SECTION520_MOTION_CACHE
    if SECTION520_MOTION_CACHE is not None:
        return SECTION520_MOTION_CACHE

    gammas, kbar, stiffness_label = get_section520_parameters()
    crank_angle_values = np.linspace(
        math.radians(SECTION520_CRANK_START_DEG),
        math.radians(SECTION520_CRANK_END_DEG),
        SECTION520_NUM_SAMPLES,
    )
    if abs(crank_angle_values[0]) < 1.0e-14:
        crank_angle_values[0] = 0.0

    theta_rows: list[np.ndarray] = []
    chain_rows: list[np.ndarray] = []
    q_rows: list[np.ndarray] = []
    a_rows: list[np.ndarray] = []
    crank_rows: list[np.ndarray] = []
    load_rows: list[np.ndarray] = []
    residual_rows: list[float] = []
    previous_theta = np.zeros(3, dtype=float)

    for index, crank_angle_rad in enumerate(crank_angle_values):
        if index == 0 and abs(crank_angle_rad) < 1.0e-14:
            theta = np.zeros(3, dtype=float)
        else:
            theta = section520_solve_configuration(float(crank_angle_rad), gammas, kbar, previous_theta)

        chain, q_point = section520_prb_joint_positions(theta, gammas)
        phi_value = float(np.sum(theta))
        a_point = section520_point_a_from_tip(q_point, phi_value)
        crank_tip = section520_crank_endpoint(float(crank_angle_rad))
        load_vector = section520_tip_load(theta, gammas, kbar)
        residual = section520_residual(theta, float(crank_angle_rad), gammas, kbar)

        theta_rows.append(theta)
        chain_rows.append(chain)
        q_rows.append(q_point)
        a_rows.append(a_point)
        crank_rows.append(crank_tip)
        load_rows.append(load_vector)
        residual_rows.append(float(np.linalg.norm(residual, ord=2)))
        previous_theta = theta

    SECTION520_MOTION_CACHE = {
        "parameter_source": SECTION520_PARAMETER_SOURCE,
        "stiffness_label": stiffness_label,
        "gammas": [float(value) for value in gammas],
        "kbar": [float(value) for value in kbar],
        "angle_deg": [float(value) for value in np.degrees(crank_angle_values)],
        "theta": [[float(value) for value in row] for row in theta_rows],
        "chain": [[[float(x), float(y)] for x, y in row] for row in chain_rows],
        "Q": [[float(row[0]), float(row[1])] for row in q_rows],
        "A": [[float(row[0]), float(row[1])] for row in a_rows],
        "crank_tip": [[float(row[0]), float(row[1])] for row in crank_rows],
        "load": [[float(value) for value in row] for row in load_rows],
        "residual_norm": [float(value) for value in residual_rows],
        "B": [float(value) for value in SECTION520_B],
    }
    return SECTION520_MOTION_CACHE


def parse_step_time(frame_label: str) -> float:
    match = re.search(r"Step Time =\s*([0-9.E+-]+)", frame_label)
    if match is None:
        return 0.0
    return float(match.group(1))


def load_verification_frames() -> list[VerificationFrame]:
    frame_rows: dict[str, dict[str, list[tuple[int, float, float, float, float]]]] = {}
    frame_order: list[str] = []
    csv_path = next((path for path in VERIFICATION_CSV_CANDIDATES if path.exists()), None)
    if csv_path is None:
        raise FileNotFoundError(
            "verificationdata.csv was not found in the project root or Abaqus folder."
        )

    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            part_name = raw_row["Part Instance Name"].strip()
            if part_name not in FEA_PART_NAMES:
                continue

            frame_label = raw_row["Frame"].strip()
            if frame_label not in frame_rows:
                frame_rows[frame_label] = {part: [] for part in FEA_PART_NAMES}
                frame_order.append(frame_label)

            frame_rows[frame_label][part_name].append(
                (
                    int(raw_row["    Node Label"]),
                    float(raw_row["X"]),
                    float(raw_row["Y"]),
                    float(raw_row["          U-U1"]),
                    float(raw_row["          U-U2"]),
                )
            )

    frames: list[VerificationFrame] = []
    for frame_label in frame_order:
        parts: dict[str, VerificationPartFrame] = {}
        for part_name in FEA_PART_NAMES:
            rows = sorted(frame_rows[frame_label][part_name], key=lambda item: item[0])
            node_labels = np.array([row[0] for row in rows], dtype=int)
            base_xy = np.array([[row[1], row[2]] for row in rows], dtype=float)
            displacement_xy = np.array([[row[3], row[4]] for row in rows], dtype=float)
            parts[part_name] = VerificationPartFrame(
                node_labels=node_labels,
                base_xy=base_xy,
                deformed_xy=base_xy + displacement_xy,
            )
        frames.append(
            VerificationFrame(
                frame_label=frame_label,
                step_time=parse_step_time(frame_label),
                parts=parts,
            )
        )

    if not frames:
        raise RuntimeError("verificationdata.csv did not contain CRANK-1 / COUP-1 / FLEX-1 rows.")
    return frames


def crank_angle_deg_from_frame(frame: VerificationFrame) -> float:
    crank_nodes = frame.parts["CRANK-1"].deformed_xy
    vector = crank_nodes[-1] - crank_nodes[0]
    return float(np.degrees(np.arctan2(vector[1], vector[0])))


def wrap_angle_0_360(angle_deg: float) -> float:
    wrapped = angle_deg % 360.0
    if wrapped < 0.0:
        wrapped += 360.0
    return wrapped


def get_section520_overlay_payload() -> dict[str, object]:
    global SECTION520_OVERLAY_CACHE
    if SECTION520_OVERLAY_CACHE is not None:
        return SECTION520_OVERLAY_CACHE

    motion = section520_solve_motion()
    frames = load_verification_frames()
    prb_angles_deg = np.asarray(motion["angle_deg"], dtype=float)

    fea_frames_payload: list[dict[str, object]] = []
    for frame in frames:
        wrapped_angle = wrap_angle_0_360(crank_angle_deg_from_frame(frame))
        matched_prb_index = int(np.argmin(np.abs(prb_angles_deg - wrapped_angle)))
        fea_frames_payload.append(
            {
                "frame_label": frame.frame_label,
                "step_time": float(frame.step_time),
                "crank_angle_deg": float(crank_angle_deg_from_frame(frame)),
                "matched_prb_index": matched_prb_index,
                "parts": {
                    part_name: {
                        "node_labels": [int(value) for value in frame.parts[part_name].node_labels],
                        "base_xy": [[float(x), float(y)] for x, y in frame.parts[part_name].base_xy],
                        "deformed_xy": [[float(x), float(y)] for x, y in frame.parts[part_name].deformed_xy],
                    }
                    for part_name in FEA_PART_NAMES
                },
            }
        )

    SECTION520_OVERLAY_CACHE = {
        "parameter_source": motion["parameter_source"],
        "stiffness_label": motion["stiffness_label"],
        "gammas": motion["gammas"],
        "kbar": motion["kbar"],
        "prb_scale_to_fea": SECTION520_TO_FEA_SCALE,
        "prb_motion": motion,
        "fea_frames": fea_frames_payload,
    }
    return SECTION520_OVERLAY_CACHE


class AtlasRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBAPP_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/atlas":
            self._handle_atlas_api(parsed.query)
            return
        if parsed.path == "/api/section4-workspace":
            self._handle_section4_workspace_api()
            return
        if parsed.path == "/api/medical-experiment":
            self._handle_medical_experiment_api(parsed.query)
            return
        if parsed.path == "/api/section700-vertical-line":
            self._handle_medical_experiment_api(parsed.query)
            return
        if parsed.path == "/api/atlas-report":
            self._handle_atlas_report_api()
            return
        if parsed.path == "/api/atlas-loads":
            self._handle_atlas_loads_api(parsed.query)
            return
        if parsed.path == "/api/section520-overlay":
            self._handle_section520_overlay_api()
            return

        if parsed.path == "/":
            self.path = "/index.html"

        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def _handle_atlas_api(self, query: str) -> None:
        try:
            params = parse_qs(query)
            kappa = float(params.get("kappa", [INTERACTIVE_DEFAULT_K])[0])
            phi_deg = float(params.get("phi_deg", [INTERACTIVE_DEFAULT_PHI_DEG])[0])
            beam = read_beam_parameters(params)

            theta0_values, a_l, b_l = generate_locus_for_case(np.deg2rad(phi_deg), kappa, INTERACTIVE_NUM_POINTS)
            limits = atlas_limits(phi_deg, kappa, beam)
            allowable_theta = np.linspace(0.0, float(limits["theta0_limit_rad"]), 220)
            allowable_a, allowable_b = sampled_trajectory(allowable_theta, phi_deg, kappa)

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
            body = json.dumps(payload).encode("utf-8")
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(HTTPStatus.BAD_REQUEST)
        else:
            self.send_response(HTTPStatus.OK)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_section4_workspace_api(self) -> None:
        try:
            payload = get_section4_workspace_payload()
            body = json.dumps(payload).encode("utf-8")
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(HTTPStatus.BAD_REQUEST)
        else:
            self.send_response(HTTPStatus.OK)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_medical_experiment_api(self, query: str) -> None:
        try:
            params = parse_qs(query)
            mode = str(params.get("mode", ["sinusoid"])[0]).strip().lower()
            tip_amplitude = float(params.get("tip_amplitude", [SECTION701_TIP_AMPLITUDE])[0])
            core_motion_time = float(params.get("core_motion_time", [SECTION701_CORE_MOTION_TIME])[0])
            beam = read_beam_parameters(params)
            if tip_amplitude <= 0.0:
                raise ValueError("tip_amplitude must be positive.")
            if core_motion_time <= 0.0:
                raise ValueError("core_motion_time must be positive.")
            if mode in {"sinusoid", "section701", "sinusoidal", "cosine"}:
                payload = get_section701_sinusoid_payload(
                    tip_amplitude=tip_amplitude,
                    core_motion_time=core_motion_time,
                    beam=beam,
                )
            else:
                payload = get_section701_sinusoid_payload(
                    tip_amplitude=tip_amplitude,
                    core_motion_time=core_motion_time,
                    beam=beam,
                )
            body = json.dumps(payload).encode("utf-8")
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(HTTPStatus.BAD_REQUEST)
        else:
            self.send_response(HTTPStatus.OK)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_atlas_loads_api(self, query: str) -> None:
        try:
            params = parse_qs(query)
            kappa = float(params.get("kappa", [INTERACTIVE_DEFAULT_K])[0])
            phi_deg = float(params.get("phi_deg", [INTERACTIVE_DEFAULT_PHI_DEG])[0])
            theta0_deg = float(params.get("theta0_deg", [0.0])[0])
            beam = read_beam_parameters(params)
            limits = atlas_limits(phi_deg, kappa, beam)
            theta0_rad = np.deg2rad(min(theta0_deg, float(limits["theta0_limit_deg"])))
            state = selected_state(
                theta0_rad,
                phi_deg,
                kappa,
                beam["beam_length"],
                beam["youngs_modulus"],
                float(limits["inertia"]),
            )
            payload = {
                "limits": limits,
                "state": state,
            }
            body = json.dumps(payload).encode("utf-8")
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(HTTPStatus.BAD_REQUEST)
        else:
            self.send_response(HTTPStatus.OK)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_atlas_report_api(self) -> None:
        try:
            panels = []
            for k_value in REPORT_K_VALUES:
                curves = []
                for angle_deg in REPORT_FORCE_ANGLES_DEG:
                    theta0_values, a_l, b_l = generate_locus_for_case(np.deg2rad(angle_deg), float(k_value), NUM_POINTS)
                    curves.append(
                        {
                            "phi_deg": float(angle_deg),
                            "theta0_values": [float(value) for value in theta0_values],
                            "a_over_l": [float(value) for value in a_l],
                            "b_over_l": [float(value) for value in b_l],
                        }
                    )
                panels.append({"kappa": float(k_value), "curves": curves})

            payload = {
                "k_values": REPORT_K_VALUES,
                "force_angles_deg": REPORT_FORCE_ANGLES_DEG,
                "panels": panels,
            }
            body = json.dumps(payload).encode("utf-8")
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(HTTPStatus.BAD_REQUEST)
        else:
            self.send_response(HTTPStatus.OK)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_section520_overlay_api(self) -> None:
        try:
            payload = get_section520_overlay_payload()
            body = json.dumps(payload).encode("utf-8")
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(HTTPStatus.BAD_REQUEST)
        else:
            self.send_response(HTTPStatus.OK)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    with ThreadingHTTPServer((HOST, PORT), AtlasRequestHandler) as server:
        print(f"Serving web app at http://{HOST}:{PORT}")
        server.serve_forever()


if __name__ == "__main__":
    main()
