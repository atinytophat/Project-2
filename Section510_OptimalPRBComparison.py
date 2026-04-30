from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

import Section200_GeometricAtlas_LoadQuery as section2atlas
import Section400_PRB3R_ReportProcedure as section4
import Section500_KappaAverageSearch as section50

# =========================
# User input
# =========================
# Section 5 uses the optimal gammas from Sec. 4.4 and then forms a
# load-independent stiffness by averaging over kappa in [0, 25].
#
# Reuse the Section 5.0 kappa grid so the averaging procedure is defined in
# one place upstream of this comparison script.
kappa_average_values = section50.kappa_values.copy()

# Figure 12 style comparison: varying kappa with fixed phi = pi/2.
figure12_load_ratios = [0.0, 0.1, 1.0, 2.0, 5.0, 25.0]
figure12_force_angle_deg = 90.0

# Figure 13 style comparison: varying phi with fixed kappa = 0.
figure13_force_angles_deg = [30.0, 60.0, 120.0, 135.0, 150.0, 175.0]
figure13_load_ratio = 0.0

num_kappa_fit_theta_samples = 80
num_locus_points = 90


def get_optimal_gammas() -> np.ndarray:
    result, _ = section4.search_characteristic_radius_factors_eq23(
        section4.l_over_t,
        section4.sigma_over_e,
        section4.gamma_step,
        section4.num_moment_samples,
        section4.num_force_samples,
        section4.force_fit_fraction,
    )
    return result.gammas.copy()


def generalized_theta_range(
    kappa: float, phi_rad: float, sample_count: int
) -> np.ndarray:
    theta_upper = section2atlas.theta0_max_for_case(phi_rad, kappa)
    if theta_upper <= 1.0e-4:
        raise RuntimeError(
            "The requested load family does not have a usable theta0 range."
        )
    return np.linspace(1.0e-4, theta_upper, sample_count)


def generalized_state_samples(
    theta_values: np.ndarray, phi_rad: float, kappa: float
) -> list[tuple[float, float, float, float, float, float]]:
    state_samples: list[tuple[float, float, float, float, float, float]] = []
    for theta0 in theta_values:
        alpha_value, qx, qy = section2atlas.compute_state_with_alpha(
            float(theta0), float(phi_rad), float(kappa)
        )
        beta_value = (
            0.0 if kappa == 0.0 else 2.0 * math.sqrt(float(alpha_value) * float(kappa))
        )
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
    gammas: np.ndarray, kappa: float, phi_rad: float, sample_count: int
) -> np.ndarray:
    theta_values = generalized_theta_range(kappa, phi_rad, sample_count)
    state_samples = generalized_state_samples(theta_values, phi_rad, kappa)
    sample_data = section4.stiffness_samples_from_eq23(gammas, state_samples)
    if sample_data is None:
        raise RuntimeError(
            "Could not compute stiffness samples for the requested load family."
        )
    _, kbar_samples = sample_data
    return np.median(kbar_samples, axis=1)


def compute_load_independent_stiffness(
    gammas: np.ndarray, kappa_values: np.ndarray, phi_rad: float, sample_count: int
) -> tuple[np.ndarray, list[tuple[float, np.ndarray]]]:
    stiffness_rows: list[np.ndarray] = []
    stiffness_by_kappa: list[tuple[float, np.ndarray]] = []

    for kappa in kappa_values:
        kbar = fit_stiffness_for_load_family(
            gammas, float(kappa), phi_rad, sample_count
        )
        stiffness_rows.append(kbar)
        stiffness_by_kappa.append((float(kappa), kbar))

    return np.mean(np.vstack(stiffness_rows), axis=0), stiffness_by_kappa


def select_section51_stiffness(
    gammas: np.ndarray,
) -> tuple[np.ndarray, list[tuple[float, np.ndarray]], str]:
    kbar, stiffness_by_kappa = compute_load_independent_stiffness(
        gammas,
        kappa_average_values,
        math.pi / 2.0,
        num_kappa_fit_theta_samples,
    )
    return kbar, stiffness_by_kappa, "computed load-independent average"


