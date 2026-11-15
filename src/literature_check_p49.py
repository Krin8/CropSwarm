"""P49 read-only synthesis of common-bean nitrogen benchmarks."""

import json
import math
from pathlib import Path

from src.crops import load_crops
from src.literature_check import compare_value, show_span
from src.precompute_cache import write_json

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = "data/p49_literature.json"
OUTPUT = "literature_check_p49.json"
DOCUMENT = "literature_check_p49.md"
MEASURES = {
    "bean_equivalence": ("Common bean · maize grain-yield fertilizer equivalent", "kg N/ha"),
    "other_equivalence": ("Other legumes · maize grain-yield fertilizer equivalent", "kg N/ha"),
    "biomass_equivalence": ("Maize dry matter fertilizer equivalent", "kg N/ha"),
    "residue": ("N in returned bean residues", "kg N/ha"),
    "mineral_soil": ("Soil mineral N stock at maize sowing", "kg N/ha"),
    "uptake": ("Additional aboveground maize N uptake", "kg N/ha"),
    "grain_n": ("Additional maize grain N uptake", "kg N/ha"),
    "litter": ("Annual N returned through fallen litter", "kg N/ha/year"),
    "grain_yield": ("Difference in maize grain yield", "kg grain/ha"),
}
LIMIT = ("Fertilizer equivalence depends on the crop, soil, weather, residue management and maize response. "
         "It can include rotational effects unrelated to nitrogen. Field-level credit and rotation "
         "suitability at the Makueni coordinate remain unverified.")


def matched_n(curve, target):
    a, b, c = curve["quadratic"], curve["linear"], curve["intercept"] - target
    delta = b**2 - 4 * a * c
    if a == 0 or delta < 0:
        raise ValueError("The printed quadratic does not cross the target yield")
    roots = [(-b + sign * math.sqrt(delta)) / (2 * a) for sign in (-1, 1)]
    feasible = [root for root in roots if root >= 0]
    if not feasible:
        raise ValueError("No nonnegative N rate matches the target yield")
    return round(min(feasible), 1)


def overlap(left, right):
    low, high = max(left[0], right[0]), min(left[1], right[1])
    return [low, high] if low <= high else None


def finding(record, catalog, old):
    row = dict(record)
    if "response_curve" in row:
        row["estimates"] = [
            {"label": target["label"], "value": matched_n(row["response_curve"], target["yield_kg_ha"])}
            for target in row["targets"]
        ]
    values = [item["value"] for item in row["estimates"]]
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"Missing estimate for {row['id']}")
    row["bounds"] = [min(values), max(values)]
    row["measure_label"], row["unit"] = MEASURES[row["measure"]]
    if row["measure"] == "bean_equivalence":
        row["catalog_finding"] = compare_value(catalog, row["bounds"])
        row["p45_overlap"] = overlap(row["bounds"], old)
    return row


def build_report(references, crops, p45):
    crop = crops["common_bean"]
    catalog = crop["n_credit_kg_ha"]
    prior, = (row for row in p45["comparisons"]
              if row.get("source") == "nadar" and row.get("crop") == "common_bean"
              and row.get("field") == "n_credit_kg_ha")
    bounds = prior["bounds"]
    rows = [finding(row, catalog, bounds) for row in references["findings"]]
    named = {row["id"]: row for row in rows}
    legacy = p45["sources"][prior["source"]]
    return {
        "label": "Illustrative, validate locally",
        "catalog": {"value": catalog, **references["catalog_source"],
                    "crop_catalog_source": crop["n_credit_source"]},
        "p45": {**references["p45_context"], **legacy, "bounds": bounds},
        "machakos": {
            "bounds": named["chui_reported"]["bounds"],
            "catalog_finding": named["chui_reported"]["catalog_finding"],
            "p45_overlap": named["chui_reported"]["p45_overlap"],
            "recomputed": named["chui_recomputed"]["estimates"],
        },
        "rows": rows, "sources": references["sources"], "access_limits": references["access_limits"],
        "limit": LIMIT,
    }


