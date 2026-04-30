from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, Slider

import Section200_GeometricAtlas_LoadQuery as section2
import Section220_Th0_max_combined as section22


# =========================
# User input
# =========================
# Beam/material properties
beam_length = 0.100
beam_width = 0.020
thickness = 0.001
youngs_modulus = 69.0e9
sigma_max = 276.0e6

# Load-family definition
phi_deg = 90.0
kappa_value = 0.0
show_plot = True

# Plot mode:
#   "summary" -> static atlas plot plus limits table
#   "interactive" -> slider along the usable atlas branch
plot_mode = "interactive"

# Interactive-mode defaults.
initial_theta0_fraction = 1.0

# Keep widget objects alive for the lifetime of the GUI window.
_GUI_REFS: dict[str, object] = {}


def stress_limited_theta0_max(length: float, thickness_value: float, sigma_limit: float, e_modulus: float) -> float:
    l_over_t = float(length / thickness_value)
    sigma_over_e = float(sigma_limit / e_modulus)
    return section22.stress_limited_theta_max_from_section22(l_over_t, sigma_over_e)


def geometric_theta0_max(phi_deg_value: float, kappa: float) -> float:
    if math.isinf(kappa):
        return float("inf")
    return float(section2.theta0_max_for_case(math.radians(phi_deg_value), kappa))


def effective_theta0_limit(theta_stress_max: float, theta_geometric_max: float) -> tuple[float, str]:
    if math.isinf(theta_geometric_max):
        return float(theta_stress_max), "stress"
    if theta_stress_max <= theta_geometric_max:
        return float(theta_stress_max), "stress"
    return float(theta_geometric_max), "geometric"


def load_limits_for_kappa(
    theta0_limit: float,
    phi_deg_value: float,
    kappa: float,
    length: float,
    e_modulus: float,
    inertia: float,
) -> dict[str, float]:
    if theta0_limit < 0.0:
        raise ValueError("theta0_limit must be nonnegative.")

    if math.isinf(kappa):
        alpha_max = 0.0
        beta_max = float(theta0_limit)
    else:
        alpha_max, _, _ = section2.compute_state_with_alpha(
            float(theta0_limit),
            math.radians(phi_deg_value),
            float(kappa),
        )
        beta_max = 0.0 if kappa == 0.0 else 2.0 * math.sqrt(float(kappa) * float(alpha_max))

    force_max = 2.0 * e_modulus * inertia * float(alpha_max) / (length * length)
    moment_max = e_modulus * inertia * float(beta_max) / length

    return {
        "alpha_max": float(alpha_max),
        "beta_max": float(beta_max),
        "force_max": float(force_max),
        "moment_max": float(moment_max),
    }


def describe_load_path(kappa: float, length: float, e_modulus: float, inertia: float) -> str:
    if math.isinf(kappa):
        return "Pure-moment branch: F = 0 and M ranges from 0 to M_max."

    alpha_scale = 2.0 * e_modulus * inertia / (length * length)
    beta_scale = e_modulus * inertia / length

    if kappa == 0.0:
        return "Pure-force branch: M = 0 and F ranges from 0 to F_max."

    return (
        "Coupled branch: F = alpha * "
        f"{alpha_scale:.6g} and M = beta * {beta_scale:.6g}, "
        f"with beta = 2*sqrt({kappa:.6g}*alpha)."
    )


