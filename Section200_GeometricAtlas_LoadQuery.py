from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
from scipy.integrate import quad
from scipy.optimize import brentq


num_points = 150
num_theta_samples = 500  # kept for parity with the MATLAB script, though direct quad is used
K_values = [0, 0.1, 1, 1.5, 2, 2.5, 5, 50]
force_angles_deg = [9, 27, 45, 63, 81, 99, 117, 135, 153, 171]


# =========================
# Plot selection
# =========================
# Set PLOT_STYLE to:
#   "report_grid" -> reproduce the multi-panel report-style atlas
#   "interactive" -> show one atlas curve with live kappa and phi sliders
PLOT_STYLE = "interactive"

# Interactive atlas defaults.
interactive_default_k = 0.0
interactive_default_phi_deg = 90.0
interactive_num_points = 120
interactive_k_min = 0.0
interactive_k_max = 50.0
interactive_k_step = 0.05
interactive_phi_min_deg = 1.0
interactive_phi_max_deg = 179.0
interactive_phi_step_deg = 1.0


def mad(values: np.ndarray) -> float:
    median = np.median(values)
    return float(np.median(np.abs(values - median)))


def compute_single_state(th0: float, phi: float, k_value: float) -> tuple[float, float]:
    _, a_l, b_l = compute_state_with_alpha(th0, phi, k_value)
    return a_l, b_l


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
    else:
        idx = kl

    return idx


def theta0_max_for_case(phi: float, k_value: float, eps_th: float = 1.0e-6) -> float:
    if k_value <= 2:
        return min(np.pi, phi + np.arccos(1.0 - k_value)) - eps_th
    return np.pi - eps_th


