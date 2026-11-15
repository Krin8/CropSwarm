"""Build the regional literature audit from opened sources and the crop catalog."""

import json
from pathlib import Path

from src.crops import load_crops
from src.literature_check import FIELDS, INSIDE, OUTSIDE, compare_value, show_span
from src.precompute_cache import write_json

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "literature_check_p45.json"
DOCUMENT = "literature_check_p45.md"
NO_BENCHMARK = "no usable benchmark"
METRIC_NAMES = {
    "water": "Water",
    "nitrogen": "Nitrogen",
    "erosion": "Erosion",
    "climate_fit": "Climate fit",
    "income": "Income",
    "risk": "Risk",
}


def comparison_row(record, crops, sources):
    bounds = record.get("bounds")
    field = record.get("field")
    source = sources[record["source"]]
    if field is not None:
        value = crops[record["crop"]][field]
        if "minus_crop" in record:
            value -= crops[record["minus_crop"]][field]
        unit = "mm of in-window rainfall" if field == "min_rain_mm" else FIELDS[field][1]
        model = f"{value:g} {unit}"
    else:
        value = None
        model = record["model_text"]

    if bounds is None:
        finding = NO_BENCHMARK
        reference = record["reference"]
    else:
        if value is None:
            raise ValueError("A numeric benchmark requires a catalog field")
        finding = compare_value(value, bounds)
        reference = record.get("reference", f"{show_span(bounds)} {unit}")
    return {
        "metric": record["metric"],
        "check": record["check"],
        "model": model,
        "reference": reference,
        "finding": finding,
        "bounds": bounds,
        "interpretation": record["interpretation"],
        "source": record["source"],
        "locator": source["locator"],
    }


def build_report(references, crops):
    sources = references["sources"]
    regions = {
        region_id: {**region, "rows": [], "counts": {
            metric: {INSIDE: 0, OUTSIDE: 0, NO_BENCHMARK: 0} for metric in METRIC_NAMES
        }}
        for region_id, region in references["regions"].items()
    }
    for record in references["comparisons"]:
        row = comparison_row(record, crops, sources)
        region = regions[record["region"]]
        region["rows"].append(row)
        region["counts"][row["metric"]][row["finding"]] += 1
    return {"regions": regions, "sources": sources, "unreachable": references["unreachable"]}


def metric_counts(region):
    return [
        {
            "Metric": label,
            "Usable": region["counts"][metric][INSIDE] + region["counts"][metric][OUTSIDE],
            "Inside range": region["counts"][metric][INSIDE],
            "Outside range": region["counts"][metric][OUTSIDE],
            "Context only": region["counts"][metric][NO_BENCHMARK],
        }
        for metric, label in METRIC_NAMES.items()
    ]


def render_markdown(report):
    lines = [
        "# Regional literature cross-check (P45)",
        "",
        "Illustrative comparisons. Validate locally before using any value. This audit follows the "
        "[P35 scoring cross-check](literature_check.md) and applies no corrections.",
        "",
        "## What counts as a benchmark",
        "",
        "We searched for Telangana and peninsular Indian irrigated rice systems and for maize–bean "
        "systems in semi-arid eastern Kenya. The tables compare each eligible source and crop or crop "
        "contrast with the corresponding catalog quantity. A comparable observation uses the same crop "
        "and endpoint in the region. Where a study uses a different cultivar, water regime or window, "
        "the row specifies the difference. Crop water estimates and treatment spans describe the "
        "named study conditions. A point estimate has equal bounds, so any difference is classed "
        "as outside. Spans and points are descriptive references. Formal uncertainty intervals "
        "for transfers to the demo fields are unavailable.",
        "",
        "Each usable comparison counts once, including the explicitly linked paddy–green gram "
        "contrast. The counts are comparisons, and some share a study or the same measurements. "
        "Climate-fit counts cover crop duration only. Seasonal rainfall and yield contrasts give "
        "context without defining the model's climate cut-offs. Nitrogen credits describe an "
        "immediately following crop's fertilizer-equivalent N, so residue N, mineral N and uptake "
        "remain contextual evidence. Crop ET is consumptive use. Gross withdrawals and paddy "
        "percolation require separate measurements. The model starts each seasonal bucket empty, "
        "represents one crop per slot and has no grain-yield output.",
        "",
    ]
    for region in report["regions"].values():
        lines.extend([f"## {region['name']}", "", region["scope"], "",
                      "| Metric | Usable | Inside range | Outside range | Context only |",
                      "| --- | ---: | ---: | ---: | ---: |"])
        lines.extend("| " + " | ".join(map(str, row.values())) + " |" for row in metric_counts(region))
        lines.extend(["", "| Metric and comparison | Model | Published reference | Finding | Interpretation | Source |",
                      "| --- | --- | --- | --- | --- | --- |"])
        for row in region["rows"]:
            source = report["sources"][row["source"]]
            cells = [
                f"{METRIC_NAMES[row['metric']]} · {row['check']}",
                row["model"], row["reference"], row["finding"], row["interpretation"],
                f"[{source['name']}](#{row['source']})",
            ]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines.extend([
        "## Gaps that matter for interpretation", "",
        "- Telangana has regional benchmarks for crop ET and rice duration. The local green-manure "
        "trial supports a benefit under incorporation. A matched fertilizer response after harvested "
        "grain legumes in irrigated rice remains unverified.",
        "- In eastern Kenya, the common-bean N credit is below both Katumani season estimates. The "
        "comparison relies on an older yield-equivalence trial with substantial seasonal differences. "
        "The separate site-specific mineral N study and the observed maize–bean intercrop responses "
        "help explain why a single credit or one crop per slot simplifies the system.",
        "- No comparable regional benchmark was identified for the model's N demand proxy, erosion "
        "cover index, same-family disease risk penalty, relative income index or heat and rainfall "
        "cut-offs. No evidence here constrains the demo farms' irrigation supply fractions or "
        "between-season water carryover. A regional comparison cannot establish local performance "
        "or rotation suitability.",
        "", "## Sources opened and read", "",
    ])
    for key, source in report["sources"].items():
        link = f"[Publication]({source['url']})"
        if "full_text" in source:
            link += f" · [Author manuscript]({source['full_text']})"
        lines += [f'<a id="{key}"></a>', "",
                  f"- **{source['name']}**. {source['locator']}. {source['design']} {link}", ""]
    lines.extend(["## Unreachable or partially accessible sources", ""])
    lines.extend(f"- {item['reason']} [{item['name']}]({item['url']})" for item in report["unreachable"])
    lines.extend(["", "Regenerate the report and app data offline with `python -m src.literature_check_p45`.", ""])
    return "\n".join(lines)


def generate(root=ROOT):
    references = json.loads((root / "data/p45_literature.json").read_text())
    report = build_report(references, load_crops(root / "data/crops.csv"))
    write_json(root / "data/processed" / OUTPUT, report)
    (root / "docs" / DOCUMENT).write_text(render_markdown(report), encoding="utf-8")


if __name__ == "__main__":
    generate()
