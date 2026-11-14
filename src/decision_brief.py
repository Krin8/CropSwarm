"""Render reference farm briefs entirely from saved CropSwarm outputs."""

from datetime import date
from itertools import islice
import json
from pathlib import Path
import subprocess

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.scoring import METRICS, ROOT
from src.sensitivity import check_first

BRIEFS = ROOT / "docs/briefs"
REFERENCE_FILES = ("assessment", "strategies", "sensitivity", "robust_stability", "context", "uncertainty", "validity")
TEMPLATE = Environment(loader=FileSystemLoader(Path(__file__).with_name("templates")),
                       autoescape=select_autoescape()).get_template("decision_brief.html")
METRIC_LABELS = ("Water", "Nitrogen", "Erosion", "Climate fit", "Income index", "Risk")
ROBUST_LABELS = {"expected": "Expected score", "conditional_cvar": "Feasible-only CVaR",
                 "minimax_regret": "Minimax regret"}


def brief_release(root=ROOT):
    path = root / "docs/briefs/release.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def repository_version(root=ROOT):
    """Use local Git when available, then the provenance of the bundled release."""
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel", "HEAD"], cwd=root,
                                capture_output=True, text=True, check=True, timeout=2)
        directory, commit = result.stdout.splitlines()
        if Path(directory).resolve() == root.resolve():
            return commit
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return brief_release(root).get("source_commit", "Unavailable")


def brief_filename(farm_id, preset):
    return f"{farm_id}_{preset}"


def reference_inputs(load, farm_id):
    return (load(farm_id, prefix) for prefix in REFERENCE_FILES)


def rotation_text(pick):
    crops = iter(pick["crop_names"])
    years = [" → ".join(islice(crops, len(year))) for year in pick["crop_ids"]]
    if len(years) > 1 and len(set(years)) == 1:
        return f"{years[0]} × {len(years)} years"
    return " / ".join(years)


def climate_summary(assessment):
    metrics = assessment["metrics"]
    regimes = metrics["annual_climate_regimes"]["value"]
    year_range = f"{min(regimes)}–{max(regimes)}" if regimes else "Years unavailable"
    dry = metrics["longest_observed_dry_spell"]["value"]
    cv = metrics["rainfall_cv"]["value"]
    vegetation = metrics["ndvi_peaks"]["value"]
    count = sum(entry["good_composites"] for entry in vegetation.values())
    return [
        ("Weather years", year_range, "NASA POWER"),
        ("Longest dry spell", f"{dry} days" if dry is not None else "Unavailable", "NASA POWER"),
        ("Annual rainfall variability (CV)", f"{cv:.2f}" if cv is not None else "Unavailable", "NASA POWER"),
        ("Quality-screened NDVI composites", f"{count:,}" if vegetation else "Unavailable", "NASA Terra MODIS"),
    ]


def render_brief(farm, preset, assessment, comparison, sensitivity, robust, context, uncertainty, validity, *,
                 generated_on: date, commit: str):
    """Keep saved shortlist order and derive display gaps without rerunning the model."""
    historical = uncertainty["scenarios"]["historical"]["strategies"]
    entries = comparison["strategies"]
    rows = []
    for entry in entries:
        key = entry["strategy_id"]
        outcomes = historical[key]
        water = outcomes["metrics"]["water"]
        rows.append({
            "label": "Baseline" if key == "baseline" else key.replace("_", " ").capitalize(),
            "rotation": rotation_text(entry), "score": entry["objectives"][preset],
            "metrics": [(entry["metrics"][metric]["score"], entry["metrics"][metric]["evidence"]["label"])
                        for metric in METRICS],
            "evidence": entry["evidence_label"],
            "wins": outcomes["wins_pct"][preset], "water": (water["p10"], water["p90"]),
            "flags": [flag.replace("_", " ") for flag in entry["flags"]],
        })

    top = sorted(rows, key=lambda row: -row["score"])[:2]
    gap = top[0]["score"] - top[1]["score"] if len(top) > 1 else None
    tolerance = sensitivity["design"]["near_tie_gap"]
    checks = check_first(sensitivity["presets"][preset]["ranking"])

    focus = robust["presets"][preset]
    counts = robust["design"]["draw_counts"]
    count = max(counts)
    picks = []
    for objective, name in ROBUST_LABELS.items():
        case = focus["draw_counts"][str(count)]["objectives"][objective]
        pick = case["top"][0] if case["top"] else None
        if pick:
            picks.append({"label": name, "rotation": rotation_text(pick), "evidence": pick["evidence_label"],
                          "feasible": pick["feasible_draws"], "share": pick["feasible_share"],
                          "value": pick[objective], "same": focus["stability"][objective]["same_pick"], "near_tie": case["near_tie"]})

    site_sources = []
    for source in validity["sources"]:
        label, _, url = source.partition(" | ")
        if ("Cropland Data Layer" in label or "MCD12Q1" in label) and url.startswith("https://"):
            site_sources.append((label, url))
    soil_source = context["soil"]["available_water_mm_0_30"]["source"]
    site_notes = validity["flags"] if entries[0]["flags"] else assessment["validation_flags"]
    return TEMPLATE.render(
        farm=farm, preset=preset.replace("_", " ").capitalize(), commit=commit, date=generated_on.isoformat(),
        climate=climate_summary(assessment), rows=rows, metric_labels=METRIC_LABELS, top=top, gap=gap,
        tolerance=tolerance, near_tie=gap is not None and gap <= tolerance,
        checks=checks, picks=picks, count=count, counts=", ".join(map(str, counts)),
        robust_tolerance=robust["precision_tolerance"],
        site_notes=site_notes[:1],
        power=assessment["metrics"]["rainfall_cv"]["source"].rsplit(" | ", 1)[-1],
        modis=assessment["metrics"]["ndvi_peaks"]["source"].rsplit(" | ", 1)[-1],
        terrain_source=context["terrain"]["mean_slope_pct"]["source"],
        soil_source=soil_source,
        site_sources=site_sources,
        soil_label="USDA SSURGO" if "SSURGO" in soil_source else "ISRIC SoilGrids",
        distinct_threshold=comparison["selection"]["difference_threshold"],
    )
