"""Synthetic chronological and reproducibility tests for the preregistered P37 design."""

import json

import numpy as np
import pandas as pd
import pytest

from src.county_yield_data import FEATURES
from src.data_pipeline import ROOT
from src import local_recalibration as study

CONFIG = {**json.loads((ROOT / "config/climate_yield.json").read_text()),
          "forest_trees": 3, "bootstrap_draws": 12}


@pytest.fixture
def frames():
    rng = np.random.default_rng(42)
    result = {}
    for state in ("20", "31", "40"):
        rows = []
        for district in range(4):
            for year in range(1990, 2007):
                if year == 1993 and district == 0:
                    continue
                features = rng.uniform(size=len(FEATURES))
                rows.append({"fips": f"{state}{district * 2 + 1:03d}", "district": str(district),
                             "district_name": f"District {district}", "practice": "non_irrigated", "year": year,
                             "yield_bu_ac": 20 + district + year - 1990 + 5 * features[1],
                             **dict(zip(FEATURES, features, strict=True))})
        result[state] = pd.DataFrame(rows)
    return result


def test_district_k_windows_share_the_same_later_tail(frames):
    district = frames["31"].loc[lambda x: x.district.eq("0")].sample(frac=1, random_state=42)
    calibration, test, years = study.district_windows(district)
    assert 1993 not in years
    assert set(test.year) == set(years[12:])
    for k in study.YEARS:
        assert set(calibration[k].year) == set(years[:k])
        if k:
            assert calibration[k].year.max() < test.year.min()
    with pytest.raises(ValueError, match="13 observed years"):
        study.district_windows(district.loc[district.year.lt(2000)])


def test_mutating_all_test_labels_cannot_change_fits_or_alpha(frames, monkeypatch):
    targets = {key: frames[key] for key in ("31", "40")}
    original_fit_source = study.fit_source
    origins = {study.district_windows(group)[1].year.min()
               for frame in targets.values() for _, group in frame.groupby("district")}

    def check_source(rows, config):
        assert rows.year.max() + 1 in origins
        assert set(rows.fips.str[:2]) == {"20"}
        return original_fit_source(rows, config)

    monkeypatch.setattr(study, "fit_source", check_source)
    _, reference = study.evaluate(frames["20"], targets, CONFIG)
    shifted = {}
    for state, frame in targets.items():
        copy = frame.copy()
        for _, group in frame.groupby("district"):
            _, test, _ = study.district_windows(group)
            copy.loc[test.index, "yield_bu_ac"] += 100
        shifted[state] = copy
    _, repeated = study.evaluate(frames["20"], shifted, CONFIG)
    pd.testing.assert_frame_equal(reference[list(study.METHODS)], repeated[list(study.METHODS)])


def test_seeded_curves_and_prediction_keys_reproduce(frames):
    targets = {key: frames[key] for key in ("31", "40")}
    report, rows = study.evaluate(frames["20"], targets, CONFIG)
    after, repeated = study.evaluate(frames["20"].sample(frac=1, random_state=42),
                                     {key: value.sample(frac=1, random_state=42)
                                      for key, value in targets.items()}, CONFIG)
    assert report == after
    pd.testing.assert_frame_equal(rows, repeated)
    assert not rows.duplicated(["state", "fips", "year", "k"]).any()
    assert len(rows.drop_duplicates(["state", "fips", "year"])) * len(study.YEARS) == len(rows)
    for state in report["states"].values():
        assert state["smallest_k_beating_trend"]["local_trend"] is None
        assert state["curves"]["0"]["source"]["rmse_delta_vs_local_trend"] is None
        assert state["curves"]["0"]["local_trend"]["status"] == "unavailable at zero local years"
        assert state["curves"]["12"]["local_trend"]["rmse_delta_vs_local_trend"]["bootstrap_95"] == [0.0, 0.0]
        for k in study.YEARS:
            assert state["curves"][str(k)]["source"]["rmse_bu_ac"] == state["curves"]["0"]["source"]["rmse_bu_ac"]