def system_parameters(
    length: float,
    width: float,
    thickness_value: float,
    e_modulus: float,
    sigma_limit: float,
    phi_deg_value: float,
    kappa: float,
) -> dict[str, float]:
    if length <= 0.0 or width <= 0.0 or thickness_value <= 0.0:
        raise ValueError("beam_length, beam_width, and thickness must be positive.")
    if e_modulus <= 0.0 or sigma_limit <= 0.0:
        raise ValueError("youngs_modulus and sigma_max must be positive.")
    if kappa < 0.0:
        raise ValueError("kappa_value must be nonnegative, or set it to float('inf') for pure moment.")

    inertia = section22.rectangular_second_moment(width, thickness_value)
    l_over_t = length / thickness_value
    sigma_over_e = sigma_limit / e_modulus
    theta0_stress_max = stress_limited_theta0_max(length, thickness_value, sigma_limit, e_modulus)
    theta0_geometric_max = geometric_theta0_max(phi_deg_value, kappa)
    theta0_limit, governing_limit = effective_theta0_limit(theta0_stress_max, theta0_geometric_max)
    limits = load_limits_for_kappa(theta0_limit, phi_deg_value, kappa, length, e_modulus, inertia)

    return {
        "inertia": float(inertia),
        "l_over_t": float(l_over_t),
        "sigma_over_e": float(sigma_over_e),
        "theta0_stress_max": float(theta0_stress_max),
        "theta0_geometric_max": float(theta0_geometric_max),
        "theta0_limit": float(theta0_limit),
        "governing_limit": governing_limit,
        "alpha_max": float(limits["alpha_max"]),
        "beta_max": float(limits["beta_max"]),
        "force_max": float(limits["force_max"]),
        "moment_max": float(limits["moment_max"]),
    }


def endpoint_response(theta0_limit: float, phi_deg_value: float, kappa: float) -> dict[str, float]:
    if math.isinf(kappa):
        a_l, b_l, _ = section22.pure_moment_response(theta0_limit)
        return {
            "theta0_rad": float(theta0_limit),
            "theta0_deg": float(math.degrees(theta0_limit)),
            "a_over_l": float(a_l),
            "b_over_l": float(b_l),
            "alpha": 0.0,
            "beta": float(theta0_limit),
        }

    alpha_value, a_l, b_l = section2.compute_state_with_alpha(
        float(theta0_limit),
        math.radians(phi_deg_value),
        float(kappa),
    )
    beta_value = 0.0 if kappa == 0.0 else 2.0 * math.sqrt(float(kappa) * float(alpha_value))
    return {
        "theta0_rad": float(theta0_limit),
        "theta0_deg": float(math.degrees(theta0_limit)),
        "a_over_l": float(a_l),
        "b_over_l": float(b_l),
        "alpha": float(alpha_value),
        "beta": float(beta_value),
    }


def sampled_trajectory(theta_values: np.ndarray, phi_deg_value: float, kappa: float) -> tuple[np.ndarray, np.ndarray]:
    a_values = np.zeros_like(theta_values, dtype=float)
    b_values = np.zeros_like(theta_values, dtype=float)

    if math.isinf(kappa):
        for idx, theta0 in enumerate(theta_values):
            a_l, b_l, _ = section22.pure_moment_response(float(theta0))
            a_values[idx] = float(a_l)
            b_values[idx] = float(b_l)
        return a_values, b_values

    phi_rad = math.radians(phi_deg_value)
    for idx, theta0 in enumerate(theta_values):
        _, a_l, b_l = section2.compute_state_with_alpha(float(theta0), phi_rad, float(kappa))
        a_values[idx] = float(a_l)
        b_values[idx] = float(b_l)
    return a_values, b_values


def build_plot_data(theta0_limit: float, theta0_geometric_max: float, phi_deg_value: float, kappa: float) -> dict[str, np.ndarray]:
    usable_theta = np.linspace(0.0, float(theta0_limit), 220)
    usable_a, usable_b = sampled_trajectory(usable_theta, phi_deg_value, kappa)

    if math.isinf(kappa):
        return {
            "full_theta": usable_theta,
            "full_a": usable_a,
            "full_b": usable_b,
            "usable_theta": usable_theta,
            "usable_a": usable_a,
            "usable_b": usable_b,
        }

    full_theta, full_a, full_b = section2.generate_locus_for_case(
        math.radians(phi_deg_value),
        float(kappa),
        num_points_local=260,
    )
    return {
        "full_theta": np.asarray(full_theta, dtype=float),
        "full_a": np.asarray(full_a, dtype=float),
        "full_b": np.asarray(full_b, dtype=float),
        "usable_theta": usable_theta,
        "usable_a": usable_a,
        "usable_b": usable_b,
    }