def equilibrium_residual(
    theta: np.ndarray, load_vector: np.ndarray, gammas: np.ndarray, kbar: np.ndarray
) -> np.ndarray:
    return kbar * theta - section4.prb3r_jacobian(theta, gammas).T @ load_vector


def solve_prb3r_equilibrium(
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
            residual = equilibrium_residual(theta, load_vector, gammas, kbar)
            if np.linalg.norm(residual, ord=2) < 1.0e-10:
                converged = True
                break

            tangent = np.zeros((3, 3), dtype=float)
            step = 1.0e-7
            try:
                for idx in range(3):
                    theta_shift = theta.copy()
                    theta_shift[idx] += step
                    residual_shift = equilibrium_residual(
                        theta_shift, load_vector, gammas, kbar
                    )
                    tangent[:, idx] = (residual_shift - residual) / step
                delta = np.linalg.solve(tangent, -residual)
            except np.linalg.LinAlgError:
                break

            theta += delta
            if np.linalg.norm(delta, ord=2) < 1.0e-10:
                residual = equilibrium_residual(theta, load_vector, gammas, kbar)
                if np.linalg.norm(residual, ord=2) < 1.0e-8:
                    converged = True
                    break

        if converged:
            qx, qy, theta0 = section4.prb3r_forward_kinematics(theta, gammas)
            return theta, np.array([qx, qy, theta0], dtype=float)

    raise RuntimeError(
        "Could not solve the PRB 3R static equilibrium for this load case."
    )


def evaluate_load_family(
    gammas: np.ndarray,
    kbar: np.ndarray,
    phi_deg: float,
    kappa: float,
    point_count: int,
) -> dict[str, np.ndarray | float]:
    phi_rad = math.radians(phi_deg)
    theta0_values, actual_x, actual_y = section2atlas.generate_locus_for_case(
        phi_rad, kappa, point_count
    )

    prb_x: list[float] = []
    prb_y: list[float] = []
    prb_theta0: list[float] = []
    tip_error: list[float] = []
    slope_error: list[float] = []
    theta_guess: np.ndarray | None = None

    for theta0_actual, qx_actual, qy_actual in zip(theta0_values, actual_x, actual_y):
        alpha_value, _, _ = section2atlas.compute_state_with_alpha(
            float(theta0_actual), phi_rad, kappa
        )
        beta_value = (
            0.0 if kappa == 0.0 else 2.0 * math.sqrt(float(alpha_value) * float(kappa))
        )
        atlas_guess = section4.prb3r_inverse_kinematics(
            float(qx_actual), float(qy_actual), float(theta0_actual), gammas
        )
        theta_guess, prb_state = solve_prb3r_equilibrium(
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
        prb_theta0.append(float(prb_state[2]))
        tip_error.append(
            math.hypot(
                float(prb_state[0]) - float(qx_actual),
                float(prb_state[1]) - float(qy_actual),
            )
        )
        slope_error.append(abs(float(prb_state[2]) - float(theta0_actual)))

    tip_error_array = np.asarray(tip_error, dtype=float)
    slope_error_array = np.asarray(slope_error, dtype=float)
    max_tip_index = int(np.argmax(tip_error_array))

    return {
        "theta0_actual": np.asarray(theta0_values, dtype=float),
        "actual_x": np.asarray(actual_x, dtype=float),
        "actual_y": np.asarray(actual_y, dtype=float),
        "prb_x": np.asarray(prb_x, dtype=float),
        "prb_y": np.asarray(prb_y, dtype=float),
        "prb_theta0": np.asarray(prb_theta0, dtype=float),
        "tip_error": tip_error_array,
        "slope_error": slope_error_array,
        "max_tip_error": float(np.max(tip_error_array)),
        "max_slope_error_deg": float(np.rad2deg(np.max(slope_error_array))),
        "theta0_at_max_tip_error_deg": float(np.rad2deg(theta0_values[max_tip_index])),
    }


def plot_comparison_grid(
    cases: list[dict[str, np.ndarray | float]],
    labels: list[str],
    title: str,
) -> plt.Figure:
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
    axes = axes.ravel()

    for axis, case, label in zip(axes, cases, labels):
        actual_x = np.asarray(case["actual_x"], dtype=float)
        actual_y = np.asarray(case["actual_y"], dtype=float)
        prb_x = np.asarray(case["prb_x"], dtype=float)
        prb_y = np.asarray(case["prb_y"], dtype=float)
        max_tip_error = float(case["max_tip_error"])

        axis.plot(
            prb_x, prb_y, color="#d62728", linewidth=2.0, label="Optimal PRB 3R model"
        )
        axis.plot(
            actual_x, actual_y, "k.", markersize=3.0, label="Numerical integration"
        )
        axis.set_title(f"{label}\nmax tip error/L = {100.0 * max_tip_error:.2f}%")
        axis.set_xlabel("a / l")
        axis.set_ylabel("b / l")
        axis.set_xlim(-0.1, 1.05)
        axis.set_ylim(0.0, 1.05)
        axis.set_aspect("equal", adjustable="box")
        axis.grid(True, alpha=0.25)

    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", ncol=2)
    fig.suptitle(title, fontsize=13)
    return fig


def main() -> None:
    gammas = get_optimal_gammas()
    kbar, stiffness_by_kappa, stiffness_label = select_section51_stiffness(gammas)

    print("Section 5.1 optimal PRB 3R comparison")
    print(f"gammas = [{gammas[0]:.2f} {gammas[1]:.2f} {gammas[2]:.2f} {gammas[3]:.2f}]")
    print(f"{stiffness_label} kbar = [{kbar[0]:.5f} {kbar[1]:.5f} {kbar[2]:.5f}]")
    if stiffness_by_kappa:
        print("kappa-averaging stiffness values:")
        for kappa_value, stiffness in stiffness_by_kappa:
            print(
                f"  kappa = {kappa_value:>5g} -> "
                f"[{stiffness[0]:.5f} {stiffness[1]:.5f} {stiffness[2]:.5f}]"
            )

    figure12_cases = [
        evaluate_load_family(
            gammas, kbar, figure12_force_angle_deg, float(kappa), num_locus_points
        )
        for kappa in figure12_load_ratios
    ]
    print("\nFigure 12 style cases (varying kappa, phi = 90 deg):")
    for kappa, case in zip(figure12_load_ratios, figure12_cases):
        print(
            f"  kappa = {kappa:g} -> "
            f"max tip error/L = {100.0 * float(case['max_tip_error']):.2f}%, "
            f"max slope error = {float(case['max_slope_error_deg']):.2f} deg"
        )

    figure13_cases = [
        evaluate_load_family(
            gammas, kbar, float(phi_deg), figure13_load_ratio, num_locus_points
        )
        for phi_deg in figure13_force_angles_deg
    ]
    print("\nFigure 13 style cases (varying phi, kappa = 0):")
    for phi_deg, case in zip(figure13_force_angles_deg, figure13_cases):
        print(
            f"  phi = {phi_deg:g} deg -> "
            f"max tip error/L = {100.0 * float(case['max_tip_error']):.2f}%, "
            f"max slope error = {float(case['max_slope_error_deg']):.2f} deg, "
            f"theta0 at max tip error = {float(case['theta0_at_max_tip_error_deg']):.2f} deg"
        )

    figure12 = plot_comparison_grid(
        figure12_cases,
        [rf"$\kappa = {kappa:g}$" for kappa in figure12_load_ratios],
        (
            "Section 5.1 Comparison of the Optimal PRB 3R Model With Numerical Integration\n"
            rf"Varying $\kappa$ with fixed $\phi = {figure12_force_angle_deg:g}^\circ$"
        ),
    )
    figure13 = plot_comparison_grid(
        figure13_cases,
        [rf"$\phi = {phi_deg:g}^\circ$" for phi_deg in figure13_force_angles_deg],
        (
            "Section 5.1 Comparison of the Optimal PRB 3R Model With Numerical Integration\n"
            rf"Varying $\phi$ with fixed $\kappa = {figure13_load_ratio:g}$"
        ),
    )

    figure12.canvas.manager.set_window_title("Section 5.1 Figure 12 Style Comparison")
    figure13.canvas.manager.set_window_title("Section 5.1 Figure 13 Style Comparison")
    plt.show()


if __name__ == "__main__":
    main()
