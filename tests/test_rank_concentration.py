from collections import Counter

import numpy as np
import pytest

from src.rank_concentration import (null_reference, ordered_samples, ranked_prefix, shuffled_null, tails,
                                    top_slots)


def test_rank_percentile_cutoff_and_p44_ties():
    # Exactly 1% of 200 takes two slots. A fractional third slot rounds up.
    assert top_slots(200) == (1, 2, 4)
    assert top_slots(201) == (2, 3, 5)
    assert top_slots(1) == (1, 1, 1)
    # Among three rows tied for second, prefer the first input row at that score.
    assert ranked_prefix(np.array([.8, .9, .8, .2, .8]), 3).tolist() == [1, 0, 2]


def test_samples_are_unique_uniform_prefixes_with_fixed_seed():
    for population, slots in [(7, 4), (30, 17)]:
        draws = ordered_samples(np.random.default_rng(28), population, slots, 1000)
        np.testing.assert_array_equal(draws, ordered_samples(np.random.default_rng(28), population, slots, 1000))
        assert all(len(set(row)) == slots for row in draws)
        firsts = np.bincount(draws[:, 0], minlength=population)
        assert len(firsts) == population and firsts.min() > 0


def test_null_respects_varying_eligibility_count_and_repeats():
    def bits(*entries):
        return np.packbits(entries).tobytes()

    masks = Counter({bits(True, False, False): 2, bits(False, True, False): 1})
    maxima, sizes = shuffled_null(masks, 3, 3, np.random.default_rng(17), replications=32)
    assert (maxima == 2).all() and (sizes == 1).all()
    assert null_reference(maxima[:, 0], sizes[:, 0], 3) == {
        "mean_set_size": 1., "mean_max_share": 2/3, "max_share_95_range": [2/3, 2/3],
    }
    random_masks = Counter({bits(True, True, False): 2, bits(False, True, True): 2})
    result = shuffled_null(random_masks, 3, 4, np.random.default_rng(17), replications=32)
    assert len(np.unique(result[0])) > 1
    repeated = shuffled_null(random_masks, 3, 4, np.random.default_rng(17), replications=32)
    for left, right in zip(result, repeated, strict=True):
        np.testing.assert_array_equal(left, right)
    with pytest.raises(ValueError, match="cell count"):
        shuffled_null(random_masks, 3, 3, np.random.default_rng(17), replications=1)


def test_monte_carlo_tails_include_ties_and_plus_one():
    assert tails(3, 2, np.array([2, 3, 4, 2]), np.array([1, 2, 1, 3])) == {
        "max_share_p": 3/5, "set_size_p": 3/5, "joint_p": 2/5,
    }


def test_saved_analysis_has_all_members_and_matches_p44_scope():
    import json

    from src.rank_concentration import OUTPUT, ROOT
    from src.rank_concentration_report import DOCUMENT, render

    data = ROOT / "data/processed"
    report = json.loads((data / OUTPUT).read_text())
    p44 = json.loads((data / "consensus_shortlist_p44.json").read_text())
    cutoffs = [f"{q:g}" for q in report["design"]["q_pct"]]
    assert cutoffs == ["0.5", "1", "2"]
    assert report["design"]["null_replicates"] >= 1000
    assert "EXPLORATORY" in report["label"]
    assert (ROOT / "docs" / DOCUMENT).read_text() == render(report)
    assert report["farms"].keys() == p44["farms"].keys()
    for farm_id, farm in report["farms"].items():
        old = p44["farms"][farm_id]
        assert farm["p44_counts_reproduced"]
        assert all(farm[key] == old[key] for key in ("variants", "draws", "cells_per_preset", "rotation_count"))
        assert farm["presets"].keys() == old["presets"].keys()
        cells = farm["cells_per_preset"]
        published = json.loads((data / f"strategies_{farm_id}.json").read_text())
        for outcomes in farm["presets"].values():
            assert list(outcomes) == cutoffs
            previous = set()
            for q, row in outcomes.items():
                assert row["size"] == len(row["members"])
                assert all(item["share"] >= .5 for item in row["members"])
                allowed = {item["rotation_key"] for item in row["members"]}
                assert previous <= allowed
                assert all(item["member"] == (item["rotation_key"] in allowed) for item in row["published"])
                assert all(item["share"] == item["count"] / cells for item in row["published"] + row["members"])
                assert [item["strategy"] for item in row["published"]] == [
                    item["strategy_id"] for item in published["strategies"]]
                assert (row["largest_share"] >= .5) == bool(allowed)
                assert 0 < row["joint_p"] <= min(row["max_share_p"], row["set_size_p"]) <= 1
                assert len(farm["null"][q]["max_share_95_range"]) == 2
                previous = allowed