def selected_state(
    theta0_rad: float,
    phi_deg_value: float,
    kappa: float,
    length: float,
    e_modulus: float,
    inertia: float,
) -> dict[str, float]:
    theta0_rad = float(max(0.0, theta0_rad))

    if math.isinf(kappa):
        a_l, b_l, _ = section22.pure_moment_response(theta0_rad)
        alpha_value = 0.0
        beta_value = float(theta0_rad)
    else:
        alpha_value, a_l, b_l = section2.compute_state_with_alpha(
            theta0_rad,
            math.radians(phi_deg_value),
            float(kappa),
        )
        beta_value = 0.0 if kappa == 0.0 else 2.0 * math.sqrt(float(kappa) * float(alpha_value))

    force_value = 2.0 * e_modulus * inertia * float(alpha_value) / (length * length)
    moment_value = e_modulus * inertia * float(beta_value) / length
    force_x = force_value * math.cos(math.radians(phi_deg_value))
    force_y = force_value * math.sin(math.radians(phi_deg_value))

    return {
        "theta0_rad": float(theta0_rad),
        "theta0_deg": float(math.degrees(theta0_rad)),
        "a_over_l": float(a_l),
        "b_over_l": float(b_l),
        "alpha": float(alpha_value),
        "beta": float(beta_value),
        "force": float(force_value),
        "moment": float(moment_value),
        "force_x": float(force_x),
        "force_y": float(force_y),
    }


def interactive_table_rows(
    system: dict[str, float],
    state: dict[str, float],
    phi_deg_value: float,
    kappa: float,
) -> list[tuple[str, str]]:
    return [
        ("phi [deg]", f"{phi_deg_value:.4f}"),
        ("kappa [-]", "inf" if math.isinf(kappa) else f"{kappa:.6g}"),
        ("theta0 [rad]", f"{state['theta0_rad']:.6f}"),
        ("theta0 [deg]", f"{state['theta0_deg']:.4f}"),
        ("theta0 max [deg]", f"{math.degrees(system['theta0_limit']):.4f}"),
        ("governing limit", str(system["governing_limit"])),
        ("a/L [-]", f"{state['a_over_l']:.6f}"),
        ("b/L [-]", f"{state['b_over_l']:.6f}"),
        ("alpha [-]", f"{state['alpha']:.6f}"),
        ("beta [-]", f"{state['beta']:.6f}"),
        ("Force [N]", f"{state['force']:.6f}"),
        ("Moment [N*m]", f"{state['moment']:.6f}"),
        ("Fx [N]", f"{state['force_x']:.6f}"),
        ("Fy [N]", f"{state['force_y']:.6f}"),
    ]


