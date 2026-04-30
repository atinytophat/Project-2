# ME7571 Project 2

Compliant mechanism project built around Hai-Jun Su's PRB 3R model.

## Main pieces

- `Section200...` through `Section701...`: Python experiments and analysis scripts
- `webapp/`: browser UI for the atlas, PRB workflow, mechanism overlay, and medical motion study
- `Abaqus/verificationdata.csv`: FEA verification data used by the Section 5 overlay

## Run locally

From `webapp/`:

```powershell
python server.py
```

Then open:

```text
http://127.0.0.1:8123/
```
