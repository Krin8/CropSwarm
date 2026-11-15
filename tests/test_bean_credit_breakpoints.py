"""P51 exact ranking, endpoints and matched-draw tests."""

from dataclasses import dataclass
import json

import numpy as np
import pytest

from src.bean_credit_breakpoints import CATALOG, DRAW_CREDITS, GRID_SOURCES, OUTPUT, build, leader_runs, replay, top_two
from src.bean_credit_report import DOCUMENT, render
from src.scoring import ROOT
from src.sensitivity import Outcome


@dataclass
class SimpleModel:
    ids: list
    crops: dict
    credits: np.ndarray
    nitrogen_bounds: tuple
    season_labels: list
    threshold: float


def test_top_two_resolve_equal_scores_in_canonical_order_and_keep_precision():
    rows = np.array([[1, 2], [1, 3], [2, 3]])
    result = top_two(np.array([0.5, 0.7, 0.7]), rows, list, 0.01)
    assert result["leader"]["rotation"] == [1, 3]
    assert result["runner_up"]["rotation"] == [2, 3]
    assert result["gap"] == 0
    assert result["near_tie"]
    assert top_two(np.array([0.0, 0.01, 0.0]), rows, list, 0.01)["near_tie"]
    assert not top_two(np.array([0.0, 0.010001, 0.0]), rows, list, 0.01)["near_tie"]


def test_leader_runs_keep_brackets_and_mark_reentry():
    def point(credit, leader, close):
        return {"credit": credit, "leader": {"rotation": [leader]}, "near_tie": close}

    points = [point(0.7, 1, False), point(22, 1, True), point(30, 2, False),
              point(44, 3, False), point(80, 1, True)]
    result = leader_runs(points)
    assert not result["retains_catalog_leader"]
    assert [row["catalog_leader"] for row in result["leader_intervals"]] == [True, False, False, True]
    assert result["leader_intervals"][0]["first_credit"] == 0.7
    assert result["leader_intervals"][0]["last_credit"] == 22
    assert [(row["before"]["credit"], row["after"]["credit"], row["near_tie"])
            for row in result["breakpoints"]] == [(22, 30, True), (30, 44, False), (44, 80, True)]
    assert leader_runs(points[:2])["retains_catalog_leader"]


def test_replay_fixes_credit_for_each_paired_draw_without_mutating_inputs():
    def model(bean, threshold):
        return SimpleModel(["common_bean", "maize"], {"common_bean": {"n_credit_kg_ha": bean}},
                           np.array([bean, 0.]), (-1, bean), ["season"], threshold)

    class Search:
        def evaluate(self, counterfactual, reference=None):
            winner = np.array([[int(counterfactual.credits[0] < counterfactual.threshold)]])
            changed = (winner != reference).any(axis=1) if reference is not None else np.array([False])
            return Outcome(winner, np.array([0.7]), np.array([0.6]), changed, np.array([True]))

    original = model(22., 25.)
    draws = [model(19., 20.), model(23., 80.), model(24., 45.)]
    result = replay(original, Search(), ["balanced"], draws)["balanced"]
    assert [row["paired_disagreement_count"] for row in result] == [0, 0, 2]
    assert result[2]["paired_disagreement_fraction"] == pytest.approx(2 / 3)
    assert result[0]["winner_change_fraction"] == pytest.approx(1 / 3)
    assert result[1]["winner_change_fraction"] == pytest.approx(2 / 3)
    assert [draw.credits[0] for draw in draws] == [19, 23, 24]
    assert replay(original, Search(), ["balanced"], draws)["balanced"] == result


def test_committed_p51_rebuilds_byte_for_byte(tmp_path):
    saved = ROOT / "data/processed" / OUTPUT
    output = tmp_path / OUTPUT
    report = build(output=output)
    assert output.read_bytes() == saved.read_bytes()
    assert render(report) == (ROOT / "docs" / DOCUMENT).read_text()


def test_saved_results_show_all_grid_settings_draw_counts_and_fixed_metrics():
    report = json.loads((ROOT / "data/processed" / OUTPUT).read_text())
    assert [row["credit"] for row in report["credit_grid"]] == list(GRID_SOURCES)
    assert report["canonical_count"] == 16914
    expected = {"water_saver": (68, 80), "soil_builder": (30, 44), "income": (68, 80), "balanced": (68, 80)}
    for preset, result in report["presets"].items():
        assert [row["credit"] for row in result["grid"]] == list(GRID_SOURCES)
        edge, = result["breakpoints"]
        assert (edge["before"]["credit"], edge["after"]["credit"]) == expected[preset]
        assert edge["before"]["near_tie"] and edge["after"]["near_tie"] and edge["near_tie"]
        assert [row["credit"] for row in result["matched_draws"]] == list(DRAW_CREDITS)
        for row in result["matched_draws"]:
            assert sum(winner["count"] for winner in row["winners"]) == row["evaluations"] == 512
        assert result["matched_draws"][0]["paired_disagreement_count"] == 0

    options = report["published_strategies"]
    reference = next(row["strategies"] for row in options if row["credit"] == CATALOG)
    for row in options:
        for i, strategy in enumerate(row["strategies"]):
            assert strategy["flags"] == reference[i]["flags"]
            assert strategy["rotation"] == reference[i]["rotation"]
            for name, metric in strategy["metrics"].items():
                assert metric["source"] and metric["evidence_label"]
                assert metric["delta"] == pytest.approx(metric["value"] - reference[i]["metrics"][name]["value"])
                assert metric["score_delta"] == pytest.approx(
                    metric["score"] - reference[i]["metrics"][name]["score"])
                if name != "nitrogen":
                    assert metric["delta"] == metric["score_delta"] == 0
    baseline, water_saver, *_ = options[-1]["strategies"]
    assert baseline["metrics"]["nitrogen"]["delta"] == 29
    assert water_saver["metrics"]["nitrogen"]["delta"] == 0
    assert water_saver["metrics"]["nitrogen"]["score_delta"] < 0
