"""Offline uniform-weather sweep with exact search at every grid cell."""

import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

from src.optimizer import allowed_layers, canonical_cycle, enumerate_canonical_rotations
from src.precompute_cache import write_json
from src.scoring import METRICS, ROOT, baseline_indices, historical_metrics, preload, score_rotations

POWER = "NASA POWER cached historical daily climate; uniform illustrative shifts"


def shifted_model(model, temperature_change_c, rainfall_change_pct):
    """Recompute score additions and the existing median-water hard screen."""
    additions = model.additions.copy()
    suitable = np.zeros_like(model.suitable)
    rain_factor = 1 + rainfall_change_pct / 100
    if rain_factor < 0:
        raise ValueError("Rainfall factor must be nonnegative")
    for slot in range(len(model.season_labels)):
        for index, crop_id in enumerate(model.ids):
            windows = model.histories[slot, index]
            if not windows:
                continue
            metrics = historical_metrics(windows, model.crops[crop_id], model.storage, model.slope,
                                         model.farm["irrigation"]["supply_fraction"], model.policy,
                                         heat_shift=temperature_change_c, rain_factor=rain_factor)
            additions[slot, index] = metrics.mean(axis=0)
            suitable[slot, index] = (model.planting_windows[slot, index] and
                                     np.median(metrics[:, 1]) <= model.policy["max_median_unmet_water_fraction"])
    model.additions = additions
    model.suitable = suitable
    return model


def rotation_id(sequence, slots):
    key = ",".join(str(value) for value in canonical_cycle(sequence, slots))
    return "rotation_" + hashlib.sha256(key.encode()).hexdigest()[:12]


def rotation_record(model, sequence, *, canonical=True):
    slots = len(model.season_labels)
    if canonical:
        sequence = canonical_cycle(sequence, slots)
    ids = [model.ids[int(index)] for index in sequence]
    return {"crop_ids": [ids[i:i + slots] for i in range(0, len(ids), slots)],
            "crop_names": [model.crops[crop_id]["display_name"] for crop_id in ids]}


def exact_cell(model, presets, years):
    """Enumerate every currently feasible rotation; keep baseline even if it has flags."""
    layers = allowed_layers(model, years)
    if any(not len(layer) for layer in layers):
        rotations = np.empty((0, years * len(model.season_labels)), dtype=int)
    else:
        rotations = enumerate_canonical_rotations(layers, len(model.season_labels))
    baseline = baseline_indices(model, years)
    _, baseline_scores, baseline_flags = score_rotations(model, baseline)
    flags = {key: np.flatnonzero(value[0]).tolist() for key, value in baseline_flags.items() if value.any()}
    weights = {name: np.array([values[metric] for metric in METRICS], dtype=float)
               for name, values in presets.items()}
    if len(rotations):
        _, scores, _ = score_rotations(model, rotations)
    else:
        scores = np.empty((0, len(METRICS)))
    results = {}
    slots = len(model.season_labels)
    for preset, vector in weights.items():
        baseline_score = float(baseline_scores[0] @ vector)
        if len(rotations):
            objectives = scores @ vector
            # The canonical enumerator is lexicographically ordered; first exact max wins.
            best_index = int(np.argmax(objectives))
            exact_score = float(objectives[best_index])
            best = rotations[best_index]
            winner_is_baseline = baseline_score >= exact_score
            winner = baseline if winner_is_baseline else best
            exact_id = rotation_id(best, slots)
        else:
            exact_score = None
            winner = baseline
            winner_is_baseline = True
            exact_id = None
        results[preset] = {"winner_id": "baseline" if winner_is_baseline else rotation_id(winner, slots),
                           "winner": rotation_record(model, winner, canonical=not winner_is_baseline),
                           "baseline_score": baseline_score, "exact_optimum_score": exact_score,
                           "exact_optimum_id": exact_id, "exact_optimum": rotation_record(model, best) if len(rotations) else None,
                           "feasible_count": int(len(rotations)), "baseline_flags": flags,
                           "status": "complete" if len(rotations) else "no feasible alternative"}
    return results


