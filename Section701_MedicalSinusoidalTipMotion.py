from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
from scipy.optimize import least_squares

import Section400_PRB3R_ReportProcedure as section4
import Section510_OptimalPRBComparison as section51


# =========================
# User input
# =========================
# This is a prescribed-motion steering test for an intubation-inspired
# compliant distal segment. The base of the normalized PRB beam is fixed at
# (0, 0), and the undeformed tip lies at (1, 0).
tip_amplitude = 0.10
num_time_points = 161
core_motion_time = 8.0
end_hold_time = 1.0
total_motion_time = core_motion_time + 2.0 * end_hold_time
max_heading_deg = 25.0

# Because x is intentionally left free, define the desired tip heading from a
# nominal forward rate that is tuned from the actual vertical speed so the
# maximum tip-heading magnitude stays near the requested intubation-like limit.
max_heading_rad = math.radians(max_heading_deg)

# Small continuity regularization used only to stay on one smooth branch of the
# under-constrained kinematic family.
continuity_weight = 1.0e-3


def load_project_prb_parameters() -> tuple[np.ndarray, np.ndarray]:
    """Reuse the PRB parameters from the existing Section 4/5 pipeline."""
    gammas = section51.get_optimal_gammas()
    kbar, _, _ = section51.select_section51_stiffness(gammas)
    return np.asarray(gammas, dtype=float), np.asarray(kbar, dtype=float)


def forward_kinematics_3R(theta: np.ndarray, gamma: np.ndarray) -> tuple[float, float, float]:
    """Return the normalized PRB tip position and tip angle."""
    return section4.prb3r_forward_kinematics(np.asarray(theta, dtype=float), np.asarray(gamma, dtype=float))


def joint_positions_3R(theta: np.ndarray, gamma: np.ndarray) -> np.ndarray:
    """Return the normalized PRB joint coordinates from the base to the tip."""
    theta1, theta2, theta3 = np.asarray(theta, dtype=float)
    theta12 = theta1 + theta2
    theta123 = theta12 + theta3

    origin = np.array([0.0, 0.0], dtype=float)
    p1 = np.array([gamma[0], 0.0], dtype=float)
    p2 = p1 + gamma[1] * np.array([math.cos(theta1), math.sin(theta1)], dtype=float)
    p3 = p2 + gamma[2] * np.array([math.cos(theta12), math.sin(theta12)], dtype=float)
    p4 = p3 + gamma[3] * np.array([math.cos(theta123), math.sin(theta123)], dtype=float)
    return np.vstack([origin, p1, p2, p3, p4])


