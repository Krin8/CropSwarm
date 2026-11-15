"""Rank, threshold, dominance and isolated reproducibility tests for P44."""

from collections import Counter

import numpy as np

from src.consensus_shortlist import ranks, strict_dominator, threshold_keys


def test_top_three_uses_distinct_admitted_rows_and_baseline_first_ties():
    matrix = np.array([[.9, .5], [.9, .5], [.9, .5], [.7, .4], [1., 1.]])
    weights = np.array([.5, .5])
    np.testing.assert_array_equal(ranks(matrix, weights, np.array([True, False, True, True, False])),
                                  [0, 2, 3])
    assert ranks(matrix, weights, np.array([False, False, True, False, False])) == [2]


def test_threshold_counts_include_exact_bound_and_keep_ineligible_in_denominator():
    top = Counter({4: 5, 7: 4, 3: 6, 5: 0})
    assert threshold_keys(top, 10, 40) == {3, 4, 7}
    assert threshold_keys(top, 10, 50) == {3, 4}
    assert threshold_keys(top, 10, 60) == {3}
    assert threshold_keys(top, 10, 70) == set()


def test_strict_dominance_requires_six_better_metrics_and_a_feasible_witness():
    target = np.full(6, .2)
    scores = np.array([[.3] * 6, [.2, .4, .4, .4, .4, .4], [.2 + 1e-13] * 6])
    assert strict_dominator(scores, np.array([True, True, True]), target)
    assert not strict_dominator(scores, np.array([False, True, True]), target)
    assert not strict_dominator(scores, np.array([False, False, False]), target)
