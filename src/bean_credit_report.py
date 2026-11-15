"""Render the saved P51 exact sweep and replay as a Markdown report."""

import json

from src.bean_credit_breakpoints import OUTPUT, PLAN
from src.scoring import METRICS, ROOT

DOCUMENT = "bean_credit_breakpoints.md"


def rotation_text(rotation):
    pairs = [" / ".join(crop.replace("_", " ") for crop in year) for year in rotation]
    if len(set(pairs)) == 1:
        return f"{pairs[0]} each year"
    return " → ".join(pairs)


def credit_interval(row):
    first, last = row["first_credit"], row["last_credit"]
    return f"{first:g}" if first == last else f"{first:g}–{last:g}"


def preset_title(name):
    return name.replace("_", " ").capitalize()


def table(headers, rows):
    return ["| " + " | ".join(str(cell) for cell in row) + " |"
            for row in (headers, ["---"] * len(headers), *rows)]


def render(report):
    presets = report["presets"]
    unit = report["credit_unit"]
    catalog = report["catalog_credit"]
    design = report["draw_design"]
    credits = report["credit_grid"]
    number = len(credits)
    stays = sum(row["retains_catalog_leader"] for row in presets.values())
    flips = sum(len(row["breakpoints"]) for row in presets.values())
    near_flips = sum(edge["near_tie"] for row in presets.values() for edge in row["breakpoints"])
    published = report["published_strategies"]
    baseline = next(row for row in published if row["credit"] == catalog)
    nitrogen = [row["strategies"][0]["metrics"]["nitrogen"]["value"] for row in published]
    return "\n".join([
        "# Makueni bean-credit breakpoints (P51)", "",
        report["caveat"], "", report["credit_evidence"], "",
        f"Exact search evaluated {report['canonical_count']:,} feasible canonical {report['horizon_years']}-year "
        f"rotations at each of {number} tested credits. The {catalog:g} {unit} catalog leader held across "
        f"the full grid in {stays} of {len(presets)} presets. "
        f"{near_flips} of {flips} observed flips met the near-tie rule. "
        f"[Preregistration]({PLAN}) · [Full-precision results](../data/processed/{OUTPUT})", "",
        "## Tested leader intervals", "",
        "Each row covers consecutive tested credit settings. The exact search picks the first canonical row at an exact tie. "
        "The adjacent points bracket a change and leave its location between tested credits unresolved.", "",
        *table(("Preset", f"Tested credit ({unit})", "Exact leader", f"Catalog leader at {catalog:g}"),
               [(preset_title(name), credit_interval(row), rotation_text(row["rotation"]),
                 "Yes" if row["catalog_leader"] else "No")
                for name, result in presets.items() for row in result["leader_intervals"]]), "",
        "## Breakpoints and top-two gaps", "",
        f"Near-tie means a gap of at most {design['near_tie_gap']:g} weighted-score points at either endpoint "
        "(existing design choice). The table shows the flag at each endpoint. Scores and gaps use full precision "
        "for comparisons. Displayed gaps are rounded.", "",
        *table(("Preset", f"Flip bracket ({unit})", "Flip is a near-tie",
                "Before gap", "Before close", "After gap", "After close"),
               [(preset_title(name), f"{edge['before']['credit']:g}–{edge['after']['credit']:g}",
                 "Yes" if edge["near_tie"] else "No", f"{edge['before']['gap']:.6f}",
                 "Yes" if edge["before"]["near_tie"] else "No", f"{edge['after']['gap']:.6f}",
                 "Yes" if edge["after"]["near_tie"] else "No")
                for name, result in presets.items() for edge in result["breakpoints"]]), "",
        "### All nominal rankings", "",
        *table(("Preset", f"Credit ({unit})", "Exact leader", "Leader score", "Runner-up", "Runner-up score",
                "Top-two gap", "Near-tie"),
               [(preset_title(name), f"{row['credit']:g}", rotation_text(row["leader"]["rotation"]),
                 f"{row['leader']['score']:.6f}", rotation_text(row["runner_up"]["rotation"]),
                 f"{row['runner_up']['score']:.6f}", f"{row['gap']:.6f}", "Yes" if row["near_tie"] else "No")
                for name, result in presets.items() for row in result["grid"]]), "",
        "## Baseline and displayed alternatives", "",
        f"The baseline and four displayed cycles are held fixed throughout. Baseline source: {report['baseline_source']}. "
        f"The baseline’s modeled raw nitrogen balance spans {min(nitrogen):g} to {max(nitrogen):g} kg N/ha per slot "
        "across the grid. All other raw metrics and the hard-rule flags are identical at every credit. "
        "The nitrogen score can change even for a cycle without common bean. "
        "Its raw nitrogen balance stays fixed, while the catalog-wide upper bound increases whenever the bean "
        "credit exceeds the highest credit among the other crops.", "",
        "Absolute values for each unchanged metric are shown once. "
        f"All deltas for these five metrics are zero. Source tags and evidence labels are in the "
        f"[full results](../data/processed/{OUTPUT}).", "",
        *table(("Published strategy", "Cycle", "Metric", "Raw value", "Normalized score", "Source tag", "Evidence"),
               [(preset_title(row["strategy"]), rotation_text(row["rotation"]), preset_title(metric),
                 f"{data['value']:.5g} {data['unit']}", f"{data['score']:.6f}", data["source"], data["evidence_label"])
                for row in baseline["strategies"] for metric, data in row["metrics"].items()
                if metric != "nitrogen"]), "",
        f"For nitrogen, deltas are relative to {catalog:g} {unit}. Each preset column gives the weighted score "
        "and rank among the five published cycles, including the baseline. Exact ties in this table use published order. "
        f"Overall exact ranks use the full canonical pool above. [Crop catalog](../data/crops.csv)", "",
        *table((f"Credit ({unit})", "Published strategy", "N balance (kg N/ha per slot)",
                "Change in N balance", "N score", "Change in N score",
                *(preset_title(name) + " score (rank)" for name in presets)),
               [(f"{item['credit']:g}", preset_title(row["strategy"]), f"{metric['value']:.2f}",
                 f"{metric['delta']:+.2f}", f"{metric['score']:.6f}", f"{metric['score_delta']:+.6f}",
                 *(f"{row['presets'][name]['score']:.6f} ({row['presets'][name]['rank_among_published']})"
                   for name in presets))
                for item in published for row in item["strategies"] for metric in [row["metrics"]["nitrogen"]]]), "",
        "## Matched P22 draws", "",
        f"Each of the three fixed-credit cases uses the same {design['joint_draws']} draws and seed {design['seed']} "
        "(P22 design choices). Within each draw, only the bean credit changes between cases. "
        "P22 can vary the assumed baseline and include it as an exception to the usual feasibility rules. "
        "The change rate uses each credit’s own P22 reference winner. Material changes additionally require that "
        f"the reference becomes ineligible or that its score is more than {design['near_tie_gap']:g} points lower. "
        "The paired column compares winners from the same draw at the catalog credit. "
        "P22’s published original sampled the credit along with its other assumptions. "
        "It is included separately for context.", "",
        *table(("Preset", f"Fixed credit ({unit})", "Own nominal P22 reference", "Changes vs own reference",
                "Material changes", f"Paired differences vs fixed {catalog:g}", "Draw top-score range",
                "Most frequent rotation", "Share of draws it wins"),
               [(preset_title(name), f"{row['credit']:g}", rotation_text(row["reference_winner"]),
                 f"{row['winner_change_fraction']:.2%}", f"{row['material_change_fraction']:.2%}",
                 f"{row['paired_disagreement_count']}/{row['evaluations']} ({row['paired_disagreement_fraction']:.2%})",
                 f"{row['top_score_range'][0]:.3f}–{row['top_score_range'][1]:.3f}",
                 rotation_text(row["winners"][0]["cycle"]), f"{row['winners'][0]['count'] / row['evaluations']:.2%}")
                for name, result in presets.items() for row in result["matched_draws"]]), "",
        f"The full winner counts are available in the [saved replay](../data/processed/{OUTPUT}) and in the "
        "Validation panel. These are frequencies under modeled assumptions. Field suitability needs local evidence.", "",
        *table(("Preset", "Earlier P22 sampled-credit change rate", "Earlier P22 material-change rate"),
               [(preset_title(name), f"{row['p22_sampled_credit_context']['winner_change_fraction']:.2%}",
                 f"{row['p22_sampled_credit_context']['material_change_fraction']:.2%}")
                for name, row in presets.items()]), "",
        "## Provenance", "",
        *table((f"Credit ({unit})", "Source"),
               [(f"{row['credit']:g}", row["source"]) for row in credits]), "",
        "[P45 Katumani trial](literature_check_p45.md#nadar) · [P49 Machakos estimates](literature_check_p49.md) "
        "· [P22 draw design](sensitivity.md) · [Original strategy evidence](../data/processed/strategies_kenya_makueni_north.json)", "",
        "Regenerate the new results and report offline with `python -m src.bean_credit_breakpoints` "
        "and `python -m src.bean_credit_report`.", "",
    ])


if __name__ == "__main__":
    report = json.loads((ROOT / "data/processed" / OUTPUT).read_text())
    (ROOT / "docs" / DOCUMENT).write_text(render(report))
