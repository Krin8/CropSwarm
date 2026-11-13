import csv
from pathlib import Path

import pytest

from src.crops import HEADER_NOTE, SEASON_LABELS, load_crops
from src.validation import load_and_validate


ROOT = Path(__file__).resolve().parents[1]
CROPS = ROOT / "data/crops.csv"


def test_crop_catalog_loads_with_all_farm_baselines():
    farms = load_and_validate(ROOT / "config/farms.json", "farms")
    crops = load_crops(CROPS, farms=farms)

    assert len(crops) == 15
    assert crops["maize"]["water_need_mm"] > crops["common_bean"]["water_need_mm"]
    assert crops["common_bean"]["is_legume"] is True
    assert set(crops["fallow"]["seasons_allowed"]) == SEASON_LABELS
    assert crops["fallow"]["heat_tolerance_c"] is None


@pytest.mark.parametrize(
    ("field", "invalid", "message"),
    [
        ("cover_score", "1.01", "cover_score"),
        ("relative_income_index", "-0.01", "relative_income_index"),
        ("water_need_source", " ", "water_need_source"),
        ("heat_tolerance_c", "nan", "finite number"),
        ("max_rain_mm", "0", "rainfall bounds"),
        ("seasons_allowed", '["unknown"]', "seasons_allowed"),
        ("crop_id", "Winter-wheat", "snake_case"),
        ("root_depth_source", None, "invalid crop table columns"),
    ],
)
def test_crop_validator_rejects_invalid_values_and_missing_columns(tmp_path, field, invalid, message):
    with CROPS.open(encoding="utf-8", newline="") as source:
        source.readline()
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        rows = list(reader)
    if invalid is None:
        columns.remove(field)
        for row in rows:
            del row[field]
    else:
        rows[1][field] = invalid

    edited = tmp_path / "crops.csv"
    with edited.open("w", encoding="utf-8", newline="") as target:
        target.write(f"{HEADER_NOTE}\n")
        writer = csv.DictWriter(target, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match=message):
        load_crops(edited)


def test_crop_validator_rejects_unknown_baseline_crop():
    farms = load_and_validate(ROOT / "config/farms.json", "farms")
    farms[0]["baseline_rotation_cycle"][0] = ["unknown_crop"]

    with pytest.raises(ValueError, match="unknown baseline crop IDs"):
        load_crops(CROPS, farms=farms)
