"""Generate the P35 scoring literature comparison from the audit and live catalog."""

import json
from pathlib import Path

from src.crops import load_crops
from src.precompute_cache import write_json

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = "data/p35_literature.json"
OUTPUT = "literature_check_p35.json"
INSIDE = "inside range"
OUTSIDE = "outside range"
UNAVAILABLE = "no usable source"
FIELDS = {
    "n_credit_kg_ha": ("Nitrogen credit", "kg N/ha"),
    "n_demand_kg_ha": ("Nitrogen demand proxy", "kg N/ha"),
    "water_need_mm": ("Seasonal crop water demand", "mm"),
    "season_length_days": ("Duration of crop water window", "days"),
    "cover_score": ("Erosion protection index", "index"),
    "disease_family": ("Disease family label", "category"),
}
KS_TRANSITIONS = {
    "ks_soy_wheat": ("soybean", ("winter_wheat",), "K-State soybean → winter wheat"),
    "ks_soy_warm_cereal": ("soybean", ("maize", "sorghum"), "K-State soybean → maize or sorghum"),
    "ks_fallow_wheat_no_profile": ("fallow", ("winter_wheat",), "K-State fallow → winter wheat without profile N test"),
    "ks_sorghum_wheat": ("sorghum", ("winter_wheat",), "K-State sorghum → winter wheat"),
    "ks_sunflower_wheat": ("sunflower", ("winter_wheat",), "K-State sunflower → winter wheat"),
}


def compare_value(value, bounds):
    if bounds is None:
        return UNAVAILABLE
    low, high = bounds
    if low > high:
        raise ValueError("Literature bounds must be ordered")
    return INSIDE if low <= value <= high else OUTSIDE


def show_span(bounds):
    low, high = bounds
    if low == high:
        return f"{low:g}"
    return f"{low:g} to {high:g}"


def converted_n_bounds(values, refs):
    # The catalog stores these US crop credits in whole kg N/ha.
    factor = refs["conversion"]["lb_ac_to_kg_ha"]
    return tuple(round(value * factor) for value in values)


def audit_row(check, item, value, reference, status, rationale, source=None):
    return {"Check": check, "Crop or contrast": item, "Model": value, "Published reference": reference,
            "Finding": status, "Interpretation": rationale, "source": source}


def crop_rows(crops, refs):
    ranges = refs["parameter_ranges"]
    rows = []
    for crop_id, crop in crops.items():
        for field, (check, unit) in FIELDS.items():
            value = crop[field]
            displayed = value if isinstance(value, str) else f"{value:g} {unit}"
            source = None
            reference, rationale = "—", "No comparable crop-specific numeric benchmark was identified."
            finding = UNAVAILABLE
            if crop_id == "fallow":
                rationale = ("Unplanted model slot. The zeros describe the scoring convention, "
                             "which omits actual soil evaporation, cover and residual N.")
            elif field == "disease_family":
                family, source = refs["families"][crop_id]
                reference = family
                finding = INSIDE if family == value else OUTSIDE
                rationale = "Categorical taxonomic match. Host range and risk magnitude remain separate."
            elif field == "n_demand_kg_ha":
                source = "msu_n"
                reference = "Site- and yield-dependent soil/fertilizer guidance"
                rationale = "A fixed demand proxy cannot be calibrated with applied fertilizer rates or soil-test targets."
            elif field == "cover_score":
                source = "rusle"
                reference = "Crop-stage and management dependent"
                rationale = "A fixed species index has no calibrated mapping to canopy cover, residue cover or RUSLE C."
            elif (bounds := ranges.get(field, {}).get(crop_id)) is not None:
                low, high, source = bounds
                if source == "umn_credit":
                    a, b = converted_n_bounds((low, high), refs)
                    reference = f"{show_span((a, b))} {unit} ({low:g} lb N/acre, rounded conversion)"
                    low, high = a, b
                    rationale = "First-year corn reference only. It does not quantify benefits for other successors."
                else:
                    reference = f"{show_span((low, high))} {unit}"
                    rationale = "Reference comparison. Local variety, season and management can change the value."
                finding = compare_value(value, (low, high))
                if (crop_id, field) == ("winter_wheat", "season_length_days"):
                    rationale = "Span of three regional winter-wheat examples under different dormancy conditions."
                elif source == "patil":
                    rationale = "Two Bangalore seasons of measured actual ET. Potential local demand remains uncertain."
                elif source == "rao":
                    rationale = "Sole pigeonpea before maize in one Hyderabad cycle. Equivalence used maize total dry matter."
                elif source == "dalal":
                    rationale = "Queensland chickpea before wheat. Six estimable years, two unavailable. Largest value followed frost damage."
            elif field == "n_credit_kg_ha" and crop_id in ("green_gram", "cowpea"):
                source = "lengwati"
                reference = "About 20 kg N/ha per crop before maize"
                rationale = ("Positive direction agrees. The trial provides an approximate treatment magnitude "
                             "without species-specific bounds suitable for classifying the catalog value.")
            elif field == "n_credit_kg_ha" and crop_id == "cereal_rye_cover":
                source = "sare"
                reference = "N immobilization after mature rye reported"
                rationale = "The model sets carryover to zero. The source gives no single numeric carryover value."
            elif crop_id == "cereal_rye_cover" and field in ("water_need_mm", "season_length_days"):
                source = "qi" if field == "water_need_mm" else "sare"
                reference = "May ET 1.9 to 3.1 mm/day" if field == "water_need_mm" else "Timing varies with termination"
                rationale = "The study does not give a comparable total for the catalog's cover window."
            rows.append(audit_row(check, crop["display_name"], displayed, reference, finding, rationale, source))
    return rows