def plot_limits_summary(
    phi_deg_value: float,
    kappa: float,
    governing_limit: str,
    theta0_stress_max: float,
    theta0_geometric_max: float,
    theta0_limit: float,
    endpoint: dict[str, float],
    limits: dict[str, float],
    path_description: str,
) -> None:
    plot_data = build_plot_data(theta0_limit, theta0_geometric_max, phi_deg_value, kappa)

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13.5, 5.8),
        gridspec_kw={"width_ratios": [1.35, 1.0]},
        constrained_layout=True,
    )

    atlas_axis = axes[0]
    table_axis = axes[1]

    atlas_axis.plot(
        plot_data["full_a"],
        plot_data["full_b"],
        color="#b0b0b0",
        linewidth=2.0,
        linestyle="--",
        label="Full geometric branch",
    )
    atlas_axis.plot(
        plot_data["usable_a"],
        plot_data["usable_b"],
        color="#1f77b4",
        linewidth=2.4,
        label="Usable branch",
    )
    atlas_axis.scatter(
        [endpoint["a_over_l"]],
        [endpoint["b_over_l"]],
        color="#d62728",
        s=55,
        zorder=5,
        label="Governing endpoint",
    )
    atlas_axis.scatter([1.0], [0.0], color="black", s=22, zorder=5)
    atlas_axis.annotate(
        rf"$\theta_0 = {endpoint['theta0_deg']:.2f}^\circ$",
        xy=(endpoint["a_over_l"], endpoint["b_over_l"]),
        xytext=(12, 10),
        textcoords="offset points",
        fontsize=10,
        color="#333333",
    )
    atlas_axis.set_title(
        "Section 2 Load Family"
        + "\n"
        + rf"$\phi = {phi_deg_value:g}^\circ$, "
        + (rf"$\kappa = {kappa:g}$" if not math.isinf(kappa) else r"$\kappa = \infty$")
    )
    atlas_axis.set_xlabel("a / L")
    atlas_axis.set_ylabel("b / L")
    atlas_axis.set_xlim(min(-0.1, float(np.min(plot_data["full_a"])) - 0.05), 1.05)
    atlas_axis.set_ylim(min(-0.02, float(np.min(plot_data["full_b"])) - 0.02), max(1.05, float(np.max(plot_data["full_b"])) + 0.05))
    atlas_axis.grid(True, alpha=0.25)
    atlas_axis.set_aspect("equal", adjustable="box")
    atlas_axis.legend(loc="best")

    table_axis.axis("off")
    rows = [
        ("phi [deg]", f"{phi_deg_value:.4f}"),
        ("kappa [-]", "inf" if math.isinf(kappa) else f"{kappa:.6g}"),
        ("governing limit", governing_limit),
        ("theta0 stress [rad]", f"{theta0_stress_max:.6f}"),
        ("theta0 stress [deg]", f"{math.degrees(theta0_stress_max):.4f}"),
        ("theta0 geometric [rad]", "inf" if math.isinf(theta0_geometric_max) else f"{theta0_geometric_max:.6f}"),
        ("theta0 limit [rad]", f"{theta0_limit:.6f}"),
        ("theta0 limit [deg]", f"{math.degrees(theta0_limit):.4f}"),
        ("alpha endpoint [-]", f"{endpoint['alpha']:.6f}"),
        ("beta endpoint [-]", f"{endpoint['beta']:.6f}"),
        ("force endpoint [N]", f"{limits['force_max']:.6f}"),
        ("moment endpoint [N*m]", f"{limits['moment_max']:.6f}"),
        ("a/L endpoint [-]", f"{endpoint['a_over_l']:.6f}"),
        ("b/L endpoint [-]", f"{endpoint['b_over_l']:.6f}"),
    ]
    table = table_axis.table(
        cellText=[[label, value] for label, value in rows],
        colLabels=["Quantity", "Value"],
        cellLoc="left",
        colLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.05, 1.3)
    table_axis.set_title("Derived Limits", pad=8)
    table_axis.text(
        0.0,
        0.02,
        path_description,
        transform=table_axis.transAxes,
        fontsize=9.5,
        va="bottom",
        ha="left",
        wrap=True,
    )

    plt.show()


