"""Render the saved P46 comparisons without recomputing scores."""

import json

from src.regional_scoring_variants import LEVELS, MAKUENI, OUTPUT, TELANGANA
from src.scoring import METRICS, ROOT, UNITS

DOCUMENT = "regional_scoring_variants.md"


def cycle(rotation):
    return " → ".join(" / ".join(crop.replace("_", " ") for crop in year) for year in rotation)


def number(value, spec):
    return "unavailable" if value is None else format(value, spec)


def flags(record):
    def display(indices):
        return ", ".join(str(i + 1) for i in indices) or "none"

    changes = []
    for flag, old in record["original_flags"].items():
        new = record["variant_flags"][flag]
        if old != new:
            changes.append(f"{flag.replace('_', ' ')} slots {display(old)} → {display(new)}")
    return " · ".join(changes) or "No change"


def render(report):
    settings = report["design"]
    active = [row for farm in report["farms"].values() for level, result in farm["levels"].items()
              if level != "original" for row in result["nominal"].values()]
    changed = sum(row["label_changed"] for row in active)
    created = sum(row["near_tie_appeared"] for row in active)
    resolved = sum(row["near_tie_disappeared"] for row in active)
    lines = [
        "# Regional literature-informed variants (P46)", "",
        "[Preregistration](p46_plan.md) was committed as `24b48fb` before evaluation. "
        "[Full-precision results](../data/processed/regional_scoring_variants_p46.json).", "",
        "Illustrative what-if, validate locally. Each substitution applies to one farm. "
        "Makueni cropland is unverified and Telangana's second season remains tentative. "
        "Regional results cannot establish crop responses at the demo points or the quality of a rotation.", "",
        "## Inputs and exact comparisons", "",
    ]

    def table(headings, rows):
        def line(row):
            return "| " + " | ".join(map(str, row)) + " |"

        lines.extend([line(headings), line(["---"] * len(headings)), *(line(row) for row in rows), ""])

    for target, label in ((MAKUENI, "Makueni common-bean nitrogen credit"), (TELANGANA, "Telangana paddy water demand")):
        correction = report["corrections"][target]
        values = correction["values"]
        source = correction["source"]
        lines.extend([f"- **{label}** ({correction['unit']}). Catalog {values['original']:g}. "
                      f"Low {values['low']:g}, mid {values['mid']:g}, high {values['high']:g}. "
                      f"{source['locator']}. [{source['name']}]({source['url']})"])
    lines.extend(["", "Endpoints are literature values and midpoints are design choices. The Makueni "
                  "trial estimated fertilizer equivalence before sole maize. The model applies the credit to "
                  "every slot after bean and recalculates the nitrogen normalization denominator. A normalized "
                  "nitrogen score can change even when raw nitrogen stays the same. Telangana's trial spans "
                  "100 days after transplanting. The model applies its totals to 120-day crop windows and "
                  "reapplies the same water screen. Its water score uses cached NASA POWER with soil storage "
                  "and the assumed irrigation fraction.", "",
                  f"Near-ties use {settings['near_tie_gap']:g} weighted points, a design choice. Spearman uses only "
                  "rotations feasible in both settings. Each winner and near-top set is computed in its own pool. "
                  "Near-top counts include the winner. Equal objectives use the first canonical row. "
                  "An exact top-tie count of one means the leader is alone within the numerical tolerance.", "",
                  f"The [P22 replay](sensitivity.md) uses {settings['joint_draws']} matched draws per farm with "
                  f"seed {settings['seed']}. It fixes the changed coordinate while preserving the other sampled "
                  "inputs. Rates compare each draw with its own nominal reference, and the paired count compares "
                  "the two winners on the same draw. A material change requires a changed winner and either "
                  "reference ineligibility or a gap above the near-tie tolerance. Original P22 winner histograms, "
                  "nominal references and change rates reproduced.", "",
                  f"**{changed} of {len(active)}** active level–preset comparisons changed the nominal leader. "
                  f"Top-two near-ties created **{created}**, resolved **{resolved}**.", "",
                  "## All configurations", "",
                  "Each pairing points to the exact same farm-level results as its constituent single changes. "
                  "The farms have independent pools and scores. Kansas uses the original inputs for every pairing.", ""])
    table(["Makueni setting", "Telangana setting", "Kansas setting"],
          ((case["makueni"], case["telangana"], "original") for case in report["configurations"]))

    for farm in report["farms"].values():
        lines.extend([f"## {farm['name']}", ""])
        for level, outcome in farm["levels"].items():
            lines.extend([f"### {level.title()} input", ""])
            old = farm["levels"]["original"]["p22"]
            sample = next(iter(outcome["nominal"].values()))
            lines.extend([f"Feasible canonical rotations **{sample['original_count']:,} → {sample['variant_count']:,}**. "
                          f"Common {sample['common_count']:,}, added {sample['added_count']:,}, "
                          f"removed {sample['excluded_count']:,}.", ""])
            table(["Preset", "Original leader (score)", "Variant leader (score)", "Changed",
                   "Original leader feasible / optimal", "Rank ρ"],
                  ((name.replace("_", " "),
                    f"{cycle(r['original_rotation'])} ({r['original_score']:.6f})",
                    f"{cycle(r['variant_rotation'])} ({r['variant_score']:.6f})",
                    "yes" if r["label_changed"] else "no",
                    f"{'yes' if r['original_still_feasible'] else 'no'} / {'yes' if r['original_still_optimal'] else 'no'}",
                    number(r["rank_spearman"], ".6f"))
                   for name, r in outcome["nominal"].items()))
            table(["Preset", "Top-two gap original → variant", "Exact top ties original → variant",
                   "Near-top count original → variant", "Entered / left", "Top-two near-tie"],
                  ((name.replace("_", " "),
                    f"{number(r['original_top_two_gap'], '.6f')} → {number(r['variant_top_two_gap'], '.6f')}",
                    f"{r['original_exact_ties']} → {r['variant_exact_ties']}",
                    f"{r['original_near_top']} → {r['variant_near_top']}",
                    f"{r['entered_near_top']} / {r['left_near_top']}",
                    "created" if r["near_tie_appeared"] else "resolved" if r["near_tie_disappeared"] else "no change")
                   for name, r in outcome["nominal"].items()))
            table(["Preset", "P22 change original → variant", "Change (pp)", "Material original → variant",
                   "Material change (pp)", "Paired winners differ"],
                  ((name.replace("_", " "), f"{old[name]['winner_change_fraction']:.2%} → {r['winner_change_fraction']:.2%}",
                    f"{100 * r['winner_change_delta']:+.2f}",
                    f"{old[name]['material_change_fraction']:.2%} → {r['material_change_fraction']:.2%}",
                    f"{100 * r['material_change_delta']:+.2f}",
                    f"{r['paired_disagreement_count']}/{r['draws']} ({r['paired_disagreement_fraction']:.2%})")
                   for name, r in outcome["p22"].items()))
            lines.extend(["Published baseline and shortlist deltas are variant minus original, shown as raw / normalized. "
                          "Flags locate slots in the displayed rotation.", ""])
            table(["Published option", *(f"{m.replace('_', ' ').title()} ({u})" for m, u in zip(METRICS, UNITS, strict=True)),
                   "Flag changes"],
                  ((r["strategy"].replace("_", " "),
                    *(f"{r['raw_delta'][m]:+.5f} / {r['score_delta'][m]:+.5f}" for m in METRICS),
                    flags(r)) for r in outcome["shortlist"]))

    lines.extend(["The [P43 Kansas variants](literature_variant.md), [P44 consensus runs](consensus_shortlist.md), "
                  "[P42 smoother](smooth_climate_fit.md), and published rotation shortlists use their original "
                  "settings and results.", "",
                  "Rebuild the results with `python -m src.regional_scoring_variants` and this report with "
                  "`python -m src.regional_scoring_report`. Both commands run offline.", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    cached = json.loads((ROOT / "data/processed" / OUTPUT).read_text())
    (ROOT / "docs" / DOCUMENT).write_text(render(cached), encoding="utf-8")
