"""P44b ranking, denominator, and replay regressions."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from src.consensus_shortlist_p44b import SMOOTH, count_frequencies, verify_legacy
from src.consensus_shortlist import threshold_keys


def test_all_variant_cells_count_with_baseline_first_and_unique_top_three(tmp_path):
    def cells(draw):
        codes = np.array([1, 1, 2, 3, 4])
        old_rank = np.array([[.6], [.6], [.6], [.8], [.2]])
        for name in ("original", SMOOTH):
            scores = old_rank.copy()
            if name == SMOOTH:
                scores[2] = .9
            if draw != "nominal" and name == SMOOTH:
                scores[2] = .6
            yield name, codes, scores, np.array([True, False, True, True, False]), np.array(
                [False, True, True, True, False])

    replay = SimpleNamespace(
        ids=range(5), width=1, cells=cells, model="nominal", draws=lambda: iter((0, 1)),
        samples=(0, 1), legacy=("original",), names=("original", SMOOTH), encode=int,
        saved_p22={"presets": {"balanced": {"joint": {"winners": [{"cycle": 3, "count": 2}]}}}},
    )
    old = {"rotation_count": 3, "cells_per_preset": 2}
    path = tmp_path / "legacy.csv"
    pd.DataFrame({"rotation_key": [1, 2, 3], "cells_per_preset": [2, 2, 2],
                  "balanced_top1_count": [0, 0, 2], "balanced_top3_count": [2, 2, 2]}).to_csv(path, index=False)
    expected = {"original": {"balanced": (3, 0)}, SMOOTH: {"balanced": (2, 1)}}
    weights = {"balanced": np.array([1])}
    replayed = count_frequencies(replay, weights, [1], expected, old, path)
    first, third = replayed["counts"]["balanced"]
    assert first == {3: 4}
    assert third == {1: 4, 2: 4, 3: 4}
    assert replayed["baseline_hits"]["balanced"] == [0, 4]
    assert replayed["flagged_baselines"] == 4
    assert threshold_keys(third, 4, 60) == {1, 2, 3}


def test_p44_reproduction_rejects_a_missing_count(tmp_path):
    path = tmp_path / "old.csv"
    pd.DataFrame({"rotation_key": [0], "cells_per_preset": [1],
                  "x_top1_count": [1], "x_top3_count": [1]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="top3 counts"):
        verify_legacy(path, {"rotation_count": 1, "cells_per_preset": 1}, np.array([True]),
                      {"x": {0: 1}}, {"x": {0: 0}})
