from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, Slider

import Section520_CompliantFourBar as section520
import Section600_VerificationDataViewer as section600


PRB_SCALE = 100.0
PRB_COLORS = {
    "beam": "#111111",
    "coupler": "#111111",
    "crank": "#111111",
    "point_q": "#111111",
    "point_a": "#111111",
}
_GUI_REFS: dict[str, object] = {}


def crank_angle_deg_from_frame(frame: section600.FrameData) -> float:
    crank_nodes = frame.parts["CRANK-1"].deformed_xy
    vector = crank_nodes[-1] - crank_nodes[0]
    return float(np.degrees(np.arctan2(vector[1], vector[0])))


def wrap_angle_0_360(angle_deg: float) -> float:
    wrapped = angle_deg % 360.0
    if wrapped < 0.0:
        wrapped += 360.0
    return wrapped


def fea_points(frame: section600.FrameData) -> dict[str, np.ndarray]:
    return {
        "B": frame.parts["CRANK-1"].deformed_xy[0],
        "A": frame.parts["CRANK-1"].deformed_xy[-1],
        "Q": frame.parts["FLEX-1"].deformed_xy[-1],
    }


def compute_plot_limits(
    fea_frames: list[section600.FrameData],
    prb_motion: dict[str, np.ndarray],
) -> tuple[float, float, float, float]:
    all_points: list[np.ndarray] = []

    for frame in fea_frames:
        for part_data in frame.parts.values():
            all_points.append(part_data.base_xy)
            all_points.append(part_data.deformed_xy)

    all_points.append(PRB_SCALE * np.asarray(prb_motion["chain"], dtype=float).reshape(-1, 2))
    all_points.append(PRB_SCALE * np.asarray(prb_motion["A"], dtype=float))
    all_points.append(PRB_SCALE * np.asarray(prb_motion["Q"], dtype=float))
    all_points.append(PRB_SCALE * np.asarray(prb_motion["crank_tip"], dtype=float))

    stacked = np.vstack(all_points)
    xmin = float(np.min(stacked[:, 0]))
    xmax = float(np.max(stacked[:, 0]))
    ymin = float(np.min(stacked[:, 1]))
    ymax = float(np.max(stacked[:, 1]))
    span = max(xmax - xmin, ymax - ymin)
    padding = 0.08 * span if span > 0.0 else 1.0
    return xmin - padding, xmax + padding, ymin - padding, ymax + padding


def get_prb_motion() -> tuple[np.ndarray, np.ndarray, str, dict[str, np.ndarray]]:
    gammas, kbar, stiffness_label = section520.get_section52_parameters()
    crank_angle_values = section520.crank_angle_grid(
        section520.crank_angle_start_deg,
        section520.crank_angle_end_deg,
        section520.num_crank_samples,
    )
    motion = section520.solve_motion(crank_angle_values, gammas, kbar)
    return gammas, kbar, stiffness_label, motion