def render(report):
    catalog, prior, machakos = (report[key] for key in ("catalog", "p45", "machakos"))
    intersection = machakos["p45_overlap"]
    overlap_text = f"Their reported spans overlap at {show_span(intersection)} kg N/ha." if intersection else (
        "The reported spans are disjoint.")
    catalog_position = ("within" if machakos["catalog_finding"] == "inside range" else "outside")
    katumani = ", ".join(f"{value:g} kg N/ha for {season}"
                         for value, season in zip(prior["bounds"], prior["seasons"], strict=True))
    lines = [
        "# Additional bean nitrogen benchmarks (P49)", "",
        "Illustrative comparisons. Validate locally before using any value.", "",
        f"The catalog uses **{catalog['value']:g} kg N/ha** for common bean. Chui's Machakos field-yield fits "
        f"span **{show_span(machakos['bounds'])} kg N/ha**. The catalog value falls {catalog_position} the reported Machakos span. "
        f"The earlier Katumani trial reported **{show_span(prior['bounds'])} kg N/ha**. {overlap_text} "
        "These bounds describe published conditions and carry no field-level uncertainty interval. "
        f"[Catalog](../data/crops.csv) · [{catalog['name']}, {catalog['locator']}]({catalog['url']}) · "
        f"[Chui thesis]({report['sources']['chui']['url']}) · [P45 Katumani comparison](literature_check_p45.md#nadar)", "",
        catalog["note"], "",
        "Fertilizer equivalence matches a maize response to "
        "an N fertilizer curve. Nitrogen in residues, soil mineral N and maize uptake quantify other parts of "
        "the system. Yield equivalence can reflect water, other nutrients and crop-break effects.", "",
        "## Earlier Katumani reference", "",
        f"Following maize fertilizer equivalents were {katumani}. {prior['soil']} {prior['residues']} {prior['method']} "
        f"[{prior['name']}, {prior['locator']}]({prior['url']})", "",
        "## Estimates and trial conditions", "",
        "| Crop and site | Following maize season or trial period | Soil | Residue management | Estimate and method | Use in this comparison | Source |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        source = report["sources"][row["source"]]
        entries = "<br>".join(f"{item['label']} ({item['value']:g} {row['unit']})" for item in row["estimates"])
        note = row["caveat"]
        if "catalog_finding" in row:
            note += f" Catalog value {row['catalog_finding']}."
            intersection = row["p45_overlap"]
            note += (f" Numeric overlap with P45 is {show_span(intersection)} kg N/ha."
                     if intersection else " Its span lies outside the Katumani interval.")
        lines.append(f"| {row['crop']} · {row['site']} | {row['season']} | {row['soil']} | {row['residues']} | "
                     f"{row['measure_label']}. {row['method']}<br>{entries} | {note} | "
                     f"[{source['name']}]({source['url']}) · {row['locator']} |")
    lines.extend([
        "", "## How to read the Machakos discrepancy", "",
        "Page 156 gives the full site-by-season list. Page 147 assigns different residue groups to the Kimutwa "
        "values. The Table 37b equation labels support a separate check for one short-rains season. Following "
        "Appendix Table 21, we matched the zero-added-N maize-after-bean fitted intercept to the lower "
        "nonnegative root of the continuous-maize curve. This is a recalculation of the same experiment. "
        "The thesis's contradictory assignments and dependence on a fitted yield response "
        f"limit what can be inferred about residue management. [Chui thesis]({report['sources']['chui']['url']})",
        "", report["limit"], "", "## Sources opened and read", "",
    ])
    for source in report["sources"].values():
        lines.append(f"- **{source['name']}**. {source['publication']} {source['locator']}. [Source]({source['url']})")
    lines.extend(["", "## Unreachable or partial full texts", ""])
    for source in report["access_limits"]:
        lines.append(f"- **{source['name']}**. {source['status']} {source['fallback']} [Record]({source['url']})")
    lines.extend(["", "Regenerate offline with `python -m src.literature_check_p49`.", ""])
    return "\n".join(lines)


def build(root=ROOT):
    references = json.loads((root / REFERENCES).read_text())
    p45 = json.loads((root / "data/p45_literature.json").read_text())
    result = build_report(references, load_crops(root / "data/crops.csv"), p45)
    write_json(root / "data/processed" / OUTPUT, result)
    (root / "docs" / DOCUMENT).write_text(render(result))


if __name__ == "__main__":
    build()
