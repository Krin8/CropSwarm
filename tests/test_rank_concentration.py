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
