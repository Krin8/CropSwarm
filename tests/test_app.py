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
    assert any("Robustness check" in row.value for row in app.subheader)
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
    if site == "telangana_a":
        assert any("Identical consecutive crop" in row.value for row in app.warning)


def test_sensitivity_panel_uses_the_selected_named_preset():
    app = AppTest.from_file(str(ROOT / "app/main.py")).run()
    next(widget for widget in app.selectbox if widget.label == "Start from a priority preset").set_value("income").run()
    data = json.loads((ROOT / "data/processed/sensitivity_us_high_plains_b.json").read_text())
    first = data["presets"]["income"]["ranking"][0]
    assert not app.exception
    assert any(row.value == f"**Priority {first['rank']} · {first['question']}**" for row in app.markdown)
    assert any("Income" in row.value and "inputs varied" in row.value for row in app.caption)
