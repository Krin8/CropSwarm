"""Explain exact/near ties without changing P16 scoring or winner grids."""

import json
from pathlib import Path

import numpy as np

from src.optimizer import allowed_layers, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, metric_rows, preload, score_rotations
from src.stress_test import rotation_id, rotation_record, shifted_model

CLIMATE_RESPONSIVE = frozenset({"water", "erosion", "climate_fit"})
CLIMATE_FIXED = frozenset(METRICS) - CLIMATE_RESPONSIVE


def alternative_groups(alternatives, threshold):
    """Compare the four displayed, normalized score vectors using complete-link groups."""
    ids = [row["strategy_id"] for row in alternatives]
    vectors = {row["strategy_id"]: np.array([row["metrics"][metric]["score"] for metric in METRICS])
               for row in alternatives}
    pairs = []
    for i, first in enumerate(ids):
        for second in ids[i + 1:]:
            deltas = np.abs(vectors[first] - vectors[second])
            pairs.append({"first": first, "second": second,
                          "max_difference": float(deltas.max()), "near_duplicate": bool(deltas.max() <= threshold),
                          "metric_differences": {metric: float(value) for metric, value in zip(METRICS, deltas, strict=True)}})
    near = {(p["first"], p["second"]): p["near_duplicate"] for p in pairs}
    groups = []
    for identifier in ids:
        target = next((group for group in groups if all(
            near.get((member, identifier), near.get((identifier, member), False)) for member in group)), None)
        if target is None:
            groups.append([identifier])
        else:
            target.append(identifier)
    return {"displayed_alternatives": len(ids), "meaningfully_different_groups": len(groups),
            "groups": groups, "pairs": pairs}


def detailed_top_two(model, weights, years):
    """Return metric vectors for the top two distinct-cycle strategies, baseline included."""
    layers = allowed_layers(model, years)
    rotations = (enumerate_canonical_rotations(layers, len(model.season_labels)) if all(len(layer) for layer in layers)
                 else np.empty((0, years * len(model.season_labels)), dtype=int))
    baseline = baseline_indices(model, years)
    base_raw, base_scores, _ = score_rotations(model, baseline)
    slots = len(model.season_labels)

    def detail(sequence, raw, scores, is_baseline):
        return {"id": rotation_id(sequence, slots), "is_baseline": is_baseline,
                "rotation": rotation_record(model, sequence, canonical=not is_baseline),
                "weighted_score": float(scores @ weights), "metrics": metric_rows(raw, scores)}

    candidates = [detail(baseline, base_raw[0], base_scores[0], True)]
    if len(rotations):
        raw, scores, _ = score_rotations(model, rotations)
        order = np.argsort(-(scores @ weights), kind="stable")
        seen = set()
        for index in order:
            identifier = rotation_id(rotations[index], slots)
            if identifier in seen:
                continue
            seen.add(identifier)
            candidates.append(detail(rotations[index], raw[index], scores[index], False))
            if len(seen) == 2:
                break
    distinct = {}
    for candidate in candidates:
        old = distinct.get(candidate["id"])
        if old is None or candidate["weighted_score"] > old["weighted_score"] or (
                candidate["weighted_score"] == old["weighted_score"] and candidate["is_baseline"]):
            distinct[candidate["id"]] = candidate
    return sorted(distinct.values(), key=lambda row: (-row["weighted_score"], not row["is_baseline"], row["id"]))[:2]


def explain_pair(pair, weights, exact_tolerance):
    first, second = pair
    differences = {}
    for metric, weight in zip(METRICS, weights, strict=True):
        one, two = first["metrics"][metric], second["metrics"][metric]
        delta = one["score"] - two["score"]
        differences[metric] = {"top_score": one["score"], "second_score": two["score"],
                               "score_difference": delta, "weighted_contribution": float(weight * delta),
                               "identical": abs(delta) <= exact_tolerance,
                               "responds_to_uniform_climate_shift": metric in CLIMATE_RESPONSIVE,
                               "source": one["source"]}
    same_crops = sorted(c for year in first["rotation"]["crop_ids"] for c in year) == sorted(
        c for year in second["rotation"]["crop_ids"] for c in year)
    identical_vector = all(row["identical"] for row in differences.values())
    gap = first["weighted_score"] - second["weighted_score"]
    if identical_vector and same_crops:
        cause = "crop order has the same modeled metric vector"
    elif identical_vector:
        cause = "different crop mixes have the same modeled metric vector"
    else:
        cause = "different metric scores nearly balance under preset weights"
    return {"top": first, "second": second, "gap": gap,
            "metric_differences": differences,
            "identical_metrics": [metric for metric, row in differences.items() if row["identical"]],
            "different_metrics": [metric for metric, row in differences.items() if not row["identical"]],
            "same_crop_multiset": same_crops, "cause": cause,
            "climate_fixed_metrics": sorted(CLIMATE_FIXED), "bug_or_rounding": False}


