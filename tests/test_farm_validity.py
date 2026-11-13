import json
from pathlib import Path

import pandas as pd

from src import farm_validity


def test_cdl_neighborhood_agreement_and_baseline_uncertainty():
    root = farm_validity.ROOT
    cache = farm_validity.RequestCache(root / "data/raw/p7/cdl", offline=True)
    result = farm_validity.run_us(root, cache, {"farm_id": "us_high_plains_b"})

    assert result["center_matches_entire_sample_every_year"] is True
    assert result["neighborhood"]["2019"]["category_counts"] == {"Fallow/Idle Cropland": 9}
    assert result["neighborhood"]["2021"]["center"]["category"] == "Sorghum"
    assert result["spring_ndvi_2019_peaks"] == ["2019-04-07"]
    assert result["verdict"] == "pass with flags"


def test_kenya_threshold_requires_three_aligned_years_and_qualifying_cover(monkeypatch):
    frame = pd.DataFrame({"date": pd.to_datetime(["2019-05-09", "2019-12-03"]),
                          "composite_date": ["2019-05-16", "2019-12-11"]})
    observations = {str(year): {"status": "complete", "peaks": {"0.12": [f"{year}-05-09", f"{year}-12-03"]}}
                    for year in range(2019, 2022)}
    observations["2021"]["status"] = "incomplete"
    monkeypatch.setattr(farm_validity, "vegetation", lambda _: (observations, None))

    assert farm_validity.kenya_evidence(frame, {"qualifies": True})["passes"] is False
    observations["2021"]["status"] = "complete"
    qualifying = farm_validity.kenya_evidence(frame, {"qualifies": True})
    assert qualifying["qualifying_years"] == 3
    assert qualifying["passes"] is True
    assert qualifying["annual"]["2019"]["long_rain_peaks"] == ["2019-05-16"]
    assert farm_validity.kenya_evidence(frame, {"qualifies": False})["passes"] is False


def test_three_offline_verdicts_include_visible_kenya_flag_and_telangana_coverage():
    processed = Path(farm_validity.ROOT) / "data/processed"
    records = [json.loads(path.read_text()) for path in processed.glob("validity_*.json")]
    by_farm = {entry["farm_id"]: entry for entry in records}

    assert len(by_farm) == 3
    kenya = by_farm["kenya_makueni_north"]
    assert kenya["retained"] is True
    assert "cropland unverified" in kenya["flags"]
    assert all(candidate["land_cover"]["center_class"] == 10 for candidate in kenya["alternatives"].values())
    telangana = by_farm["telangana_a"]["evidence"]
    assert telangana["ndvi_2022_gap_filled"] is True
    assert telangana["two_peak_years"] == 0
    assert telangana["prior_land_cover"]["center_class"] == 12
