"""P46 substitutions use the original mechanics and preserve the source model."""

from copy import deepcopy
import json

import numpy as np
import pytest

from src.crops import load_crops
from src.regional_scoring_variants import MAKUENI, TELANGANA, design, nominal_comparison, regional_model
from src.scoring import ROOT, baseline_indices, preload, score_rotations


def read(path):
    return json.loads((ROOT / path).read_text())


def test_design_contains_every_pair_and_checks_p45_bounds():
    crops = load_crops(ROOT / "data/crops.csv")
    evidence = read("data/p45_literature.json")
    corrections, cases = design(crops, evidence)
    assert len({(case["makueni"], case["telangana"]) for case in cases}) == len(cases) == 16
    assert corrections[MAKUENI]["values"] == {"original": 22, "low": 44, "mid": 62, "high": 80}
    assert corrections[TELANGANA]["values"] == {"original": 575, "low": 473.9, "mid": 565.85, "high": 657.8}
    changed = deepcopy(crops)
    changed["paddy"]["water_need_mm"] = 300
    with pytest.raises(ValueError, match="differ from the P46 plan"):
        design(changed, evidence)


@pytest.mark.parametrize("farm_id", [MAKUENI, TELANGANA])
def test_overlay_matches_rebuilding_the_unmodified_scorer(farm_id):
    farm = next(row for row in read("config/farms.json") if row["farm_id"] == farm_id)
    model = preload(farm)
    specs, _ = design(model.crops, read("data/p45_literature.json"))
    correction = specs[farm_id]
    variant = regional_model(model, correction, "high")
    crop_id, field = correction["crop"], correction["field"]
    expected_catalog = deepcopy(model.crops)
    expected_catalog[crop_id][field] = correction["values"]["high"]
    expected = preload(farm, crops=expected_catalog)
    sequence = baseline_indices(model)
    for actual, rebuilt in zip(score_rotations(variant, sequence)[:2],
                               score_rotations(expected, sequence)[:2], strict=True):
        np.testing.assert_array_equal(actual, rebuilt)
    np.testing.assert_array_equal(variant.suitable, expected.suitable)
    np.testing.assert_array_equal(variant.additions, expected.additions)
    assert variant.nitrogen_bounds == expected.nitrogen_bounds
    assert model.crops[crop_id][field] == correction["values"]["original"]
    assert regional_model(model, None, "original") is model


def test_nominal_ranks_separate_pool_membership_and_top_two_changes():
    farm = next(row for row in read("config/farms.json") if row["farm_id"] == MAKUENI)
    model = preload(farm)
    rows = np.arange(8).reshape(4, 2)
    old = np.array([.8, .799, .2, .5])
    new = np.array([.9, .65, .35, .7])
    result = nominal_comparison(model, rows, old, new, np.array([True, True, True, False]),
                                np.array([False, True, True, True]), .01)
    assert result["label_changed"] and not result["original_still_feasible"]
    assert result["near_tie_disappeared"] and not result["near_tie_appeared"]
    assert result["added_count"] == result["excluded_count"] == 1
    assert result["common_count"] == 2 and result["rank_spearman"] == pytest.approx(1)
