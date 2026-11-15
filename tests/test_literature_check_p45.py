"""Regional benchmarks use comparable endpoints and ship as offline data."""

import json

from src.crops import load_crops
from src.literature_check import INSIDE, OUTSIDE
from src.literature_check_p45 import (DOCUMENT, NO_BENCHMARK, OUTPUT, ROOT, build_report,
                                      metric_counts, render_markdown)


def test_context_does_not_count_and_crop_contrasts_use_catalog_values():
    regions = {"region": {"name": "Fixture", "scope": "Fixture region"}}
    sources = {"example": {"name": "Fixture study", "locator": "Table 1"}}
    shared = {"region": "region", "metric": "water", "crop": "rice", "field": "water_need_mm",
              "source": "example", "interpretation": "Fixture comparison"}
    references = {"regions": regions, "sources": sources, "unreachable": [], "comparisons": [
        {**shared, "check": "Within", "bounds": [500, 600]},
        {**shared, "check": "Different point estimate", "bounds": [560, 560]},
        {**shared, "check": "Crop contrast", "bounds": [200, 240], "minus_crop": "pulse"},
        {**shared, "check": "Gross irrigation", "reference": "1,250 mm applied"},
    ]}
    crops = {"rice": {"water_need_mm": 550}, "pulse": {"water_need_mm": 350}}
    region = build_report(references, crops)["regions"]["region"]
    assert [row["finding"] for row in region["rows"]] == [INSIDE, OUTSIDE, INSIDE, NO_BENCHMARK]
    assert region["rows"][2]["model"] == "200 mm"
    assert region["rows"][3]["bounds"] is None
    counts = {row["Metric"]: row for row in metric_counts(region)}
    assert counts["Water"] == {"Metric": "Water", "Usable": 3, "Inside range": 2,
                               "Outside range": 1, "Context only": 1}
    assert counts["Erosion"]["Usable"] == 0


def test_offline_outputs_reproduce_the_regional_audit():
    refs = json.loads((ROOT / "data/p45_literature.json").read_text())
    report = build_report(refs, load_crops(ROOT / "data/crops.csv"))
    assert report == json.loads((ROOT / "data/processed" / OUTPUT).read_text())
    assert render_markdown(report) == (ROOT / "docs" / DOCUMENT).read_text()
    telangana = report["regions"]["telangana_a"]
    makueni = report["regions"]["kenya_makueni_north"]
    assert [row["Usable"] for row in metric_counts(telangana)] == [5, 0, 0, 1, 0, 0]
    assert [row["Usable"] for row in metric_counts(makueni)] == [2, 2, 0, 2, 0, 0]
    bean, = [r for r in makueni["rows"] if r["check"] == "Common bean before sole maize · N credit"]
    assert (bean["model"], bean["bounds"], bean["finding"]) == ("22 kg N/ha", [44, 80], OUTSIDE)
    assert all(row["locator"] and row["source"] in report["sources"]
               for region in report["regions"].values() for row in region["rows"])
    assert all(f"[{item['name']}]({item['url']})" in render_markdown(report)
               for item in report["unreachable"])
