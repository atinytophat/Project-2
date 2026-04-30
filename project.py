from __future__ import annotations

from typing import Iterable


# Representative medical-material examples for quick comparison.
# These are grade-specific public values where available, not universal constants
# for the entire polymer family. Replace them with exact supplier data before
# final design decisions.
#
# Stored fields are aimed at the compliant-deformation workflow:
# - elastic_modulus_pa: preferred stiffness input
# - yield_strength_pa: use when an actual yield value is published
# - design_strength_limit_pa: conservative placeholder for sigma_max if no yield
#   value is available and only a break/ultimate strength is published
#
# Sources used for the entries below:
# - Flexible PVC:
#   Teknor Apex medical PVC overview + MF-165-J3R-79NT medical film bulletin
# - Pebax:
#   Arkema PEBAX 7233 SA 01 MED product overview / TDS
# - Medical-grade TPU:
#   Lubrizol Tecoflex TPU - Clear datasheet (representative grade EG-93A)

MATERIAL_DATABASE = {
    "flexible_pvc": {
        "display_name": "Flexible PVC",
        "example_grade": "Teknor Apex MF-165-J3R-79NT",
        "family": "Medical-grade flexible PVC",
        "hardness": "81A",
        "density_g_cc": 1.25,
        "elastic_modulus_pa": None,
        "yield_strength_pa": None,
        "design_strength_limit_pa": 18.6e6,
        "ultimate_tensile_strength_pa": 18.6e6,
        "elongation_pct": 300.0,
        "strength_limit_basis": "Ultimate tensile strength used as placeholder sigma_max; public yield value not listed.",
        "modulus_basis": "No public modulus found in the source bulletin.",
        "notes": "Medical PVC family spans a broad Shore A range; choose an exact extrusion/molding grade before analysis.",
    },
    "pebax": {
        "display_name": "PEBAX",
        "example_grade": "Arkema PEBAX 7233 SA 01 MED",
        "family": "Medical-grade PEBA",
        "hardness": "61D",
        "density_g_cc": 1.01,
        "elastic_modulus_pa": 513.0e6,
        "yield_strength_pa": None,
        "design_strength_limit_pa": 56.0e6,
        "ultimate_tensile_strength_pa": 56.0e6,
        "elongation_pct": 300.0,
        "strength_limit_basis": "Stress at break used as placeholder sigma_max; public yield value not listed.",
        "modulus_basis": "Conditioned flexural modulus from Arkema product data.",
        "notes": "Useful as a stiffer medical elastomer/tubing material; exact MED grade should be matched to the device process.",
    },
    "medical_grade_tpu": {
        "display_name": "Medical-grade TPU",
        "example_grade": "Lubrizol Tecoflex Clear EG-93A",
        "family": "Medical-grade TPU",
        "hardness": "87A",
        "density_g_cc": 1.08,
        "elastic_modulus_pa": 22.1e6,
        "yield_strength_pa": None,
        "design_strength_limit_pa": 53.1e6,
        "ultimate_tensile_strength_pa": 53.1e6,
        "elongation_pct": 390.0,
        "strength_limit_basis": "Ultimate tensile strength used as placeholder sigma_max; public yield value not listed.",
        "modulus_basis": "Flexural modulus converted from 3,200 psi to 22.1 MPa.",
        "notes": "Representative aliphatic polyether TPU; exact Tecoflex/Pellethane grade should be chosen before final design.",
    },
}


def format_value(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def build_table(rows: Iterable[dict[str, object]]) -> str:
    headers = [
        ("display_name", "Material"),
        ("example_grade", "Representative Medical Grade"),
        ("hardness", "Hardness"),
        ("density_g_cc", "Density [g/cc]"),
        ("elastic_modulus_mpa", "Elastic Modulus [MPa]"),
        ("yield_strength_mpa", "Yield Strength [MPa]"),
        ("design_strength_limit_mpa", "Design Strength [MPa]"),
        ("elongation_pct", "Elongation [%]"),
        ("notes", "Notes"),
    ]

    formatted_rows = [
        [format_value(row[key]) for key, _ in headers]
        for row in rows
    ]
    widths = []
    for col_idx, (_, label) in enumerate(headers):
        max_width = len(label)
        for row in formatted_rows:
            max_width = max(max_width, len(row[col_idx]))
        widths.append(max_width)

    def format_row(values: list[str]) -> str:
        return " | ".join(value.ljust(width) for value, width in zip(values, widths))

    header_row = format_row([label for _, label in headers])
    separator_row = "-+-".join("-" * width for width in widths)
    body_rows = [format_row(row) for row in formatted_rows]
    return "\n".join([header_row, separator_row, *body_rows])


def build_material_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for material in MATERIAL_DATABASE.values():
        rows.append(
            {
                **material,
                "elastic_modulus_mpa": None
                if material["elastic_modulus_pa"] is None
                else float(material["elastic_modulus_pa"]) / 1.0e6,
                "yield_strength_mpa": None
                if material["yield_strength_pa"] is None
                else float(material["yield_strength_pa"]) / 1.0e6,
                "design_strength_limit_mpa": None
                if material["design_strength_limit_pa"] is None
                else float(material["design_strength_limit_pa"]) / 1.0e6,
            }
        )
    return rows


def main() -> None:
    print("Representative medical-material property store")
    print("These are example medical grades for early comparison, not universal family constants.")
    print("If yield strength is unavailable in the public source, design_strength_limit is a placeholder based on published break/ultimate strength.")
    print()
    print(build_table(build_material_rows()))


if __name__ == "__main__":
    main()
