import copy

import pytest

from src.validation import (clean_power_value, load_and_validate, validate_farm,
                            validate_metric, validate_weight_presets)


def test_power_fill_and_sourced_metric():
    assert clean_power_value(-999) is None
    assert clean_power_value(12) == 12.0
    metric = {"value": 12, "unit": "mm", "source": "expert estimate, validate locally", "illustrative": True}
    validate_metric(metric)
    with pytest.raises(ValueError, match="source"):
        validate_metric({**metric, "source": ""})


def test_farm_required_fields_and_supply():
    farm = {"farm_id": "test_farm", "name": "Test", "lat": 0, "lon": 0, "region": "Test",
            "tier": 1, "label": "illustrative representative farm",
            "irrigation": {"supply_fraction": 0, "basis": "assumption, validate locally"},
            "baseline_rotation_cycle": [["maize"]], "baseline_source": "assumption, validate locally",
            "seasons_per_year": 1, "seasons_basis": "assumption, validate locally",
            "coordinate_source": "user-selected", "validation_flags": [], "evidence_refs": ["test"]}
    validate_farm(farm)
    for field in farm:
        bad = copy.deepcopy(farm)
        del bad[field]
        with pytest.raises(ValueError, match="missing required"):
            validate_farm(bad)
    for fraction in (-0.01, 1.01):
        bad = copy.deepcopy(farm)
        bad["irrigation"]["supply_fraction"] = fraction
        with pytest.raises(ValueError, match="supply_fraction"):
            validate_farm(bad)
    bad = copy.deepcopy(farm)
    bad["irrigation"]["basis"] = ""
    with pytest.raises(ValueError, match="basis"):
        validate_farm(bad)


def test_weights_sum_and_label():
    data = {"label": "design choice, not empirical", "presets": {
        name: {"water": 1, "nitrogen": 0, "erosion": 0, "climate_fit": 0, "income": 0, "risk": 0}
        for name in ("water_saver", "soil_builder", "income", "balanced")}}
    validate_weight_presets(data)
    bad = copy.deepcopy(data)
    bad["presets"]["balanced"]["water"] = 0.999
    with pytest.raises(ValueError, match="sum"):
        validate_weight_presets(bad)
    bad = copy.deepcopy(data)
    bad["label"] = ""
    with pytest.raises(ValueError, match="label"):
        validate_weight_presets(bad)


def test_checked_in_configs_pass():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    farms = load_and_validate(root / "config/farms.json", "farms")
    assert len(farms) == 3
    load_and_validate(root / "config/weights_presets.json", "weights")
