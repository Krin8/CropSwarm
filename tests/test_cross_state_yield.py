import json

import numpy as np
import pandas as pd
import pytest

import src.climate_yield as existing
from src.climate_yield_validity import DISTRICT_SCHEME
from src.county_yield_data import FEATURES
from src.cross_state_yield import (DISTRICT_BLOCK, attach_reference, evaluate, outer_state_splits,
                                   predictions_for_transfer, validate)
from src.cross_state_yield_data import ROOT, prepare_state, target_districts

SETTINGS = {**json.loads((ROOT / "config/climate_yield.json").read_text()),
            "forest_trees": 3, "permutation_repeats": 2, "bootstrap_draws": 12}


@pytest.fixture
def state_frames():
    rng = np.random.default_rng(42)
    states = {}
    for i, state in enumerate(("20", "31", "40")):
        rows = []
        for district in range(4):
            for year in range(2000, 2005):
                weather = rng.uniform(size=len(FEATURES))
                rows.append({"fips": f"{state}{district * 2 + 1:03d}", "district": str(district),
                             "year": year, "practice": "non_irrigated", "yield_bu_ac": 15 + i
                             + district + (year - 2000) + 4 * weather[1],
                             **dict(zip(FEATURES, weather, strict=True))})
        states[state] = pd.DataFrame(rows)
    return states


def test_transfer_cannot_use_held_out_state_for_trends_tuning_or_training(state_frames, monkeypatch):
    data = {state: validate(frame, state) for state, frame in state_frames.items()}
    old_tune, old_trend = existing.tune, existing.CountyTrends.__init__
    for sources, held_state, train, target in outer_state_splits(data):
        assert held_state not in sources
        assert set(train.fips).isdisjoint(target.fips)
        assert set(train[DISTRICT_BLOCK]).isdisjoint(target[DISTRICT_BLOCK])
        assert set(train.year) == set(target.year)

        def record_tune(rows, key, config):
            assert set(rows.state) == set(sources)
            assert key == DISTRICT_BLOCK
            return old_tune(rows, key, config)

        def record_trend(self, rows):
            assert set(rows.state).issubset(sources)
            assert held_state not in set(rows.state)
            return old_trend(self, rows)

        monkeypatch.setattr(existing, "tune", record_tune)
        monkeypatch.setattr(existing.CountyTrends, "__init__", record_trend)
        first, params = predictions_for_transfer(train, target, SETTINGS)
        repeated, other = predictions_for_transfer(train, target.assign(yield_bu_ac=target.yield_bu_ac + 1000), SETTINGS)
        assert params == other
        pd.testing.assert_frame_equal(first[list(existing.MODELS)], repeated[list(existing.MODELS)])
        with pytest.raises(ValueError, match="overlap"):
            predictions_for_transfer(pd.concat([train, target]), target, SETTINGS)


def test_all_fixed_experiments_are_reproducible(state_frames):
    _, own = existing.analyse(state_frames["20"], SETTINGS, schemes=DISTRICT_SCHEME)
    report, rows = evaluate(state_frames, own, SETTINGS)
    shuffled = {key: value.sample(frac=1, random_state=42) for key, value in state_frames.items()}
    other, repeated = evaluate(shuffled, own.sample(frac=1, random_state=42), SETTINGS)
    assert report == other
    pd.testing.assert_frame_equal(rows, repeated)
    assert set(report["cases"]) == {"in_state_31", "in_state_40", "20_to_31", "20_to_40", "31_to_20", "40_to_20",
                                    "pooled_holdout_20", "pooled_holdout_31", "pooled_holdout_40", "pooled"}
    assert report["learned_configuration_count"] == 5
    assert report["cases"]["pooled"]["bootstrap_blocks"] == 3
    assert report["cases"]["pooled"]["n"] == sum(map(len, state_frames.values()))
    matched = rows.loc[rows.case.eq("31_to_20")]
    with pytest.raises(ValueError, match="different county-years"):
        attach_reference(matched, own.iloc[:-1])


def test_data_builder_keeps_yield_eligible_county_and_records_missing_weather(tmp_path):
    raw = pd.DataFrame([
        {"STATE_ANSI": "31", "COUNTY_ANSI": "001", "COUNTY_CODE": "001", "COUNTY_NAME": "Adams",
         "ASD_CODE": "70", "ASD_DESC": "Test district", "YEAR": str(year), "VALUE": "40",
         "SHORT_DESC": "WHEAT, WINTER - YIELD, MEASURED IN BU / ACRE"}
        for year in range(1991, 2012)
    ])
    coords = pd.DataFrame([{"fips": "31001", "county": "Adams fixture", "lat": 40., "lon": -98.}])
    window = {"onset_month": 10, "year_offset": -1}
    crop = {"season_length_days": 260, "water_need_mm": 550., "heat_tolerance_c": 30.}
    frame, coverage, manifest = prepare_state(raw, coords, SETTINGS, window, crop,
                                              tmp_path / "cache", tmp_path / "archive")
    assert frame.empty and coverage["retained_counties"] == 0 and coverage["yield_counties"] == 1
    assert len(coverage["counties"][0]["unavailable_windows"]) == 21
    assert all(row["coverage"] == "incomplete" for row in manifest)
    with pytest.raises(ValueError, match="Unresolved"):
        target_districts(pd.concat([raw, raw.iloc[:1].assign(ASD_CODE="99")]), coords)


def test_committed_yield_inventory_reproduces_with_no_geography_or_network():
    from src.cross_state_yield_data import ARCHIVE, yield_inventory

    source = pd.read_csv(ARCHIVE / "quickstats_targets.csv", dtype=str, keep_default_na=False)
    expected = json.loads((ROOT / "data/processed/climate_yield_transfer_yield_inventory.json").read_text())
    assert yield_inventory(source, SETTINGS) == expected
    assert sum(row["eligible_counties"] for row in expected.values()) == 117
    assert sum(row["eligible_rows"] for row in expected.values()) == 3544