def desired_tip_motion(time_values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the prescribed y-tip motion and matching heading history.

    The user requirement is that y_tip starts at zero, moves negative first,
    then returns through zero and reaches positive values like a sine wave.
    Use an eased phase inside a sine wave, so:
    - y(0) = 0
    - dy/dt(0) = 0, so the beam starts horizontal
    - first extremum is y = -A
    - theta0 = 0 at y = -A and y = A because dy/dt = 0 there
    """
    clamped_motion_time = np.clip(
        np.asarray(time_values, dtype=float) - float(end_hold_time),
        0.0,
        float(core_motion_time),
    )
    normalized_time = clamped_motion_time / float(core_motion_time)
    eased_phase = 2.0 * math.pi * (3.0 * normalized_time**2 - 2.0 * normalized_time**3)
    eased_phase_rate = (
        2.0
        * math.pi
        * (6.0 * normalized_time - 6.0 * normalized_time**2)
        / float(core_motion_time)
    )
    active_motion_mask = (
        (np.asarray(time_values, dtype=float) >= float(end_hold_time))
        & (np.asarray(time_values, dtype=float) <= float(end_hold_time + core_motion_time))
    )
    eased_phase_rate = np.where(active_motion_mask, eased_phase_rate, 0.0)

    y_desired = -tip_amplitude * np.sin(eased_phase)
    dy_dt = -tip_amplitude * np.cos(eased_phase) * eased_phase_rate

    peak_vertical_speed = max(float(np.max(np.abs(dy_dt))), 1.0e-12)
    nominal_forward_rate = peak_vertical_speed / math.tan(max_heading_rad)

    theta0_desired = np.zeros_like(time_values, dtype=float)
    for idx, y_rate in enumerate(dy_dt):
        if abs(float(y_rate)) <= 1.0e-12:
            theta0_desired[idx] = 0.0
        else:
            theta0_desired[idx] = math.atan2(float(y_rate), nominal_forward_rate)

    return y_desired, theta0_desired


def solve_frame(
    y_target: float,
    theta0_target: float,
    gamma: np.ndarray,
    initial_guess: np.ndarray,
) -> np.ndarray:
    """Solve one smooth PRB configuration for the prescribed y and theta0.

    Since x is free, this is a two-constraint problem with three PRB angles.
    A small continuity penalty keeps the solution on one continuous branch as
    time advances.
    """
    initial_guess_array = np.asarray(initial_guess, dtype=float)

    def residual(theta: np.ndarray) -> np.ndarray:
        tip_x, tip_y, tip_theta = forward_kinematics_3R(theta, gamma)
        del tip_x  # x is intentionally free in this prescribed-motion study.
        return np.array(
            [
                tip_y - float(y_target),
                tip_theta - float(theta0_target),
                continuity_weight * (theta[0] - initial_guess_array[0]),
                continuity_weight * (theta[1] - initial_guess_array[1]),
                continuity_weight * (theta[2] - initial_guess_array[2]),
            ],
            dtype=float,
        )

    result = least_squares(
        residual,
        initial_guess_array,
        xtol=1.0e-12,
        ftol=1.0e-12,
        gtol=1.0e-12,
        max_nfev=600,
    )
    if not result.success:
        raise RuntimeError(
            f"Could not solve the sinusoidal steering frame for y = {y_target:.5f}, theta0 = {theta0_target:.5f}."
        )
    return np.asarray(result.x, dtype=float)


def solve_motion(
    gamma: np.ndarray,
    kbar: np.ndarray,
) -> list[dict[str, float | np.ndarray]]:
    """Solve the prescribed sinusoidal steering motion by continuation in time."""
    del kbar  # Stored for consistency with the project; not needed for pure kinematics here.

    time_values = np.linspace(0.0, total_motion_time, num_time_points)
    y_desired_values, theta0_desired_values = desired_tip_motion(time_values)

    results: list[dict[str, float | np.ndarray]] = []
    previous_theta = np.zeros(3, dtype=float)

    for time_value, y_target, theta0_target in zip(time_values, y_desired_values, theta0_desired_values):
        theta = solve_frame(float(y_target), float(theta0_target), gamma, previous_theta)
        tip_x, tip_y, theta0_actual = forward_kinematics_3R(theta, gamma)
        results.append(
            {
                "t": float(time_value),
                "theta": np.asarray(theta, dtype=float),
                "y_target": float(y_target),
                "theta0_target": float(theta0_target),
                "x_actual": float(tip_x),
                "y_actual": float(tip_y),
                "theta0_actual": float(theta0_actual),
                "chain": joint_positions_3R(theta, gamma),
            }
        )
        previous_theta = theta

    return results


def build_interactive_figure(
    results: list[dict[str, float | np.ndarray]],
    gamma: np.ndarray,
) -> tuple[plt.Figure, Slider]:
    """Build an interactive Matplotlib figure with a time slider."""
    del gamma

    time_values = np.array([float(row["t"]) for row in results], dtype=float)
    x_actual = np.array([float(row["x_actual"]) for row in results], dtype=float)
    y_actual = np.array([float(row["y_actual"]) for row in results], dtype=float)
    y_target = np.array([float(row["y_target"]) for row in results], dtype=float)
    theta0_target_deg = np.rad2deg([float(row["theta0_target"]) for row in results])
    theta0_actual_deg = np.rad2deg([float(row["theta0_actual"]) for row in results])

    fig = plt.figure(figsize=(12.0, 7.6))
    grid = fig.add_gridspec(2, 2, width_ratios=[1.4, 1.0], height_ratios=[1.0, 1.0])

    ax_shape = fig.add_subplot(grid[:, 0])
    ax_y = fig.add_subplot(grid[0, 1])
    ax_theta = fig.add_subplot(grid[1, 1], sharex=ax_y)

    undeformed_chain = np.array(
        [
            [0.0, 0.0],
            [results[0]["chain"][1][0], 0.0],
            [results[0]["chain"][2][0], 0.0],
            [results[0]["chain"][3][0], 0.0],
            [1.0, 0.0],
        ],
        dtype=float,
    )
    ax_shape.plot(
        undeformed_chain[:, 0],
        undeformed_chain[:, 1],
        linestyle="--",
        linewidth=1.8,
        color="#8a96a7",
        label="Undeformed PRB beam",
    )
    ax_shape.plot(
        x_actual,
        y_actual,
        linewidth=2.0,
        color="#ef8c54",
        alpha=0.85,
        label="Tip path",
    )
    initial_chain = np.asarray(results[0]["chain"], dtype=float)
    chain_line, = ax_shape.plot(initial_chain[:, 0], initial_chain[:, 1], linewidth=2.6, color="#0c8aa4", label="PRB beam")
    joint_points = ax_shape.scatter(initial_chain[1:, 0], initial_chain[1:, 1], s=30, color="#0c8aa4", zorder=4)
    tip_marker = ax_shape.scatter([x_actual[0]], [y_actual[0]], s=44, color="#ef8c54", zorder=5)

    ax_shape.set_aspect("equal", adjustable="box")
    ax_shape.set_xlim(-0.02, 1.05)
    ax_shape.set_ylim(-0.18, 0.18)
    ax_shape.set_xlabel("x / L")
    ax_shape.set_ylabel("y / L")
    ax_shape.set_title(f"Section 701 sinusoidal tip steering (|theta0| <= {max_heading_deg:.0f} deg target)")
    ax_shape.grid(True, linestyle=":", linewidth=0.8, alpha=0.6)
    ax_shape.legend(loc="upper left")

    ax_y.plot(time_values, y_target, linestyle="--", linewidth=2.0, color="#ef8c54", label="Desired y")
    ax_y.plot(time_values, y_actual, linewidth=2.0, color="#0c8aa4", label="Actual y")
    y_time_marker = ax_y.scatter([time_values[0]], [y_actual[0]], s=36, color="#0c8aa4", zorder=4)
    ax_y.set_ylabel("y / L")
    ax_y.set_title("Tip y over time")
    ax_y.grid(True, linestyle=":", linewidth=0.8, alpha=0.6)
    ax_y.legend(loc="upper right")

    ax_theta.plot(time_values, theta0_target_deg, linestyle="--", linewidth=2.0, color="#ef8c54", label="Desired theta0")
    ax_theta.plot(time_values, theta0_actual_deg, linewidth=2.0, color="#0c8aa4", label="Actual theta0")
    theta_time_marker = ax_theta.scatter([time_values[0]], [theta0_actual_deg[0]], s=36, color="#0c8aa4", zorder=4)
    ax_theta.set_xlabel("time")
    ax_theta.set_ylabel("theta0 (deg)")
    ax_theta.set_title("Tip heading over time")
    ax_theta.grid(True, linestyle=":", linewidth=0.8, alpha=0.6)
    ax_theta.legend(loc="upper right")

    slider_ax = fig.add_axes([0.14, 0.05, 0.72, 0.035])
    time_slider = Slider(
        ax=slider_ax,
        label="time",
        valmin=float(time_values[0]),
        valmax=float(time_values[-1]),
        valinit=float(time_values[0]),
        valstep=float(time_values[1] - time_values[0]),
    )

    def update(selected_time: float) -> None:
        frame_index = int(np.argmin(np.abs(time_values - float(selected_time))))
        frame = results[frame_index]
        chain = np.asarray(frame["chain"], dtype=float)

        chain_line.set_data(chain[:, 0], chain[:, 1])
        joint_points.set_offsets(chain[1:, :2])
        tip_marker.set_offsets(np.array([[float(frame["x_actual"]), float(frame["y_actual"])]], dtype=float))
        y_time_marker.set_offsets(np.array([[time_values[frame_index], y_actual[frame_index]]], dtype=float))
        theta_time_marker.set_offsets(np.array([[time_values[frame_index], theta0_actual_deg[frame_index]]], dtype=float))
        ax_shape.set_title(
            "Section 701 sinusoidal tip steering\n"
            f"t = {time_values[frame_index]:.2f}, y = {y_actual[frame_index]:.3f}, theta0 = {theta0_actual_deg[frame_index]:.2f} deg"
        )
        fig.canvas.draw_idle()

    time_slider.on_changed(update)
    fig.tight_layout(rect=[0.0, 0.09, 1.0, 1.0])
    return fig, time_slider


def main() -> None:
    gammas, kbar = load_project_prb_parameters()
    results = solve_motion(gammas, kbar)
    figure, slider = build_interactive_figure(results, gammas)

    # Keep the slider alive for the lifetime of the GUI.
    figure._section701_slider = slider  # type: ignore[attr-defined]
    plt.show()


if __name__ == "__main__":
    main()
