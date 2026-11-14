from dataclasses import replace
import json

import numpy as np
import pytest

from src.optimizer import allowed_layers, enumerate_canonical_rotations
from src.robust_optimization import (ColonyFitness, chunk_objectives, colony_trials, draw_oracles, exact_pick,
                                     lower_cvar, metric_rows, prepare_metrics, utilities, weighted_scores)
from src.scoring import METRICS, ROOT, preload, score_rotations
from src.sensitivity import ExactSearch, joint_samples, numeric


@pytest.fixture(scope="module")
def kansas():
    farms = json.loads((ROOT / "config/farms.json").read_text())
    return preload(next(f for f in farms if f["farm_id"] == "us_high_plains_b"))


def test_cvar_averages_exact_tail_mass_and_handles_fractional_boundary():
    scores = np.array([[.4, .1, .3, .2], [.8, .8, .2, .2]])
    np.testing.assert_allclose(lower_cvar(scores, .375), [(.1 + .5 * .2) / 1.5, .2])
    np.testing.assert_allclose(lower_cvar(scores, .1), [.1, .2])
    np.testing.assert_allclose(lower_cvar(scores, 1), scores.mean(axis=1))


def test_minimax_regret_and_tolerance_ties():
    scores = np.array([[.2, .8, .6], [.4, .7, .4]])
    result = utilities(scores, np.array([.6, .9, .7]), .1)
    np.testing.assert_allclose(result[:, 2], [1 - .4, 1 - .3])
    assert exact_pick(np.array([.5999999, .6, .58]), 1e-6) == (0, .6, 2)
    assert exact_pick(np.array([.5999999, .6, .58]), 1e-6, preferred=1) == (1, .6, 2)


def test_metric_chunking_and_objectives_match_unchunked(kansas):
    rotations = enumerate_canonical_rotations(allowed_layers(kansas, 3), 1)[:19]
    models = [kansas] * 11
    scores = np.empty((19, len(models), 6), dtype=np.float32)
    feasible = np.empty(scores.shape[:2], dtype=bool)
    prepare_metrics(models, rotations, scores, feasible, 4)
    direct = score_rotations(kansas, rotations)[1].astype(np.float32)
    np.testing.assert_array_equal(scores, np.repeat(direct[:, None], len(models), axis=1))
    assert feasible.all()
    np.testing.assert_array_equal(metric_rows(kansas, [[0, 0, 0]])[0], np.zeros((1, 6)))
    assert not metric_rows(kansas, [[0, 0, 0]])[1][0]

    rng = np.random.default_rng(42)
    weight = np.array([.35, .15, .1, .15, .1, .15])
    data = rng.uniform(size=scores.shape).astype(np.float32)
    oracle = weighted_scores(data, weight).max(axis=0)
    expected = utilities(weighted_scores(data, weight), oracle, .1)
    np.testing.assert_allclose(chunk_objectives(data, weight, oracle, .1, 4), expected, atol=1e-15, rtol=0)


def test_swarm_and_p22_prefix_reproduce(kansas):
    settings = json.loads((ROOT / "config/sensitivity.json").read_text())
    item = numeric("assumption", "Check", "fixture", "assumption", ("irrigation",), .5, settings)
    draws = joint_samples([item], settings, 11)
    assert draws == joint_samples([item], settings, 17)[:11]
    layers = allowed_layers(kansas, 3)
    rotations = enumerate_canonical_rotations(layers, 1)
    rng = np.random.default_rng(42)
    data = rng.uniform(size=(len(rotations), len(draws), 6)).astype(np.float32)
    presets = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]
    weight = np.array([presets["balanced"][m] for m in METRICS])
    oracle = weighted_scores(data, weight).max(axis=0)
    optimizer = {**json.loads((ROOT / "config/optimizer.json").read_text()), "iterations": 4, "ants": 12}
    config = {"aco_trials": 2, "aco_restarts": 5, "tie_tolerance": 1e-6}
    exact = chunk_objectives(data, weight, oracle, .1, 13)
    index = 2

    def run():
        colony = ColonyFitness(rotations, data, weight, oracle, .1, 1, len(kansas.ids))
        shifted = np.roll(rotations[:5], 1, axis=1)
        np.testing.assert_allclose(colony(shifted, index), exact[:5, index], atol=1e-15)
        return colony_trials(kansas, layers, weight, optimizer, config, colony, index, exact[:, index].max())

    first = run()
    assert first == run()
    assert len({seed for trial in first["runs"] for seed in trial["seeds"]}) == 10
    assert first["best_of_five_hits"] >= first["single_hits"]
    assert first["best_of_five_mean_gap"] <= first["single_mean_gap"]



def test_oracle_includes_newly_feasible_options_and_matches_p22(kansas):
    # Remove an otherwise feasible crop from the nominal pool and restore it in the draw.
    reduced = kansas.suitable.copy()
    reduced[:, kansas.ids.index("soybean")] = False
    nominal = replace(kansas, suitable=reduced)
    rotations = enumerate_canonical_rotations(allowed_layers(nominal, 3), 1)
    models = [nominal, kansas]
    cache = np.empty((len(rotations), len(models), len(METRICS)), dtype=np.float32)
    feasibility = np.empty(cache.shape[:2], dtype=bool)
    prepare_metrics(models, rotations, cache, feasibility, 9)
    presets = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]
    search = ExactSearch(presets, 3, 1, .01)
    reference = [search.evaluate(model).top_scores for model in models]
    np.testing.assert_allclose(draw_oracles(models, rotations, cache, feasibility, search.weights, 3, 9),
                               reference, atol=5e-8, rtol=0)
