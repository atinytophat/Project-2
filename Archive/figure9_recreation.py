"""Recreate the pure-moment comparison in Fig. 9 from Haijun Su's paper."""

from __future__ import annotations

import math

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

import Section4_GammasAndStiffness as section4


PRB1R_GAMMA_MOMENT = 0.735
PRB1R_KBAR_MOMENT = 1.51
REPRESENTATIVE_THETA0 = [9.0 * math.pi / 50.0, 37.0 * math.pi / 50.0, 3.0 * math.pi / 2.0]


def actual_tip_locus(theta0_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    qx = np.sin(theta0_values) / theta0_values
    qy = (1.0 - np.cos(theta0_values)) / theta0_values
    return qx, qy


def actual_beam_centerline(theta0: float, num_points: int = 300) -> tuple[np.ndarray, np.ndarray]:
    xi = np.linspace(0.0, 1.0, num_points)
    if abs(theta0) < 1.0e-12:
        return xi, np.zeros_like(xi)
    x = np.sin(theta0 * xi) / theta0
    y = (1.0 - np.cos(theta0 * xi)) / theta0
    return x, y


def prb3r_tip_locus(theta0_values: np.ndarray, gammas: np.ndarray, kbar_moment: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    qx = np.zeros_like(theta0_values)
    qy = np.zeros_like(theta0_values)
    for idx, theta0 in enumerate(theta0_values):
        eta = theta0
        theta = eta / kbar_moment
        qx[idx], qy[idx], _ = section4.prb3r_forward_kinematics(theta, gammas)
    return qx, qy


def prb3r_chain_nodes(theta0: float, gammas: np.ndarray, kbar_moment: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    eta = theta0
    theta = eta / kbar_moment
    t1, t2, t3 = theta
    t12 = t1 + t2
    t123 = t12 + t3

    x_nodes = np.array(
        [
            0.0,
            gammas[0],
            gammas[0] + gammas[1] * math.cos(t1),
            gammas[0] + gammas[1] * math.cos(t1) + gammas[2] * math.cos(t12),
            gammas[0] + gammas[1] * math.cos(t1) + gammas[2] * math.cos(t12) + gammas[3] * math.cos(t123),
        ]
    )
    y_nodes = np.array(
        [
            0.0,
            0.0,
            gammas[1] * math.sin(t1),
            gammas[1] * math.sin(t1) + gammas[2] * math.sin(t12),
            gammas[1] * math.sin(t1) + gammas[2] * math.sin(t12) + gammas[3] * math.sin(t123),
        ]
    )
    return x_nodes, y_nodes


def prb1r_tip_locus(theta0_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    eta = theta0_values
    theta_prb = eta / PRB1R_KBAR_MOMENT
    qx = (1.0 - PRB1R_GAMMA_MOMENT) + PRB1R_GAMMA_MOMENT * np.cos(theta_prb)
    qy = PRB1R_GAMMA_MOMENT * np.sin(theta_prb)
    return qx, qy


def main() -> None:
    result = section4.get_figure9_parameters()
    gammas = result.gammas
    kbar_moment = result.kbar_moment

    theta0_values = np.linspace(1.0e-4, 3.0 * math.pi / 2.0, 300)
    qx_actual, qy_actual = actual_tip_locus(theta0_values)
    qx_prb3r, qy_prb3r = prb3r_tip_locus(theta0_values, gammas, kbar_moment)
    qx_prb1r, qy_prb1r = prb1r_tip_locus(theta0_values)

    fig = plt.figure(figsize=(13, 10), constrained_layout=True)
    grid = gridspec.GridSpec(3, 2, figure=fig, width_ratios=[1.7, 1.0])

    ax_main = fig.add_subplot(grid[:, 0])
    ax_main.plot(qx_actual, qy_actual, color="black", linewidth=2.0, label="Numerical Integration")
    ax_main.plot(qx_prb3r, qy_prb3r, color="#1f77b4", linewidth=2.0, label="PRB 3R Model")
    ax_main.plot(qx_prb1r, qy_prb1r, color="#d62728", linewidth=2.0, linestyle="--", label="PRB 1R Model")

    for theta0 in REPRESENTATIVE_THETA0:
        qx_mark = math.sin(theta0) / theta0
        qy_mark = (1.0 - math.cos(theta0)) / theta0
        ax_main.plot(qx_mark, qy_mark, "o", color="black", markersize=4)

    ax_main.set_title("Figure 9 Recreation: Pure-Moment Tip Loci")
    ax_main.set_xlabel("a / l")
    ax_main.set_ylabel("b / l")
    ax_main.set_xlim(-0.2, 1.05)
    ax_main.set_ylim(0.0, 0.95)
    ax_main.set_aspect("equal", adjustable="box")
    ax_main.grid(True, alpha=0.25)
    ax_main.legend(loc="lower left")

    panel_titles = [
        r"$\theta_0 = 9\pi/50$",
        r"$\theta_0 = 37\pi/50$",
        r"$\theta_0 = 3\pi/2$",
    ]

    for row, (theta0, title) in enumerate(zip(REPRESENTATIVE_THETA0, panel_titles)):
        ax = fig.add_subplot(grid[row, 1])
        x_beam, y_beam = actual_beam_centerline(theta0)
        x_chain, y_chain = prb3r_chain_nodes(theta0, gammas, kbar_moment)

        ax.plot(x_beam, y_beam, color="black", linewidth=2.0, label="Deflected beam")
        ax.plot(x_chain, y_chain, color="#1f77b4", linewidth=1.8, marker="o", label="3R chain")

        ax.set_title(title)
        ax.set_xlim(-0.2, 1.05)
        ax.set_ylim(0.0, 0.95)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.25)
        if row == 0:
            ax.legend(loc="lower left", fontsize=9)

    fig.suptitle(
        "PRB 3R parameters from Section 4 search\n"
        f"gammas = [{gammas[0]:.2f}, {gammas[1]:.2f}, {gammas[2]:.2f}, {gammas[3]:.2f}], "
        f"kbar = [{kbar_moment[0]:.3f}, {kbar_moment[1]:.3f}, {kbar_moment[2]:.3f}]",
        fontsize=13,
    )

    plt.show()


if __name__ == "__main__":
    main()