def effect_rows(crops, refs, policy):
    effects = refs["effects"]
    rows = []
    for key, (crop, _, label) in KS_TRANSITIONS.items():
        evidence = effects[key]
        bounds = converted_n_bounds(evidence["lb_ac"], refs)
        value = crops[crop]["n_credit_kg_ha"]
        rows.append(audit_row("Predecessor N effect", label, f"{value:+g} kg N/ha",
                              f"{show_span(bounds)} kg N/ha ({show_span(evidence['lb_ac'])} lb N/acre)",
                              compare_value(value, bounds),
                              "Signed change in N credit. Positive means less fertilizer N in this Kansas guidance. "
                              "The example is conditional on the named transition.", evidence["source"]))
    # This additional regional comparator is deliberate. FAO's broad range is separately listed.
    texas = effects["sorghum_early_water"]
    mm = tuple(v * refs["conversion"]["inch_to_mm"] for v in texas["inch"])
    demand = crops["sorghum"]["water_need_mm"]
    rows.append(audit_row("Water demand, early grain sorghum", "Texas, 90–105 day group",
                          f"{demand:g} mm", f"{show_span(mm)} mm (10–15 inches)", compare_value(demand, mm),
                          "The catalogue is at the FAO lower bound but above this maturity-specific Texas range.",
                          texas["source"]))

    pa = effects["legume_pa_water"]
    pa_delta = [v - pa["fallow_mm"] for v in pa["legume_mm"]]
    rows.append(audit_row("Following-crop initial soil water", "Legume before winter wheat vs fallow, Garden City",
                          "0 mm change at each window reset", f"{show_span(pa_delta)} mm in 0–1.8 m",
                          compare_value(0, pa_delta),
                          "Plant-available water at wheat planting was lower after sole legume crops. "
                          "The model resets its shallower bucket and cannot represent this carryover.",
                          pa["source"]))

    erosion = effects["cover_erosion"]
    protection = 100 * (crops["cereal_rye_cover"]["cover_score"] - crops["fallow"]["cover_score"])
    bounds = erosion["by_control_tillage_pct"]
    rows.append(audit_row("Erosion direction and relative effect", "Rye cover versus bare at equal slope and rain",
                          f"{protection:g}% lower erosion index",
                          f"{erosion['mean_pct']}% mean soil-loss reduction, {show_span(bounds)}% across control tillage",
                          compare_value(protection, bounds),
                          "Magnitude is within the broad winter-cover benchmark. The study pooled cover types and sites. "
                          "Its percentages do not calibrate the rye index or estimate site soil loss.", erosion["source"]))

    scf = effects["palouse_scf"]
    loss_ratio_change = (scf["pea_wheat_no_till"] / scf["fallow_wheat"] - 1) * 100
    rows.append(audit_row("Predecessor protection after planting", "Same winter-wheat slot after pea or fallow",
                          "0% change in wheat erosion index at equal weather",
                          f"RUSLE surface-cover subfactor {scf['fallow_wheat']:g} → {scf['pea_wheat_no_till']:g} "
                          f"({loss_ratio_change:+.1f}%)", UNAVAILABLE,
                          "The treatments also change tillage. This demonstrates a missing residue mechanism. "
                          "It cannot isolate a pea-only effect or set a numeric scoring parameter.", scf["source"]))

    spot = effects["tan_spot"]
    decrease = [a - b for a, b in zip(spot["continuous_no_till_pct"], spot["rotation_no_till_pct"], strict=True)]
    equal = crops["sorghum"]["disease_family"] == crops["winter_wheat"]["disease_family"]
    weight = policy["same_family_risk_share"]
    modeled = weight * (1 - equal)
    rows.append(audit_row("Disease direction and magnitude", "Sorghum → wheat versus wheat → wheat",
                          f"{modeled:g} improvement in per-transition risk index",
                          f"{min(decrease):.2f} to {max(decrease):.2f} percentage points less tan spot",
                          UNAVAILABLE, "The model charges the same immediately preceding Poaceae penalty in both cases. "
                          "The no-till field comparison shows a reduction. Index points cannot be converted to severity.",
                          spot["source"]))
    rows.append(audit_row("Policy penalties", "Same-family transition and bare slot",
                          f"{weight:g} and {policy['bare_slot_risk_share']:g} index points per unit share",
                          "Different diseases require different break lengths, e.g. 1 to 5 years or longer",
                          UNAVAILABLE, "The equal coefficients are a design choice. The bare penalty mixes protection "
                          "with disease risk, and disease breaks cannot be calibrated by family alone.", "sask"))
    return rows


def build_rows(root=ROOT):
    refs = json.loads((root / REFERENCES).read_text())
    crops = load_crops(root / "data/crops.csv")
    policy = json.loads((root / "config/scoring.json").read_text())
    return [*crop_rows(crops, refs), *effect_rows(crops, refs, policy)], refs["sources"]


def table_markdown(rows, sources):
    columns = ("Check", "Crop or contrast", "Model", "Published reference", "Finding", "Interpretation")

    def line(values):
        return "| " + " | ".join(value.replace("|", r"\|") for value in values) + " |"

    def row_line(row):
        source = sources.get(row["source"])
        citation = f" [{source['title']}, {source['locator']}]({source['url']})" if source else ""
        return line([*(row[key] for key in columns[:-1]), row["Interpretation"] + citation])

    return "\n".join([line(columns), line(["---"] * len(columns)), *(row_line(row) for row in rows)])


if __name__ == "__main__":
    rows, sources = build_rows()
    write_json(ROOT / "data/processed" / OUTPUT,
               {"label": "illustrative, validate locally", "rows": rows, "sources": sources})