def build_interactive_figure(
    system: dict[str, float],
    phi_deg_value: float,
    kappa: float,
    length: float,
    e_modulus: float,
) -> tuple[plt.Figure, dict[str, object]]:
    theta0_limit = float(system["theta0_limit"])
    theta0_geometric_max = float(system["theta0_geometric_max"])
    inertia = float(system["inertia"])
    plot_data = build_plot_data(theta0_limit, theta0_geometric_max, phi_deg_value, kappa)

    initial_theta0 = float(np.clip(initial_theta0_fraction, 0.0, 1.0)) * theta0_limit
    current_state = selected_state(
        initial_theta0,
        phi_deg_value,
        kappa,
        length,
        e_modulus,
        inertia,
    )

    fig = plt.figure(figsize=(14.2, 7.2), constrained_layout=False)
    grid = fig.add_gridspec(
        2,
        2,
        height_ratios=[18, 2],
        width_ratios=[1.35, 1.0],
        left=0.06,
        right=0.98,
        bottom=0.14,
        top=0.92,
        wspace=0.18,
        hspace=0.20,
    )

    atlas_axis = fig.add_subplot(grid[0, 0])
    table_axis = fig.add_subplot(grid[0, 1])
    slider_axis = fig.add_subplot(grid[1, 0])
    button_axis = fig.add_subplot(grid[1, 1])

    atlas_axis.plot(
        plot_data["full_a"],
        plot_data["full_b"],
        color="#b3b3b3",
        linewidth=2.0,
        linestyle="--",
        label="Full geometric branch",
    )
    atlas_axis.plot(
        plot_data["usable_a"],
        plot_data["usable_b"],
        color="#1f77b4",
        linewidth=2.5,
        label="Usable branch",
    )
    selected_path, = atlas_axis.plot(
        [plot_data["usable_a"][0], current_state["a_over_l"]],
        [plot_data["usable_b"][0], current_state["b_over_l"]],
        color="#ff7f0e",
        linewidth=3.0,
        label="Selected segment",
    )
    selected_point = atlas_axis.scatter(
        [current_state["a_over_l"]],
        [current_state["b_over_l"]],
        color="#d62728",
        s=70,
        zorder=5,
        label="Selected point",
    )
    atlas_axis.scatter([1.0], [0.0], color="black", s=22, zorder=5)
    point_label = atlas_axis.text(
        0.03,
        0.97,
        "",
        transform=atlas_axis.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#cccccc"},
    )

    atlas_axis.set_title(
        "Interactive Section 2 Load Family"
        + "\n"
        + rf"$\phi = {phi_deg_value:g}^\circ$, "
        + (rf"$\kappa = {kappa:g}$" if not math.isinf(kappa) else r"$\kappa = \infty$")
    )
    atlas_axis.set_xlabel("a / L")
    atlas_axis.set_ylabel("b / L")
    atlas_axis.set_xlim(min(-0.1, float(np.min(plot_data["full_a"])) - 0.05), 1.05)
    atlas_axis.set_ylim(
        min(-0.02, float(np.min(plot_data["full_b"])) - 0.02),
        max(1.05, float(np.max(plot_data["full_b"])) + 0.05),
    )
    atlas_axis.set_aspect("equal", adjustable="box")
    atlas_axis.grid(True, alpha=0.25)
    atlas_axis.legend(loc="best")

    table_axis.axis("off")
    table = table_axis.table(
        cellText=[
            [label, value]
            for label, value in interactive_table_rows(system, current_state, phi_deg_value, kappa)
        ],
        colLabels=["Quantity", "Value"],
        cellLoc="left",
        colLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.05, 1.34)
    table_axis.set_title("Loads for Selected Deflection", pad=8)
    description_text = table_axis.text(
        0.0,
        0.02,
        describe_load_path(kappa, length, e_modulus, inertia),
        transform=table_axis.transAxes,
        fontsize=9.5,
        va="bottom",
        ha="left",
        wrap=True,
    )

    slider = Slider(
        ax=slider_axis,
        label=r"$\theta_0$ [deg]",
        valmin=0.0,
        valmax=float(math.degrees(theta0_limit)),
        valinit=current_state["theta0_deg"],
        valstep=float(math.degrees(theta0_limit)) / 300.0 if theta0_limit > 0.0 else 1.0,
        color="#1f77b4",
    )
    slider_axis.set_title("Move along the usable atlas branch", fontsize=10, pad=8)

    reset_button = Button(button_axis, "Reset to max")
    button_axis.set_title("Slider Controls", fontsize=10, pad=8)

    def update_label(state: dict[str, float]) -> None:
        point_label.set_text(
            "\n".join(
                [
                    rf"$\theta_0 = {state['theta0_deg']:.2f}^\circ$",
                    rf"$F = {state['force']:.3f}\ \mathrm{{N}}$",
                    rf"$M = {state['moment']:.3f}\ \mathrm{{N\cdot m}}$",
                ]
            )
        )

    def update_table(state: dict[str, float]) -> None:
        for row_idx, (_, value_text) in enumerate(
            interactive_table_rows(system, state, phi_deg_value, kappa),
            start=1,
        ):
            table[(row_idx, 1)].get_text().set_text(value_text)

    def update_plot_from_theta(theta0_deg_value: float) -> None:
        theta0_rad_value = math.radians(float(theta0_deg_value))
        state = selected_state(
            theta0_rad_value,
            phi_deg_value,
            kappa,
            length,
            e_modulus,
            inertia,
        )
        usable_theta = np.asarray(plot_data["usable_theta"], dtype=float)
        end_index = int(np.searchsorted(usable_theta, theta0_rad_value, side="right"))
        end_index = max(2, min(end_index, usable_theta.size))

        selected_path.set_data(
            plot_data["usable_a"][:end_index],
            plot_data["usable_b"][:end_index],
        )
        selected_point.set_offsets([[state["a_over_l"], state["b_over_l"]]])
        update_label(state)
        update_table(state)
        fig.canvas.draw_idle()

    update_label(current_state)

    def on_slider_change(theta0_deg_value: float) -> None:
        update_plot_from_theta(theta0_deg_value)

    def on_reset(_: object) -> None:
        slider.reset()

    slider.on_changed(on_slider_change)
    reset_button.on_clicked(on_reset)
    description_text.set_wrap(True)

    return fig, {
        "slider": slider,
        "reset_button": reset_button,
        "selected_point": selected_point,
        "selected_path": selected_path,
        "table": table,
        "point_label": point_label,
    }