def tipping_point(cells, temperatures, rainfall_changes):
    """Find nearest change in normalized grid-step distance, excluding the reference cell."""
    reference = next(cell for cell in cells if cell["temperature_change_c"] == 0 and
                     cell["rainfall_change_pct"] == 0)
    original = reference["winner_id"]
    temp_step = min(b-a for a, b in zip(temperatures, temperatures[1:]))
    rain_step = min(b-a for a, b in zip(rainfall_changes, rainfall_changes[1:]))
    changed = [cell for cell in cells if cell["winner_id"] != original and cell["status"] == "complete"]
    if not changed:
        return {"found": False, "reference_winner_id": original, "cell": None,
                "sentence": "No top-strategy change occurs within the tested temperature and rainfall grid."}
    key = lambda cell: (((cell["temperature_change_c"] / temp_step) ** 2 +
                         (cell["rainfall_change_pct"] / rain_step) ** 2),
                        cell["temperature_change_c"], abs(cell["rainfall_change_pct"]),
                        cell["rainfall_change_pct"])
    point = min(changed, key=key)
    temp = point["temperature_change_c"]
    rain = point["rainfall_change_pct"]
    return {"found": True, "reference_winner_id": original,
            "cell": {"temperature_change_c": temp, "rainfall_change_pct": rain,
                     "winner_id": point["winner_id"]},
            "sentence": f"The top strategy first changes at +{temp:g} °C and {rain:+g}% rainfall "
                        "(nearest grid cell in normalized steps from unchanged historical weather)."}


def cycle_label(record):
    years = [" then ".join(row) for row in record["crop_ids"]]
    return years[0] + " (repeated annually)" if len(set(years)) == 1 else " → ".join(years)


def sweep(model, presets, config, years):
    temperatures = config["temperature_changes_c"]
    rains = config["rainfall_changes_pct"]
    if 0 not in temperatures or 0 not in rains:
        raise ValueError("The stress grid must contain unchanged historical weather")
    if temperatures != sorted(set(temperatures)) or rains != sorted(set(rains)):
        raise ValueError("Stress grid axes must be sorted and unique")
    grids = {name: [] for name in presets}
    rotations = {}
    for temp in temperatures:
        for rain in rains:
            shifted_model(model, temp, rain)
            cell = exact_cell(model, presets, years)
            for name, result in cell.items():
                for key in ("winner_id", "exact_optimum_id"):
                    identifier = result[key]
                    if identifier and identifier != "baseline":
                        rotations[identifier] = result["winner" if key == "winner_id" else "exact_optimum"]
                grids[name].append({"temperature_change_c": temp, "rainfall_change_pct": rain,
                                    **{key: value for key, value in result.items() if key not in ("winner", "exact_optimum")}})
    base_rotation = rotation_record(model, baseline_indices(model, years), canonical=False)
    rotations["baseline"] = base_rotation
    out = {name: {"cells": cells, "tipping_point": tipping_point(cells, temperatures, rains),
                  "reference_winner_id": next(c["winner_id"] for c in cells
                                              if c["temperature_change_c"] == 0 and c["rainfall_change_pct"] == 0)}
           for name, cells in grids.items()}
    for entry in out.values():
        tip = entry["tipping_point"]
        if tip["found"]:
            before = cycle_label(rotations[tip["reference_winner_id"]])
            after = cycle_label(rotations[tip["cell"]["winner_id"]])
            tip["sentence"] += f" The top rotation changes from {before} to {after}."
    return {"farm_id": model.farm["farm_id"], "label": "illustrative; validate locally",
            "climate_source": POWER, "grid_source": config["source"],
            "temperature_changes_c": temperatures, "rainfall_changes_pct": rains,
            "distance_rule": config["distance_rule"], "tie_rule": config["tie_rule"],
            "horizon_years": years,
            "rotation_catalog": rotations, "presets": out,
            "caveat": "Uniform shifts to cached historical daily weather are a sensitivity stress test, not a climate projection. Crop calendars and soil storage stay fixed. Crop and irrigation inputs are illustrative; validate locally."}


