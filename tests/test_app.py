import json
import re

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
    assert not any("Validation · historical back-test" in row.value for row in app.subheader)
    app.toggle(key="show_technical").set_value(True).run()
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
    assert any(row.value == "Robustness check under weather shifts" for row in app.subheader)
    assert any("varies many assumptions together and repeats the full search" in row.value for row in app.caption)
    assert any("shifts the crop values by up to ±18%" in row.value for row in app.caption)
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
        assert any("The same crop is grown twice in a row" in row.value for row in app.warning)
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
    app.toggle(key="show_technical").set_value(True).run()
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
    app.toggle(key="show_technical").set_value(True).run()
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


def visible_text(app):
    values = [row.value for kind in ("title", "header", "subheader", "markdown", "caption", "info", "warning", "success")
              for row in getattr(app, kind)]
    for table in app.dataframe:
        values.extend(map(str, table.value.columns))
        values.extend(table.value.astype(str).to_numpy().ravel())
    for kind in ("selectbox", "slider", "number_input", "radio", "toggle", "expander"):
        values.extend(widget.label for widget in getattr(app, kind))
    return values


@pytest.mark.parametrize("site", ["us_high_plains_b", "telangana_a", "kenya_makueni_north"])
def test_farmer_view_hides_technical_panels_and_internal_phase_labels(site):
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    app.selectbox(key="farm_picker").set_value(site).run()
    assert not app.exception
    text = visible_text(app)
    assert not [value for value in text if re.search(r"\bP\d{1,2}[a-z]?\b", value)]
    assert not any("Spearman" in value or "Bootstrap" in value for value in text)
    assert not any(row.value == "Opportunity windows" for row in app.subheader)
    assert any(row.label == "What do these words mean?" for row in app.expander)
    assert any(value.startswith("**Best in test runs** ·") for value in text)
    assert any(value.startswith("In plain words · Rain averages about") for value in text)
    assert all(widget.help for widget in app.slider)


def test_telangana_offers_telugu_wording_local_seasons_and_crop_names():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    app.selectbox(key="farm_picker").set_value("telangana_a").run()
    assert any("Kharif (Vanakalam) · Jun–Sep" in widget.label for widget in app.selectbox)
    comparison = next(table.value for table in app.dataframe if "Strategy" in table.value.columns)
    assert comparison["Rotation"][0] == "Every year: Paddy rice (వరి) → Paddy rice (వరి)"
    app.radio(key="language_telangana_a").set_value("te").run()
    assert not app.exception
    assert any(row.value == "పంట క్రమాల పోలిక" for row in app.subheader)
    comparison = next(table.value for table in app.dataframe if "ఎంపిక" in table.value.columns)
    assert list(comparison["ఎంపిక"]) == ["ప్రస్తుత పంట క్రమం", "నీటి పొదుపు", "నేల సారం పెంపు", "ఆదాయం", "సమతుల్యం"]
    assert comparison["పంట క్రమం"][0] == "ప్రతి సంవత్సరం: వరి (Paddy rice) → వరి (Paddy rice)"
    assert any("ముసాయిదా అనువాదం" in row.value for row in app.caption)
    assert any("ఒకే పంటను వరుసగా" in row.value for row in app.warning)
    assert any(row.value.startswith("నిర్ణయం రైతుదే") for row in app.success)
    assert {"నీరు", "నత్రజని", "నేల కోత", "వాతావరణ అనుకూలత", "ఆదాయం", "చీడపీడల ముప్పు"} <= {
        widget.label for widget in app.slider}


def test_kansas_uses_local_units_until_metric_is_chosen():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    assert not any(widget.label == "Language" for widget in app.radio)
    local = next(table.value for table in app.dataframe if "Strategy" in table.value.columns)
    column = "Water shortage · typical (in per season)"
    assert column in local.columns
    assert any(widget.label == "Farm size (acre)" for widget in app.number_input)
    app.radio(key="units_us_high_plains_b").set_value("metric").run()
    assert not app.exception
    metric = next(table.value for table in app.dataframe if "Strategy" in table.value.columns)
    assert list(metric["Water shortage · typical (mm per season)"] / 25.4) == pytest.approx(list(local[column]), abs=.01)
    assert any(widget.label == "Farm size (ha)" for widget in app.number_input)


def test_edited_inputs_in_local_units_recompute_the_comparison():
    app = AppTest.from_file(str(ROOT / "app/main.py"), default_timeout=120).run()
    reference = next(table.value for table in app.dataframe if "Strategy" in table.value.columns)
    soil = next(widget for widget in app.number_input if widget.label.startswith("Water the top 12 in"))
    assert soil.value == pytest.approx(60.2 / 25.4, abs=.005)
    app.slider(key="supply_us_high_plains_b").set_value(50)
    next(button for button in app.button if button.label == "Apply farm inputs").click().run()
    assert not app.exception
    assert any("new exact comparison" in row.value for row in app.caption)
    supply, water_mm, rotation, area_ha = app.session_state["edits_us_high_plains_b"]
    # The untouched soil value keeps the exact metric reference despite being shown in rounded inches.
    assert (supply, water_mm, area_ha) == (.5, 60.2, 0)
    assert rotation == [["fallow"], ["winter_wheat"], ["sorghum"]]
    irrigated = next(table.value for table in app.dataframe if "Strategy" in table.value.columns)
    assert irrigated.iloc[0, 4] < reference.iloc[0, 4]
