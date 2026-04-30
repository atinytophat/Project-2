from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

import Section400_PRB3R_ReportProcedure as section4

num_theta_samples = 120


def get_gammas() -> np.ndarray:
    result, _ = section4.search_characteristic_radius_factors_eq23(
        section4.l_over_t,
        section4.sigma_over_e,
        section4.gamma_step,
        section4.num_moment_samples,
        section4.num_force_samples,
        section4.force_fit_fraction,
    )
    return result.gammas.copy()


def pure_moment_theta_samples(gammas: np.ndarray, sample_count: int) -> tuple[np.ndarray, np.ndarray]:
    theta0_values = section4.section45_pure_moment_theta_range(sample_count)
    state_samples = section4.precompute_state_samples(theta0_values, "pure_moment")

    theta_prb_samples: list[np.ndarray] = []
    theta0_valid: list[float] = []

    for theta0, qx, qy, _, _, _ in state_samples:
        theta = section4.prb3r_inverse_kinematics(qx, qy, theta0, gammas)
        if theta is None:
            break
        theta_prb_samples.append(theta)
        theta0_valid.append(theta0)

    if not theta_prb_samples:
        raise RuntimeError("Could not compute any PRB angle samples for the pure-moment case.")

    return np.array(theta0_valid, dtype=float), np.column_stack(theta_prb_samples)


def fit_section45_stiffness(theta0_values: np.ndarray, theta_prb_samples: np.ndarray) -> np.ndarray:
    # For pure moment, Eq. (23) gives tau_i = theta0, so
    # k_i * Theta_i = theta0. A zero-intercept linear regression of
    # theta0 against Theta_i gives k_i directly.
    return section4.stiffness_from_linear_regression(theta_prb_samples, np.vstack([theta0_values] * 3))


def plot_section45(theta0_values: np.ndarray, theta_prb_samples: np.ndarray, kbar: np.ndarray, gammas: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))

    colors = ["tab:blue", "tab:orange", "tab:green"]
    labels = [r"actual $\Theta_1$", r"actual $\Theta_2$", r"actual $\Theta_3$"]
    fit_labels = [r"linear fit of $\tau_1$", r"linear fit of $\tau_2$", r"linear fit of $\tau_3$"]

    for idx in range(3):
        ax.plot(theta_prb_samples[idx], theta0_values, "o", markersize=3.5, color=colors[idx], label=labels[idx])
        ax.plot(theta0_values / kbar[idx], theta0_values, "-", linewidth=1.8, color=colors[idx], label=fit_labels[idx])

    ax.set_xlabel(r"$\Theta_i$")
    ax.set_ylabel(r"$\theta_0$")
    ax.set_title("Section 4.5 Pure-Moment Fit")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=9)

    gamma_text = (
        rf"$\gamma=[{gammas[0]:.2f}, {gammas[1]:.2f}, {gammas[2]:.2f}, {gammas[3]:.2f}]$" "\n"
        rf"$k_1={kbar[0]:.5f},\ k_2={kbar[1]:.5f},\ k_3={kbar[2]:.5f}$"
    )
    ax.text(
        0.03,
        0.97,
        gamma_text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "0.75"},
    )

    plt.tight_layout()
    plt.show()


def main() -> None:
    gammas = get_gammas()
    theta0_values, theta_prb_samples = pure_moment_theta_samples(gammas, num_theta_samples)
    kbar = fit_section45_stiffness(theta0_values, theta_prb_samples)
    if kbar is None:
        raise RuntimeError("Could not fit the Section 4.5 pure-moment stiffnesses.")

    print("Section 4.5 pure-moment fit")
    print(f"gammas = [{gammas[0]:.2f} {gammas[1]:.2f} {gammas[2]:.2f} {gammas[3]:.2f}]")
    print(f"k1 = {kbar[0]:.5f}")
    print(f"k2 = {kbar[1]:.5f}")
    print(f"k3 = {kbar[2]:.5f}")

    plot_section45(theta0_values, theta_prb_samples, kbar, gammas)


if __name__ == "__main__":
    main()
