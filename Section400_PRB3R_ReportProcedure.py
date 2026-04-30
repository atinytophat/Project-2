from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np

import Section200_GeometricAtlas_LoadQuery as section2atlas
from Section220_Th0_max_combined import stress_limited_theta_max_from_section22

l_over_t = 100.0
sigma_over_e = 0.03
gamma_step = 0.05
num_moment_samples = 80
num_force_samples = 80
force_fit_fraction = 0.35


@dataclass(frozen=True)
class ExtremeLoadFit:
    gammas: np.ndarray
    objective: float


def precompute_state_samples(
    theta_values: np.ndarray,
    load_case: Literal["pure_moment", "pure_force"],
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
            alpha_value, qx, qy = section2atlas.compute_state_with_alpha(
                float(theta0), math.pi / 2.0, 0.0
            )
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


def prb3r_forward_kinematics(
    theta: np.ndarray, gammas: np.ndarray
) -> tuple[float, float, float]:
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


def prb3r_inverse_kinematics(
    qx: float, qy: float, theta0: float, gammas: np.ndarray
) -> np.ndarray | None:
    px = qx - gammas[0] - gammas[3] * math.cos(theta0)
    py = qy - gammas[3] * math.sin(theta0)

    denom = 2.0 * gammas[1] * gammas[2]
    cos_theta2 = (px * px + py * py - gammas[1] ** 2 - gammas[2] ** 2) / denom
    if cos_theta2 < -1.0 - 1.0e-10 or cos_theta2 > 1.0 + 1.0e-10:
        return None

    cos_theta2 = max(-1.0, min(1.0, cos_theta2))
    theta2_candidates = [math.acos(cos_theta2), -math.acos(cos_theta2)]
    solutions: list[np.ndarray] = []

    for theta2 in theta2_candidates:
        base = (
            gammas[1] ** 2
            + gammas[2] ** 2
            + 2.0 * gammas[1] * gammas[2] * math.cos(theta2)
        )
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

    if not solutions:
        return None

    # For the monotonic-curvature cases used in Sec. 4, keep one consistent branch.
    if theta0 >= 0.0:
        solutions.sort(
            key=lambda vec: (np.sum(np.maximum(0.0, -vec) ** 2), np.linalg.norm(vec))
        )
    else:
        solutions.sort(
            key=lambda vec: (np.sum(np.maximum(0.0, vec) ** 2), np.linalg.norm(vec))
        )
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


def stiffness_from_linear_regression(
    theta_samples: np.ndarray, torque_samples: np.ndarray
) -> np.ndarray | None:
    if theta_samples.size == 0:
        return None

    kbar = np.zeros(3, dtype=float)
    for idx in range(3):
        denom = float(np.dot(theta_samples[idx], theta_samples[idx]))
        if denom <= 1.0e-14:
            return None
        kbar[idx] = float(np.dot(theta_samples[idx], torque_samples[idx]) / denom)
    return kbar


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


def fit_stiffness_from_states(
    gammas: np.ndarray,
    state_samples: list[tuple[float, float, float, float, float, float]],
) -> np.ndarray | None:
    sample_data = stiffness_samples_from_eq23(gammas, state_samples)
    if sample_data is None:
        return None
    theta_prb_samples, kbar_samples = sample_data

    return stiffness_from_linear_regression(
        theta_prb_samples,
        theta_prb_samples * kbar_samples,
    )


def common_theta_range_for_extreme_load_comparison(
    l_over_t_value: float,
    sigma_over_e_value: float,
    sample_count: int,
    force_fit_fraction_value: float,
) -> tuple[np.ndarray, float]:
    theta_stress_limit = stress_limited_theta_max_from_section22(
        l_over_t_value, sigma_over_e_value
    )
    theta_common_max = force_fit_fraction_value * min(theta_stress_limit, 0.5 * math.pi)
    return np.linspace(1.0e-4, theta_common_max, sample_count), theta_stress_limit


def section45_pure_moment_theta_range(sample_count: int) -> np.ndarray:
    return np.linspace(1.0e-4, 1.5 * math.pi - 1.0e-6, sample_count)


def section46_pure_force_theta_range(sample_count: int) -> np.ndarray:
    theta_force_max = force_fit_fraction * (0.5 * math.pi)
    return np.linspace(1.0e-4, theta_force_max, sample_count)


def search_characteristic_radius_factors_eq23(
    l_over_t_value: float,
    sigma_over_e_value: float,
    gamma_step_value: float,
    moment_samples: int,
    force_samples: int,
    force_fit_fraction_value: float,
) -> tuple[ExtremeLoadFit, float]:
    theta_common_values, theta_stress_limit = (
        common_theta_range_for_extreme_load_comparison(
            l_over_t_value,
            sigma_over_e_value,
            max(moment_samples, force_samples),
            force_fit_fraction_value,
        )
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
                gamma3 = (
                    gamma_start
                    + round((gamma3 - gamma_start) / gamma_step_value)
                    * gamma_step_value
                )
                gammas = np.array([gamma0, gamma1, gamma2, gamma3], dtype=float)
                if abs(float(np.sum(gammas)) - 1.0) > 1.0e-12:
                    continue

                moment_sample_data = stiffness_samples_from_eq23(
                    gammas, moment_state_samples
                )
                if moment_sample_data is None:
                    continue
                force_sample_data = stiffness_samples_from_eq23(
                    gammas, force_state_samples
                )
                if force_sample_data is None:
                    continue

                _, moment_kbar_samples = moment_sample_data
                _, force_kbar_samples = force_sample_data
                sample_count = min(
                    moment_kbar_samples.shape[1], force_kbar_samples.shape[1]
                )
                if sample_count == 0:
                    continue

                moment_kbar_samples = moment_kbar_samples[:, :sample_count]
                force_kbar_samples = force_kbar_samples[:, :sample_count]
                objective = float(
                    np.mean(
                        np.sum((moment_kbar_samples - force_kbar_samples) ** 2, axis=0)
                    )
                )
                candidate = ExtremeLoadFit(gammas.copy(), objective)
                if best_result is None or candidate.objective < best_result.objective:
                    best_result = candidate

    if best_result is None:
        raise RuntimeError("No valid gamma set was found.")

    return best_result, theta_stress_limit


def section45_pure_moment_stiffness(
    gammas: np.ndarray, sample_count: int
) -> np.ndarray:
    state_samples = precompute_state_samples(
        section45_pure_moment_theta_range(sample_count), "pure_moment"
    )
    fit = fit_stiffness_from_states(gammas, state_samples)
    if fit is None:
        raise RuntimeError(
            "Could not compute the Section 4.5 pure-moment stiffness fit."
        )
    return fit


def section46_pure_force_stiffness(gammas: np.ndarray, sample_count: int) -> np.ndarray:
    state_samples = precompute_state_samples(
        section46_pure_force_theta_range(sample_count), "pure_force"
    )
    sample_data = stiffness_samples_from_eq23(gammas, state_samples)
    if sample_data is None:
        raise RuntimeError(
            "Could not compute the Section 4.6 pure-force stiffness samples."
        )
    _, kbar_samples = sample_data
    return np.median(kbar_samples, axis=1)


def main() -> None:
    result, theta_stress_limit = search_characteristic_radius_factors_eq23(
        l_over_t,
        sigma_over_e,
        gamma_step,
        num_moment_samples,
        num_force_samples,
        force_fit_fraction,
    )
    section45_fit = section45_pure_moment_stiffness(result.gammas, num_moment_samples)
    section46_fit = section46_pure_force_stiffness(result.gammas, num_force_samples)
    print("Section 4.4 report-procedure grid search")

    print(f"L/t = {l_over_t:.3f}")
    print(f"sigma_max / E = {sigma_over_e:.5f}")
    print(f"force-fit fraction = {force_fit_fraction:.3f}")
    print(f"theta stress limit = {theta_stress_limit:.6f} rad")
    print(
        f"gammas = [{result.gammas[0]:.2f} {result.gammas[1]:.2f} {result.gammas[2]:.2f} {result.gammas[3]:.2f}]"
    )
    print(f"search objective = {result.objective:.8e}")
    print(
        f"Sec. 4.5 pure-moment regression = [{section45_fit[0]:.5f} {section45_fit[1]:.5f} {section45_fit[2]:.5f}]"
    )
    print(
        f"Sec. 4.6 pure-force fit         = [{section46_fit[0]:.5f} {section46_fit[1]:.5f} {section46_fit[2]:.5f}]"
    )


if __name__ == "__main__":
    main()
