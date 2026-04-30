from __future__ import annotations

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


def pure_force_theta_samples(gammas: np.ndarray, sample_count: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    theta0_values = section4.section46_pure_force_theta_range(sample_count)
    state_samples = section4.precompute_state_samples(theta0_values, "pure_force")
    sample_data = section4.stiffness_samples_from_eq23(gammas, state_samples)
    if sample_data is None:
        raise RuntimeError("Could not compute any PRB angle samples for the pure-force case.")

    theta_prb_samples, kbar_samples = sample_data
    valid_count = theta_prb_samples.shape[1]
    theta0_valid = theta0_values[:valid_count]
    return theta0_valid, theta_prb_samples, kbar_samples


def fit_section46_stiffness(kbar_samples: np.ndarray) -> np.ndarray:
    return np.median(kbar_samples, axis=1)


def plot_section46(
    theta_prb_samples: np.ndarray,
    torque_samples: np.ndarray,
    kbar: np.ndarray,
    gammas: np.ndarray,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))

    colors = ["tab:blue", "tab:orange", "tab:green"]
    labels = [r"actual $\Theta_1$", r"actual $\Theta_2$", r"actual $\Theta_3$"]
    fit_labels = [r"fit of $\tau_1$", r"fit of $\tau_2$", r"fit of $\tau_3$"]

    for idx in range(3):
        theta_series = theta_prb_samples[idx]
        tau_series = torque_samples[idx]
        sort_index = np.argsort(theta_series)
        theta_sorted = theta_series[sort_index]
        theta_fit = np.linspace(float(theta_sorted[0]), float(theta_sorted[-1]), 200)

        ax.plot(theta_series, tau_series, "o", markersize=3.5, color=colors[idx], label=labels[idx])
        ax.plot(theta_fit, kbar[idx] * theta_fit, "-", linewidth=1.8, color=colors[idx], label=fit_labels[idx])

    ax.set_xlabel(r"$\Theta_i$")
    ax.set_ylabel(r"$\tau_i$")
    ax.set_title("Section 4.6 Pure-Force Fit")
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
    theta0_values, theta_prb_samples, kbar_samples = pure_force_theta_samples(gammas, num_theta_samples)
    kbar = fit_section46_stiffness(kbar_samples)
    torque_samples = theta_prb_samples * kbar_samples

    print("Section 4.6 pure-force fit")
    print(f"gammas = [{gammas[0]:.2f} {gammas[1]:.2f} {gammas[2]:.2f} {gammas[3]:.2f}]")
    print(f"k1 = {kbar[0]:.5f}")
    print(f"k2 = {kbar[1]:.5f}")
    print(f"k3 = {kbar[2]:.5f}")

    plot_section46(theta_prb_samples, torque_samples, kbar, gammas)


if __name__ == "__main__":
    main()
