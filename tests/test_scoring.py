import json

import numpy as np
import pytest

from src.scoring import ROOT, baseline_indices, daily_water_deficit, preload, score_rotations

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
