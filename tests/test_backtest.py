import json

import pandas as pd

from src.backtest import cdl_history, compute, quality_ndvi, rank_interval
from src.crops import load_crops
from src.scoring import ROOT, preload


def test_qa_filter_rejects_bad_composites():
    frame = pd.DataFrame({"date": ["2020-01-01", "2020-01-17", "2020-02-02", "2020-02-18"],
                          "ndvi": [.3, .9, .4, 1.2], "pixel_reliability": [0, 1, 0, 0],
                          "vi_quality": [0, 0, 1, 0]})
    assert quality_ndvi(frame).empty or len(quality_ndvi(frame)) == 1
    assert quality_ndvi(frame).ndvi.tolist() == [.3]


def test_rank_bootstrap_is_fixed_and_flags_small_n():
    first = rank_interval([1, 2, 3, 4, 5], [5, 3, 4, 2, 1], seed=42, draws=100)
    assert first == rank_interval([1, 2, 3, 4, 5], [5, 3, 4, 2, 1], seed=42, draws=100)
    assert first["rho"] < 0 and first["n"] == 5 and first["small_n"]
    assert rank_interval([0] * 5, [1, 2, 3, 4, 5])["rho"] is None


def test_cached_backtest_aligns_cdl_and_scoring_window():
    farms = json.loads((ROOT / "config/farms.json").read_text())
    farm = farms[0]
    model = preload(farm, crops=load_crops(ROOT / "data/crops.csv", farms=farms))
    climate = pd.read_parquet(ROOT / "data/processed/climate_us_high_plains_b.parquet")
    ndvi = pd.read_csv(ROOT / "data/processed/ndvi_us_high_plains_b.csv")
    cdl = json.loads((ROOT / "data/raw/p2_evidence/p2_wheat_cdl.json").read_text())
    assert cdl_history(cdl) == {2019: "fallow", 2020: "winter_wheat", 2021: "sorghum",
                                2022: "fallow", 2023: "winter_wheat"}
    result = compute(farm, model, climate, ndvi, cdl=cdl)
    assert len(result["rows"]) == 5
    assert set(result["seasons"]) == {"cool", "warm"}
    assert result["seasons"]["warm"]["comparisons"]["deficit_fraction_vs_ndvi_peak"]["n"] == 1
    assert result["rows"][1]["window_start"].startswith("2019-10")
    assert result["rows"][0]["deficit_mm"]["value"] is None
    assert all(row["ndvi_peak"]["source"].startswith("NASA Terra") for row in result["rows"])
