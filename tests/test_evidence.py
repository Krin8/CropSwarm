import json

import pytest

from src.evidence import GRADES, backtest_cap, crop_source_grade, evidence_for_strategy, label_for_shares
from src.scoring import ROOT, baseline_indices, preload


CONFIG = json.loads((ROOT / "config/evidence_grades.json").read_text())
FARMS = json.loads((ROOT / "config/farms.json").read_text())


def test_crop_source_requires_verified_citation_without_assumption_qualifier():
    verified = "FAO Table 14 https://www.fao.org/4/s2022e/s2022e07.htm"
    assert crop_source_grade(verified, CONFIG) == "literature"
    assert crop_source_grade("assumption, validate locally; " + verified, CONFIG) == "assumption"
    assert crop_source_grade("unverified https://example.org/parameter", CONFIG) == "assumption"


def test_sourced_cowpea_water_use_and_family_do_not_upgrade_risk_policy():
    farm = next(farm for farm in FARMS if farm["farm_id"] == "kenya_makueni_north")
    model = preload(farm)
    assert model.crops["cowpea"]["water_need_mm"] == pytest.approx((281.6 + 288.0) / 2)
    sequence = [model.ids.index(crop) for crop in ("cowpea", "fallow")]
    metrics = evidence_for_strategy(model, sequence)["metrics"]
    for metric, field in (("water", "crop.water_need_mm"), ("risk", "crop.disease_family")):
        grades = {item["crop_id"]: item["grade"] for item in metrics[metric]["inputs"]
                  if item["input"] == field}
        assert grades == {"cowpea": "literature", "fallow": "assumption"}
    assert metrics["risk"]["label"] == "low"
    assert next(item for item in metrics["risk"]["inputs"]
                if item["input"] == "model.risk_rule")["grade"] == "assumption"


def test_label_thresholds_are_conservative_at_boundaries():
    shares = dict.fromkeys(GRADES, 0.0)
    shares.update(nasa_measured=.75, literature=.15, assumption=.10)
    assert label_for_shares(shares, CONFIG) == "high"
    shares.update(nasa_measured=.50, literature=.16, assumption=.34)
    assert label_for_shares(shares, CONFIG) == "medium"
    shares.update(nasa_measured=.49, literature=.16, assumption=.35)
    assert label_for_shares(shares, CONFIG) == "low"


@pytest.mark.parametrize("farm", FARMS)
def test_every_strategy_metric_has_complete_ledger_and_support_caps(farm):
    model = preload(farm)
    evidence = evidence_for_strategy(model, baseline_indices(model, 3))
    assert set(evidence["metrics"]) == {"water", "nitrogen", "erosion", "climate_fit", "income", "risk"}
    for metric, row in evidence["metrics"].items():
        assert sum(row["shares"].values()) == pytest.approx(1)
        assert set(row["shares"]) == set(GRADES)
        assert all(item["source"] and item["grade"] in GRADES for item in row["inputs"])
        assert row["label"] in {"high", "medium", "low"}
    assert evidence["metrics"]["erosion"]["shares"]["nasa_modeled"] > 0
    assert evidence["metrics"]["income"]["label"] == "low"
    if farm["farm_id"] == "kenya_makueni_north":
        assert all(row["label"] == "low" for row in evidence["metrics"].values())
        assert all(any("Cropland" in reason for reason in row["reasons"])
                   for row in evidence["metrics"].values())
    if farm["farm_id"] == "telangana_a":
        assert any("Second crop season" in reason for reason in evidence["metrics"]["water"]["reasons"])
    if farm["farm_id"] == "us_high_plains_b":
        assert any("0 assessable" in reason for reason in evidence["metrics"]["water"]["reasons"])


def test_backtest_cap_uses_observed_small_n_and_direction():
    for farm in FARMS:
        backtest = json.loads((ROOT / "data/processed" / f"backtest_{farm['farm_id']}.json").read_text())
        cap, reason = backtest_cap(backtest, CONFIG)
        assert cap in {"low", "medium"}
        assert "Back-test" in reason


@pytest.mark.parametrize("farm", FARMS)
def test_every_cached_displayed_strategy_carries_all_metric_grades(farm):
    path = ROOT / "data/processed" / f"strategies_{farm['farm_id']}.json"
    result = json.loads(path.read_text())
    for strategy in result["strategies"]:
        assert strategy["evidence_label"] == "low"
        for metric in ("water", "nitrogen", "erosion", "climate_fit", "income", "risk"):
            evidence = strategy["metrics"][metric]["evidence"]
            assert evidence["label"] == "low"
            assert sum(evidence["shares"].values()) == pytest.approx(1)
            assert all(item["source"] for item in evidence["inputs"])
