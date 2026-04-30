from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, Slider
from scipy.optimize import least_squares

import Section400_PRB3R_ReportProcedure as section4
import Section510_OptimalPRBComparison as section510


# =========================
# User input
# =========================
crank_angle_start_deg = 0.0
crank_angle_end_deg = 360.0
num_crank_samples = 361
initial_crank_angle_deg = 0.0
show_plot = True

# Section 5.2 mechanism geometry from the paper.
Au = -1.0 / math.sqrt(2.0)
Av = 1.0 / math.sqrt(2.0)
r = 1.0 - math.sqrt(2.0) / 2.0
B = np.array([0.0, 1.0 / math.sqrt(2.0)], dtype=float)

# Keep widget objects alive for the lifetime of the GUI window.
_GUI_REFS: dict[str, object] = {}


def get_section52_parameters() -> tuple[np.ndarray, np.ndarray, str]:
    gammas = section510.get_optimal_gammas()
    kbar, _, stiffness_label = section510.select_section51_stiffness(gammas)
    return gammas, kbar, stiffness_label


def rotation_matrix(angle: float) -> np.ndarray:
    cval = math.cos(angle)
    sval = math.sin(angle)
    return np.array([[cval, -sval], [sval, cval]], dtype=float)


def prb_joint_positions(theta: np.ndarray, gammas: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    theta1, theta2, theta3 = theta
    theta12 = theta1 + theta2
    theta123 = theta12 + theta3

    origin = np.array([0.0, 0.0], dtype=float)
    p1 = np.array([gammas[0], 0.0], dtype=float)
    p2 = p1 + gammas[1] * np.array([math.cos(theta1), math.sin(theta1)], dtype=float)
    p3 = p2 + gammas[2] * np.array([math.cos(theta12), math.sin(theta12)], dtype=float)
    q = p3 + gammas[3] * np.array([math.cos(theta123), math.sin(theta123)], dtype=float)

    chain = np.vstack([origin, p1, p2, p3, q])
    return chain, q


def point_a_from_tip(q: np.ndarray, phi: float) -> np.ndarray:
    return q + rotation_matrix(phi) @ np.array([Au, Av], dtype=float)


def crank_endpoint(crank_angle_rad: float) -> np.ndarray:
    return B + r * np.array([math.cos(crank_angle_rad), math.sin(crank_angle_rad)], dtype=float)


def solve_tip_load(theta: np.ndarray, gammas: np.ndarray, kbar: np.ndarray) -> np.ndarray:
    tau = kbar * theta
    jacobian_t = section4.prb3r_jacobian(theta, gammas).T
    # The undeformed configuration is singular, so use a least-squares load recovery
    # instead of a strict inverse to keep the continuation solve well-behaved near zero crank angle.
    load_vector, *_ = np.linalg.lstsq(jacobian_t, tau, rcond=None)
    return load_vector


def compliant_four_bar_residual(
    theta: np.ndarray,
    crank_angle_rad: float,
    gammas: np.ndarray,
    kbar: np.ndarray,
) -> np.ndarray:
    _, q = prb_joint_positions(theta, gammas)
    phi = float(np.sum(theta))
    a_point = point_a_from_tip(q, phi)
    aq = q - a_point
    load_vector = solve_tip_load(theta, gammas, kbar)
    crank_tip = crank_endpoint(crank_angle_rad)

    return np.array(
        [
            a_point[0] - crank_tip[0],
            a_point[1] - crank_tip[1],
            aq[0] * load_vector[1] - aq[1] * load_vector[0] + load_vector[2],
        ],
        dtype=float,
    )


def initial_guess_for_crank_angle(crank_angle_rad: float) -> np.ndarray:
    return crank_angle_rad * np.array([0.35, 0.40, 0.25], dtype=float)


def solve_configuration(
    crank_angle_rad: float,
    gammas: np.ndarray,
    kbar: np.ndarray,
    previous_theta: np.ndarray | None,
) -> np.ndarray:
    guess_pool: list[np.ndarray] = []
    for guess in (
        previous_theta,
        initial_guess_for_crank_angle(crank_angle_rad),
        np.zeros(3, dtype=float),
    ):
        if guess is None:
            continue
        guess_array = np.array(guess, dtype=float)
        if not any(np.allclose(guess_array, existing) for existing in guess_pool):
            guess_pool.append(guess_array)

    best_result = None
    best_norm = math.inf

    for guess in guess_pool:
        result = least_squares(
            compliant_four_bar_residual,
            guess,
            args=(crank_angle_rad, gammas, kbar),
            xtol=1.0e-12,
            ftol=1.0e-12,
            gtol=1.0e-12,
            max_nfev=500,
        )
        residual_norm = float(np.linalg.norm(result.fun, ord=2))
        if residual_norm < best_norm:
            best_result = result
            best_norm = residual_norm
        if result.success and residual_norm < 1.0e-9:
            return np.array(result.x, dtype=float)

    if best_result is None:
        raise RuntimeError("The compliant four-bar solver did not return any candidate solution.")

    if best_norm > 1.0e-7:
        raise RuntimeError(
            f"Could not solve the compliant four-bar configuration at crank angle = {math.degrees(crank_angle_rad):.3f} deg."
        )

    return np.array(best_result.x, dtype=float)


def crank_angle_grid(start_deg: float, end_deg: float, sample_count: int) -> np.ndarray:
    if sample_count < 2:
        raise ValueError("num_crank_samples must be at least 2.")
    crank_angle_values = np.linspace(math.radians(start_deg), math.radians(end_deg), sample_count)
    if abs(crank_angle_values[0]) < 1.0e-14:
        crank_angle_values[0] = 0.0
    return crank_angle_values


def solve_motion(
    crank_angle_values: np.ndarray,
    gammas: np.ndarray,
    kbar: np.ndarray,
) -> dict[str, np.ndarray]:
    theta_rows: list[np.ndarray] = []
    chain_rows: list[np.ndarray] = []
    q_rows: list[np.ndarray] = []
    a_rows: list[np.ndarray] = []
    crank_rows: list[np.ndarray] = []
    load_rows: list[np.ndarray] = []
    residual_norms: list[float] = []

    previous_theta = np.zeros(3, dtype=float)

    for index, crank_angle_rad in enumerate(crank_angle_values):
        if index == 0 and abs(crank_angle_rad) < 1.0e-14:
            theta = np.zeros(3, dtype=float)
        else:
            theta = solve_configuration(crank_angle_rad, gammas, kbar, previous_theta)

        chain, q = prb_joint_positions(theta, gammas)
        phi = float(np.sum(theta))
        a_point = point_a_from_tip(q, phi)
        crank_tip = crank_endpoint(crank_angle_rad)
        load_vector = solve_tip_load(theta, gammas, kbar)
        residual = compliant_four_bar_residual(theta, crank_angle_rad, gammas, kbar)

        theta_rows.append(theta)
        chain_rows.append(chain)
        q_rows.append(q)
        a_rows.append(a_point)
        crank_rows.append(crank_tip)
        load_rows.append(load_vector)
        residual_norms.append(float(np.linalg.norm(residual, ord=2)))
        previous_theta = theta

    return {
        "crank_angle_rad": np.asarray(crank_angle_values, dtype=float),
        "theta": np.vstack(theta_rows),
        "chain": np.stack(chain_rows, axis=0),
        "Q": np.vstack(q_rows),
        "A": np.vstack(a_rows),
        "crank_tip": np.vstack(crank_rows),
        "load": np.vstack(load_rows),
        "residual_norm": np.asarray(residual_norms, dtype=float),
    }


def state_rows(
    angle_deg: float,
    theta: np.ndarray,
    q_point: np.ndarray,
    a_point: np.ndarray,
    load_vector: np.ndarray,
    residual_norm: float,
) -> list[tuple[str, str]]:
    return [
        ("BA angle [deg]", f"{angle_deg:.2f}"),
        ("theta1 [deg]", f"{math.degrees(float(theta[0])):.2f}"),
        ("theta2 [deg]", f"{math.degrees(float(theta[1])):.2f}"),
        ("theta3 [deg]", f"{math.degrees(float(theta[2])):.2f}"),
        ("tip slope [deg]", f"{math.degrees(float(np.sum(theta))):.2f}"),
        ("Qx [-]", f"{float(q_point[0]):.6f}"),
        ("Qy [-]", f"{float(q_point[1]):.6f}"),
        ("Ax [-]", f"{float(a_point[0]):.6f}"),
        ("Ay [-]", f"{float(a_point[1]):.6f}"),
        ("Fx l / EI [-]", f"{float(load_vector[0]):.6f}"),
        ("Fy l / EI [-]", f"{float(load_vector[1]):.6f}"),
        ("M / EI [-]", f"{float(load_vector[2]):.6f}"),
        ("residual norm [-]", f"{float(residual_norm):.3e}"),
    ]


def build_interactive_figure(
    motion: dict[str, np.ndarray],
    gammas: np.ndarray,
) -> tuple[plt.Figure, dict[str, object]]:
    crank_angle_values = np.asarray(motion["crank_angle_rad"], dtype=float)
    theta_rows = np.asarray(motion["theta"], dtype=float)
    chain_rows = np.asarray(motion["chain"], dtype=float)
    q_rows = np.asarray(motion["Q"], dtype=float)
    a_rows = np.asarray(motion["A"], dtype=float)
    crank_rows = np.asarray(motion["crank_tip"], dtype=float)
    load_rows = np.asarray(motion["load"], dtype=float)
    residual_rows = np.asarray(motion["residual_norm"], dtype=float)

    initial_angle_deg = float(np.clip(initial_crank_angle_deg, np.degrees(crank_angle_values[0]), np.degrees(crank_angle_values[-1])))
    initial_index = int(np.argmin(np.abs(np.degrees(crank_angle_values) - initial_angle_deg)))

    fig = plt.figure(figsize=(14.6, 7.6), constrained_layout=False)
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

    mechanism_axis = fig.add_subplot(grid[0, 0])
    table_axis = fig.add_subplot(grid[0, 1])
    slider_axis = fig.add_subplot(grid[1, 0])
    button_axis = fig.add_subplot(grid[1, 1])

    mechanism_axis.plot(q_rows[:, 0], q_rows[:, 1], color="#1f77b4", linewidth=2.0, alpha=0.75, label="Q path")
    mechanism_axis.plot(a_rows[:, 0], a_rows[:, 1], color="#ff7f0e", linewidth=2.0, alpha=0.75, label="A path")
    mechanism_axis.plot(crank_rows[:, 0], crank_rows[:, 1], color="#9467bd", linewidth=1.8, alpha=0.65, linestyle="--", label="A crank path")
    mechanism_axis.scatter([0.0, B[0]], [0.0, B[1]], color="black", s=32, zorder=6)

    current_chain = chain_rows[initial_index]
    current_q = q_rows[initial_index]
    current_a = a_rows[initial_index]
    current_crank = crank_rows[initial_index]

    prb_line, = mechanism_axis.plot(
        current_chain[:, 0],
        current_chain[:, 1],
        color="#2ca02c",
        linewidth=2.0,
        label="PRB beam",
    )
    joint_points = mechanism_axis.scatter(
        current_chain[:, 0],
        current_chain[:, 1],
        color="#2ca02c",
        s=18,
        zorder=6,
    )
    crank_line, = mechanism_axis.plot(
        [B[0], current_crank[0]],
        [B[1], current_crank[1]],
        color="#d62728",
        linewidth=2.0,
        label="BA crank",
    )
    coupler_line, = mechanism_axis.plot(
        [current_a[0], current_q[0]],
        [current_a[1], current_q[1]],
        color="#8c564b",
        linewidth=2.0,
        label="AQ link",
    )
    current_point = mechanism_axis.scatter(
        [current_q[0], current_a[0], current_crank[0]],
        [current_q[1], current_a[1], current_crank[1]],
        color=["#1f77b4", "#ff7f0e", "#d62728"],
        s=34,
        zorder=7,
    )
    mechanism_text = mechanism_axis.text(
        0.03,
        0.97,
        "",
        transform=mechanism_axis.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#cccccc"},
    )

    all_x = np.concatenate([chain_rows[:, :, 0].ravel(), a_rows[:, 0], q_rows[:, 0], crank_rows[:, 0], np.array([0.0, B[0]])])
    all_y = np.concatenate([chain_rows[:, :, 1].ravel(), a_rows[:, 1], q_rows[:, 1], crank_rows[:, 1], np.array([0.0, B[1]])])
    mechanism_axis.set_xlim(float(np.min(all_x)) - 0.10, float(np.max(all_x)) + 0.10)
    mechanism_axis.set_ylim(float(np.min(all_y)) - 0.10, float(np.max(all_y)) + 0.10)
    mechanism_axis.set_aspect("equal", adjustable="box")
    mechanism_axis.set_title("Interactive Section 5.2 Compliant Four-Bar")
    mechanism_axis.set_xlabel("x / l")
    mechanism_axis.set_ylabel("y / l")
    mechanism_axis.grid(True, alpha=0.25)
    mechanism_axis.legend(loc="best")

    angle_deg_values = np.degrees(crank_angle_values)
    path_axis = table_axis
    path_axis.plot(angle_deg_values, q_rows[:, 0], color="#1f77b4", linewidth=2.0, label=r"$Q_x$")
    path_axis.plot(angle_deg_values, q_rows[:, 1], color="#d62728", linewidth=2.0, label=r"$Q_y$")
    path_axis.plot(angle_deg_values, a_rows[:, 0], color="#ff7f0e", linewidth=1.8, alpha=0.85, label=r"$A_x$")
    path_axis.plot(angle_deg_values, a_rows[:, 1], color="#9467bd", linewidth=1.8, alpha=0.85, label=r"$A_y$")
    angle_marker = path_axis.axvline(angle_deg_values[initial_index], color="#111111", linewidth=1.8, linestyle="--")
    path_axis.set_title("Mechanism Response vs. BA Angle")
    path_axis.set_xlabel("BA angle (deg)")
    path_axis.set_ylabel("Normalized coordinate")
    path_axis.grid(True, alpha=0.25)
    path_axis.legend(loc="best")

    info_axis = path_axis.inset_axes([0.54, 0.06, 0.42, 0.42])
    info_axis.axis("off")
    current_rows = state_rows(
        angle_deg_values[initial_index],
        theta_rows[initial_index],
        current_q,
        current_a,
        load_rows[initial_index],
        residual_rows[initial_index],
    )
    info_table = info_axis.table(
        cellText=[[label, value] for label, value in current_rows],
        colLabels=["Quantity", "Value"],
        cellLoc="left",
        colLoc="left",
        loc="center",
    )
    info_table.auto_set_font_size(False)
    info_table.set_fontsize(8.4)
    info_table.scale(1.0, 1.15)

    slider = Slider(
        ax=slider_axis,
        label="BA angle [deg]",
        valmin=float(angle_deg_values[0]),
        valmax=float(angle_deg_values[-1]),
        valinit=float(angle_deg_values[initial_index]),
        valstep=float(angle_deg_values[1] - angle_deg_values[0]) if len(angle_deg_values) > 1 else 1.0,
        color="#1f77b4",
    )
    slider_axis.set_title("Rotate BA through the full motion range", fontsize=10, pad=8)

    reset_button = Button(button_axis, "Reset angle")
    button_axis.set_title("Slider Controls", fontsize=10, pad=8)

    def update_mechanism_label(index: int) -> None:
        mechanism_text.set_text(
            "\n".join(
                [
                    f"BA = {angle_deg_values[index]:.1f} deg",
                    f"Q = ({q_rows[index, 0]:.3f}, {q_rows[index, 1]:.3f})",
                    f"A = ({a_rows[index, 0]:.3f}, {a_rows[index, 1]:.3f})",
                ]
            )
        )

    def update_table(index: int) -> None:
        rows = state_rows(
            angle_deg_values[index],
            theta_rows[index],
            q_rows[index],
            a_rows[index],
            load_rows[index],
            residual_rows[index],
        )
        for row_idx, (_, value_text) in enumerate(rows, start=1):
            info_table[(row_idx, 1)].get_text().set_text(value_text)

    def update_from_angle(angle_deg: float) -> None:
        index = int(np.argmin(np.abs(angle_deg_values - float(angle_deg))))
        chain = chain_rows[index]
        q_point = q_rows[index]
        a_point = a_rows[index]
        crank_point = crank_rows[index]

        prb_line.set_data(chain[:, 0], chain[:, 1])
        joint_points.set_offsets(chain)
        crank_line.set_data([B[0], crank_point[0]], [B[1], crank_point[1]])
        coupler_line.set_data([a_point[0], q_point[0]], [a_point[1], q_point[1]])
        current_point.set_offsets(
            np.array(
                [
                    [q_point[0], q_point[1]],
                    [a_point[0], a_point[1]],
                    [crank_point[0], crank_point[1]],
                ],
                dtype=float,
            )
        )
        angle_marker.set_xdata([angle_deg_values[index], angle_deg_values[index]])
        update_mechanism_label(index)
        update_table(index)
        fig.canvas.draw_idle()

    def on_slider_change(angle_deg: float) -> None:
        update_from_angle(angle_deg)

    def on_reset(_: object) -> None:
        slider.reset()

    slider.on_changed(on_slider_change)
    reset_button.on_clicked(on_reset)
    update_mechanism_label(initial_index)

    return fig, {
        "slider": slider,
        "reset_button": reset_button,
        "prb_line": prb_line,
        "joint_points": joint_points,
        "crank_line": crank_line,
        "coupler_line": coupler_line,
        "current_point": current_point,
        "angle_marker": angle_marker,
        "info_table": info_table,
        "mechanism_text": mechanism_text,
    }


def main() -> None:
    gammas, kbar, stiffness_label = get_section52_parameters()
    crank_angle_values = crank_angle_grid(
        crank_angle_start_deg,
        crank_angle_end_deg,
        num_crank_samples,
    )
    motion = solve_motion(crank_angle_values, gammas, kbar)

    q_rows = np.asarray(motion["Q"], dtype=float)
    max_residual = float(np.max(np.asarray(motion["residual_norm"], dtype=float)))

    print("Section 5.2 compliant four-bar")
    print("parameter path = blind Section 4.4 search + Section 5.0/5.1 computed stiffness")
    print(f"gammas = [{gammas[0]:.2f} {gammas[1]:.2f} {gammas[2]:.2f} {gammas[3]:.2f}]")
    print(f"kappa grid = {np.array2string(section510.kappa_average_values, precision=3, separator=', ')}")
    print(f"{stiffness_label} kbar = [{kbar[0]:.5f} {kbar[1]:.5f} {kbar[2]:.5f}]")
    print(
        f"BA angle range = [{crank_angle_start_deg:.1f}, {crank_angle_end_deg:.1f}] deg with {num_crank_samples} samples"
    )
    print(f"Q start = [{q_rows[0, 0]:.5f} {q_rows[0, 1]:.5f}]")
    print(f"Q end = [{q_rows[-1, 0]:.5f} {q_rows[-1, 1]:.5f}]")
    print(f"max residual norm = {max_residual:.3e}")

    if show_plot:
        _, widget_refs = build_interactive_figure(motion, gammas)
        _GUI_REFS.clear()
        _GUI_REFS.update(widget_refs)
        plt.show()


if __name__ == "__main__":
    main()
