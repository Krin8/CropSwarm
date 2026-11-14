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
    assert any("What we cannot know" in row.value for row in app.subheader)
    if site == "kenya_makueni_north":
        assert any("cropland unverified" in row.value for row in app.warning)
    if site == "telangana_a":
        assert any("Identical consecutive crop" in row.value for row in app.warning)