def generate_locus_for_case(
    phi: float,
    k_value: float,
    num_points_local: int = num_points,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    th_max = theta0_max_for_case(phi, k_value)
    ths = np.linspace(0.0, th_max, num_points_local)
    a_l = np.zeros_like(ths)
    b_l = np.zeros_like(ths)

    for j, th0 in enumerate(ths):
        a_l[j], b_l[j] = compute_single_state(float(th0), float(phi), float(k_value))

    cutoff = current_curve_cutoff(a_l, b_l, ths, float(k_value))
    return ths[:cutoff], a_l[:cutoff], b_l[:cutoff]


def nondimensional_force_index(force: float, length: float, e_modulus: float, inertia: float) -> float:
    return float(force * length * length / (2.0 * e_modulus * inertia))


def nondimensional_moment(moment: float, length: float, e_modulus: float, inertia: float) -> float:
    return float(moment * length / (e_modulus * inertia))


def load_ratio_from_force_and_moment(
    force: float,
    moment: float,
    length: float,
    e_modulus: float,
    inertia: float,
) -> float:
    alpha_value = nondimensional_force_index(force, length, e_modulus, inertia)
    if alpha_value <= 0.0:
        return float("inf")
    beta_value = nondimensional_moment(moment, length, e_modulus, inertia)
    return float((beta_value * beta_value) / (4.0 * alpha_value))


def pure_moment_response(moment: float, length: float, e_modulus: float, inertia: float) -> tuple[float, float, float]:
    th0 = nondimensional_moment(moment, length, e_modulus, inertia)
    if abs(th0) < 1.0e-12:
        return 1.0, 0.0, 0.0
    a_l = np.sin(th0) / th0
    b_l = (1.0 - np.cos(th0)) / th0
    return float(a_l), float(b_l), float(th0)


def alpha_at_theta0_limit(phi_deg_value: float, k_value: float) -> float:
    phi = np.deg2rad(phi_deg_value)
    theta_upper = theta0_max_for_case(phi, k_value)
    alpha_value, _, _ = compute_state_with_alpha(theta_upper, phi, k_value)
    return float(alpha_value)


def dimensional_load_limits(
    phi_deg_value: float,
    k_value: float,
    length: float,
    e_modulus: float,
    inertia: float,
) -> dict[str, float]:
    alpha_max = alpha_at_theta0_limit(phi_deg_value, k_value)
    force_max = 2.0 * e_modulus * inertia * alpha_max / (length * length)

    if np.isinf(k_value):
        beta_max = float("inf")
        moment_max = float("inf")
    else:
        beta_max = 2.0 * np.sqrt(k_value * alpha_max)
        moment_max = beta_max * e_modulus * inertia / length

    return {
        "theta0_max_rad": float(theta0_max_for_case(np.deg2rad(phi_deg_value), k_value)),
        "theta0_max_deg": float(np.rad2deg(theta0_max_for_case(np.deg2rad(phi_deg_value), k_value))),
        "alpha_max": float(alpha_max),
        "beta_max": float(beta_max),
        "force_max": float(force_max),
        "moment_max": float(moment_max),
    }


def _find_theta0_for_alpha(alpha_target: float, phi: float, k_value: float) -> float:
    theta_upper = theta0_max_for_case(phi, k_value)
    theta_samples = np.linspace(1.0e-8, theta_upper, 500)
    alpha_samples = np.array(
        [compute_state_with_alpha(float(theta), phi, k_value)[0] for theta in theta_samples]
    )
    residuals = alpha_samples - alpha_target

    for left_idx in range(len(theta_samples) - 1):
        left_res = residuals[left_idx]
        right_res = residuals[left_idx + 1]
        if left_res == 0.0:
            return float(theta_samples[left_idx])
        if left_res * right_res < 0.0:
            return float(
                brentq(
                    lambda theta: compute_state_with_alpha(float(theta), phi, k_value)[0] - alpha_target,
                    float(theta_samples[left_idx]),
                    float(theta_samples[left_idx + 1]),
                    maxiter=200,
                )
            )

    min_idx = int(np.argmin(np.abs(residuals)))
    closest_alpha = float(alpha_samples[min_idx])
    raise ValueError(
        "No valid Section 2 solution was bracketed for this load case. "
        f"Closest alpha was {closest_alpha:.6g} at theta0 = {theta_samples[min_idx]:.6g} rad."
    )


def solve_tip_response_from_load(
    phi_deg_value: float,
    *,
    force: float | None = None,
    moment: float | None = None,
    length: float | None = None,
    e_modulus: float | None = None,
    inertia: float | None = None,
    alpha_value: float | None = None,
    k_value: float | None = None,
) -> dict[str, float]:
    phi = np.deg2rad(phi_deg_value)

    if alpha_value is None or k_value is None:
        if force is None or moment is None or length is None or e_modulus is None or inertia is None:
            raise ValueError("Dimensional mode requires force, moment, length, E, and I.")

        if force < 0.0:
            raise ValueError("This Section 2 solver expects a nonnegative tip force magnitude.")

        if force == 0.0:
            if moment < 0.0:
                raise ValueError("Negative pure moment is outside the monotonic-curvature Section 2 atlas.")
            a_l, b_l, th0 = pure_moment_response(moment, length, e_modulus, inertia)
            return {
                "a_over_l": a_l,
                "b_over_l": b_l,
                "theta0_rad": th0,
                "theta0_deg": float(np.rad2deg(th0)),
                "alpha": 0.0,
                "k": float("inf"),
                "beta": nondimensional_moment(moment, length, e_modulus, inertia),
            }

        alpha_value = nondimensional_force_index(force, length, e_modulus, inertia)
        k_value = load_ratio_from_force_and_moment(force, moment, length, e_modulus, inertia)

        if moment < 0.0:
            raise ValueError(
                "Negative tip moment may introduce an inflection point, which is outside the Section 2 atlas."
            )

    if alpha_value is None or k_value is None:
        raise ValueError("Either dimensional inputs or nondimensional alpha/k inputs must be provided.")

    if alpha_value < 0.0 or k_value < 0.0:
        raise ValueError("alpha and k must be nonnegative.")

    if alpha_value == 0.0:
        return {
            "a_over_l": 1.0,
            "b_over_l": 0.0,
            "theta0_rad": 0.0,
            "theta0_deg": 0.0,
            "alpha": 0.0,
            "k": float(k_value),
        }

    th0 = _find_theta0_for_alpha(float(alpha_value), phi, float(k_value))
    _, a_l, b_l = compute_state_with_alpha(th0, phi, float(k_value))
    return {
        "a_over_l": float(a_l),
        "b_over_l": float(b_l),
        "theta0_rad": float(th0),
        "theta0_deg": float(np.rad2deg(th0)),
        "alpha": float(alpha_value),
        "k": float(k_value),
    }


def plot_report_atlas() -> None:
    fig, axes = plt.subplots(2, 4, figsize=(14, 7), constrained_layout=True)
    axes = axes.ravel()

    for axis, k_value in zip(axes, K_values):
        for angle_deg in force_angles_deg:
            phi = np.deg2rad(angle_deg)
            _, a_l, b_l = generate_locus_for_case(phi, k_value, num_points)
            axis.plot(a_l, b_l, linewidth=1.0, label=f"{angle_deg} deg")

        axis.set_title(f"load ratio = {k_value:g}")
        axis.set_xlabel("a / L")
        axis.set_ylabel("b / L")
        axis.set_xlim(-0.55, 1.05)
        axis.set_ylim(0.0, 1.05)
        axis.grid(True, alpha=0.25)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside right center", title="force angle")
    fig.suptitle("Section 2 Trajectory Atlas", fontsize=14)
    plt.show()


def interactive_curve_summary(theta0_values: np.ndarray, phi_deg_value: float, k_value: float) -> str:
    theta0_max_deg = float(np.rad2deg(theta0_values[-1]))
    theta0_max_rad = float(theta0_values[-1])
    return (
        f"phi = {phi_deg_value:.1f} deg\n"
        f"kappa = {k_value:.2f}\n"
        f"theta0 max = {theta0_max_rad:.4f} rad\n"
        f"theta0 max = {theta0_max_deg:.2f} deg"
    )


def plot_interactive_atlas_curve(
    initial_phi_deg: float = interactive_default_phi_deg,
    initial_k_value: float = interactive_default_k,
) -> None:
    phi_rad = np.deg2rad(initial_phi_deg)
    theta0_values, a_l, b_l = generate_locus_for_case(
        phi_rad,
        float(initial_k_value),
        interactive_num_points,
    )

    fig, axis = plt.subplots(figsize=(8.5, 6.5))
    fig.subplots_adjust(left=0.11, right=0.96, top=0.90, bottom=0.26)

    (curve_line,) = axis.plot(a_l, b_l, color="#1f77b4", linewidth=2.2)
    (start_marker,) = axis.plot([a_l[0]], [b_l[0]], "ko", markersize=5)
    (end_marker,) = axis.plot([a_l[-1]], [b_l[-1]], "o", color="#d62728", markersize=7)
    info_text = axis.text(
        0.02,
        0.98,
        interactive_curve_summary(theta0_values, initial_phi_deg, float(initial_k_value)),
        transform=axis.transAxes,
        va="top",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.9, edgecolor="#cccccc"),
    )

    axis.set_title("Section 2 Interactive Atlas Curve")
    axis.set_xlabel("a / L")
    axis.set_ylabel("b / L")
    axis.set_xlim(-0.55, 1.05)
    axis.set_ylim(0.0, 1.05)
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.25)

    phi_slider_axis = fig.add_axes([0.15, 0.14, 0.72, 0.04])
    k_slider_axis = fig.add_axes([0.15, 0.08, 0.72, 0.04])

    phi_slider = Slider(
        phi_slider_axis,
        "phi (deg)",
        interactive_phi_min_deg,
        interactive_phi_max_deg,
        valinit=initial_phi_deg,
        valstep=interactive_phi_step_deg,
    )
    k_slider = Slider(
        k_slider_axis,
        "kappa",
        interactive_k_min,
        interactive_k_max,
        valinit=initial_k_value,
        valstep=interactive_k_step,
    )

    def update_curve(_: float) -> None:
        phi_deg_value = float(phi_slider.val)
        k_value = float(k_slider.val)
        theta_values_local, a_l_local, b_l_local = generate_locus_for_case(
            np.deg2rad(phi_deg_value),
            k_value,
            interactive_num_points,
        )
        curve_line.set_data(a_l_local, b_l_local)
        start_marker.set_data([a_l_local[0]], [b_l_local[0]])
        end_marker.set_data([a_l_local[-1]], [b_l_local[-1]])
        info_text.set_text(interactive_curve_summary(theta_values_local, phi_deg_value, k_value))
        axis.set_title(
            "Section 2 Interactive Atlas Curve "
            f"(phi = {phi_deg_value:.1f} deg, kappa = {k_value:.2f})"
        )
        fig.canvas.draw_idle()

    phi_slider.on_changed(update_curve)
    k_slider.on_changed(update_curve)
    plt.show()


if __name__ == "__main__":
    if PLOT_STYLE == "report_grid":
        plot_report_atlas()
    elif PLOT_STYLE == "interactive":
        plot_interactive_atlas_curve(
            initial_phi_deg=interactive_default_phi_deg,
            initial_k_value=interactive_default_k,
        )
    else:
        raise ValueError("PLOT_STYLE must be 'report_grid' or 'interactive'.")
