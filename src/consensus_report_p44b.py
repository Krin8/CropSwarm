"""Render P44b consensus and prior comparisons from the saved summary."""

import json

from src.consensus_shortlist_p44b import OUTPUT
from src.scoring import ROOT

DOCUMENT = "consensus_shortlist_p44b.md"


def cycle(rotation):
    return " → ".join("/".join(crop.replace("_", " ") for crop in year) for year in rotation)


def shares(row):
    return f"{row['top1_share']:.2%} / {row['top3_share']:.2%}"


def render(report):
    farms = list(report["farms"].values())
    thresholds = report["design"]["thresholds"]
    main = report["design"]["primary_threshold"]
    presets = [result for farm in farms for result in farm["presets"].values()]
    nonempty = {level: sum(row["thresholds"][str(level)]["size"] > 0 for row in presets) for level in thresholds}
    newly_nonempty = {level: sum(row["thresholds"][str(level)]["size"] > 0 and
                                 row["thresholds"][str(level)]["p44_size"] == 0 for row in presets)
                      for level in thresholds}
    lines = [
        "# Expanded consensus shortlist (P44b)", "",
        "[Preregistration](p44b_plan.md) was committed as `9e5f36b` before evaluation. "
        "[Saved summary](../data/processed/consensus_shortlist_p44b.json) · [Earlier P44 analysis](consensus_shortlist.md).",
        "",
        f"At the primary **{main}%** cutoff, **{nonempty[main]} of {len(presets)}** farm–preset sets are "
        f"nonempty, with **{newly_nonempty[main]}** newly nonempty since P44. "
        + " ".join(f"At {level}%, {nonempty[level]} are nonempty ({newly_nonempty[level]} newly nonempty)."
                   for level in thresholds if level != main), "",
        "Illustrative model results. Validate locally. Consensus across these variants cannot establish "
        "real-world rotation quality. Makueni cropland is unverified, and Telangana's second season is tentative.", "",
        "## Scope and replay checks", "",
    ]

    def table(headings, rows):
        def line(cells):
            return "| " + " | ".join(map(str, cells)) + " |"
        lines.extend([line(headings), line(["---"] * len(headings)), *(line(row) for row in rows), ""])

    table(["Farm", "Variants", "P22 draws", "Cells per preset P44 → P44b", "Per-rotation frequencies",
           "Cells with fewer than three", "Flagged draw baseline cells"],
          ((farm["name"], len(farm["variants"]), farm["draws"],
            f"{farm['p44_cells_per_preset']:,} → {farm['cells_per_preset']:,}",
            f"[{farm['rotation_count']:,} cycles](../data/processed/{farm['counts_file']})",
            farm["cells_with_fewer_than_three"], farm["flagged_baseline_cells"]) for farm in farms))
    lines.extend([
        "Kansas includes original, P42 and all 15 non-original P43 settings. Telangana and Makueni each "
        "include original, P42 and their three P46 settings. Every global P46 pairing maps to an existing "
        "local setting for each farm. The summary records that mapping. Each distinct local setting gets "
        "equal weight. The thresholds and the choice of variants are design choices.", "",
        f"All variants use the same cached P22 draws (seed {report['design']['seed']}). The original winner "
        "histograms and every variant's nominal reference and winner-change rate reproduced. Replaying the "
        "P44 subset also reproduced every stored top-one and top-three count and canonical rotation key. "
        "Each cell admits the draw's baseline once, including when it has hard-rule flags. Equal scores "
        "favor the baseline, then the first canonical row. Ineligible cycles earn zero rank credit. "
        "Shares use all variant-by-draw cells. Cycles absent from the linked frequency files have zero "
        "rank credit by construction. These frequencies have no sampling intervals.", "",
        "## Comparison by farm and preset", "",
        "Each size column shows P44 → P44b. The largest share is the best top-three frequency in each "
        "analysis, which can refer to different rotations. Shares for the baseline and original P22 "
        "nominal winner below track the same cycles across the two analyses.", "",
    ])
    table(["Farm", "Preset", *(f"Size at {level}%" for level in thresholds),
           "Largest top-three share P44 → P44b", "P44b most frequent top-three cycle", "P18 evidence"],
          ((farm["name"], name.replace("_", " ").title(),
            *(f"{item['thresholds'][str(level)]['p44_size']} → {item['thresholds'][str(level)]['size']}"
              for level in thresholds),
            f"{item['p44']['leaders'][0]['top3_share']:.2%} → {item['leaders'][0]['top3_share']:.2%}",
            cycle(item["leaders"][0]["cycle"]), item["leaders"][0]["evidence"]["overall"])
           for farm in farms for name, item in farm["presets"].items()))
    lines.extend(["## Fixed baseline and original winner", "", "Shares are top one / top three.", ""])
    table(["Farm", "Preset", "Fixed baseline P44 → P44b", "Baseline P18 evidence",
           "Original nominal cycle", "Original winner P44 → P44b", "Winner P18 evidence",
           "Draw baseline P44 → P44b"],
          ((farm["name"], name.replace("_", " ").title(),
            f"{shares(item['p44']['fixed_baseline'])} → {shares(item['fixed_baseline'])}",
            item["fixed_baseline"]["evidence"]["overall"], cycle(item["original_nominal"]["cycle"]),
            f"{shares(item['p44']['original_nominal'])} → {shares(item['original_nominal'])}",
            item["original_nominal"]["evidence"]["overall"],
            f"{shares(item['p44']['draw_baseline'])} → {shares(item['draw_baseline'])}")
           for farm in farms for name, item in farm["presets"].items()))
    lines.extend(["## Consensus members and shortlist overlap", "",
                  "The size table identifies every empty set. Each member below includes its top-one and "
                  "top-three frequencies. The displayed shortlist is the published list.", ""])
    members = []
    for farm in farms:
        for name, preset in farm["presets"].items():
            for level in thresholds:
                outcome = preset["thresholds"][str(level)]
                for row in outcome["members"]:
                    membership = row["published_strategy"] or "outside published shortlist"
                    dominance = (f"{row['strictly_dominated_cells']:,}/{row['admitted_cells']:,}"
                                 if row["admitted_cells"] else "unavailable")
                    members.append((farm["name"], name.replace("_", " ").title(), f"{level}%", cycle(row["cycle"]),
                                    shares(row), row["evidence"]["overall"], membership, dominance))
    if members:
        table(["Farm", "Preset", "Cutoff", "Member", "Top one / top three", "P18 evidence", "Published option",
               "Strictly dominated / admitted cells"], members)
    else:
        lines.extend(["Every tested set is empty. Dominance rates are unavailable.", ""])
    lines.extend([
        "P18 labels describe the original input evidence. P42 smoothing is a design choice. P43 sources "
        "and assumptions apply only to Kansas, and P46 regional endpoints and their transfer assumptions "
        "apply only to the corresponding farm. [P18 method](evidence_grades.md) · [P42](smooth_climate_fit.md) "
        "· [P43](literature_variant.md) · [P46](regional_scoring_variants.md)", "",
        "Rebuild offline with `python -m src.consensus_shortlist_p44b` and "
        "`python -m src.consensus_report_p44b`.", "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    report = json.loads((ROOT / "data/processed" / OUTPUT).read_text())
    (ROOT / "docs" / DOCUMENT).write_text(render(report), encoding="utf-8")
