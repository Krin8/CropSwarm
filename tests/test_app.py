import json

import pytest
from streamlit.testing.v1 import AppTest

from src.scoring import ROOT


@pytest.mark.parametrize("site", ["us_high_plains_b", "telangana_a", "kenya_makueni_north"])
def test_offline_farm_scenario_clickthrough(site, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("Streamlit attempted to contact the network")

    monkeypatch.setattr("requests.sessions.Session.request", no_network)
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    assert not app.exception
    app.selectbox(key="farm_picker").set_value(site).run()
    assert not app.exception
    next(widget for widget in app.selectbox if widget.label == "Scenario").set_value("warmer_drier").run()
    assert not app.exception
    assert any(len(table.value) == 5 and "Strategy" in table.value.columns for table in app.dataframe)
    assert any("Validation · historical back-test" in row.value for row in app.subheader)
    assert any(row.value == "Opportunity windows" for row in app.subheader)
    assert any("QA-valid composites · NDVI evidence" in row.value for row in app.caption)
    assert any("Recurrent windows" in table.value.columns for table in app.dataframe)
    assert any("NASA climate and vegetation check" in row.label for row in app.expander)
    counts = next(table.value for table in app.dataframe if "Intervals excluding zero" in table.value.columns)
    assert list(counts["Comparisons"]) == [24, 36, 10]
    assert list(counts["Correlations computed"]) == [12, 36, 10]
    assert list(counts["Intervals available"]) == [12, 36, 10]
    assert list(counts["Intervals excluding zero"]) == [4, 11, 3]
    assert any("58 of 70 comparisons" in row.value and "18 bootstrap intervals" in row.value for row in app.markdown)
    p15 = next(table.value for table in app.dataframe if "Comparison" in table.value.columns)
    p19 = next(table.value for table in app.dataframe if "MODIS response" in table.value.columns)
    assert len(p15) == 8
    assert len(p19) == 12
    assert any(row.label == "Yield back-test" for row in app.expander)
    yield_tables = [table.value for table in app.dataframe if "Paired n" in table.value.columns]
    if site == "kenya_makueni_north":
        assert not yield_tables
        assert any("A comparable seasonal yield series was not verified" in row.value for row in app.caption)
    else:
        assert len(yield_tables) == 1
        assert list(yield_tables[0]["Paired n"]) == (
            [20, 20, 17, 17, 27, 27, 25, 25] if site == "us_high_plains_b" else [27, 27])
    assert any(len(table.value) == 24 and "Passes QA" in table.value.columns for table in app.dataframe)
    assert any("Robustness check under weather shifts (P16)" in row.value for row in app.subheader)
    assert any("P22 sweeps broader assumptions jointly" in row.value for row in app.caption)
    assert any("P10 resamples weather and varies modeled parameters within ±18%" in row.value for row in app.caption)
    assert any("GPM IMERG via POWER is used only for the rainfall agreement check" in row.value for row in app.caption)
    assert any(row.value == "What to check first" for row in app.subheader)
    assert any("sensitivity inside the model" in row.value for row in app.caption)
    assert sum("Input evidence" in row.value for row in app.caption) == 3
    assert any("Joint association with top score" in table.value.columns for table in app.dataframe)
    assert any("Evidence labels:" in row.value for row in app.caption)
    assert any("Evidence" in table.value.columns for table in app.dataframe)
    assert not any("Near-duplicate metric profile" in row.value for row in app.info)
    if site != "telangana_a":
        assert any("top choices are close here" in row.value for row in app.info)
    assert any("What we cannot know" in row.value for row in app.subheader)
    if site == "kenya_makueni_north":
        assert any("cropland unverified" in row.value for row in app.warning)
        assert any("No reliable recurring low-greenness window" in row.value for row in app.info)
    if site == "telangana_a":
        assert any("Identical consecutive crop" in row.value for row in app.warning)
        assert any("No reliable recurring low-greenness window" in row.value for row in app.info)
        fit = next(table.value for table in app.dataframe if "Overall fit" in table.value.columns)
        assert "Cereal rye cover" not in set(fit["Crop"])


def test_sensitivity_panel_uses_the_selected_named_preset():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    next(widget for widget in app.selectbox if widget.label == "Start from a priority preset").set_value("income").run()
    data = json.loads((ROOT / "data/processed/sensitivity_us_high_plains_b.json").read_text())
    first = data["presets"]["income"]["ranking"][0]
    assert not app.exception
    assert any(row.value == f"**Priority {first['rank']} · {first['question']}**" for row in app.markdown)
    assert any("Income" in row.value and "inputs varied" in row.value for row in app.caption)


def test_opportunity_alternate_threshold_reports_modeled_changes_without_hiding_caveats():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    app.selectbox(key="opportunity_threshold_us_high_plains_b").set_value(.30).run()
    assert not app.exception
    assert any("alternative cutoff" in row.value for row in app.info)
    assert any("fits the screen in 1 of 15 years" in row.value for row in app.markdown)
    assert any("cost to the following crop" in row.value for row in app.caption)
    benefit = next(table.value for table in app.dataframe if "Median change" in table.value.columns)
    assert len(benefit) == 4 and set(benefit["Evidence"]) == {"LOW"}
    assert set(benefit["Crop"]) == {"Cereal rye cover"}
    fit = next(table.value for table in app.dataframe if "Overall fit" in table.value.columns)
    assert "Green gram (mung bean)" not in set(fit["Crop"])
    assert any("may be winter-wheat dormancy, not bare soil" in row.value for row in app.warning)
    assert any("No reliable planting window" in row.value for row in app.info)
    app.selectbox(key="opportunity_year_us_high_plains_b").set_value(2012).run()
    assert not app.exception


def test_learned_county_yield_panel_compares_models_and_baselines():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    app.selectbox(key="climate_yield_split").set_value("leave_one_county_out").run()
    app.selectbox(key="climate_yield_model").set_value("random_forest").run()
    assert not app.exception
    assert any(row.label == "Learned climate-yield check" for row in app.expander)
    assert any("103 counties" in row.value and "3,215 county-years" in row.value for row in app.markdown)
    performance = next(table.value for table in app.dataframe if "RMSE (bu/acre)" in table.value.columns)
    assert set(performance["Model"]) == {"County mean", "Linear trend", "Ridge", "Random forest"}
    assert any("RMSE change when shuffled (bu/acre)" in table.value.columns for table in app.dataframe)
    assert any("cannot establish causation" in row.value for row in app.caption)
    assert any("Paired RMSE change versus the linear trend" in row.value for row in app.caption)


def test_learned_yield_panel_preserves_p25_and_shows_practice_and_spatial_checks():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    assert app.selectbox(key="climate_yield_split").value == "leave_one_district_out"
    assert any("USDA district holdout" in row.value and "Random forest 9.034" in row.value
               and "Linear trend 10.758" in row.value for row in app.markdown)
    table = next(table.value for table in app.dataframe if "RMSE (bu/acre)" in table.value.columns)
    assert table.set_index("Model")["RMSE (bu/acre)"]["County mean"].startswith("11.202 ")
    app.selectbox(key="climate_yield_split").set_value("leave_one_year_out").run()
    year_table = next(table.value for table in app.dataframe if "RMSE (bu/acre)" in table.value.columns)
    assert year_table.set_index("Model")["RMSE (bu/acre)"]["County mean"].startswith("10.819 ")
    for cohort, n in (("pooled", "3,215"), ("non_irrigated", "2,005"), ("all_practices", "1,210")):
        app.selectbox(key="climate_yield_cohort").set_value(cohort).run()
        app.selectbox(key="climate_yield_split").set_value("leave_one_district_out").run()
        assert not app.exception
        assert any(f"{n} county-years" in row.value for row in app.caption)
        assert any("9 held-out folds" in row.value for row in app.caption)
        assert any("holds out one entire USDA reporting district" in row.value for row in app.caption)
        table = next(table.value for table in app.dataframe if "RMSE (bu/acre)" in table.value.columns)
        assert len(table) == 4


def test_robust_pick_shows_all_objectives_and_changes_with_preset():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    next(widget for widget in app.selectbox if widget.label == "Start from a priority preset").set_value("income").run()
    assert not app.exception
    assert any(row.value == "Robust pick under assumption changes (P28b)" for row in app.subheader)
    rows = next(table.value for table in app.dataframe if "Nominal score cost" in table.value.columns)
    assert list(rows["Pick"]) == ["Nominal score leader", "Expected score", "Feasible-only worst 10% mean", "Minimax regret"]
    assert set(rows["Evidence"]) == {"LOW"}
    assert set(rows["Across draw counts"]) <= {"Reference", "Same pick", "Pick changes"}
    assert any("Original zero-score CVaR rule at 512 draws" in row.value for row in app.caption)
    app.selectbox(key="robust_draw_count").set_value(128).run()
    assert not app.exception
    assert any("Original zero-score CVaR rule at 128 draws" in row.value for row in app.caption)
    finalists = next(table.value for table in app.dataframe if "Gap to optimum" in table.value.columns)
    assert len(finalists) == 9 and list(finalists["Place"]).count("Runner-up") == 3
    assert any("expected score 8 of 12, conditional CVaR 6 of 12, minimax regret 2 of 12" in line.value
               for line in app.caption)


def test_robust_pick_shows_original_and_held_out_telangana_swarm_results():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    app.selectbox(key="farm_picker").set_value("telangana_a").run()
    assert not app.exception
    info = next(row.value for row in app.info if "Telangana CVaR swarm check" in row.value)
    assert "Original rule: 0/10 exact hits" in info
    assert "the original search reached 10/10" in info
    assert "search reached 10/10 in best-of-five trials" in info


def test_download_brief_tracks_farm_and_named_preset():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    app.selectbox(key="farm_picker").set_value("telangana_a").run()
    next(widget for widget in app.selectbox if widget.label == "Start from a priority preset").set_value("income").run()
    assert not app.exception
    assert any("Farm decision brief · Telangana A · Income preset" in item.value for item in app.caption)
    labels = {item.proto.label for item in app.get("download_button")}
    assert "Download brief (HTML)" in labels



def test_robust_pick_flags_rare_feasibility_for_nominal_pick_and_finalists():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    app.selectbox(key="farm_picker").set_value("kenya_makueni_north").run()
    next(widget for widget in app.selectbox if widget.label == "Start from a priority preset").set_value("income").run()
    assert not app.exception
    warning = "rarely feasible; not a practical recommendation"
    rows = next(table.value for table in app.dataframe if "Nominal score cost" in table.value.columns)
    rare = rows[rows["Feasibility flag"] == warning]
    assert set(rare["Pick"]) == {"Nominal score leader", "Feasible-only worst 10% mean"}
    assert "108/512 (21.1%)" in set(rare["Feasible draws"])
    finalists = next(table.value for table in app.dataframe if "Gap to optimum" in table.value.columns)
    assert all((int(row["Feasible draws"].split("/")[0]) < 256) == (row["Feasibility flag"] == warning)
               for _, row in finalists.iterrows())
    assert any("has a near-tie with its runner-up" in row.value for row in app.info)
    assert any("preliminary" in row.value and "Picks changed across draw counts" in row.value for row in app.markdown)
