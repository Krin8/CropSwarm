from datetime import date
from html.parser import HTMLParser
import json
import re

import pytest

from src.decision_brief import ROOT, reference_inputs, render_brief
from src.scoring import METRICS

PROCESSED = ROOT / "data/processed"
SETTINGS = json.loads((PROCESSED / "app_settings.json").read_text(encoding="utf-8"))
CASES = [(farm, preset) for farm in SETTINGS["farms"] for preset in SETTINGS["weights_presets"]["presets"]]
FORBIDDEN = re.compile(r"\b(?:validated|predicts|proven|tipping[\s-]+point|forecast)\b", re.I)


class DocumentText(HTMLParser):
    """Read body content and count the rows independent of HTML formatting."""

    def __init__(self, html):
        super().__init__()
        self.body = False
        self.text = []
        self.rows = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.body = True
        if tag == "tr":
            self.rows += 1

    def handle_endtag(self, tag):
        if tag == "body":
            self.body = False

    def handle_data(self, data):
        if self.body and data.strip():
            self.text.append(data.strip())


def load(farm_id, prefix):
    return json.loads((PROCESSED / f"{prefix}_{farm_id}.json").read_text(encoding="utf-8"))


@pytest.fixture(params=CASES, ids=[f"{f['farm_id']}-{p}" for f, p in CASES])
def reference_case(request):
    farm, preset = request.param
    return farm, preset, tuple(reference_inputs(load, farm["farm_id"]))


def test_brief_matches_saved_outputs_and_avoids_forbidden_claims(reference_case):
    farm, preset, inputs = reference_case
    assessment, strategies, sensitivity, robust, _, uncertainty, _ = inputs
    date_string, hash_string = "2026-01-02", "1" * 40
    html = render_brief(farm, preset, *inputs, generated_on=date.fromisoformat(date_string), commit=hash_string)
    doc = DocumentText(html)
    text = " ".join(doc.text)
    assert not FORBIDDEN.search(html)
    assert all(line == line.rstrip() for line in html.splitlines())
    assert farm["name"] in text and "illustrative representative farm" in text
    assert date_string in text and hash_string in text
    assert "options to discuss with an extension officer" in text
    assert f'{assessment["metrics"]["longest_observed_dry_spell"]["value"]} days' in text
    assert doc.rows == 5 + 3 + 2
    assert html.count('class="option-label"') == 5
    assert html.count('<ul class="climate">') == 1
    score_rows = strategies["strategies"]
    scores = sorted([entry["objectives"][preset] for entry in score_rows], reverse=True)
    gap = scores[0] - scores[1]
    assert f"{gap:.4f} weighted points" in text
    assert ('<strong>Near-tie · ' in html) == (gap <= sensitivity["design"]["near_tie_gap"])
    for option in score_rows:
        for key in METRICS:
            metric = option["metrics"][key]
            assert f'{metric["score"]:.2f}<span class="grade">{metric["evidence"]["label"]}</span>' in html
        win = uncertainty["scenarios"]["historical"]["strategies"][option["strategy_id"]]["wins_pct"][preset]
        assert f"{win:.1f}%" in text
    for item in sensitivity["presets"][preset]["ranking"][:3]:
        assert item["question"] in text
    results = robust["presets"][preset]
    for objective, entry in results["draw_counts"]["512"]["objectives"].items():
        pick = entry["top"][0]
        assert f'{pick["feasible_draws"]}/512 ({pick["feasible_share"]:.0%})' in text
        label = "Same pick" if results["stability"][objective]["same_pick"] else "Pick changed"
        assert label in text
    assert "Preliminary" in text
    for wording in ("cannot directly measure soil nitrogen", "Results are modeled", "need local validation",
                    "The farmer decides"):
        assert wording in text


def test_brief_escapes_farm_names(reference_case):
    farm, preset, inputs = reference_case
    html = render_brief({**farm, "name": "<script>"},
                        preset, *inputs, generated_on=date(2026, 1, 2), commit="1" * 40)
    assert "&lt;script&gt;" in html
    assert "<script>" not in html
