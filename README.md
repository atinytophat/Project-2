# ME7571 Project 2

This repository recreates and extends the PRB 3R workflow from Hai-Jun Su's compliant-beam paper. The project has two main goals:

1. Recreate the paper's normalized beam, PRB, and mechanism results as faithfully as possible without hardcoding report results.
2. Extend that workflow into a design-study environment for a medical compliant segment with prescribed steering motions.

## Links

- Repository: `https://github.com/atinytophat/Project-2`
- Live web app: `https://atinytophat.github.io/Project-2/`

## Project Structure

### Core Python scripts

- `Section200_GeometricAtlas_LoadQuery.py`
  - Section 2 atlas generator and viewer.
  - Builds the normalized elastica atlas as a function of load ratio `K`, force angle `phi`, and tip slope `theta0`.
  - Supports both the report-style atlas plots and the interactive single-curve atlas view.

- `Section220_Th0_max_combined.py`
  - Combined Section 2.2 utility.
  - Solves beam response for a specified load case and performs the associated moment/yield-style checks.
  - Acts as a backend utility for later scripts that need allowable-motion logic.

- `Section223_AtlasCurveLoadSlider.py`
  - User-facing allowable-branch atlas tool.
  - Builds on the Section 2 atlas and Section 2.2 allowable-limit logic.
  - Lets the user move along the allowable portion of an atlas curve and inspect the corresponding load state.

- `Section400_PRB3R_ReportProcedure.py`
  - Main Section 4 PRB search procedure.
  - Searches for the PRB link fractions `gamma0, gamma1, gamma2, gamma3`.
  - Provides PRB kinematics, Jacobian-based load recovery, and stiffness sampling utilities used throughout the rest of the project.

- `Section450_PureMomentFit.py`
  - Pure-moment fit study.
  - Uses the Section 4 PRB geometry to compare PRB joint-angle behavior under the pure-moment reference family.
  - Produces the `theta0` vs `Theta_i` fit view used in the Section 4 workspace.

- `Section460_PureForceFit.py`
  - Pure-force fit study.
  - Uses the corrected pure-force interpretation `tau_i = k_i * Theta_i`.
  - Produces the force-family fit view used in the Section 4 workspace.

- `Section500_KappaAverageSearch.py`
  - Section 5.0 / 5.1 stiffness averaging helper.
  - Evaluates the PRB stiffnesses over the selected `K` grid and computes the load-independent average `kbar`.

- `Section510_OptimalPRBComparison.py`
  - Final Section 5 comparison script.
  - Pulls together the optimized `gamma` set and averaged `kbar`.
  - Generates the PRB-vs-atlas comparison workflow used to judge the final load-independent PRB model.

- `Section520_CompliantFourBar.py`
  - Section 5.2 compliant four-bar / crank mechanism model.
  - Uses the computed PRB parameters from the earlier search-and-average pipeline.
  - Solves the mechanism motion and acts as the basis for later FEA comparison.

- `Section600_VerificationDataViewer.py`
  - FEA motion viewer for the Abaqus verification data.
  - Loads `Abaqus/verificationdata.csv` and animates the crank, coupler, and flexible beam nodes over time.

- `Section601_PRBvsFEAOverlay.py`
  - PRB-vs-FEA overlay viewer.
  - Places the Section 520 PRB mechanism on top of the Section 600 FEA motion to compare tip position, angle, and overall motion quality.

- `Section701_MedicalSinusoidalTipMotion.py`
  - Prescribed-motion medical steering study.
  - Keeps the PRB base at `(0, 0)` and the undeformed tip at `(1, 0)`.
  - Prescribes a smooth sinusoidal tip `y` motion with bounded tip heading for intubation-inspired motion exploration.
  - Solves PRB joint angles by continuation and reports the resulting equivalent tip loads and base net moment.

- `project.py`
  - Small material-property store for the medical extension.
  - Holds representative material properties such as modulus and strength values used by the medical tab.

### FEA data

- `Abaqus/verificationdata.csv`
  - Abaqus-exported nodal motion used in Section 5 FEA verification and overlay work.
  - Contains crank, coupler, and flexible-beam node positions and displacements over time.

### Web app

- `webapp/index.html`
  - Main app layout and all screen/tab markup.

- `webapp/styles.css`
  - Full visual styling for the app, plots, controls, and screen layout.

- `webapp/app.js`
  - Frontend logic for all tabs.
  - Drives plotting, interaction, animations, and data loading.

- `webapp/server.py`
  - Optional local Python server for running the app locally with backend endpoints.
  - Useful for local development and regenerating live payloads.

- `webapp/py_backend.js`
  - Browser-side helper for the static GitHub Pages version.
  - Supports frontend-only operation where possible.

- `webapp/build_static_payloads.py`
  - Regenerates the static JSON payloads used by the GitHub Pages version of the app.

- `webapp/data/*.json`
  - Cached/precomputed payloads used by the static web app for faster loading and GitHub Pages compatibility.

## How The Workflow Fits Together

### Section 2

The project starts with the normalized elastica atlas:

- choose load ratio `K`
- choose force angle `phi`
- sweep `theta0`
- compute normalized tip coordinates and allowable limits

This atlas is the reference model. Everything PRB-related is trying to approximate this Section 2 behavior.

### Section 4

The PRB 3R model is calibrated in stages:

- search for the best `gamma` link fractions
- study the pure-moment family
- study the pure-force family
- extract stiffness behavior from torque-angle relations

### Section 5

The stiffness values are made load-independent by averaging over the chosen `K` grid, then used in the crank mechanism:

- `Section500` averages stiffnesses over the selected `K` values
- `Section510` evaluates the final PRB-vs-atlas quality
- `Section520` applies the resulting PRB model to the compliant crank mechanism
- `Section600` and `Section601` compare that PRB mechanism against FEA

### Medical extension

The medical study does not attempt to recreate a paper figure directly. Instead, it uses the computed PRB model as a design-study tool:

- prescribe a smooth sinusoidal tip motion
- solve the PRB by continuation
- recover equivalent tip force and tip moment
- compute base net moment for screening against allowable behavior

## Web App Overview

The GitHub Pages app is organized into four main tabs:

- `Section 2 Atlas`
  - interactive atlas view
  - report-style atlas view
  - allowable-branch and load inspection tools

- `Section 4 PRB`
  - gamma search view
  - pure-moment fit view
  - pure-force fit view
  - stiffness averaging / Section 5 feed view

- `Section 5 Mechanism`
  - PRB-vs-FEA crank mechanism overlay
  - crank-angle slider and animation
  - FEA and PRB visibility toggles
  - trend plots for selected tip quantities over crank angle

- `Material Library`
  - prescribed-motion medical PRB experiment
  - editable beam/material inputs
  - material presets
  - motion, load, and moment plots

## Local Run

If you want to run the development server locally:

```powershell
cd webapp
python server.py
```

Then open:

```text
http://127.0.0.1:8123/
```

## Notes

- The repo avoids hardcoding report-fit values into the reconstruction logic wherever possible.
- The Section 2 atlas is treated as the normalized reference model.
- The web app includes some static cached payloads for speed and GitHub Pages compatibility.
- FEA remains the higher-confidence validation layer for final mechanism behavior and stress interpretation.
