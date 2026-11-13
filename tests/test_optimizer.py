import itertools
import json

import numpy as np
import pytest

from src.optimizer import count_rotations, enumerate_rotations
from src.scoring import ROOT


def test_exact_enumerator_matches_independent_small_search_with_cycle_boundary():
    layers = [[0, 1, 2], [0, 1], [0, 1, 2]]
    truth = {r for r in itertools.product(*layers) if all(a != b for a, b in zip(r, (*r[1:], r[0])))}
    assert count_rotations(layers, 3) == len(truth)
    assert {tuple(row) for row in enumerate_rotations([np.array(a) for a in layers])} == truth


@pytest.mark.parametrize("farm", json.loads((ROOT / "config/farms.json").read_text()))
def test_cached_results_keep_baseline_and_distinct_candidates(farm):
    path = ROOT / "data/processed" / f"strategies_{farm['farm_id']}.json"
    result = json.loads(path.read_text())
    strategies = result["strategies"]
    assert strategies[0]["strategy_id"] == "baseline"
    assert len({tuple(map(tuple, row["crop_ids"])) for row in strategies}) >= 4
    assert not any(row["flags"] for row in strategies[1:])
    assert all(row["runs"] == 30 and len(row["per_seed_scores"]) == 30
               for row in result["verification"].values())
    for row in result["verification"].values():
        assert all(score <= row["exact_score"] + 1e-10 for score in row["per_seed_scores"])
