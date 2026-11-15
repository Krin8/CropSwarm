# Expanded consensus shortlist (P44b)

[Preregistration](p44b_plan.md) was committed as `9e5f36b` before evaluation. [Saved summary](../data/processed/consensus_shortlist_p44b.json) · [Earlier P44 analysis](consensus_shortlist.md).

At the primary **50%** cutoff, **0 of 12** farm–preset sets are nonempty, with **0** newly nonempty since P44. At 40%, 0 are nonempty (0 newly nonempty). At 60%, 0 are nonempty (0 newly nonempty).

Illustrative model results. Validate locally. Consensus across these variants cannot establish real-world rotation quality. Makueni cropland is unverified, and Telangana's second season is tentative.

## Scope and replay checks

| Farm | Variants | P22 draws | Cells per preset P44 → P44b | Per-rotation frequencies | Cells with fewer than three | Flagged draw baseline cells |
| --- | --- | --- | --- | --- | --- | --- |
| US High Plains B | 17 | 512 | 8,192 → 8,704 | [330 cycles](../data/processed/consensus_shortlist_p44b_us_high_plains_b.csv.gz) | 0 | 4352 |
| Telangana A | 5 | 512 | 512 → 2,560 | [303,132 cycles](../data/processed/consensus_shortlist_p44b_telangana_a.csv.gz) | 0 | 2145 |
| Makueni North Candidate | 5 | 512 | 512 → 2,560 | [41,707 cycles](../data/processed/consensus_shortlist_p44b_kenya_makueni_north.csv.gz) | 45 | 1615 |

Kansas includes original, P42 and all 15 non-original P43 settings. Telangana and Makueni each include original, P42 and their three P46 settings. Every global P46 pairing maps to an existing local setting for each farm. The summary records that mapping. Each distinct local setting gets equal weight. The thresholds and the choice of variants are design choices.

All variants use the same cached P22 draws (seed 42). The original winner histograms and every variant's nominal reference and winner-change rate reproduced. Replaying the P44 subset also reproduced every stored top-one and top-three count and canonical rotation key. Each cell admits the draw's baseline once, including when it has hard-rule flags. Equal scores favor the baseline, then the first canonical row. Ineligible cycles earn zero rank credit. Shares use all variant-by-draw cells. Cycles absent from the linked frequency files have zero rank credit by construction. These frequencies have no sampling intervals.

## Comparison by farm and preset

Each size column shows P44 → P44b. The largest share is the best top-three frequency in each analysis, which can refer to different rotations. Shares for the baseline and original P22 nominal winner below track the same cycles across the two analyses.

| Farm | Preset | Size at 40% | Size at 50% | Size at 60% | Largest top-three share P44 → P44b | P44b most frequent top-three cycle | P18 evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US High Plains B | Water Saver | 0 → 0 | 0 → 0 | 0 → 0 | 23.36% → 23.31% | fallow → soybean → sunflower | low |
| US High Plains B | Soil Builder | 0 → 0 | 0 → 0 | 0 → 0 | 31.93% → 32.07% | fallow → soybean → cereal rye cover | low |
| US High Plains B | Income | 0 → 0 | 0 → 0 | 0 → 0 | 26.15% → 26.10% | maize → soybean → sunflower | low |
| US High Plains B | Balanced | 0 → 0 | 0 → 0 | 0 → 0 | 22.46% → 22.33% | fallow → soybean → sunflower | low |
| Telangana A | Water Saver | 0 → 0 | 0 → 0 | 0 → 0 | 32.62% → 32.77% | soybean/fallow → soybean/fallow → soybean/fallow | low |
| Telangana A | Soil Builder | 0 → 0 | 0 → 0 | 0 → 0 | 39.84% → 39.84% | soybean/fallow → soybean/fallow → soybean/fallow | low |
| Telangana A | Income | 0 → 0 | 0 → 0 | 0 → 0 | 15.04% → 14.92% | soybean/maize → soybean/maize → soybean/maize | low |
| Telangana A | Balanced | 0 → 0 | 0 → 0 | 0 → 0 | 30.66% → 30.59% | soybean/fallow → soybean/fallow → soybean/fallow | low |
| Makueni North Candidate | Water Saver | 0 → 0 | 0 → 0 | 0 → 0 | 30.27% → 26.60% | common bean/fallow → common bean/fallow → common bean/fallow | low |
| Makueni North Candidate | Soil Builder | 0 → 0 | 0 → 0 | 0 → 0 | 21.88% → 18.71% | common bean/fallow → common bean/fallow → common bean/fallow | low |
| Makueni North Candidate | Income | 0 → 0 | 0 → 0 | 0 → 0 | 36.72% → 39.88% | maize/common bean → maize/common bean → maize/common bean | low |
| Makueni North Candidate | Balanced | 0 → 0 | 0 → 0 | 0 → 0 | 16.80% → 13.79% | green gram/fallow → green gram/fallow → green gram/fallow | low |