def build_overlay_viewer(
    fea_frames: list[section600.FrameData],
    gammas: np.ndarray,
    kbar: np.ndarray,
    stiffness_label: str,
    prb_motion: dict[str, np.ndarray],
) -> tuple[plt.Figure, dict[str, object]]:
    xmin, xmax, ymin, ymax = compute_plot_limits(fea_frames, prb_motion)
    prb_angles_deg = np.degrees(np.asarray(prb_motion["crank_angle_rad"], dtype=float))
    prb_chain = PRB_SCALE * np.asarray(prb_motion["chain"], dtype=float)
    prb_q = PRB_SCALE * np.asarray(prb_motion["Q"], dtype=float)
    prb_a = PRB_SCALE * np.asarray(prb_motion["A"], dtype=float)
    prb_crank = PRB_SCALE * np.asarray(prb_motion["crank_tip"], dtype=float)
    prb_load = np.asarray(prb_motion["load"], dtype=float)
    prb_theta = np.asarray(prb_motion["theta"], dtype=float)
    prb_residual = np.asarray(prb_motion["residual_norm"], dtype=float)

    figure = plt.figure(figsize=(15.0, 8.4), constrained_layout=False)
    grid = figure.add_gridspec(
        2,
        2,
        height_ratios=[18, 2],
        width_ratios=[1.45, 0.95],
        left=0.06,
        right=0.97,
        bottom=0.11,
        top=0.92,
        wspace=0.18,
        hspace=0.22,
    )

    plot_axis = figure.add_subplot(grid[0, 0])
    table_axis = figure.add_subplot(grid[0, 1])
    slider_axis = figure.add_subplot(grid[1, 0])
    button_axis = figure.add_subplot(grid[1, 1])

    plot_axis.set_title("Section 601 PRB vs FEA Overlay")
    plot_axis.set_xlabel("X")
    plot_axis.set_ylabel("Y")
    plot_axis.set_aspect("equal", adjustable="box")
    plot_axis.set_xlim(xmin, xmax)
    plot_axis.set_ylim(ymin, ymax)
    plot_axis.grid(True, alpha=0.25)

    fea_base_lines: dict[str, object] = {}
    fea_deformed_lines: dict[str, object] = {}
    fea_nodes: dict[str, object] = {}

    initial_fea = fea_frames[0]
    for part_name in section600.PART_NAMES:
        part_data = initial_fea.parts[part_name]
        color = section600.PART_COLORS[part_name]
        label = section600.PART_LABELS[part_name]

        base_line, = plot_axis.plot(
            part_data.base_xy[:, 0],
            part_data.base_xy[:, 1],
            linestyle="--",
            linewidth=0.9,
            color="#cc3d3d",
            alpha=0.14,
            label=f"{label} undeformed",
        )
        deformed_line, = plot_axis.plot(
            part_data.deformed_xy[:, 0],
            part_data.deformed_xy[:, 1],
            linewidth=1.35,
            color="#c62828",
            label=f"{label} FEA",
        )
        if part_name == "FLEX-1":
            node_scatter = plot_axis.scatter(
                part_data.deformed_xy[:, 0],
                part_data.deformed_xy[:, 1],
                color="#c62828",
                s=10,
                zorder=5,
            )
        else:
            node_scatter = None
        fea_base_lines[part_name] = base_line
        fea_deformed_lines[part_name] = deformed_line
        fea_nodes[part_name] = node_scatter

    prb_beam_line, = plot_axis.plot(
        prb_chain[0, :, 0],
        prb_chain[0, :, 1],
        color=PRB_COLORS["beam"],
        linewidth=1.35,
        label="PRB beam",
    )
    prb_coupler_line, = plot_axis.plot(
        [prb_a[0, 0], prb_q[0, 0]],
        [prb_a[0, 1], prb_q[0, 1]],
        color=PRB_COLORS["coupler"],
        linewidth=1.35,
        label="PRB coupler",
    )
    prb_crank_line, = plot_axis.plot(
        [float(section520.B[0] * PRB_SCALE), prb_crank[0, 0]],
        [float(section520.B[1] * PRB_SCALE), prb_crank[0, 1]],
        color=PRB_COLORS["crank"],
        linewidth=1.35,
        label="PRB crank",
    )
    prb_joint_scatter = plot_axis.scatter(
        prb_chain[0, :, 0],
        prb_chain[0, :, 1],
        color=PRB_COLORS["beam"],
        s=10,
        zorder=6,
    )
    prb_a_point = plot_axis.scatter([prb_a[0, 0]], [prb_a[0, 1]], color=PRB_COLORS["point_a"], s=18, zorder=7)
    prb_q_point = plot_axis.scatter([prb_q[0, 0]], [prb_q[0, 1]], color=PRB_COLORS["point_q"], s=18, zorder=7)

    plot_axis.legend(loc="best")

    table_axis.axis("off")
    table_text = table_axis.text(
        0.0,
        1.0,
        "",
        va="top",
        ha="left",
        fontsize=10,
        family="monospace",
        bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "#cccccc", "boxstyle": "round,pad=0.5"},
    )

    slider = Slider(
        ax=slider_axis,
        label="FEA frame index",
        valmin=0,
        valmax=len(fea_frames) - 1,
        valinit=0,
        valstep=1,
        color="#1f77b4",
    )
    slider_axis.set_title("Move through FEA time steps", fontsize=10, pad=8)

    reset_button = Button(button_axis, "Reset frame")
    button_axis.set_title("Overlay Controls", fontsize=10, pad=8)

    def summary_text(frame_index: int, prb_index: int, angle_deg: float) -> str:
        frame = fea_frames[frame_index]
        fea_key_points = fea_points(frame)
        prb_a_point_xy = prb_a[prb_index]
        prb_q_point_xy = prb_q[prb_index]
        a_error = float(np.linalg.norm(prb_a_point_xy - fea_key_points["A"]))
        q_error = float(np.linalg.norm(prb_q_point_xy - fea_key_points["Q"]))
        theta_deg = np.degrees(prb_theta[prb_index])

        return "\n".join(
            [
                f"FEA frame index : {frame_index}",
                f"FEA step time   : {frame.step_time:.6f}",
                f"FEA BA angle    : {angle_deg:.3f} deg",
                f"PRB BA angle    : {prb_angles_deg[prb_index]:.3f} deg",
                "",
                f"gammas          : [{gammas[0]:.2f}, {gammas[1]:.2f}, {gammas[2]:.2f}, {gammas[3]:.2f}]",
                f"kbar            : [{kbar[0]:.3f}, {kbar[1]:.3f}, {kbar[2]:.3f}]",
                f"stiffness path  : {stiffness_label}",
                "",
                f"theta [deg]     : ({theta_deg[0]:.2f}, {theta_deg[1]:.2f}, {theta_deg[2]:.2f})",
                f"tip slope [deg] : {float(np.sum(theta_deg)):.2f}",
                f"load [Fx,Fy,M]  : ({prb_load[prb_index,0]:.4f}, {prb_load[prb_index,1]:.4f}, {prb_load[prb_index,2]:.4f})",
                f"residual norm   : {prb_residual[prb_index]:.3e}",
                "",
                f"A error         : {a_error:.4f}",
                f"Q error         : {q_error:.4f}",
                f"FEA A           : ({fea_key_points['A'][0]:.3f}, {fea_key_points['A'][1]:.3f})",
                f"PRB A           : ({prb_a_point_xy[0]:.3f}, {prb_a_point_xy[1]:.3f})",
                f"FEA Q           : ({fea_key_points['Q'][0]:.3f}, {fea_key_points['Q'][1]:.3f})",
                f"PRB Q           : ({prb_q_point_xy[0]:.3f}, {prb_q_point_xy[1]:.3f})",
            ]
        )

    def update_frame(frame_index: int) -> None:
        index = int(frame_index)
        frame = fea_frames[index]
        fea_angle_deg = crank_angle_deg_from_frame(frame)
        wrapped_angle = wrap_angle_0_360(fea_angle_deg)
        prb_index = int(np.argmin(np.abs(prb_angles_deg - wrapped_angle)))

        for part_name in section600.PART_NAMES:
            part_data = frame.parts[part_name]
            fea_deformed_lines[part_name].set_data(part_data.deformed_xy[:, 0], part_data.deformed_xy[:, 1])
            if fea_nodes[part_name] is not None:
                fea_nodes[part_name].set_offsets(part_data.deformed_xy)

        prb_beam_line.set_data(prb_chain[prb_index, :, 0], prb_chain[prb_index, :, 1])
        prb_coupler_line.set_data(
            [prb_a[prb_index, 0], prb_q[prb_index, 0]],
            [prb_a[prb_index, 1], prb_q[prb_index, 1]],
        )
        prb_crank_line.set_data(
            [float(section520.B[0] * PRB_SCALE), prb_crank[prb_index, 0]],
            [float(section520.B[1] * PRB_SCALE), prb_crank[prb_index, 1]],
        )
        prb_joint_scatter.set_offsets(prb_chain[prb_index])
        prb_a_point.set_offsets(prb_a[prb_index : prb_index + 1])
        prb_q_point.set_offsets(prb_q[prb_index : prb_index + 1])

        table_text.set_text(summary_text(index, prb_index, fea_angle_deg))
        plot_axis.set_title(
            f"Section 601 PRB vs FEA Overlay\n{frame.frame_label}"
        )
        figure.canvas.draw_idle()

    slider.on_changed(update_frame)

    def reset_slider(_: object) -> None:
        slider.reset()

    reset_button.on_clicked(reset_slider)
    update_frame(0)

    return figure, {
        "slider": slider,
        "reset_button": reset_button,
        "prb_joint_scatter": prb_joint_scatter,
        "prb_a_point": prb_a_point,
        "prb_q_point": prb_q_point,
    }


def main() -> None:
    fea_frames = section600.load_verification_frames(section600.csv_path())
    gammas, kbar, stiffness_label, prb_motion = get_prb_motion()

    print("Section 601 PRB vs FEA overlay")
    print(f"verification file = {section600.csv_path()}")
    print(f"FEA frames = {len(fea_frames)}")
    print(f"gammas = [{gammas[0]:.2f} {gammas[1]:.2f} {gammas[2]:.2f} {gammas[3]:.2f}]")
    print(f"{stiffness_label} kbar = [{kbar[0]:.5f} {kbar[1]:.5f} {kbar[2]:.5f}]")

    figure, gui_refs = build_overlay_viewer(fea_frames, gammas, kbar, stiffness_label, prb_motion)
    _GUI_REFS["figure"] = figure
    _GUI_REFS.update(gui_refs)
    plt.show()


if __name__ == "__main__":
    main()
