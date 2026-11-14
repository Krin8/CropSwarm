import json

import numpy as np
import pandas as pd
import pytest

from src import transfer_diagnosis as study


@pytest.fixture
def frames():
    ks = pd.DataFrame({name: np.arange(21, dtype=float) for name in study.FEATURES})
    ks["practice"] = "non_irrigated"
    rows = []
    for i, value in enumerate([0, 1, 10, 19, 20, 30]):
        rows.append({"fips": f"400{i:02}", "year": 2000 + i, "district": str(i % 2),
                     "district_name": f"District {i % 2}", "yield_bu_ac": 30.,
                     "practice": "all_practices", **dict.fromkeys(study.FEATURES, value),
                     **dict(zip(study.MODELS, (32., 34., 31., 30.), strict=True))})
    return ks, pd.DataFrame(rows)


def test_range_endpoints_and_union_are_inclusive(frames):
    ks, ok = frames
    reference = study.distribution(ks)
    full = study.range_report(study.range_bins(ok, reference, "full"))
    central = study.range_report(study.range_bins(ok, reference, "central"))
    assert full["outside_any_n"] == 1
    assert central["outside_any_n"] == 3
    assert central["features"]["rainfall_mm"] == {
        "below_n": 1, "above_n": 2, "outside_n": 3, "outside_share": .5,
    }


def test_join_rejects_duplicate_and_mismatched_observations(frames):
    _, ok = frames
    left = ok.drop(columns=list(study.MODELS))
    right = ok[["fips", "year", "practice", "district", "yield_bu_ac", *study.MODELS]]
    pd.testing.assert_frame_equal(study.match_rows(left, right), ok)
    with pytest.raises(ValueError, match="unique county-years"):
        study.match_rows(left, pd.concat([right, right.iloc[:1]]))
    with pytest.raises(ValueError, match="yield_bu_ac differs"):
        study.match_rows(left, right.assign(yield_bu_ac=31.))


def test_paired_bootstrap_and_exhaustive_error_groups(frames):
    ks, ok = frames
    config = {"seed": 42, "bootstrap_draws": 30, "bootstrap_quantiles": [0.025, .975]}
    report = study.assess(ks, ok, config)
    assert report == study.assess(ks, ok, config)
    assert report["performance"]["inside"]["n"] == report["performance"]["outside"]["n"] == 3
    assert report["performance"]["inside"]["paired_rmse_delta"]["ridge"]["own_linear_trend"] == {
        "value": 1., "bootstrap_95": [1., 1.]}
    for error in report["errors"].values():
        assert error["top_years"]["above_half"] is False
        assert error["top_districts"]["above_half"] is True
        for groups in [error["year"], error["district"], *error["feature"].values()]:
            assert sum(row["n"] for row in groups) == 6
            assert sum(row["sse_share"] for row in groups) == pytest.approx(1.)
    assert study.performance(ok.iloc[:1], config)["paired_rmse_delta"]["ridge"]["own_county_mean"]["bootstrap_95"] is None


def test_saved_diagnosis_matches_p32_and_rebuilds_without_touching_inputs(tmp_path):
    source = study.ROOT / "data/processed"
    target = tmp_path / "data/processed"
    target.mkdir(parents=True)
    for name in ("climate_yield_features.csv", "climate_yield_transfer_40_features.csv",
                 "climate_yield_transfer_predictions.csv"):
        (target / name).symlink_to(source / name)
    (tmp_path / "config").symlink_to(study.ROOT / "config", target_is_directory=True)
    study.build(tmp_path)
    name = "climate_yield_transfer_diagnosis.json"
    report = json.loads((target / name).read_text())
    assert report == json.loads((source / name).read_text())
    p32 = json.loads((source / "climate_yield_transfer.json").read_text())["cases"]["20_to_40"]
    full = report["performance"]["full"]
    assert full["n"] == p32["n"] == 1800
    for model in study.LEARNERS:
        assert full["rmse"][model] == pytest.approx(p32["performance"][model]["rmse_bu_ac"]["value"])
        for baseline in study.BASELINES:
            prior = p32["rmse_delta_vs_own_baselines"][baseline.removeprefix("own_")][model]
            current = full["paired_rmse_delta"][model][baseline]
            assert current["value"] == pytest.approx(prior["value"])
            np.testing.assert_allclose(current["bootstrap_95"], prior["bootstrap_95"], atol=1e-12)