## Fixed baseline and original winner

Shares are top one / top three.

| Farm | Preset | Fixed baseline P44 → P44b | Baseline P18 evidence | Original nominal cycle | Original winner P44 → P44b | Winner P18 evidence | Draw baseline P44 → P44b |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US High Plains B | Water Saver | 0.00% / 0.68% → 0.00% / 0.68% | low | fallow → sorghum → soybean | 7.03% / 18.85% → 7.42% / 19.09% | low | 0.00% / 0.68% → 0.00% / 0.68% |
| US High Plains B | Soil Builder | 0.00% / 0.39% → 0.00% / 0.39% | low | fallow → soybean → cereal rye cover | 21.58% / 31.93% → 21.73% / 32.07% | low | 0.00% / 0.39% → 0.00% / 0.39% |
| US High Plains B | Income | 0.00% / 0.39% → 0.00% / 0.39% | low | sorghum → soybean → sunflower | 7.13% / 13.65% → 7.15% / 13.59% | low | 0.00% / 0.39% → 0.00% / 0.39% |
| US High Plains B | Balanced | 0.00% / 0.39% → 0.00% / 0.39% | low | fallow → sorghum → soybean | 6.40% / 16.11% → 6.79% / 16.29% | low | 0.00% / 0.39% → 0.00% / 0.39% |
| Telangana A | Water Saver | 0.00% / 0.00% → 0.00% / 0.00% | low | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 21.09% / 21.29% → 21.02% / 21.21% | low | 0.00% / 0.00% → 0.00% / 0.00% |
| Telangana A | Soil Builder | 0.00% / 0.00% → 0.00% / 0.00% | low | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 22.27% / 22.27% → 22.30% / 22.30% | low | 0.00% / 0.00% → 0.00% / 0.00% |
| Telangana A | Income | 0.20% / 0.20% → 0.20% / 0.20% | low | pigeonpea/maize → pigeonpea/maize → pigeonpea/maize | 3.52% / 3.91% → 3.55% / 3.98% | low | 0.98% / 0.98% → 0.98% / 0.98% |
| Telangana A | Balanced | 0.00% / 0.00% → 0.00% / 0.00% | low | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 18.36% / 18.55% → 18.36% / 18.59% | low | 0.00% / 0.00% → 0.00% / 0.00% |
| Makueni North Candidate | Water Saver | 0.98% / 1.95% → 0.98% / 1.95% | low | green gram/fallow → green gram/fallow → green gram/fallow | 25.59% / 30.08% → 22.23% / 25.90% | low | 1.17% / 2.34% → 1.29% / 2.62% |
| Makueni North Candidate | Soil Builder | 0.98% / 1.95% → 1.13% / 2.15% | low | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 5.86% / 8.01% → 4.10% / 5.43% | low | 1.17% / 2.34% → 1.64% / 3.12% |
| Makueni North Candidate | Income | 31.05% / 36.72% → 34.38% / 39.88% | low | maize/green gram → maize/green gram → maize/green gram | 11.72% / 14.84% → 10.70% / 14.34% | low | 32.42% / 38.67% → 35.74% / 41.80% |
| Makueni North Candidate | Balanced | 1.17% / 2.73% → 1.88% / 3.44% | low | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 7.23% / 9.77% → 5.98% / 7.81% | low | 1.37% / 3.12% → 2.07% / 3.83% |

## Consensus members and shortlist overlap

The size table identifies every empty set. Each member below includes its top-one and top-three frequencies. The displayed shortlist is the published list.

Every tested set is empty. Dominance rates are unavailable.

P18 labels describe the original input evidence. P42 smoothing is a design choice. P43 sources and assumptions apply only to Kansas, and P46 regional endpoints and their transfer assumptions apply only to the corresponding farm. [P18 method](evidence_grades.md) · [P42](smooth_climate_fit.md) · [P43](literature_variant.md) · [P46](regional_scoring_variants.md)

Rebuild offline with `python -m src.consensus_shortlist_p44b` and `python -m src.consensus_report_p44b`.
