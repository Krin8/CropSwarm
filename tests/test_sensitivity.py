from dataclasses import replace
import json

import numpy as np
import pandas as pd
import pytest

from src.evidence import FIELD_SOURCES
from src.scoring import METRICS, ROOT, preload
from src.sensitivity import ExactSearch, analyse, apply_values, check_first, inventory, numeric, rank_inputs

DESIGN = json.loads((ROOT / "config/sensitivity.json").read_text())
POLICY = json.loads((ROOT / "config/scoring.json").read_text())


@pytest.fixture
def sample(tmp_path):
    labels = ["warm"]
    farm = {"farm_id": "sample", "seasons_per_year": 1, "seasons_basis": "assumption, validate locally",
            "irrigation": {"supply_fraction": 0., "basis": "assumption, validate locally"},
            "baseline_rotation_cycle": [["a"]], "baseline_source": "assumption, validate locally"}
    seasons = {"slots": [{"eligible_labels": labels}], "season_windows": {
        "warm": {"onset_month": 4, "cessation_month": 5, "source": "fixture"}}}
    crop = {"display_name": "Crop", "seasons_allowed": labels, "season_length_days": 50,
            "heat_tolerance_c": 35., "min_temp_c": 15., "max_temp_c": 30., "min_rain_mm": 0.,
            "max_rain_mm": 500., "n_credit_kg_ha": 0., "n_demand_kg_ha": 20., "cover_score": .5,
            "relative_income_index": .5, "disease_family": "family", "water_need_mm": 100.,
            "seasons_source": farm["seasons_basis"], **dict.fromkeys(FIELD_SOURCES.values(), farm["seasons_basis"])}
    crops = {"a": crop, "b": {**crop, "display_name": "Bean", "n_credit_kg_ha": 10., "water_need_mm": 117.,
                            "water_need_source": "Fixture (104–120 mm) https://example.invalid/fixture"}}
    context = {"soil": {"available_water_mm_0_30": {"value": 10., "source": "fixture"}},
               "terrain": {"mean_slope_pct": {"value": 4.}}}
    (tmp_path / "context_sample.json").write_text(json.dumps(context))
    dates = pd.date_range("2001-01-01", "2003-12-31")
    rain = np.where(dates.month == 4, 2.5, 0.)
    climate = pd.DataFrame({"PRECTOTCORR": rain, "T2M": 20., "T2M_MAX": 30.}, index=dates)

    def prepare(farm, crops, policy, calendar):
        return preload(farm, processed=tmp_path, crops=crops, policy=policy, season_calendar=calendar, climate=climate)

    model = prepare(farm, crops, POLICY, seasons)

    def rebuild(inputs, values):
        return prepare(*apply_values(model, seasons, inputs, values))

    inputs = inventory(model, seasons, {"verified_crop_source_urls": ["example.invalid"]}, DESIGN)
    return model, seasons, {row.key: row for row in inputs}, rebuild


def test_sweep_uses_existing_scores_and_changes_feasibility(sample):
    model, seasons, inputs, rebuild = sample
    assert inputs["irrigation"].bounds == (0, .2)
    assert inputs["b.water_need_mm"].bounds == (104, 120)
    assert inputs["b.water_need_mm"].grade == "literature"
    assert not inputs["a.n_credit_kg_ha"].levels
    changed = rebuild([inputs["warm.onset_month"]], [1])
    assert changed.days[0, 0][1] == 5 and not changed.suitable[0, 0]
    assert model.days[0, 0][1] == 4 and model.suitable[0, 0]
    assert seasons["season_windows"]["warm"]["onset_month"] == 4
    irri = rebuild([inputs["irrigation"]], [.2])
    assert irri.additions[0, 0, 1] == pytest.approx(model.additions[0, 0, 1] * .8)


def test_canonical_winner_and_baseline_tie(sample):
    model, _, inputs, rebuild = sample
    presets = {"priority": {m: float(m == "nitrogen") for m in METRICS}}
    search = ExactSearch(presets, 2, 1, DESIGN["near_tie_gap"])
    assert search.rotations(((0, 1), (0, 1))).tolist() == [[0, 1]]
    original = search.evaluate(model)
    assert original.winners.tolist() == [[0, 1]]
    new = rebuild([inputs["b.seasons_allowed"]], [()])
    excluded = search.evaluate(new, original.winners)
    assert excluded.winners.tolist() == [[0, 0]]
    assert excluded.material_changes.tolist() == [True]
    equal_scores = replace(model, demand=np.array([20., 20.]), credits=np.zeros(2))
    assert search.evaluate(equal_scores).winners.tolist() == [[0, 0]]


def test_ranking_and_text_keep_ties_and_weak_effects(sample):
    _, _, inputs, _ = sample
    effects = [
        ("irrigation", .8, .09), ("warm.onset_month", .8, .09),
        ("max_hot_day_fraction", 0, .005),
    ]
    rows = [{"key": key, "question": inputs[key].question, "grade": inputs[key].grade,
             "source": inputs[key].source, "one_at_a_time": {
                 "material_change_fraction": change, "top_score_span": span, "reference_excluded_fraction": 0, "evaluations": 5}}
            for key, change, span in reversed(effects)]
    ranked = rank_inputs(rows, DESIGN)
    assert [row["rank"] for row in ranked] == [1, 1, 3]
    assert [row["weak"] for row in ranked] == [False, False, True]
    text = check_first(ranked)
    assert text[0]["question"] == inputs["irrigation"].question
    assert "80%" in text[0]["reason"] and "shares this priority" in text[0]["reason"]
    assert "small effect" in text[2]["reason"]
    assert all(row["grade"] == "assumption" for row in text)


def test_fixed_seed_reproduces_sweep_and_joint_results(sample):
    model, _, inputs, rebuild = sample
    config = {**DESIGN, "joint_draws": 32}
    selected = [inputs[key] for key in ("irrigation", "b.seasons_allowed", "baseline", "b.water_need_mm")]
    presets = {"water": {m: float(m == "water") for m in METRICS}}
    result = analyse(model, presets, config, selected, 2, rebuild)
    assert result == analyse(model, presets, config, selected, 2, rebuild)
    assert result["input_count"] == len(selected)
    assert result["sweep_evaluations"] == sum(len(row.levels) for row in selected)
    output = result["presets"]["water"]
    assert output["joint"]["evaluations"] == config["joint_draws"]
    assert all(row["one_at_a_time"]["evaluations"] for row in output["ranking"])
    assert {row["joint_association"]["method"] for row in output["ranking"]} == {"Spearman ρ", "rank η"}
    assert output["joint"]["top_score_range"][0] <= output["reference_top_score"] <= output["joint"]["top_score_range"][1]
