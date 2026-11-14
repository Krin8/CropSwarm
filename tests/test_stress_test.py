import json

import numpy as np
import pytest

from src.optimizer import allowed_layers, enumerate_canonical_rotations
from src.scoring import METRICS, ROOT, baseline_indices, preload, score_rotations
from src.stress_test import canonical_cycle, exact_cell, rotation_id, sweep, tipping_point


def kansas_fixture():
    farm = json.loads((ROOT / "config/farms.json").read_text())[0]
    preset = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]["water_saver"]
    return preload(farm), {"water_saver": preset}


def test_exact_cell_matches_independent_full_enumeration():
    model, presets = kansas_fixture()
    observed = exact_cell(model, presets, 3)["water_saver"]
    rotations = enumerate_canonical_rotations(allowed_layers(model, 3), len(model.season_labels))
    _, scores, _ = score_rotations(model, rotations)
    vector = np.array([presets["water_saver"][metric] for metric in METRICS])
    _, baseline_scores, _ = score_rotations(model, baseline_indices(model, 3))
    assert observed["feasible_count"] == len(rotations)
    assert np.isclose(observed["exact_optimum_score"], (scores @ vector).max())
    assert observed["baseline_score"] == float(baseline_scores[0] @ vector)


def test_tipping_rule_with_no_change_and_nearest_changed_fixture():
    temps = [0, .5, 1]
    rains = [-10, 0, 10]
    cells = [{"temperature_change_c": t, "rainfall_change_pct": r,
              "winner_id": "baseline" if (t, r) != (.5, 0) else "rotation_x", "status": "complete"}
             for t in temps for r in rains]
    point = tipping_point(cells, temps, rains)
    assert point["found"] and point["cell"] == {
        "temperature_change_c": .5, "rainfall_change_pct": 0, "winner_id": "rotation_x"}
    for cell in cells:
        cell["winner_id"] = "baseline"
    assert not tipping_point(cells, temps, rains)["found"]


def test_whole_year_cycle_shift_is_same_strategy_but_season_swap_is_not():
    assert canonical_cycle([2, 1, 3], 1) == canonical_cycle([1, 3, 2], 1)
    assert rotation_id([2, 1, 3], 1) == rotation_id([1, 3, 2], 1)
    assert rotation_id([2, 1, 3, 4], 2) == rotation_id([3, 4, 2, 1], 2)
    assert rotation_id([2, 1, 3, 4], 2) != rotation_id([1, 2, 3, 4], 2)


def test_deterministic_canonical_ties_reproduce_exact_sweep_on_cached_fixture():
    model, presets = kansas_fixture()
    config = {"temperature_changes_c": [0, .5], "rainfall_changes_pct": [-10, 0],
              "source": "design choice, not empirical", "distance_rule": "test grid steps",
              "tie_rule": "lexicographic canonical ties"}
    first = sweep(model, presets, config, 3)
    model, _ = kansas_fixture()
    second = sweep(model, presets, config, 3)
    assert first == second
    assert len(first["presets"]["water_saver"]["cells"]) == 4
    assert first["presets"]["water_saver"]["reference_winner_id"]


@pytest.mark.parametrize("farm_id", ["us_high_plains_b", "telangana_a", "kenya_makueni_north"])
def test_processed_sweep_has_full_grid_and_exact_scores(farm_id):
    path = ROOT / "data/processed" / f"stress_test_{farm_id}.json"
    result = json.loads(path.read_text())
    assert "lexicographically" in result["tie_rule"]
    assert "design choice" in result["grid_source"]
    assert len(result["presets"]) == 4
    for preset in result["presets"].values():
        cells = preset["cells"]
        assert len(cells) == 35
        assert len({(row["temperature_change_c"], row["rainfall_change_pct"]) for row in cells}) == 35
        assert all(row["feasible_count"] > 0 for row in cells)
        assert all(row["winner_id"] in result["rotation_catalog"] for row in cells)
    if farm_id == "telangana_a":
        assert not result["presets"]["water_saver"]["tipping_point"]["found"]