def main() -> None:
    system = system_parameters(
        beam_length,
        beam_width,
        thickness,
        youngs_modulus,
        sigma_max,
        phi_deg,
        kappa_value,
    )
    endpoint = endpoint_response(system["theta0_limit"], phi_deg, kappa_value)
    path_description = describe_load_path(
        kappa_value,
        beam_length,
        youngs_modulus,
        system["inertia"],
    )

    print("Section 2 load-family limits and atlas slider")
    print(f"phi = {phi_deg:.6f} deg")
    print(f"kappa = {'inf' if math.isinf(kappa_value) else f'{kappa_value:.12g}'} [-]")
    print(f"L = {beam_length:.12g} m")
    print(f"b = {beam_width:.12g} m")
    print(f"t = {thickness:.12g} m")
    print(f"E = {youngs_modulus:.12g} Pa")
    print(f"sigma_max = {sigma_max:.12g} Pa")
    print(f"I = {system['inertia']:.12g} m^4")
    print(f"L/t = {system['l_over_t']:.12g} [-]")
    print(f"sigma/E = {system['sigma_over_e']:.12g} [-]")
    print(f"theta0_max_stress = {system['theta0_stress_max']:.12g} rad")
    print(f"theta0_max_stress = {math.degrees(system['theta0_stress_max']):.12g} deg")
    if math.isinf(system["theta0_geometric_max"]):
        print("theta0_max_geometric = inf rad")
    else:
        print(f"theta0_max_geometric = {system['theta0_geometric_max']:.12g} rad")
        print(f"theta0_max_geometric = {math.degrees(system['theta0_geometric_max']):.12g} deg")
    print(f"governing_limit = {system['governing_limit']}")
    print(f"theta0_limit = {system['theta0_limit']:.12g} rad")
    print(f"theta0_limit = {math.degrees(system['theta0_limit']):.12g} deg")
    print(f"alpha_range = [0, {system['alpha_max']:.12g}] [-]")
    print(f"beta_range = [0, {system['beta_max']:.12g}] [-]")
    print(f"force_range = [0, {system['force_max']:.12g}] N")
    print(f"moment_range = [0, {system['moment_max']:.12g}] N*m")
    print(f"a/L endpoint = {endpoint['a_over_l']:.12g} [-]")
    print(f"b/L endpoint = {endpoint['b_over_l']:.12g} [-]")
    print(path_description)

    if show_plot:
        if plot_mode == "summary":
            plot_limits_summary(
                phi_deg,
                kappa_value,
                str(system["governing_limit"]),
                float(system["theta0_stress_max"]),
                float(system["theta0_geometric_max"]),
                float(system["theta0_limit"]),
                endpoint,
                {
                    "alpha_max": float(system["alpha_max"]),
                    "beta_max": float(system["beta_max"]),
                    "force_max": float(system["force_max"]),
                    "moment_max": float(system["moment_max"]),
                },
                path_description,
            )
        elif plot_mode == "interactive":
            _, widget_refs = build_interactive_figure(
                system,
                phi_deg,
                kappa_value,
                beam_length,
                youngs_modulus,
            )
            _GUI_REFS.clear()
            _GUI_REFS.update(widget_refs)
            plt.show()
        else:
            raise ValueError("plot_mode must be 'summary' or 'interactive'.")


if __name__ == "__main__":
    main()
