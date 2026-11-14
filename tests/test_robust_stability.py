import numpy as np

from src.robust_stability import bootstrap_choices, conditional_cvar, evaluations, rank_top


def test_feasible_cvar_uses_only_feasible_scores_including_real_zeros():
    scores = np.array([[0., 0., .2, .6], [0., .4, .8, .9], [0., 0., 0., 0.]])
    feasible = np.array([[0, 0, 1, 1], [1, 1, 1, 1], [0, 0, 0, 0]], dtype=bool)
    np.testing.assert_allclose(conditional_cvar(scores, feasible, .375), [.2, .4 / 3, np.nan])
    np.testing.assert_allclose(conditional_cvar(scores, feasible, 1.), [.4, .525, np.nan])


def test_draw_prefix_chunking_and_original_cvar_are_preserved():
    rng = np.random.default_rng(42)
    cache = rng.uniform(size=(13, 17, 6)).astype(np.float32)
    feasible = rng.uniform(size=cache.shape[:2]) > .25
    cache[~feasible] = 0
    weight = np.full(6, 1/6)
    oracle = np.ones(17)
    one = evaluations(cache, feasible, weight, oracle, .1, [4, 9, 17], 13)
    many = evaluations(cache, feasible, weight, oracle, .1, [4, 9, 17], 3)
    for count in one:
        np.testing.assert_allclose(many[count], one[count], atol=1e-15)
        np.testing.assert_array_equal(one[count][:, 1], conditional_cvar(
            (cache @ weight)[:, :count], feasible[:, :count], .1))
    assert (one[17][:, 1] >= one[17][:, 3]).all()


def test_rank_and_bootstrap_keep_ties_and_exclude_undefined_candidates():
    assert rank_top(np.array([.5, .5, np.nan, .3]), 1e-6, 1, 3) == ([1, 0, 3], .5, 2)
    assert rank_top(np.array([np.nan]), 1e-6, 0, 3) == ([], None, 0)
    scores = np.array([[0., .5], [0., .5], [0., 0.]])
    feasible = scores != 0
    kwargs = {"objective": "conditional_cvar", "count": 2, "repeats": 40, "seed": 42}
    first = bootstrap_choices(scores, feasible, np.ones(2), .1, 1e-6, **kwargs)
    assert first == bootstrap_choices(scores, feasible, np.ones(2), .1, 1e-6, **kwargs)
    assert 0 < first["valid_replicates"] < 40
    assert first["win_share"] == [.5, .5, 0.]


def test_held_out_exploration_is_seeded_and_stays_in_canonical_space():
    import json

    from src.optimizer import allowed_layers, enumerate_canonical_rotations
    from src.robust_stability import TailFitness, swarm_trials
    from src.scoring import METRICS, ROOT, preload

    model = preload(json.loads((ROOT / "config/farms.json").read_text())[0])
    layers = allowed_layers(model, 3)
    rotations = enumerate_canonical_rotations(layers, 1)
    rng = np.random.default_rng(42)
    metrics = rng.uniform(size=(len(rotations), 7, len(METRICS))).astype(np.float32)
    feasible = rng.uniform(size=metrics.shape[:2]) > .3
    weight = np.ones(len(METRICS)) / len(METRICS)
    optimum = conditional_cvar(metrics @ weight, feasible, .1)
    optimizer = {**json.loads((ROOT / "config/optimizer.json").read_text()), "iterations": 2, "ants": 12}

    def run():
        fitness = TailFitness(rotations, metrics, feasible, weight, .1, 1, len(model.ids), conditional=True)
        return swarm_trials(model, layers, weight, optimizer, fitness, optimum, 1e-6,
                            2, 5, 10000, exploration=.2)

    first = run()
    assert first == run()
    assert {s for t in first["trials"] for s in t["seeds"]} == set(range(10000, 10010))
    assert first["trials_visiting_a_winner"] == first["best_of_five_hits"]
