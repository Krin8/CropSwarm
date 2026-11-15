"""P42 overlay math, scoring isolation and P22 replay."""

import json

import numpy as np

from src.scoring import METRICS, ROOT, baseline_indices, preload, score_rotations
from src.sensitivity import ExactSearch, apply_values, inventory, joint_samples, measures
from src.smooth_climate_fit import (CLIMATE_METRIC, compare_scores, matched_draw_results,
                                    smooth_heat, smooth_model, smooth_window_scores)
from src.literature_variant import crop_sequence


def read(path):
    return json.loads((ROOT / path).read_text())


def test_smooth_heat_is_monotone_and_preserves_the_fixed_band():
    counts = np.array([20, 21, 22, 26, 30, 31, 32])
    np.testing.assert_allclose(smooth_heat(counts, 26), [1, 1, .972, .5, .028, 0, 0])
    assert (np.diff(smooth_heat(np.arange(0, 31), 12.5)) <= 0).all()
    assert smooth_heat(0, 2) < 1


def test_window_fit_preserves_rain_and_mean_temperature_gates():
    crop = {"heat_tolerance_c": 30, "min_rain_mm": 20, "max_rain_mm": 100,
            "min_temp_c": 16, "max_temp_c": 25}
    profile = np.tile([1., 20., 30.], (20, 1))
    profile[:2, 2] = 31
    too_dry = profile.copy()
    too_dry[:, 0] *= .9
    too_cold = profile.copy()
    too_cold[:, 1] = 15.
    at_threshold = profile.copy()
    at_threshold[:, 2] = 30.
    windows = dict(enumerate((profile, too_dry, too_cold, at_threshold)))
    np.testing.assert_allclose(smooth_window_scores(windows, crop, .1), [.5, 0, 0, .784])


def test_smoothing_changes_only_climate_and_preserves_flagged_baseline_and_fallow():
    farm = next(farm for farm in read("config/farms.json") if farm["farm_id"] == "telangana_a")
    model = preload(farm)
    original_additions = model.additions.copy()
    smoothed = smooth_model(model)
    paddy = baseline_indices(model)
    fallow = [model.ids.index("fallow")] * len(paddy)
    _, old, new, flags = compare_scores(model, smoothed, [paddy, fallow])
    np.testing.assert_array_equal(model.additions, original_additions)
    assert smoothed.suitable is model.suitable
    assert flags["identical_consecutive_crop"][0].all()
    assert old[1, CLIMATE_METRIC] == new[1, CLIMATE_METRIC] == 1
    assert np.any(smoothed.additions[:, :, 3] != original_additions[:, :, 3])

    slot = (0, model.ids.index("paddy"))
    model.histories[slot] = {}
    assert smooth_model(model).additions[slot][3] == original_additions[slot][3]


def test_matched_draw_comparison_replays_a_fixed_seed():
    farm = read("config/farms.json")[0]
    seasons = read(f"data/processed/seasons_{farm['farm_id']}.json")
    config = read("config/sensitivity.json") | {"joint_draws": 6}
    model = preload(farm)
    presets = {"balanced": dict.fromkeys(METRICS, 1 / len(METRICS))}
    search = ExactSearch(presets, 3, 1, config["near_tie_gap"])
    inputs = inventory(model, seasons, read("config/evidence_grades.json"), config)

    def build_fixture_draws():
        for sample in joint_samples(inputs, config):
            new_farm, crops, policy, calendar = apply_values(model, seasons, inputs, sample)
            yield preload(new_farm, crops=crops, policy=policy, season_calendar=calendar)

    def decode(sequence):
        return crop_sequence(model, sequence)

    reference = search.evaluate(model)
    outcomes = [search.evaluate(draw, reference.winners) for draw in build_fixture_draws()]
    saved = {"presets": {"balanced": {"reference_winner": decode(reference.winners[0]),
                                     "reference_top_score": reference.top_scores[0],
                                     "joint": measures(outcomes, reference, 0, decode)}}}
    args = model, smooth_model(model), search, presets
    first = matched_draw_results(*args, build_fixture_draws(), saved)
    assert first == matched_draw_results(*args, build_fixture_draws(), saved)
    row = first["balanced"]
    assert row["draws"] == config["joint_draws"]
    assert row["original_change_fraction"] == saved["presets"]["balanced"]["joint"]["winner_change_fraction"]
    assert row["paired_disagreement_fraction"] == row["paired_disagreement_count"] / row["draws"]
