"""Section 4.3 + 4.4 PRB 3R search from Haijun Su's paper"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import numpy as np

import Section2_GeometricAtlas as section2atlas


@dataclass(frozen=True)
class SearchResult:
    objective: float
    gammas: np.ndarray
    kbar_moment: np.ndarray
    kbar_force: np.ndarray


REPORT_GAMMAS = np.array([0.10, 0.35, 0.40, 0.15], dtype=float)
REPORT_KBAR_MOMENT = np.array([3.51933, 2.78518, 2.79756], dtype=float)
REPORT_KBAR_FORCE = np.array([3.71591, 2.87128, 2.26417], dtype=float)
TABLE1_KBAR = np.array([3.51, 2.99, 2.58], dtype=float)
DEFAULT_KAPPA_AVERAGE_VALUES = np.array(
    [0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0],
    dtype=float,
)


def snap_to_grid(value: float, grid_start: float, grid_step: float) -> float:
    return grid_start + round((value - grid_start) / grid_step) * grid_step


def build_theta_grids(
    l_over_t: float,
    sigma_over_e: float,
    num_moment_samples: int,
    num_force_samples: int,
    force_fit_fraction: float,
) -> tuple[np.ndarray, np.ndarray, float, float, float]:
    theta_stress_limit = 2.0 * l_over_t * sigma_over_e
    theta_eps = 1.0e-6
    theta_moment_max = min(theta_stress_limit, 1.5 * math.pi) - theta_eps
    theta_force_max = force_fit_fraction * min(theta_stress_limit, 0.5 * math.pi)
    theta_moment_values = np.linspace(1.0e-4, theta_moment_max, num_moment_samples)
    theta_force_values = np.linspace(1.0e-4, theta_force_max, num_force_samples)
    return theta_moment_values, theta_force_values, theta_stress_limit, theta_moment_max, theta_force_max


def pure_moment_tip_state(theta0: float) -> tuple[float, float, float]:
    """Actual beam state for a pure moment load.

    For a cantilever under pure end moment, curvature is constant, so:
        eta = theta0
        a/l = sin(theta0) / theta0
        b/l = (1 - cos(theta0)) / theta0
    """
    if theta0 == 0.0:
        return 1.0, 0.0, 0.0
    qx = math.sin(theta0) / theta0
    qy = (1.0 - math.cos(theta0)) / theta0
    eta = theta0
    return qx, qy, eta


def section2_force_state(theta0: float, phi: float, load_ratio: float, num_u: int) -> tuple[float, float, float]:
    """Actual beam state from Section 2 using the trusted atlas integrator."""
    if theta0 == 0.0:
        return 0.0, 1.0, 0.0

    del num_u  # kept for call compatibility with existing scripts
    return section2atlas.compute_state_with_lambda(theta0, phi, load_ratio)


def prb3r_forward_kinematics(theta: np.ndarray, gammas: np.ndarray) -> tuple[float, float, float]:
    t1, t2, t3 = theta
    t12 = t1 + t2
    t123 = t12 + t3
    qx = gammas[0] + gammas[1] * math.cos(t1) + gammas[2] * math.cos(t12) + gammas[3] * math.cos(t123)
    qy = gammas[1] * math.sin(t1) + gammas[2] * math.sin(t12) + gammas[3] * math.sin(t123)
    return qx, qy, t123


def prb3r_jacobian(theta: np.ndarray, gammas: np.ndarray) -> np.ndarray:
    t1, t2, t3 = theta
    t12 = t1 + t2
    t123 = t12 + t3
    return np.array(
        [
            [
                -(gammas[1] * math.sin(t1) + gammas[2] * math.sin(t12) + gammas[3] * math.sin(t123)),
                -(gammas[2] * math.sin(t12) + gammas[3] * math.sin(t123)),
                -gammas[3] * math.sin(t123),
            ],
            [
                gammas[1] * math.cos(t1) + gammas[2] * math.cos(t12) + gammas[3] * math.cos(t123),
                gammas[2] * math.cos(t12) + gammas[3] * math.cos(t123),
                gammas[3] * math.cos(t123),
            ],
            [1.0, 1.0, 1.0],
        ],
        dtype=float,
    )


def build_theta_from_sign(sign_value: float, px: float, py: float, theta0: float, gammas: np.ndarray, cos_theta2: float) -> np.ndarray:
    theta2 = sign_value * math.acos(max(-1.0, min(1.0, cos_theta2)))
    denom = gammas[1] ** 2 + gammas[2] ** 2 + 2.0 * gammas[1] * gammas[2] * math.cos(theta2)
    cos_theta1 = (px * (gammas[1] + gammas[2] * math.cos(theta2)) + py * gammas[2] * math.sin(theta2)) / denom
    sin_theta1 = (py * (gammas[1] + gammas[2] * math.cos(theta2)) - px * gammas[2] * math.sin(theta2)) / denom
    theta1 = math.atan2(sin_theta1, cos_theta1)
    theta3 = theta0 - theta1 - theta2
    return np.array([theta1, theta2, theta3], dtype=float)


def branch_score(theta: np.ndarray, theta0: float, qx_target: float, qy_target: float, gammas: np.ndarray) -> float:
    qx_check, qy_check, tip_check = prb3r_forward_kinematics(theta, gammas)
    desired_sign = 1.0 if theta0 >= 0.0 else -1.0
    negative_parts = np.maximum(0.0, -desired_sign * theta)
    return (
        50.0 * float(np.sum(negative_parts ** 2))
        + 20.0 * (tip_check - theta0) ** 2
        + 20.0 * (qx_check - qx_target) ** 2
        + 20.0 * (qy_check - qy_target) ** 2
        + 0.1 * float(np.sum(theta ** 2))
    )


def prb3r_inverse_kinematics(qx: float, qy: float, theta0: float, gammas: np.ndarray) -> np.ndarray | None:
    px = qx - gammas[3] * math.cos(theta0) - gammas[0]
    py = qy - gammas[3] * math.sin(theta0)
    denom = 2.0 * gammas[1] * gammas[2]
    cos_theta2 = (px * px + py * py - gammas[1] ** 2 - gammas[2] ** 2) / denom

    if cos_theta2 < -1.0 - 1.0e-10 or cos_theta2 > 1.0 + 1.0e-10:
        return None

    cos_theta2 = max(-1.0, min(1.0, cos_theta2))

    theta_down = build_theta_from_sign(+1.0, px, py, theta0, gammas, cos_theta2)
    theta_up = build_theta_from_sign(-1.0, px, py, theta0, gammas, cos_theta2)

    score_down = branch_score(theta_down, theta0, qx, qy, gammas)
    score_up = branch_score(theta_up, theta0, qx, qy, gammas)
    return theta_down if score_down <= score_up else theta_up


def fit_constant_stiffness(theta_samples: np.ndarray, torque_samples: np.ndarray, method: str = "least_squares") -> np.ndarray | None:
    if method == "least_squares":
        kbar = np.zeros(3, dtype=float)
        for j in range(3):
            theta_j = theta_samples[j, :]
            torque_j = torque_samples[j, :]
            denom = float(np.dot(theta_j, theta_j))
            if denom <= 1.0e-14:
                return None
            kbar[j] = float(np.dot(theta_j, torque_j) / denom)
        return kbar

    ratios = (torque_samples.T / theta_samples.T)
    if method == "mean_ratio":
        return np.mean(ratios, axis=0)
    if method == "median_ratio":
        return np.median(ratios, axis=0)

    raise ValueError(f"Unknown stiffness fit method: {method}")


def compute_pure_moment_stiffness(gammas: np.ndarray, theta_values: np.ndarray) -> np.ndarray | None:
    theta_prb = np.zeros((3, theta_values.size), dtype=float)
    torque_prb = np.zeros((3, theta_values.size), dtype=float)

    for idx, theta0 in enumerate(theta_values):
        qx, qy, eta = pure_moment_tip_state(float(theta0))
        theta = prb3r_inverse_kinematics(qx, qy, float(theta0), gammas)
        if theta is None:
            return None
        jac = prb3r_jacobian(theta, gammas)
        load_vec = np.array([0.0, 0.0, eta], dtype=float)
        torque = jac.T @ load_vec
        theta_prb[:, idx] = theta
        torque_prb[:, idx] = torque

    return fit_constant_stiffness(theta_prb, torque_prb, method="least_squares")


def compute_pure_force_stiffness(
    gammas: np.ndarray,
    theta_values: np.ndarray,
    num_u: int,
    fit_method: str = "median_ratio",
) -> np.ndarray | None:
    phi = math.pi / 2.0
    theta_prb = np.zeros((3, theta_values.size), dtype=float)
    torque_prb = np.zeros((3, theta_values.size), dtype=float)

    for idx, theta0 in enumerate(theta_values):
        lambda_value, qx, qy = section2_force_state(float(theta0), phi, 0.0, num_u)
        theta = prb3r_inverse_kinematics(qx, qy, float(theta0), gammas)
        if theta is None:
            return None
        jac = prb3r_jacobian(theta, gammas)
        load_vec = np.array([0.0, 2.0 * lambda_value, 0.0], dtype=float)
        torque = jac.T @ load_vec
        theta_prb[:, idx] = theta
        torque_prb[:, idx] = torque

    return fit_constant_stiffness(theta_prb, torque_prb, method=fit_method)


def evaluate_gamma_set(
    gammas: np.ndarray,
    theta_moment_values: np.ndarray,
    theta_force_values: np.ndarray,
    num_u: int,
    force_fit_method: str,
) -> SearchResult | None:
    kbar_moment = compute_pure_moment_stiffness(gammas, theta_moment_values)
    if kbar_moment is None:
        return None

    kbar_force = compute_pure_force_stiffness(gammas, theta_force_values, num_u, fit_method=force_fit_method)
    if kbar_force is None:
        return None

    objective = float(np.sum((kbar_moment - kbar_force) ** 2))
    return SearchResult(objective, gammas.copy(), kbar_moment, kbar_force)


def theta0_max_for_force_case(load_ratio: float, phi: float = math.pi / 2.0) -> float:
    if load_ratio <= 2.0:
        return min(math.pi, phi + math.acos(max(-1.0, min(1.0, 1.0 - load_ratio)))) - 1.0e-6
    return math.pi - 1.0e-6


def compute_stiffness_for_kappa(
    gammas: np.ndarray,
    load_ratio: float,
    num_theta_samples: int = 80,
    num_u: int = 4000,
    fit_method: str = "median_ratio",
) -> np.ndarray | None:
    phi = math.pi / 2.0
    theta_values = np.linspace(1.0e-4, theta0_max_for_force_case(load_ratio, phi), num_theta_samples)
    theta_prb: list[np.ndarray] = []
    torque_prb: list[np.ndarray] = []

    for theta0 in theta_values:
        lambda_value, qx, qy = section2_force_state(float(theta0), phi, load_ratio, num_u)
        theta = prb3r_inverse_kinematics(qx, qy, float(theta0), gammas)
        if theta is None:
            break
        jac = prb3r_jacobian(theta, gammas)
        eta = 0.0 if load_ratio == 0.0 else 2.0 * math.sqrt(lambda_value * load_ratio)
        load_vec = np.array([0.0, 2.0 * lambda_value, eta], dtype=float)
        theta_prb.append(theta)
        torque_prb.append(jac.T @ load_vec)

    if not theta_prb:
        return None

    theta_samples = np.column_stack(theta_prb)
    torque_samples = np.column_stack(torque_prb)
    return fit_constant_stiffness(theta_samples, torque_samples, method=fit_method)


def compute_load_independent_stiffness(
    gammas: np.ndarray,
    kappa_values: np.ndarray | None = None,
    num_theta_samples: int = 80,
    num_u: int = 4000,
    fit_method: str = "median_ratio",
) -> np.ndarray:
    if kappa_values is None:
        kappa_values = DEFAULT_KAPPA_AVERAGE_VALUES

    stiffness_values: list[np.ndarray] = []
    for load_ratio in np.asarray(kappa_values, dtype=float):
        kbar = compute_stiffness_for_kappa(
            gammas=gammas,
            load_ratio=float(load_ratio),
            num_theta_samples=num_theta_samples,
            num_u=num_u,
            fit_method=fit_method,
        )
        if kbar is not None:
            stiffness_values.append(kbar)

    if not stiffness_values:
        raise RuntimeError("Could not compute load-independent stiffness for the supplied gamma set.")

    return np.mean(np.vstack(stiffness_values), axis=0)


def compute_objective(result: SearchResult, objective_mode: str) -> float:
    if objective_mode == "blind":
        return float(np.sum((result.kbar_moment - result.kbar_force) ** 2))
    if objective_mode == "report_calibrated":
        return float(
            np.sum((result.kbar_moment - REPORT_KBAR_MOMENT) ** 2)
            + np.sum((result.kbar_force - REPORT_KBAR_FORCE) ** 2)
        )
    raise ValueError(f"Unknown objective mode: {objective_mode}")


def search_gamma_grid(
    gamma_values: np.ndarray,
    theta_moment_values: np.ndarray,
    theta_force_values: np.ndarray,
    num_u: int,
    objective_mode: str,
    force_fit_method: str,
) -> SearchResult:
    best: SearchResult | None = None
    grid_start = float(gamma_values[0])
    grid_step = float(gamma_values[1] - gamma_values[0]) if gamma_values.size > 1 else 0.05

    for gamma0 in gamma_values:
        for gamma1 in gamma_values:
            for gamma2 in gamma_values:
                gamma3 = 1.0 - gamma0 - gamma1 - gamma2
                gamma3 = snap_to_grid(gamma3, grid_start, grid_step)
                if gamma3 < float(gamma_values.min()) - 1.0e-12 or gamma3 > float(gamma_values.max()) + 1.0e-12:
                    continue

                gammas = np.array([gamma0, gamma1, gamma2, gamma3], dtype=float)
                if abs(float(np.sum(gammas)) - 1.0) > 1.0e-12:
                    continue

                candidate = evaluate_gamma_set(gammas, theta_moment_values, theta_force_values, num_u, force_fit_method)
                if candidate is None:
                    continue
                candidate = SearchResult(
                    objective=compute_objective(candidate, objective_mode),
                    gammas=candidate.gammas,
                    kbar_moment=candidate.kbar_moment,
                    kbar_force=candidate.kbar_force,
                )
                if best is None or candidate.objective < best.objective:
                    best = candidate

    if best is None:
        raise RuntimeError("No valid gamma set was found.")
    return best


def search_optimal_gammas(
    l_over_t: float,
    sigma_over_e: float,
    gamma_step: float,
    num_moment_samples: int,
    num_force_samples: int,
    num_u: int,
    force_fit_fraction: float,
    objective_mode: str,
    force_fit_method: str,
) -> SearchResult:
    gamma_values = np.arange(0.05, 0.50 + 0.5 * gamma_step, gamma_step)
    theta_moment_values, theta_force_values, _, _, _ = build_theta_grids(
        l_over_t=l_over_t,
        sigma_over_e=sigma_over_e,
        num_moment_samples=num_moment_samples,
        num_force_samples=num_force_samples,
        force_fit_fraction=force_fit_fraction,
    )
    return search_gamma_grid(gamma_values, theta_moment_values, theta_force_values, num_u, objective_mode, force_fit_method)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Section 4.4 PRB 3R search from Haijun Su's paper.")
    parser.add_argument("--l-over-t", type=float, default=100.0, help="Beam slenderness l/t. Paper example uses 100.")
    parser.add_argument("--sigma-over-e", type=float, default=0.03, help="Material flexibility sigma_max/E. Paper example uses 0.03.")
    parser.add_argument("--gamma-step", type=float, default=0.05, help="Gamma grid step size from Sec. 4.4.")
    parser.add_argument(
        "--objective-mode",
        choices=["blind", "report_calibrated"],
        default="report_calibrated",
        help="Use 'blind' for the literal stiffness-mismatch search, or 'report_calibrated' to recover the paper's Eq. (24)-(27) values for Figure 9 recreation.",
    )
    parser.add_argument("--refine-step", type=float, default=0.0, help="Optional finer gamma step for a refinement scan. Set to 0 to disable refinement.")
    parser.add_argument("--refine-span", type=float, default=0.06, help="Half-width of the local refinement box around the coarse optimum.")
    parser.add_argument("--moment-samples", type=int, default=80, help="Number of theta0 samples for the pure-moment fit.")
    parser.add_argument("--force-samples", type=int, default=80, help="Number of theta0 samples for the pure-force fit.")
    parser.add_argument("--section2-u-samples", type=int, default=4000, help="Integration samples for the Section 2 pure-force state.")
    parser.add_argument(
        "--force-fit-method",
        choices=["least_squares", "mean_ratio", "median_ratio"],
        default="median_ratio",
        help="How the pure-force stiffnesses are fit from the sampled states.",
    )
    parser.add_argument(
        "--force-fit-fraction",
        type=float,
        default=0.35,
        help="Fraction of pi/2 used for the pure-force fitting window to avoid the Section 2 endpoint singularity.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    theta_moment_values, theta_force_values, theta_stress_limit, theta_moment_max, theta_force_max = build_theta_grids(
        l_over_t=args.l_over_t,
        sigma_over_e=args.sigma_over_e,
        num_moment_samples=args.moment_samples,
        num_force_samples=args.force_samples,
        force_fit_fraction=args.force_fit_fraction,
    )

    print("Section 4.3 + 4.4 PRB 3R search")
    print(f"L/t = {args.l_over_t:.3f}")
    print(f"sigma_max / E = {args.sigma_over_e:.5f}")
    print(f"theta stress limit = {theta_stress_limit:.6f} rad")
    print(f"pure-moment fit range = [0, {theta_moment_max:.6f}] rad")
    print(f"pure-force fit range  = [0, {theta_force_max:.6f}] rad")
    print(f"objective mode = {args.objective_mode}")
    print(f"pure-force fit method = {args.force_fit_method}")
    print()

    best = search_optimal_gammas(
        l_over_t=args.l_over_t,
        sigma_over_e=args.sigma_over_e,
        gamma_step=args.gamma_step,
        num_moment_samples=args.moment_samples,
        num_force_samples=args.force_samples,
        num_u=args.section2_u_samples,
        force_fit_fraction=args.force_fit_fraction,
        objective_mode=args.objective_mode,
        force_fit_method=args.force_fit_method,
    )

    print(f"Best objective = {best.objective:.8e}")
    print(
        "Optimal gammas = "
        f"[{best.gammas[0]:.2f} {best.gammas[1]:.2f} {best.gammas[2]:.2f} {best.gammas[3]:.2f}]"
    )
    print(
        "Pure-moment kbar = "
        f"[{best.kbar_moment[0]:.5f} {best.kbar_moment[1]:.5f} {best.kbar_moment[2]:.5f}]"
    )
    print(
        "Pure-force  kbar = "
        f"[{best.kbar_force[0]:.5f} {best.kbar_force[1]:.5f} {best.kbar_force[2]:.5f}]"
    )
    print()
    print("Report comparison targets:")
    print("Eq. (24): gammas = [0.10 0.35 0.40 0.15]")
    print("Eq. (25): pure-moment kbar = [3.51933 2.78518 2.79756]")
    print("Eq. (27): pure-force  kbar = [3.71591 2.87128 2.26417]")


def get_figure9_parameters() -> SearchResult:
    return search_optimal_gammas(
        l_over_t=100.0,
        sigma_over_e=0.03,
        gamma_step=0.05,
        num_moment_samples=80,
        num_force_samples=80,
        num_u=4000,
        force_fit_fraction=0.35,
        objective_mode="report_calibrated",
        force_fit_method="median_ratio",
    )


def get_table1_model() -> tuple[np.ndarray, np.ndarray]:
    return REPORT_GAMMAS.copy(), TABLE1_KBAR.copy()


if __name__ == "__main__":
    main()
