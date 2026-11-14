import copy
import json

import pytest

from src.crops import load_crops
from src.localize import Locale, validate_locales
from src.scoring import METRICS, ROOT


@pytest.fixture(scope="module")
def inputs():
    farms = json.loads((ROOT / "config/farms.json").read_text())
    return {"data": json.loads((ROOT / "config/locales.json").read_text(encoding="utf-8")), "farms": farms,
            "crops": load_crops(ROOT / "data/crops.csv", farms=farms),
            "presets": json.loads((ROOT / "config/weights_presets.json").read_text())["presets"]}


def check(inputs, data):
    return validate_locales(data, inputs["farms"], inputs["crops"], METRICS, inputs["presets"])


def test_committed_wording_is_valid_and_bundled_for_the_offline_app(inputs):
    check(inputs, inputs["data"])
    bundle = json.loads((ROOT / "data/processed/app_settings.json").read_text())
    assert bundle["locales"] == inputs["data"]


@pytest.mark.parametrize("damage", [
    lambda data: data["metrics"]["water"]["meaning"].pop("te"),
    lambda data: data["glossary"][0]["term"].pop("sw"),
    lambda data: data["farms"]["telangana_a"]["crop_names"].pop("paddy"),
    lambda data: data["farms"]["telangana_a"]["crop_names"].update(not_a_crop="x"),
    lambda data: data["farms"]["us_high_plains_b"]["units"].update(depth="feet"),
    lambda data: data["farms"].pop("kenya_makueni_north"),
    lambda data: data["presets"].pop("balanced"),
])
def test_incomplete_wording_is_rejected(inputs, damage):
    data = copy.deepcopy(inputs["data"])
    damage(data)
    with pytest.raises(ValueError):
        check(inputs, data)


def test_local_names_units_and_english_fallback(inputs):
    data = inputs["data"]
    telugu = Locale(data, "telangana_a", "te")
    english = Locale(data, "telangana_a", "en")
    assert telugu.crop("paddy", "Paddy rice") == "వరి (Paddy rice)"
    assert english.crop("paddy", "Paddy rice") == "Paddy rice (వరి)"
    assert Locale(data, "us_high_plains_b").crop("sorghum", "Grain sorghum") == "Grain sorghum"
    window = {"onset_month": 6, "cessation_month": 9}
    assert english.season("monsoon", window) == "Kharif (Vanakalam) · Jun–Sep"
    assert telugu.season("monsoon", window) == "వానాకాలం (ఖరీఫ్) · Jun–Sep"
    assert english.season("warm") == "Warm"
    # A language the farm does not offer falls back to English, as does any untranslated text.
    assert Locale(data, "us_high_plains_b", "te").language == "en"
    assert Locale(data, "kenya_makueni_north", "sw").text("existing_rotation") == "Mzunguko wa sasa"
    assert "rupees" in english.metric_meaning("income")
    assert "US dollars" in Locale(data, "us_high_plains_b").metric_meaning("income")
    assert telugu.glossary(draws=500)[0][0].endswith("(Rotation)")
    assert "500" in " ".join(meaning for _, meaning in english.glossary(draws=500))


def test_unit_conversion_is_display_only_and_reversible(inputs):
    kansas = Locale(inputs["data"], "us_high_plains_b")
    assert kansas.unit("depth") == "in" and kansas.to_local("depth", 25.4) == pytest.approx(1)
    assert kansas.to_local("area", 1) == pytest.approx(2.4711, abs=1e-4)
    assert kansas.to_local("nitrogen", 100) == pytest.approx(89.22, abs=.01)
    assert Locale(inputs["data"], "telangana_a").to_local("nitrogen", 100) == pytest.approx(40.47, abs=.01)
    for kind in ("area", "depth", "nitrogen"):
        assert kansas.to_metric(kind, kansas.to_local(kind, 60.2)) == pytest.approx(60.2)
    metric = Locale(inputs["data"], "us_high_plains_b", local_units=False)
    assert [metric.unit(kind) for kind in ("area", "depth", "nitrogen")] == ["ha", "mm", "kg/ha"]
    assert metric.metric_value("water", 120.0) == (120.0, "mm of water short per season")
    value, unit = kansas.metric_value("water", 127.0)
    assert value == pytest.approx(5) and unit.startswith("in ")
    assert kansas.metric_value("income", .5)[0] == .5
