import json

import numpy as np
import pytest

from src.scoring import METRICS, ROOT, baseline_indices, daily_water_deficit, preload, score_rotations

FARMS = json.loads((ROOT / "config/farms.json").read_text())


def test_bucket_reuses_storage_and_handles_runoff():
    rain = np.array([[30., 0., 0.], [10., 10., 10.]])
    assert daily_water_deficit(rain, 30, 10).tolist() == [10, 0]
    assert daily_water_deficit(rain, 30, 20).tolist() == [0, 0]


@pytest.mark.parametrize("farm", FARMS, ids=[farm["farm_id"] for farm in FARMS])
def test_baseline_metrics_and_visible_violations(farm):
    model = preload(farm)
    baseline = baseline_indices(model)
    raw, score, flags = score_rotations(model, np.tile(baseline, (3, 1)))
    assert np.isfinite(raw).all()
    assert np.all((0 <= score) & (score <= 1))
    assert np.array_equal(score[0], score[1])
    if farm["farm_id"] == "telangana_a":
        assert flags["identical_consecutive_crop"].all()


def test_legume_credit_and_water_score():
    model = preload(FARMS[0])
    fallow, wheat, pea = (model.ids.index(crop) for crop in ("fallow", "winter_wheat", "field_pea"))
    raw, score, _ = score_rotations(model, [[fallow, wheat], [pea, wheat], [fallow, fallow]])
    assert raw[1, 1] > raw[0, 1]
    assert score[1, 1] > score[0, 1]
    assert score[2, 0] > score[0, 0]


def test_legume_improves_nitrogen_over_active_cereal_rotation():
    model = preload(next(farm for farm in FARMS if farm["farm_id"] == "telangana_a"))
    rice, chickpea, maize = (model.ids.index(crop) for crop in ("paddy", "chickpea", "maize"))
    raw, score, flags = score_rotations(model, [[rice, maize], [rice, chickpea]])
    assert not any(flag.any() for flag in flags.values())
    assert raw[1, 1] > raw[0, 1]
    assert score[1, 1] > score[0, 1]


def test_telangana_paddy_baseline_flagged_and_loses_to_water_saver():
    farm = next(farm for farm in FARMS if farm["farm_id"] == "telangana_a")
    model = preload(farm)
    result = json.loads((ROOT / "data/processed/strategies_telangana_a.json").read_text())
    alternative = next(row for row in result["strategies"] if row["strategy_id"] == "water_saver")
    candidate = [model.ids.index(crop) for year in alternative["crop_ids"] for crop in year]
    raw, scores, flags = score_rotations(model, [baseline_indices(model, result["horizon_years"]), candidate])
    assert flags["identical_consecutive_crop"][0].all()
    assert not any(flag[1].any() for flag in flags.values())
    assert raw[1, 0] < raw[0, 0]
    preset = json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]["water_saver"]
    objectives = scores @ np.array([preset[metric] for metric in METRICS])
    assert objectives[1] > objectives[0]
