"""Exact top-two score margins around the previously reported P16 tipping cells."""

import json
from pathlib import Path

import numpy as np

from src.optimizer import allowed_layers, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, preload, score_rotations
from src.stress_test import rotation_id, shifted_model


def before_cell(tip, temperatures, rains):
    """Select one monotone, adjacent predecessor; the reported tip is unchanged."""
    temp, rain = tip["temperature_change_c"], tip["rainfall_change_pct"]
    temp_step = min(b - a for a, b in zip(temperatures, temperatures[1:]))
    rain_step = min(b - a for a, b in zip(rains, rains[1:]))
    options = []
    if temp > 0:
        options.append((temp - temp_step, rain, 0))
    if rain != 0:
        options.append((temp, rain - np.sign(rain) * rain_step, 1))
    if not options:
        raise ValueError("A tipping cell must differ from unchanged weather")
    choice = max(options, key=lambda row: ((row[0] / temp_step) ** 2 + (row[1] / rain_step) ** 2,
                                           -row[2]))
    return {"temperature_change_c": float(choice[0]), "rainfall_change_pct": int(choice[1])}


def exact_top_two(model, weights, years):
    """Score baseline and every feasible rotation, collapsing whole-year cyclic duplicates."""
    layers = allowed_layers(model, years)
    rotations = (enumerate_canonical_rotations(layers, len(model.season_labels)) if all(len(layer) for layer in layers)
                 else np.empty((0, years * len(model.season_labels)), dtype=int))
    baseline = baseline_indices(model, years)
    _, base_scores, _ = score_rotations(model, baseline)
    base = {"id": rotation_id(baseline, len(model.season_labels)),
            "score": float(base_scores[0] @ weights), "is_baseline": True}
    candidates = [base]
    if len(rotations):
        _, scores, _ = score_rotations(model, rotations)
        objectives = scores @ weights
        unique = set()
        for index in np.argsort(-objectives, kind="stable"):
            identifier = rotation_id(rotations[index], len(model.season_labels))
            if identifier in unique:
                continue
            unique.add(identifier)
            candidates.append({"id": identifier, "score": float(objectives[index]), "is_baseline": False})
            if len(unique) == 2:
                break
    # The baseline may be one of the feasible rotations. Preserve its tag on an exact tie.
    distinct = {}
    for candidate in candidates:
        old = distinct.get(candidate["id"])
        if old is None or candidate["score"] > old["score"] or (candidate["score"] == old["score"] and candidate["is_baseline"]):
            distinct[candidate["id"]] = candidate
    top = sorted(distinct.values(), key=lambda row: (-row["score"], not row["is_baseline"], row["id"]))[:2]
    if len(top) < 2:
        return {"top": top[0] if top else None, "second": None, "gap": None,
                "feasible_count": int(len(rotations))}
    return {"top": top[0], "second": top[1], "gap": max(0., top[0]["score"] - top[1]["score"]),
            "feasible_count": int(len(rotations))}


def analyse(model, grid, presets, config):
    temperatures, rains = grid["temperature_changes_c"], grid["rainfall_changes_pct"]
    points = {}
    selected = {}
    for preset, entry in grid["presets"].items():
        tip = entry["tipping_point"]
        if not tip["found"]:
            selected[preset] = {"status": "no tipping in grid", "before": None, "after": None,
                                "near_tie": False, "sentence": "No top-strategy change occurs in this grid."}
            continue
        after = {key: tip["cell"][key] for key in ("temperature_change_c", "rainfall_change_pct")}
        before = before_cell(after, temperatures, rains)
        cells = {(row["temperature_change_c"], row["rainfall_change_pct"]): row for row in entry["cells"]}
        if cells[before["temperature_change_c"], before["rainfall_change_pct"]]["winner_id"] != tip["reference_winner_id"]:
            raise ValueError(f"Before cell already changed for {preset}")
        selected[preset] = {"status": "tip", "before_cell": before, "after_cell": after}
        points[tuple(before.values())] = before
        points[tuple(after.values())] = after
    weights = {name: np.array([value[metric] for metric in METRICS]) for name, value in presets.items()}
    measured = {}
    for point in points.values():
        shifted_model(model, point["temperature_change_c"], point["rainfall_change_pct"])
        measured[(point["temperature_change_c"], point["rainfall_change_pct"])] = {
            name: exact_top_two(model, vector, grid["horizon_years"]) for name, vector in weights.items()}
    for preset, record in selected.items():
        if record["status"] != "tip":
            continue
        before = record.pop("before_cell")
        after = record.pop("after_cell")
        first = measured[tuple(before.values())][preset]
        second = measured[tuple(after.values())][preset]
        record["before"] = {**before, **first}
        record["after"] = {**after, **second}
        tolerance = config["near_tie_gap"]
        record["near_tie_before"] = first["gap"] is not None and first["gap"] <= tolerance
        record["near_tie_after"] = second["gap"] is not None and second["gap"] <= tolerance
        record["near_tie"] = record["near_tie_before"] or record["near_tie_after"]
        record["sentence"] = (f"At {before['temperature_change_c']:+g} °C and {before['rainfall_change_pct']:+g}% rain, "
                              f"the top-two score gap is {first['gap']:.4f}; at "
                              f"{after['temperature_change_c']:+g} °C and {after['rainfall_change_pct']:+g}% rain, "
                              f"it is {second['gap']:.4f}.")
    return {"farm_id": grid["farm_id"], "label": "illustrative; validate locally",
            "grid_source": "data/processed/stress_test_<farm_id>.json; P16 grid, unchanged",
            "score_source": "src.scoring.score_rotations; config/weights_presets.json; cached NASA POWER climate",
            "tolerance": {"value": config["near_tie_gap"], "unit": "normalized weighted-score points",
                          "source": config["source"], "rule": config["near_tie_rule"]},
            "before_cell_rule": config["before_cell_rule"], "presets": selected}


def build(root=ROOT):
    root = Path(root)
    farms = json.loads((root / "config/farms.json").read_text())
    presets = json.loads((root / "config/weights_presets.json").read_text())["presets"]
    config = json.loads((root / "config/stress_margins.json").read_text())
    for farm in farms:
        farm_id = farm["farm_id"]
        grid = json.loads((root / "data/processed" / f"stress_test_{farm_id}.json").read_text())
        result = analyse(preload(farm, root=root), grid, presets, config)
        write_json(root / "data/processed" / f"stress_margins_{farm_id}.json", result)
        print(farm_id, {name: entry["near_tie"] for name, entry in result["presets"].items()}, flush=True)


if __name__ == "__main__":
    build()
