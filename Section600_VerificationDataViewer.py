from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, Slider


CSV_FILENAME = "verificationdata.csv"
PART_NAMES = ("CRANK-1", "COUP-1", "FLEX-1")
PART_COLORS = {
    "CRANK-1": "#d62728",
    "COUP-1": "#ff7f0e",
    "FLEX-1": "#1f77b4",
}
PART_LABELS = {
    "CRANK-1": "Crank",
    "COUP-1": "Coupler",
    "FLEX-1": "Flex",
}
_GUI_REFS: dict[str, object] = {}


@dataclass
class PartFrameData:
    node_labels: np.ndarray
    base_xy: np.ndarray
    deformed_xy: np.ndarray


@dataclass
class FrameData:
    frame_label: str
    step_time: float
    parts: dict[str, PartFrameData]


def csv_path() -> Path:
    return Path(__file__).resolve().with_name(CSV_FILENAME)


def parse_step_time(frame_label: str) -> float:
    match = re.search(r"Step Time =\s*([0-9.E+-]+)", frame_label)
    if match is None:
        return 0.0
    return float(match.group(1))


def load_verification_frames(path: Path) -> list[FrameData]:
    frame_rows: dict[str, dict[str, list[tuple[int, float, float, float, float]]]] = {}
    frame_order: list[str] = []

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            part_name = raw_row["Part Instance Name"].strip()
            if part_name not in PART_NAMES:
                continue

            frame_label = raw_row["Frame"].strip()
            if frame_label not in frame_rows:
                frame_rows[frame_label] = {part: [] for part in PART_NAMES}
                frame_order.append(frame_label)

            frame_rows[frame_label][part_name].append(
                (
                    int(raw_row["    Node Label"]),
                    float(raw_row["X"]),
                    float(raw_row["Y"]),
                    float(raw_row["          U-U1"]),
                    float(raw_row["          U-U2"]),
                )
            )

    frames: list[FrameData] = []
    for frame_label in frame_order:
        part_map: dict[str, PartFrameData] = {}
        for part_name in PART_NAMES:
            rows = sorted(frame_rows[frame_label][part_name], key=lambda item: item[0])
            if not rows:
                continue

            node_labels = np.array([row[0] for row in rows], dtype=int)
            base_xy = np.array([[row[1], row[2]] for row in rows], dtype=float)
            displacement_xy = np.array([[row[3], row[4]] for row in rows], dtype=float)
            part_map[part_name] = PartFrameData(
                node_labels=node_labels,
                base_xy=base_xy,
                deformed_xy=base_xy + displacement_xy,
            )

        frames.append(
            FrameData(
                frame_label=frame_label,
                step_time=parse_step_time(frame_label),
                parts=part_map,
            )
        )

    if not frames:
        raise RuntimeError("No CRANK-1 / COUP-1 / FLEX-1 frame data were found in the CSV.")

    return frames


def compute_plot_limits(frames: list[FrameData]) -> tuple[float, float, float, float]:
    all_points: list[np.ndarray] = []
    for frame in frames:
        for part_data in frame.parts.values():
            all_points.append(part_data.base_xy)
            all_points.append(part_data.deformed_xy)

    stacked = np.vstack(all_points)
    xmin = float(np.min(stacked[:, 0]))
    xmax = float(np.max(stacked[:, 0]))
    ymin = float(np.min(stacked[:, 1]))
    ymax = float(np.max(stacked[:, 1]))
    span = max(xmax - xmin, ymax - ymin)
    padding = 0.08 * span if span > 0.0 else 1.0
    return xmin - padding, xmax + padding, ymin - padding, ymax + padding


def build_viewer(frames: list[FrameData]) -> tuple[plt.Figure, dict[str, object]]:
    xmin, xmax, ymin, ymax = compute_plot_limits(frames)

    figure = plt.figure(figsize=(14.0, 8.0), constrained_layout=False)
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

    plot_axis.set_title("Section 600 Verification Data Viewer")
    plot_axis.set_xlabel("X")
    plot_axis.set_ylabel("Y")
    plot_axis.set_aspect("equal", adjustable="box")
    plot_axis.set_xlim(xmin, xmax)
    plot_axis.set_ylim(ymin, ymax)
    plot_axis.grid(True, alpha=0.25)

    base_lines: dict[str, object] = {}
    deformed_lines: dict[str, object] = {}
    node_scatters: dict[str, object] = {}

    initial_frame = frames[0]
    for part_name in PART_NAMES:
        part_data = initial_frame.parts[part_name]
        color = PART_COLORS[part_name]
        label = PART_LABELS[part_name]

        base_line, = plot_axis.plot(
            part_data.base_xy[:, 0],
            part_data.base_xy[:, 1],
            linestyle="--",
            linewidth=1.4,
            color=color,
            alpha=0.35,
            label=f"{label} undeformed",
        )
        deformed_line, = plot_axis.plot(
            part_data.deformed_xy[:, 0],
            part_data.deformed_xy[:, 1],
            linewidth=2.2,
            color=color,
            label=f"{label} current",
        )
        node_scatter = plot_axis.scatter(
            part_data.deformed_xy[:, 0],
            part_data.deformed_xy[:, 1],
            color=color,
            s=20,
            zorder=5,
        )

        base_lines[part_name] = base_line
        deformed_lines[part_name] = deformed_line
        node_scatters[part_name] = node_scatter

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
        label="Frame index",
        valmin=0,
        valmax=len(frames) - 1,
        valinit=0,
        valstep=1,
        color="#1f77b4",
    )
    slider_axis.set_title("Move through time steps", fontsize=10, pad=8)

    reset_button = Button(button_axis, "Reset frame")
    button_axis.set_title("Slider Controls", fontsize=10, pad=8)

    def summary_text(frame_index: int) -> str:
        frame = frames[frame_index]
        lines = [
            f"Frame index : {frame_index}",
            f"Step time   : {frame.step_time:.6f}",
            "",
        ]
        for part_name in PART_NAMES:
            part_data = frame.parts[part_name]
            tip_xy = part_data.deformed_xy[-1]
            base_tip_xy = part_data.base_xy[-1]
            delta_xy = tip_xy - base_tip_xy
            lines.extend(
                [
                    f"{PART_LABELS[part_name]}",
                    f"  nodes     : {len(part_data.node_labels)}",
                    f"  tip XY    : ({tip_xy[0]:.4f}, {tip_xy[1]:.4f})",
                    f"  tip dXY   : ({delta_xy[0]:.4f}, {delta_xy[1]:.4f})",
                    "",
                ]
            )
        return "\n".join(lines).rstrip()

    def update_frame(frame_index: int) -> None:
        index = int(frame_index)
        frame = frames[index]

        for part_name in PART_NAMES:
            part_data = frame.parts[part_name]
            deformed_lines[part_name].set_data(part_data.deformed_xy[:, 0], part_data.deformed_xy[:, 1])
            node_scatters[part_name].set_offsets(part_data.deformed_xy)

        table_text.set_text(summary_text(index))
        plot_axis.set_title(
            f"Section 600 Verification Data Viewer\n{frame.frame_label}"
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
    }


def main() -> None:
    path = csv_path()
    frames = load_verification_frames(path)
    print(f"Loaded verification data from: {path}")
    print(f"Frames: {len(frames)}")
    for part_name in PART_NAMES:
        node_count = len(frames[0].parts[part_name].node_labels)
        print(f"  {part_name}: {node_count} nodes")

    figure, gui_refs = build_viewer(frames)
    _GUI_REFS["figure"] = figure
    _GUI_REFS.update(gui_refs)
    plt.show()


if __name__ == "__main__":
    main()