def analyse(model, grid, margins, strategies, presets, config):
    points = {}
    for preset, entry in margins["presets"].items():
        if entry["status"] != "tip" or not entry["near_tie"]:
            continue
        for side in ("before", "after"):
            row = entry[side]
            points[row["temperature_change_c"], row["rainfall_change_pct"]] = None
    weights = {name: np.array([preset[metric] for metric in METRICS]) for name, preset in presets.items()}
    examined = {}
    for temperature, rain in points:
        shifted_model(model, temperature, rain)
        examined[temperature, rain] = {
            preset: explain_pair(detailed_top_two(model, vector, grid["horizon_years"]), vector,
                                 config["exact_metric_tolerance"])
            for preset, vector in weights.items()}
    findings = {}
    for preset, entry in margins["presets"].items():
        if entry["status"] != "tip" or not entry["near_tie"]:
            findings[preset] = {"status": entry["status"], "changed_cells": sum(
                cell["winner_id"] != grid["presets"][preset]["reference_winner_id"]
                for cell in grid["presets"][preset]["cells"]), "grid_cells": len(grid["presets"][preset]["cells"])}
            continue
        pairs = {}
        for side in ("before", "after"):
            row = entry[side]
            pairs[side] = {"temperature_change_c": row["temperature_change_c"],
                           "rainfall_change_pct": row["rainfall_change_pct"],
                           **examined[row["temperature_change_c"], row["rainfall_change_pct"]][preset]}
            if not np.isclose(pairs[side]["gap"], row["gap"], atol=1e-12, rtol=0):
                raise ValueError(f"P16b margin mismatch at {preset} {side}")
        cells = grid["presets"][preset]["cells"]
        findings[preset] = {"status": "near tie", "changed_cells": sum(
            cell["winner_id"] != grid["presets"][preset]["reference_winner_id"] for cell in cells),
            "grid_cells": len(cells), "before": pairs["before"], "after": pairs["after"]}
    alternative = alternative_groups(strategies["strategies"][1:], config["alternative_max_metric_difference"])
    return {"farm_id": grid["farm_id"], "label": "illustrative; validate locally",
            "grid_source": "data/processed/stress_test_<farm_id>.json; unchanged P16 grid",
            "margin_source": "data/processed/stress_margins_<farm_id>.json; P16b",
            "metric_source": "src.scoring.score_rotations and data/crops.csv; source tags on each metric",
            "tie_break_rule": grid["tie_rule"] + "; whole-year cyclic shifts share a strategy label",
            "alternative_difference": {"threshold": config["alternative_max_metric_difference"],
                                       "source": config["source"], "rule": config["rule"]},
            "exact_metric_tolerance": {"value": config["exact_metric_tolerance"],
                                       "source": config["exact_metric_tolerance_source"]},
            "alternatives": alternative, "presets": findings,
            "interpretation": "Climate-fixed nitrogen, income and family/cover risk components do not change under uniform weather shifts for a fixed rotation. Water, erosion and climate-fit can change. Equal weighted scores may still describe different rotations. This is a modeled robustness check, not a climate projection."}


def build(root=ROOT):
    root = Path(root)
    farms = json.loads((root / "config/farms.json").read_text())
    presets = json.loads((root / "config/weights_presets.json").read_text())["presets"]
    config = json.loads((root / "config/tie_diagnosis.json").read_text())
    for farm in farms:
        farm_id = farm["farm_id"]
        processed = root / "data/processed"
        grid = json.loads((processed / f"stress_test_{farm_id}.json").read_text())
        margins = json.loads((processed / f"stress_margins_{farm_id}.json").read_text())
        strategies = json.loads((processed / f"strategies_{farm_id}.json").read_text())
        result = analyse(preload(farm, root=root), grid, margins, strategies, presets, config)
        write_json(processed / f"tie_diagnosis_{farm_id}.json", result)
        print(farm_id, result["alternatives"]["meaningfully_different_groups"],
              {name: row["changed_cells"] for name, row in result["presets"].items()}, flush=True)


if __name__ == "__main__":
    build()
