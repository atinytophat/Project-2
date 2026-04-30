#!/usr/bin/env python3
"""Recreate Fig. 12: actual vs PRB 3R tip loci for different load ratios at phi = pi/2."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

import Section4_GammasAndStiffness as section4


phi_deg = 90.0
phi_rad = math.radians(phi_deg)
load_ratios = [0.0, 0.1, 1.0, 2.0, 5.0, 25.0]
num_theta_samples = 120
num_u_samples = 6000


def theta0_max_for_load_ratio(kappa: float, phi: float) -> float:
    if kappa <= 2.0:
        return min(math.pi, phi + math.acos(1.0 - kappa)) - 1.0e-6
    return math.pi - 1.0e-6


def solve_prb3r_equilibrium(
    lambda_value: float,
    eta: float,
    phi: float,
    gammas: np.ndarray,
    kbar: np.ndarray,
    theta0_guess: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    theta = np.zeros(3, dtype=float) if theta0_guess is None else theta0_guess.copy()
    load_vec = np.array([2.0 * lambda_value * math.cos(phi), 2.0 * lambda_value * math.sin(phi), eta], dtype=float)

    for _ in range(80):
        jac = section4.prb3r_jacobian(theta, gammas)
        residual = kbar * theta - jac.T @ load_vec
        if np.linalg.norm(residual, ord=2) < 1.0e-10:
            break

        tangent = np.zeros((3, 3), dtype=float)
        step = 1.0e-7
        for idx in range(3):
            theta_shift = theta.copy()
            theta_shift[idx] += step
            jac_shift = section4.prb3r_jacobian(theta_shift, gammas)
            residual_shift = kbar * theta_shift - jac_shift.T @ load_vec
            tangent[:, idx] = (residual_shift - residual) / step

        delta = np.linalg.solve(tangent, -residual)
        theta += delta

        if np.linalg.norm(delta, ord=2) < 1.0e-10:
            break

    qx, qy, tip_slope = section4.prb3r_forward_kinematics(theta, gammas)
    return theta, np.array([qx, qy, tip_slope], dtype=float)


def actual_and_prb_loci(kappa: float, gammas: np.ndarray, kbar: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    theta_max = theta0_max_for_load_ratio(kappa, phi_rad)
    theta0_values = np.linspace(1.0e-4, theta_max, num_theta_samples)

    actual_points = np.zeros((num_theta_samples, 2), dtype=float)
    prb_points = np.zeros((num_theta_samples, 2), dtype=float)
    theta_guess = None

    for idx, theta0 in enumerate(theta0_values):
        lambda_value, qx_actual, qy_actual = section4.section2_force_state(theta0, phi_rad, kappa, num_u_samples)
        eta = 0.0 if kappa == 0.0 else 2.0 * math.sqrt(lambda_value * kappa)

        actual_points[idx, :] = [qx_actual, qy_actual]
        theta_guess, prb_state = solve_prb3r_equilibrium(lambda_value, eta, phi_rad, gammas, kbar, theta_guess)
        prb_points[idx, :] = prb_state[:2]

    return theta0_values, actual_points[:, 0], actual_points[:, 1], prb_points


gammas, kbar = section4.get_table1_model()

fig, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
axes = axes.ravel()

for axis, kappa in zip(axes, load_ratios):
    _, qx_actual, qy_actual, prb_points = actual_and_prb_loci(kappa, gammas, kbar)
    axis.plot(prb_points[:, 0], prb_points[:, 1], color="#1f77b4", linewidth=1.8, label="Optimal PRB 3R model")
    axis.plot(qx_actual, qy_actual, "k.", markersize=3.0, label="Numerical integration")
    axis.set_title(rf"$\kappa = {kappa:g}$")
    axis.set_xlabel("a / l")
    axis.set_ylabel("b / l")
    axis.set_xlim(-0.1, 1.05)
    axis.set_ylim(0.0, 1.05)
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.25)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=2)
fig.suptitle(
    "Figure 12 Recreation: Actual vs Optimal PRB 3R Loci\n"
    rf"$\phi = \pi/2$, "
    f"gammas = [{gammas[0]:.2f}, {gammas[1]:.2f}, {gammas[2]:.2f}, {gammas[3]:.2f}], "
    f"kbar = [{kbar[0]:.2f}, {kbar[1]:.2f}, {kbar[2]:.2f}]",
    fontsize=13,
)

plt.show()
