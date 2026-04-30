from __future__ import annotations

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq


# =========================
# User input
# =========================
# Set INPUT_MODE to:
#   "dimensional"    -> specify F0, M0, L, E, I, t, sigma_max, phi
#   "nondimensional" -> specify alpha, beta, l_over_t, sigma_over_e, phi
INPUT_MODE = "dimensional"

phi_deg =90.0

# Dimensional inputs
F0 = 1/4
M0 = 0.0
beam_length = 1
youngs_modulus = 69*(10^9)
beam_width = 0.5
thickness = 0.01
sigma_max = 35*(10^6)

# Nondimensional inputs
alpha_input = 0.5
beta_input = 0.0
l_over_t = 100.0
sigma_over_e = 0.01


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


def theta0_max_for_case(phi: float, k_value: float, eps_th: float = 1.0e-6) -> float:
    if k_value <= 2.0:
        return min(np.pi, phi + np.arccos(1.0 - k_value)) - eps_th
    return np.pi - eps_th


def nondimensional_force_index(force: float, length: float, e_modulus: float, inertia: float) -> float:
    return float(force * length * length / (2.0 * e_modulus * inertia))


def nondimensional_moment(moment: float, length: float, e_modulus: float, inertia: float) -> float:
    return float(moment * length / (e_modulus * inertia))


def rectangular_second_moment(width: float, thickness_value: float) -> float:
    return float(width * thickness_value**3 / 12.0)


def load_ratio(alpha_value: float, beta_value: float) -> float:
    if alpha_value <= 0.0:
        return float("inf")
    return float((beta_value * beta_value) / (4.0 * alpha_value))


def allowable_mnet(l_over_t_value: float, sigma_over_e_value: float) -> float:
    return float(2.0 * l_over_t_value * sigma_over_e_value)


def stress_limited_theta_max_from_section22(l_over_t_value: float, sigma_over_e_value: float) -> float:
    # For the pure-moment case used to set the Section 4.4 stress limit,
    # the allowable normalized fixed-end moment is equal to the maximum tip slope.
    return allowable_mnet(l_over_t_value, sigma_over_e_value)


def pure_moment_response(beta_value: float) -> tuple[float, float, float]:
    th0 = beta_value
    if abs(th0) < 1.0e-12:
        return 1.0, 0.0, 0.0
    a_l = np.sin(th0) / th0
    b_l = (1.0 - np.cos(th0)) / th0
    return float(a_l), float(b_l), float(th0)


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
        "No valid Section 2.1 solution was bracketed for this load case. "
        f"Closest alpha was {closest_alpha:.6g} at theta0 = {theta_samples[min_idx]:.6g} rad."
    )


def solve_tip_response(alpha_value: float, beta_value: float, phi_deg_value: float) -> dict[str, float]:
    phi = np.deg2rad(phi_deg_value)

    if alpha_value < 0.0:
        raise ValueError("alpha must be nonnegative.")
    if beta_value < 0.0:
        raise ValueError("Negative beta may introduce an inflection point, outside Section 2.1.")

    if alpha_value == 0.0:
        a_l, b_l, th0 = pure_moment_response(beta_value)
        return {
            "a_over_l": a_l,
            "b_over_l": b_l,
            "theta0_rad": th0,
            "theta0_deg": float(np.rad2deg(th0)),
            "alpha": 0.0,
            "beta": float(beta_value),
            "k": float("inf"),
        }

    k_value = load_ratio(alpha_value, beta_value)
    th0 = _find_theta0_for_alpha(alpha_value, phi, k_value)
    _, a_l, b_l = compute_state_with_alpha(th0, phi, k_value)
    return {
        "a_over_l": float(a_l),
        "b_over_l": float(b_l),
        "theta0_rad": float(th0),
        "theta0_deg": float(np.rad2deg(th0)),
        "alpha": float(alpha_value),
        "beta": float(beta_value),
        "k": float(k_value),
    }


def mnet_from_response(alpha_value: float, beta_value: float, a_l: float, b_l: float, phi_deg_value: float) -> float:
    phi = np.deg2rad(phi_deg_value)
    return float(beta_value + 2.0 * alpha_value * (a_l * np.sin(phi) - b_l * np.cos(phi)))


def dimensional_inputs_to_nondimensional() -> tuple[float, float, float, float]:
    second_moment = rectangular_second_moment(beam_width, thickness)
    alpha_value = nondimensional_force_index(F0, beam_length, youngs_modulus, second_moment)
    beta_value = nondimensional_moment(M0, beam_length, youngs_modulus, second_moment)
    return (
        alpha_value,
        beta_value,
        beam_length / thickness,
        sigma_max / youngs_modulus,
    )


def run_case() -> None:
    if INPUT_MODE == "dimensional":
        alpha_value, beta_value, l_over_t_value, sigma_over_e_value = dimensional_inputs_to_nondimensional()
    elif INPUT_MODE == "nondimensional":
        alpha_value = float(alpha_input)
        beta_value = float(beta_input)
        l_over_t_value = float(l_over_t)
        sigma_over_e_value = float(sigma_over_e)
    else:
        raise ValueError("INPUT_MODE must be 'dimensional' or 'nondimensional'.")

    response = solve_tip_response(alpha_value, beta_value, phi_deg)
    m_net = mnet_from_response(
        response["alpha"],
        response["beta"],
        response["a_over_l"],
        response["b_over_l"],
        phi_deg,
    )
    m_allow = allowable_mnet(l_over_t_value, sigma_over_e_value)
    margin = m_allow - m_net

    print("Section 2.2 stress check for combined tip force and moment")
    print(f"phi = {phi_deg:.6f} deg")
    if INPUT_MODE == "dimensional":
        print(f"width = {beam_width:.12g}")
        print(f"thickness = {thickness:.12g}")
        print(f"I = {rectangular_second_moment(beam_width, thickness):.12g}")
    print(f"alpha = {response['alpha']:.12g}")
    print(f"beta = {response['beta']:.12g}")
    print(f"k = {response['k']:.12g}")
    print(f"a/L = {response['a_over_l']:.12g}")
    print(f"b/L = {response['b_over_l']:.12g}")
    print(f"theta0 = {response['theta0_rad']:.12g} rad")
    print(f"theta0 = {response['theta0_deg']:.12g} deg")
    print(f"M_net = {m_net:.12g}")
    print(f"M_allow = {m_allow:.12g}")
    print(f"margin = {margin:.12g}")
    print(f"yields = {m_net > m_allow}")


if __name__ == "__main__":
    run_case()
