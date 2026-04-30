# Project Context Notes

## Source Files Read

- `me7751_project_description.txt`
- `HaijunSuPaper.txt`
- `Project 2 Proposal - Kenny Tanaka.txt`

## Assignment Requirements

- Topic must be a compliant mechanism problem.
- Because this is a planar mechanism, the analytical model must use the pseudo-rigid-body (PRB) method.
- The project must include finite element validation used as ground truth.
- The project must include an interactive GUI app.
- The app must let the user vary key design or loading parameters.
- The app must display analytical predictions, FEA or validated surrogate results, and the discrepancy between them.
- The final report must be written like an ASME-style technical paper.

## Selected Project Topic

- The proposed mechanism is a compliant steering mechanism for an endotracheal intubation robot.
- Motivation: replace a segmented tendon-driven soft robotic chain with a more predictable compliant mechanism.
- Main performance goals:
  - relate tendon actuation to tip deflection and curvature,
  - improve steering precision and controllability,
  - preserve flexibility within the endotracheal tube geometry,
  - compare analytical predictions against FEA.

## Paper Takeaways From Haijun Su PRB 3R Paper

- The paper proposes a planar PRB 3R model for large-deflection cantilever beams under combined tip force and moment.
- The PRB 3R model uses four rigid links, three revolute joints, and three torsional springs.
- It is more accurate than the standard PRB 1R model for large deflections.
- The paper reports:
  - about 2.2% maximum tip-point error versus numerical integration across broad load cases,
  - about 1.2% maximum tip error in the compliant four-bar example versus FEA.

## Core PRB 3R Relations

- Characteristic radius factors satisfy:
  - `gamma0 + gamma1 + gamma2 + gamma3 = 1`
- Forward kinematics:
  - `Qx = gamma0 + gamma1*cos(theta1) + gamma2*cos(theta1 + theta2) + gamma3*cos(theta1 + theta2 + theta3)`
  - `Qy = gamma1*sin(theta1) + gamma2*sin(theta1 + theta2) + gamma3*sin(theta1 + theta2 + theta3)`
  - `phi = theta1 + theta2 + theta3`
- Joint torques are modeled with torsional springs:
  - `tau_i = k_i * theta_i`
- Normalized spring stiffness:
  - `k_i_bar = k_i / (EI / l)`

## Optimized PRB 3R Parameters Reported In The Paper

- `gamma0 = 0.10`
- `gamma1 = 0.35`
- `gamma2 = 0.40`
- `gamma3 = 0.15`
- `k1 = 3.51 * EI / l`
- `k2 = 2.99 * EI / l`
- `k3 = 2.58 * EI / l`

## Practical Direction For This Project

- A reasonable first analytical model is to represent the compliant steering section as a planar flexible beam using the PRB 3R approximation.
- Tendon pull can likely be represented as an equivalent tip force, tip moment, or combined load depending on how the tendon routing is defined.
- The next engineering step is to choose a specific geometry and actuation idealization for the distal steering section so the PRB equations can be specialized to this mechanism.
- The FEA model should validate tip position, curvature or angle, and stress for the same loading cases.
- The GUI can compare PRB predictions against FEA data tables or a fitted surrogate model.
