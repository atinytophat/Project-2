from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

import Section200_GeometricAtlas_LoadQuery as section2atlas
import Section400_PRB3R_ReportProcedure as section4

# =========================
# User input
# =========================
# Section 5.1 stiffness family is evaluated at phi = pi/2.
phi_deg = 90.0
num_theta_samples = 80

kappa_values = np.array([0.0, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0], dtype=float)

# Set to False when you want only the printed grid search results.
show_plot = True


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


def generalized_theta_range(kappa: float, phi_rad: float, sample_count: int) -> np.ndarray:
    theta_upper = section2atlas.theta0_max_for_case(phi_rad, kappa)
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
        alpha_value, qx, qy = section2atlas.compute_state_with_alpha(
            float(theta0), float(phi_rad), float(kappa)
        )
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


def fit_stiffness_for_load_family(
    gammas: np.ndarray,
    kappa: float,
    phi_rad: float,
    sample_count: int,
) -> np.ndarray:
    theta_values = generalized_theta_range(kappa, phi_rad, sample_count)
    state_samples = generalized_state_samples(theta_values, phi_rad, kappa)
    sample_data = section4.stiffness_samples_from_eq23(gammas, state_samples)
    if sample_data is None:
        raise RuntimeError("Could not compute stiffness samples for the requested load family.")
    _, kbar_samples = sample_data
    return np.median(kbar_samples, axis=1)


def compute_stiffness_rows(
    gammas: np.ndarray,
    kappa_values: np.ndarray,
    phi_rad: float,
    sample_count: int,
) -> np.ndarray:
    rows = []
    for kappa in np.asarray(kappa_values, dtype=float):
        rows.append(fit_stiffness_for_load_family(gammas, float(kappa), phi_rad, sample_count))
    return np.vstack(rows)


def arithmetic_average(stiffness_rows: np.ndarray) -> np.ndarray:
    return np.mean(stiffness_rows, axis=0)


def plot_kappa_stiffness_curves(
    kappa_values: np.ndarray,
    stiffness_rows: np.ndarray,
    average_kbar: np.ndarray,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), constrained_layout=True)
    component_labels = [r"$\bar{k}_1$", r"$\bar{k}_2$", r"$\bar{k}_3$"]

    for idx, axis in enumerate(axes):
        axis.plot(kappa_values, stiffness_rows[:, idx], "o-", color="#1f77b4", linewidth=2.0, markersize=5, label="10-point curve")
        axis.axhline(average_kbar[idx], color="#d62728", linestyle="--", linewidth=1.5, label="10-point average")
        axis.set_title(component_labels[idx])
        axis.set_xlabel(r"$\kappa$")
        axis.set_ylabel(component_labels[idx])
        axis.grid(True, alpha=0.25)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2)
    fig.suptitle("Section 5 Ten-Point Kappa Average", fontsize=13)
    plt.show()


def main() -> None:
    gammas = get_gammas()
    phi_rad = math.radians(phi_deg)
    stiffness_rows = compute_stiffness_rows(gammas, kappa_values, phi_rad, num_theta_samples)
    average_kbar = arithmetic_average(stiffness_rows)

    print("Section 5 ten-point kappa average")
    print(f"gammas = [{gammas[0]:.2f} {gammas[1]:.2f} {gammas[2]:.2f} {gammas[3]:.2f}]")
    print(f"phi = {phi_deg:.1f} deg")
    print(f"kappas = {np.array2string(kappa_values, precision=3, separator=', ')}")
    print(f"num theta samples per kappa = {num_theta_samples}")
    print(f"average kbar = [{average_kbar[0]:.5f} {average_kbar[1]:.5f} {average_kbar[2]:.5f}]")

    if show_plot:
        plot_kappa_stiffness_curves(kappa_values, stiffness_rows, average_kbar)


if __name__ == "__main__":
    main()
