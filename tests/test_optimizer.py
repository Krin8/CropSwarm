import itertools
import json

import numpy as np
import pytest

from src.optimizer import aco_restarts, allowed_layers, count_rotations, enumerate_rotations
from src.scoring import METRICS, ROOT, preload


def test_exact_enumerator_matches_independent_small_search_with_cycle_boundary():
    layers = [[0, 1, 2], [0, 1], [0, 1, 2]]
    truth = {r for r in itertools.product(*layers) if all(a != b for a, b in zip(r, (*r[1:], r[0])))}
    assert count_rotations(layers, 3) == len(truth)
    assert {tuple(row) for row in enumerate_rotations([np.array(a) for a in layers])} == truth


@pytest.mark.parametrize("farm", json.loads((ROOT / "config/farms.json").read_text()))
def test_cached_results_keep_baseline_and_distinct_candidates(farm):
    path = ROOT / "data/processed" / f"strategies_{farm['farm_id']}.json"
    result = json.loads(path.read_text())
    strategies = result["strategies"]
    assert strategies[0]["strategy_id"] == "baseline"
    assert len({tuple(map(tuple, row["crop_ids"])) for row in strategies}) >= 4
    assert not any(row["flags"] for row in strategies[1:])
    for row in result["verification"].values():
        single = row["single_run"]
        grouped = row["best_of_restarts"]
        assert single["runs"] == grouped["runs"] == len(row["trials"]) == 30
        assert grouped["optimum_hits"] >= single["optimum_hits"]
        seeds = [seed for trial in row["trials"] for seed in trial["seeds"]]
        assert len(set(seeds)) == len(seeds) == 150
        for trial, initial, best in zip(row["trials"], single["scores"], grouped["scores"], strict=True):
            assert len(trial["scores"]) == len(trial["seeds"]) == 5
            assert initial == trial["scores"][0]
            valid = [score for score in trial["scores"] if score is not None]
            assert best == max(valid, default=None)
            assert all(score <= row["exact_score"] + 1e-10 for score in valid)


def test_best_of_five_reproduces_with_fixed_seeds():
    farm = json.loads((ROOT / "config/farms.json").read_text())[0]
    model = preload(farm)
    config = json.loads((ROOT / "config/optimizer.json").read_text())
    preset = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]["water_saver"]
    weights = np.array([preset[metric] for metric in METRICS])
    args = (model, allowed_layers(model, config["default_years"]), weights, config, 3)
    first_seeds, first_runs, first_best = aco_restarts(*args)
    second_seeds, second_runs, second_best = aco_restarts(*args)
    assert first_seeds == second_seeds
    for (score, sequence), (other_score, other_sequence) in zip(first_runs, second_runs, strict=True):
        assert score == other_score
        np.testing.assert_array_equal(sequence, other_sequence)
    assert first_best[0] == second_best[0]
    np.testing.assert_array_equal(first_best[1], second_best[1])
