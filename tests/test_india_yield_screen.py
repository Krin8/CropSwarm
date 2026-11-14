import json

import pandas as pd
import pytest

from src.climate_yield import grouped_splits
from src.india_yield_screen import ROOT, archive_screen, build


@pytest.fixture
def archived_rows():
    geography = [{"map_code": 100 + i, "feature_id": i, "state": f"State {i}",
                  "district": f"District {i}"} for i in range(4)]
    return pd.DataFrame([
        {**place, "source_code": place["map_code"] + 1, "crop": "Rice",
         "year": year, "yield_kg_ha": 500 + place["feature_id"] + year}
        for place in geography for year in range(1990, 1994)
    ]), pd.DataFrame(geography)


def screen(raw, mapping, **kwargs):
    return archive_screen(raw, mapping, first_year=1990, last_year=1993, minimum_years=4,
                          minimum_districts=2, **kwargs)


def test_coverage_screen_excludes_conflicts_bad_mapping_and_low_coverage(archived_rows):
    rows, geography = archived_rows
    # Duplicate the first identical value; conflict with the second district's first yield.
    first = rows.iloc[[0]]
    conflict = rows.iloc[[4]].assign(yield_kg_ha=1)
    rows = pd.concat([rows, first, conflict]).reset_index(drop=True)
    geography = geography.iloc[:-1].copy()
    geography.loc[2, "state"] = "Unmatched state"
    result = screen(rows, geography)
    assert result["selected_crop"] is None
    assert [d["status"] for d in result["district_coverage"]] == [
        "meets_yield_and_geography_gate", "excluded_fewer_than_minimum_yield_years",
        "excluded_inconsistent_polygon_metadata", "excluded_missing_polygon",
    ]
    assert result["district_coverage"][1]["conflicting_years"] == [1990]
    assert result["candidates"][0]["district_years_meeting_yield_and_geography"] == 4


def test_irrigation_gate_and_crop_selection_reproduce(archived_rows):
    rows, geography = archived_rows
    metadata = {"season": "kharif", "irrigation_share": None, "rainfed_dominance_documented": False}
    result = screen(rows, geography)
    assert result["candidates"][0]["passes_yield_and_geography_gate"]
    assert result["selected_crop"] is None

    rainfed = {"Rice": {**metadata, "rainfed_dominance_documented": True}}
    assert screen(rows, geography, crops=rainfed)["selected_crop"] == "Rice"

    two_crops = pd.concat([rows, rows.assign(crop="Millet")], ignore_index=True)
    comparable = {"Rice": {**metadata, "irrigation_share": .4}, "Millet": {**metadata, "irrigation_share": .1}}
    first = screen(two_crops, geography, crops=comparable)
    second = screen(two_crops.sample(frac=1, random_state=42), geography, crops=comparable)
    assert first == second
    assert first["selected_crop"] == "Millet"


@pytest.mark.parametrize("column", ["year", "state"])
def test_existing_grouped_split_keeps_held_out_year_or_state_out(archived_rows, column):
    rows, _ = archived_rows
    for train_positions, test_positions in grouped_splits(rows, column):
        train, test = rows.iloc[train_positions], rows.iloc[test_positions]
        assert set(train[column]).isdisjoint(test[column])
        for fit, validation in grouped_splits(train, column, n_splits=3):
            assert set(train.iloc[fit][column]).isdisjoint(train.iloc[validation][column])
            assert set(train.iloc[fit][column]).isdisjoint(test[column])
        if column == "state":
            assert set(train["map_code"]).isdisjoint(test["map_code"])


def test_committed_screen_matches_archive():
    saved = json.loads((ROOT / "data/processed/climate_yield_india_screen.json").read_text())
    assert build() == saved
    assert saved["power_requests"] == saved["india_model_fits"] == 0