def winner_map_svg(result):
    """Standalone four-preset map; app renders the same grid interactively."""
    colors = ("#397b64", "#af6c38", "#557ab5", "#a05e84", "#727548", "#7e69a8", "#b65d54", "#4d8589")
    temperatures = result["temperature_changes_c"]
    rains = result["rainfall_changes_pct"]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1010" viewBox="0 0 1000 1010">',
             '<rect width="1000" height="1010" fill="white"/>',
             f'<text x="30" y="35" font-family="sans-serif" font-size="20">{escape(result["farm_id"])} · exact-search winner maps</text>',
             '<text x="30" y="57" font-family="sans-serif" font-size="12">Uniform shifts to NASA POWER historical weather · design choice, not a climate projection</text>']
    for panel, (preset, entry) in enumerate(result["presets"].items()):
        ox = 30 + (panel % 2) * 490
        oy = 85 + (panel // 2) * 445
        cells = {(cell["temperature_change_c"], cell["rainfall_change_pct"]): cell
                 for cell in entry["cells"]}
        identifiers = list(dict.fromkeys(cell["winner_id"] for cell in entry["cells"]))
        parts.extend([f'<rect x="{ox}" y="{oy}" width="465" height="420" fill="none" stroke="#bbb"/>',
                      f'<text x="{ox+15}" y="{oy+28}" font-family="sans-serif" font-size="16">{escape(preset.replace("_", " ").title())}</text>'])
        for row, temp in enumerate(reversed(temperatures)):
            y = oy + 62 + row * 39
            parts.append(f'<text x="{ox+10}" y="{y+23}" font-family="sans-serif" font-size="11">+{temp:g}°</text>')
            for col, rain in enumerate(rains):
                x = ox + 48 + col * 44
                identifier = cells[temp, rain]["winner_id"]
                index = identifiers.index(identifier)
                parts.extend([f'<rect x="{x}" y="{y}" width="42" height="37" fill="{colors[index % len(colors)]}" '
                              f'stroke="{"#111" if temp == 0 and rain == 0 else "#fff"}" '
                              f'stroke-width="{"2" if temp == 0 and rain == 0 else "1"}"/>',
                              f'<text x="{x+11}" y="{y+24}" font-family="sans-serif" font-size="12" fill="white">S{index+1}</text>'])
        for col, rain in enumerate(rains):
            parts.append(f'<text x="{ox+48+col*44}" y="{oy+353}" font-family="sans-serif" font-size="11">{rain:+g}%</text>')
        parts.append(f'<text x="{ox+50}" y="{oy+381}" font-family="sans-serif" font-size="12">Rainfall change · temperature rises upward</text>')
        for index, identifier in enumerate(identifiers):
            label = cycle_label(result["rotation_catalog"][identifier])
            short = label[:25] + "…" if len(label) > 25 else label
            y = oy + 70 + index * 35
            parts.extend([f'<rect x="{ox+280}" y="{y-11}" width="14" height="14" fill="{colors[index % len(colors)]}"/>',
                          f'<text x="{ox+300}" y="{y}" font-family="sans-serif" font-size="10">S{index+1}: {escape(short)}</text>'])
        parts.append(f'<text x="{ox+15}" y="{oy+409}" font-family="sans-serif" font-size="11">'
                     f'{"No tip in grid" if not entry["tipping_point"]["found"] else "Outlined cell: unchanged weather"}</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def build(root=ROOT):
    root = Path(root)
    farms = json.loads((root / "config/farms.json").read_text())
    presets = json.loads((root / "config/weights_presets.json").read_text())["presets"]
    config = json.loads((root / "config/stress_test.json").read_text())
    optimizer = json.loads((root / "config/optimizer.json").read_text())
    for farm in farms:
        model = preload(farm, root=root)
        result = sweep(model, presets, config, optimizer["default_years"])
        write_json(root / "data/processed" / f"stress_test_{farm['farm_id']}.json", result)
        charts = root / "docs/charts"
        charts.mkdir(parents=True, exist_ok=True)
        (charts / f"stress_{farm['farm_id']}.svg").write_text(winner_map_svg(result))
        print(farm["farm_id"], {name: (entry["tipping_point"]["cell"] if entry["tipping_point"]["found"] else None)
                                for name, entry in result["presets"].items()}, flush=True)


if __name__ == "__main__":
    build()
