"""Render the complete P47 summary from saved results."""

import json

from src.rank_concentration import OUTPUT, ROOT

DOCUMENT = "rank_concentration.md"


def rotation_label(cycle):
    return " → ".join(" / ".join(crop.replace("_", " ") for crop in year) for year in cycle)


def render(report):
    design = report["design"]
    cutoffs = [f"{q:g}" for q in design["q_pct"]]
    outcomes = [case for farm in report["farms"].values() for case in farm["presets"].values()]
    nonempty = ", ".join(f"{sum(case[q]['size'] > 0 for case in outcomes)} of {len(outcomes)} at {q}%"
                         for q in cutoffs)
    largest = max(case[q]["largest_share"] for case in outcomes for q in cutoffs)
    minimum_p = 1 / (design["null_replicates"] + 1)
    none_reached = all(case[q]["max_share_p"] == minimum_p for case in outcomes for q in cutoffs)
    tail_summary = (
        f" In each of the {len(outcomes) * len(cutoffs)} comparisons, every shuffled maximum was below "
        f"the observed maximum (empirical p = 1/{design['null_replicates'] + 1:,})."
        if none_reached else ""
    )
    rows = [
        "# P47 chance-adjusted rank concentration", "",
        "**EXPLORATORY.** The empty P44 top-three sets motivated this wider rank check. "
        f"A rotation enters a stable-top set if it ranks in the listed top fraction in at least "
        f"{design['min_share']:.0%} of the variant-by-draw cells. This describes the tested settings. "
        "The thresholds and rounding are design choices. Results are illustrative and need local validation. "
        "[Preregistration](p47_plan.md) · [P44](consensus_shortlist.md) · "
        f"[Every member and its exact hit count](../data/processed/{OUTPUT})", "",
        f"Nonempty sets appeared in {nonempty}. The largest observed share was {largest:.2%}." +
        tail_summary, "",
        "## Search spaces and cells", "",
        "| Farm | P44 variants | P22 draws | Cells per preset | Canonical union | Admitted rotations per cell | Top slot ranges at 0.5%, 1%, 2% |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for farm in report["farms"].values():
        low, high = farm["admitted_rotations_per_cell"]
        bounds = [f"{a:,}–{b:,}" for a, b in farm["top_slots_per_cell"].values()]
        rows.append(f"| {farm['name']} | {len(farm['variants'])} | {farm['draws']} | "
                    f"{farm['cells_per_preset']:,} | {farm['rotation_count']:,} | {low:,}–{high:,} | "
                    f"{', '.join(bounds)} |")
    rows.extend([
        "", "Percentile is 100 times (rank minus 1) divided by the number of admitted rotations. "
        "Ineligible rotations get zero hits and keep all cells in the denominator. The code selects only "
        "the ranks needed to reproduce P44's top-one and top-three counts and the three P47 cutoffs. "
        "The exact fraction uses the ceiling of the slot count, so different thresholds can occupy "
        "the same number of slots in small cells.", "",
        "## Set size, largest share and shuffled reference", "",
        f"{design['null_replicates']:,} independent null replicates preserve the admitted rotation labels in each "
        "cell and shuffle their ordering. The maximum is taken over the full canonical union. "
        "The 95% range describes shuffled maxima. Plus-one upper-tail p-values include ties and are unadjusted. "
        "The joint p-value counts replicates meeting or exceeding both the observed set size and maximum share.", "",
        "| Farm | Preset | Top fraction | Members | Largest share | Null mean members | Null mean largest share | Null largest share 95% range | p for largest | p for size | p for both |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ])
    for farm in report["farms"].values():
        for preset, outcomes in farm["presets"].items():
            for q in cutoffs:
                status, null = outcomes[q], farm["null"][q]
                low, high = null["max_share_95_range"]
                rows.append(
                    f"| {farm['name']} | {preset.replace('_', ' ').title()} | {q}% | {status['size']:,} | "
                    f"{status['largest_share']:.2%} | {null['mean_set_size']:.2f} | {null['mean_max_share']:.2%} | "
                    f"{low:.2%} to {high:.2%} | {status['max_share_p']:.4f} | {status['set_size_p']:.4f} | "
                    f"{status['joint_p']:.4f} |")
    rows.extend(["", "## Published baseline and alternatives", "",
                 "Bold shares mark set membership. These are shares of all cells for the fixed published cycles.", "",
                 "| Farm | Preset | Published strategy | 0.5% | 1% | 2% |",
                 "| --- | --- | --- | ---: | ---: | ---: |"])
    for farm in report["farms"].values():
        for preset, outcomes in farm["presets"].items():
            for strategies in zip(*(outcomes[q]["published"] for q in cutoffs), strict=True):
                item = strategies[0]
                shares = [f"**{row['share']:.2%}**" if row["member"] else f"{row['share']:.2%}"
                          for row in strategies]
                rows.append(f"| {farm['name']} | {preset.replace('_', ' ').title()} | "
                            f"{item['strategy'].replace('_', ' ').title()} · {rotation_label(item['cycle'])} | "
                            f"{' | '.join(shares)} |")
    rows.extend([
        "", "The saved output lists every canonical member with its cycle, hit count and share. "
        "The Validation panel displays the complete member list for the selected farm, preset and threshold.", "",
        "## Interpretation and reproduction", "",
        report["limit"] + " The comparison treats variant-by-draw cells as independent only in the null. "
        "Repeated use of the same model and assumptions can raise observed concentration. "
        "Field performance requires local evidence.", "",
        "Rebuild offline with `python -m src.rank_concentration`, then regenerate this page with "
        "`python -m src.rank_concentration_report`. The replay writes its own processed output.", "",
    ])
    return "\n".join(rows)


def main():
    report = json.loads((ROOT / "data/processed" / OUTPUT).read_text())
    (ROOT / "docs" / DOCUMENT).write_text(render(report))


if __name__ == "__main__":
    main()
