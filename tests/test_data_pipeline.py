from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from src.data_pipeline import (
    BAND_NAMES, IMERG, MODIS, POWER, UTC_RAIN, Chunk, band_metadata, cache_hit,
    fetch_chunk, modis_data, power_data, read_json, write_json,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sample_modis():
    return Chunk("demo", "modis_example", MODIS, {
        "startDate": "A2022001", "endDate": "A2022017",
    })


def modis_body(days):
    values = {"ndvi": 5000, "evi": -3000, "pixel_reliability": 1, "vi_quality": 2116, "composite_date": 5}
    return {"nrows": 1, "ncols": 1, "subset": [
        {"band": BAND_NAMES[field], "modis_date": day, "data": [value]}
        for day in days for field, value in values.items()
    ]}


def test_modis_retries_partial_then_reuses_complete_cache(tmp_path, sample_modis):
    partial, complete = Mock(status_code=200), Mock(status_code=200)
    partial.json.return_value = modis_body(["A2022001"])
    complete.json.return_value = modis_body(["A2022001", "A2022017"])
    http = Mock(side_effect=[requests.Timeout("fixture timeout"), partial, complete])
    sleep = Mock()
    assert fetch_chunk(sample_modis, tmp_path, get=http, sleep=sleep) == "fetched"
    assert [call.args[0] for call in sleep.call_args_list] == [2, 8]
    raw = read_json(sample_modis.path(tmp_path))
    assert [entry["status"] for entry in raw["attempts"]] == [None, 200, 200]
    assert raw["params"] == sample_modis.params
    assert raw["timestamp"]
    assert cache_hit(sample_modis, raw)
    never_network = Mock(side_effect=AssertionError("cache hit attempted a request"))
    assert fetch_chunk(sample_modis, tmp_path, get=never_network) == "cached"
    never_network.assert_not_called()


def test_offline_modis_scaling_qa_and_pixel_date(tmp_path, sample_modis):
    write_json(sample_modis.path(tmp_path), {
        "status": 200, "url": MODIS, "params": sample_modis.params,
        "body": modis_body(["A2022001", "A2022017"]),
    })
    frame = modis_data([sample_modis], tmp_path, band_metadata(ROOT))
    assert list(frame.ndvi) == [0.5, 0.5]
    assert frame.evi.isna().all()
    assert list(frame.pixel_reliability) == [1, 1]
    assert list(frame.vi_quality) == [2116, 2116]
    assert str(frame.iloc[0].composite_date) == "2022-01-05"
    assert pd.isna(frame.iloc[1].composite_date)


def test_power_fill_and_utc_rain_stay_separate(tmp_path):
    chunks = [
        Chunk("demo", standard, POWER, {
            "start": "20000101", "end": "20000102", "time-standard": standard,
            "parameters": "PRECTOTCORR" if standard == "LST" else f"{IMERG},PRECTOTCORR",
        })
        for standard in ("LST", "UTC")
    ]
    for chunk, values in zip(chunks, (
        {"PRECTOTCORR": {"20000101": 0, "20000102": -999}},
        {"PRECTOTCORR": {"20000101": 1.5, "20000102": 2.5}, IMERG: {"20000101": 4, "20000102": -999}},
    ), strict=True):
        body = {
            "header": {"fill_value": -999}, "properties": {"parameter": values},
            "parameters": {key: {"units": "mm/day"} for key in values},
        }
        write_json(chunk.path(tmp_path), {"status": 200, "url": POWER, "params": chunk.params, "body": body})
    frame, units = power_data(chunks, tmp_path)
    rows = frame.loc[frame.date.dt.year == 2000].iloc[:2]
    assert rows.iloc[0].PRECTOTCORR == 0
    assert pd.isna(rows.iloc[1].PRECTOTCORR)
    assert list(rows[UTC_RAIN]) == [1.5, 2.5]
    assert rows.iloc[0][IMERG] == 4
    assert pd.isna(rows.iloc[1][IMERG])
    assert units[IMERG] == units[UTC_RAIN] == "mm/day"
