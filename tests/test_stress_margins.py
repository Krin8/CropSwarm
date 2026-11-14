import json

import numpy as np

from src.optimizer import allowed_layers, enumerate_rotations
from src.scoring import METRICS, ROOT, baseline_indices, preload, score_rotations
from src.stress_margins import analyse, before_cell, exact_top_two
from src.stress_test import rotation_id


def fixture():
    farm = json.loads((ROOT / "config/farms.json").read_text())[0]
    grid = json.loads((ROOT / "data/processed/stress_test_us_high_plains_b.json").read_text())
    presets = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]
    config = json.loads((ROOT / "config/stress_margins.json").read_text())
    return preload(farm), grid, presets, config


def test_before_cell_is_adjacent_and_moves_toward_reference():
    temps = [0., .5, 1., 1.5, 2.]
    rains = [-20, -10, 0, 10]
    assert before_cell({"temperature_change_c": 0., "rainfall_change_pct": -20}, temps, rains) == {
        "temperature_change_c": 0., "rainfall_change_pct": -10}
    assert before_cell({"temperature_change_c": 1., "rainfall_change_pct": 10}, temps, rains) == {
        "temperature_change_c": 1., "rainfall_change_pct": 0}


def test_top_two_excludes_cyclic_duplicates_and_matches_independent_scores():
    model, _, presets, _ = fixture()
    vector = np.array([presets["water_saver"][metric] for metric in METRICS])
    result = exact_top_two(model, vector, 3)
    rotations = enumerate_rotations(allowed_layers(model, 3))
    _, scores, _ = score_rotations(model, rotations)
    best_by_cycle = {}
    for sequence, score in zip(rotations, scores @ vector, strict=True):
        identifier = rotation_id(sequence, 1)
        best_by_cycle[identifier] = max(best_by_cycle.get(identifier, -np.inf), float(score))
    baseline = baseline_indices(model, 3)
    _, baseline_score, _ = score_rotations(model, baseline)
    baseline_id = rotation_id(baseline, 1)
    best_by_cycle[baseline_id] = max(best_by_cycle.get(baseline_id, -np.inf), float(baseline_score[0] @ vector))
    expected = sorted(best_by_cycle.values(), reverse=True)[:2]
    assert result["top"]["id"] != result["second"]["id"]
    assert np.isclose(result["top"]["score"], expected[0])
    assert np.isclose(result["second"]["score"], expected[1])
    assert np.isclose(result["gap"], expected[0] - expected[1])


def test_margin_analysis_reproduces_without_changing_p16_grid():
    model, grid, presets, config = fixture()
    before = json.dumps(grid, sort_keys=True)
    first = analyse(model, grid, presets, config)
    model, _, _, _ = fixture()
    second = analyse(model, grid, presets, config)
    assert first == second
    assert json.dumps(grid, sort_keys=True) == before
    assert all(row["near_tie"] == (row["near_tie_before"] or row["near_tie_after"])
               for row in first["presets"].values() if row["status"] == "tip")


def test_saved_margins_match_unchanged_grid_top_scores():
    for farm_id in ("us_high_plains_b", "telangana_a", "kenya_makueni_north"):
        grid = json.loads((ROOT / "data/processed" / f"stress_test_{farm_id}.json").read_text())
        margins = json.loads((ROOT / "data/processed" / f"stress_margins_{farm_id}.json").read_text())
        for preset, record in margins["presets"].items():
            if record["status"] != "tip":
                assert not grid["presets"][preset]["tipping_point"]["found"]
                continue
            cells = {(cell["temperature_change_c"], cell["rainfall_change_pct"]): cell
                     for cell in grid["presets"][preset]["cells"]}
            for side in ("before", "after"):
                row = record[side]
                original = cells[row["temperature_change_c"], row["rainfall_change_pct"]]
                expected = max(original["baseline_score"], original["exact_optimum_score"])
                assert np.isclose(row["top"]["score"], expected, atol=1e-12)
                assert row["top"]["id"] != row["second"]["id"]
                assert row["gap"] >= 0
