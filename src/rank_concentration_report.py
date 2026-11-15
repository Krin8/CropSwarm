"""Render the complete P47 summary from saved results."""

import json

from src.rank_concentration import OUTPUT, ROOT

DOCUMENT = "rank_concentration.md"
RECONCILIATION = (
    "P44’s top-three sets were empty for every farm and preset, and P47 found nonempty sets in broader "
    "top-percent bands using the same scoring settings and draws."
)


def band_count(bounds):
    low, high = bounds
    return f"{low:,}" if low == high else f"{low:,}–{high:,}"


def null_statement(report):
    floor = report["design"]["null_replicates"] + 1
    return (f"The largest observed share in every comparison exceeds an independent-shuffle null (floor 1/{floor}); "
            "the null ignores dependence between cells, so this is not a significance test.")


def rotation_label(cycle):
    return " → ".join(" / ".join(crop.replace("_", " ") for crop in year) for year in cycle)


def render(report):
    design = report["design"]
    cutoffs = [f"{q:g}" for q in design["q_pct"]]
    outcomes = [case for farm in report["farms"].values() for case in farm["presets"].values()]
    nonempty = ", ".join(f"{sum(case[q]['size'] > 0 for case in outcomes)} of {len(outcomes)} at {q}%"
                         for q in cutoffs)
    largest = max(case[q]["largest_share"] for case in outcomes for q in cutoffs)
    rows = [
        "# P47 chance-adjusted rank concentration", "",
        "**EXPLORATORY.** "
        f"A rotation enters a stable-top set if it ranks in the listed top fraction in at least "
        f"{design['min_share']:.0%} of the variant-by-draw cells. This describes the tested settings. "
        "The thresholds and rounding are design choices. Results are illustrative and need local validation. "
        "[Preregistration](p47_plan.md) · [P44](consensus_shortlist.md) · "
        "[Every stable-top member and share](#stable-top-member-shares)", "",
        f"Nonempty sets appeared in {nonempty}. The largest observed share was {largest:.2%}.", "",
        RECONCILIATION, "",
        null_statement(report), "",
        "## Search spaces and cells", "",
        "| Farm | P44 variants | P22 draws | Cells per preset | Canonical union | Admitted rotations per cell | "
        + " | ".join(f"Rotations per cell in top {q}%" for q in cutoffs) + " |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for farm in report["farms"].values():
        low, high = farm["admitted_rotations_per_cell"]
        bounds = [band_count(farm["top_slots_per_cell"][q]) for q in cutoffs]
        rows.append(f"| {farm['name']} | {len(farm['variants'])} | {farm['draws']} | "
                    f"{farm['cells_per_preset']:,} | {farm['rotation_count']:,} | {low:,}–{high:,} | "
                    f"{' | '.join(bounds)} |")
    rows.extend([
        "", "Percentile is 100 times (rank minus 1) divided by the number of admitted rotations. "
        "Ineligible rotations get zero hits and keep all cells in the denominator. The code selects only "
        "the ranks needed to reproduce P44's top-one and top-three counts and the three P47 cutoffs. "
        "Each band column gives the minimum and maximum absolute number of rotations admitted to that top band "
        "in a single cell. Counts vary with eligibility. The slot count rounds up, so different thresholds can "
        "occupy the same number of slots in small cells.", "",
        "## Set size, largest share and shuffled reference", "",
        f"{design['null_replicates']:,} independent null replicates preserve the admitted rotation labels in each "
        "cell and shuffle their ordering. The maximum is taken over the full canonical union. "
        "The 95% range is a descriptive spread of shuffled maxima.", "",
        "| Farm | Preset | Top fraction | Members | Largest share | Null mean members | Null mean largest share | "
        "Null largest share 95% range |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ])
    for farm in report["farms"].values():
        for preset, outcomes in farm["presets"].items():
            for q in cutoffs:
                status, null = outcomes[q], farm["null"][q]
                low, high = null["max_share_95_range"]
                rows.append(
                    f"| {farm['name']} | {preset.replace('_', ' ').title()} | {q}% | {status['size']:,} | "
                    f"{status['largest_share']:.2%} | {null['mean_set_size']:.2f} | {null['mean_max_share']:.2%} | "
                    f"{low:.2%} to {high:.2%} |")
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
        "", "## Stable-top member shares", "",
        "Each entry shows the number and share of all variant-by-draw cells in the band. "
        "A dash means the rotation did not enter the stable-top set at that cutoff. "
        f"[Saved member data](../data/processed/{OUTPUT})", "",
    ])
    for farm in report["farms"].values():
        rows.extend([f"### {farm['name']}", ""])
        for preset, outcomes in farm["presets"].items():
            name = preset.replace("_", " ").title()
            # Membership is nested, so the widest band contains every rotation reported here.
            widest = outcomes[cutoffs[-1]]["members"]
            if not widest:
                rows.extend([f"**{name}.** All three sets were empty.", ""])
                continue
            members = {q: {row["rotation_key"]: row for row in outcomes[q]["members"]} for q in cutoffs}
            rows.extend([
                f"#### {name}", "",
                "| Canonical rotation | " + " | ".join(f"Top {q}%" for q in cutoffs) + " |",
                "| --- | " + " | ".join("---:" for _ in cutoffs) + " |",
            ])
            cells = farm["cells_per_preset"]
            for row in widest:
                entries = [members[q].get(row["rotation_key"]) for q in cutoffs]
                shares = [f"{entry['count']:,}/{cells:,} ({entry['share']:.2%})" if entry else "—"
                          for entry in entries]
                rows.append(f"| {rotation_label(row['cycle'])} | {' | '.join(shares)} |")
            rows.append("")
    rows.extend([
        "## Interpretation and reproduction", "",
        "Repeated use of the same model and assumptions can raise observed concentration. "
        "Ranking consistency within the model leaves field performance unresolved.", "",
        "Regenerate this page from the saved P47 results with `python -m src.rank_concentration_report`.", "",
    ])
    return "\n".join(rows)


def main():
    report = json.loads((ROOT / "data/processed" / OUTPUT).read_text())
    (ROOT / "docs" / DOCUMENT).write_text(render(report))


if __name__ == "__main__":
    main()
