# P44 consensus shortlist across scoring variants

**All 12 farm–preset consensus sets were empty at 50%. They were also empty at 40% and 60%.** The closest to a set was Telangana soil builder, where the repeated soybean–fallow cycle was in the top three in 204 of 512 cells (39.84%). It needed one more top-three appearance to meet 40%. The most frequent Kansas cycle was fallow → soybean → cereal rye cover under soil builder (2,616 of 8,192 cells, 31.93%). The fixed Makueni maize–common bean baseline led the income preset in 159 of 512 cells (31.05%) and reached the top three in 188 (36.72%).

The [preregistration](p44_plan.md) was committed as `ba7ce72` before evaluating any rotation. The [summary JSON](../data/processed/consensus_shortlist_p44.json) preserves threshold membership, evidence labels and shortlist comparisons. The compressed CSV tables give each canonical cycle's top-one and top-three counts and shares for all four presets. All results are illustrative and need local validation.

## Scope and ranking

| Farm | Configurations | P22 draws | Cells per preset | CSV with rotation frequencies | Cells with fewer than three | Cells with a flagged draw baseline |
| --- | --- | --- | --- | --- | --- | --- |
| US High Plains B | 16 | 512 | 8,192 | [330 rotations](../data/processed/consensus_shortlist_p44_us_high_plains_b.csv.gz) | 0 | 4,096 |
| Telangana A | 1 | 512 | 512 | [303,132 rotations](../data/processed/consensus_shortlist_p44_telangana_a.csv.gz) | 0 | 429 |
| Makueni North Candidate | 1 | 512 | 512 | [41,707 rotations](../data/processed/consensus_shortlist_p44_kenya_makueni_north.csv.gz) | 9 | 323 |

Kansas crosses the 512 P22 draws with all 16 P43 configurations, including the original and all combinations of nitrogen, disease and off/43/70/97 mm water carryover. Each configuration contributes equally. Telangana and Makueni each use one scoring specification, the original. Both lack a P43 benchmark. P44 predates the [P42 smoother](smooth_climate_fit.md) and the [P46 regional variants](regional_scoring_variants.md). Its frequencies describe the tested configurations.

The replay reproduced each original P22 winner histogram and nominal winner, and the P43 variant-specific winner-change rates. A cell ranks all canonical feasible rotations plus the draw's baseline, once even when it is also feasible. A flagged baseline remains a comparison row. Exact ties favor that baseline, then the first canonical cycle in catalog order. Ineligible alternatives receive no credit. Counts are divided by all cells, including cells with fewer than three candidates. The frequency files include every eligible or admitted draw rotation, the nominal eligible alternatives, and the fixed reference strategies. All other canonical cycles have zero top-rank counts. Counts for Kansas, Telangana and Makueni describe different variant sets and share the same draw-generation design. They are descriptive frequencies over model assumptions, with no sampling intervals.

## Consensus and fixed baseline

| Farm | Preset | Set size at 40 / 50 / 60% | Most frequent top-three rotation | Top-three cells (share) | P18 label | Fixed baseline top one / top three | Overlap at 50% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US High Plains B | Water Saver | 0 / 0 / 0 | fallow → soybean → sunflower | 1,914 (23.36%) | low | 0.00% / 0.68% | 0 |
| US High Plains B | Soil Builder | 0 / 0 / 0 | fallow → soybean → cereal rye cover | 2,616 (31.93%) | low | 0.00% / 0.39% | 0 |
| US High Plains B | Income | 0 / 0 / 0 | maize → soybean → sunflower | 2,142 (26.15%) | low | 0.00% / 0.39% | 0 |
| US High Plains B | Balanced | 0 / 0 / 0 | fallow → soybean → sunflower | 1,840 (22.46%) | low | 0.00% / 0.39% | 0 |
| Telangana A | Water Saver | 0 / 0 / 0 | soybean/fallow → soybean/fallow → soybean/fallow | 167 (32.62%) | low | 0.00% / 0.00% | 0 |
| Telangana A | Soil Builder | 0 / 0 / 0 | soybean/fallow → soybean/fallow → soybean/fallow | 204 (39.84%) | low | 0.00% / 0.00% | 0 |
| Telangana A | Income | 0 / 0 / 0 | soybean/maize → soybean/maize → soybean/maize | 77 (15.04%) | low | 0.20% / 0.20% | 0 |
| Telangana A | Balanced | 0 / 0 / 0 | soybean/fallow → soybean/fallow → soybean/fallow | 157 (30.66%) | low | 0.00% / 0.00% | 0 |
| Makueni North Candidate | Water Saver | 0 / 0 / 0 | fallow/green gram → fallow/green gram → fallow/green gram | 155 (30.27%) | low | 0.98% / 1.95% | 0 |
| Makueni North Candidate | Soil Builder | 0 / 0 / 0 | green gram/fallow → green gram/fallow → green gram/fallow | 112 (21.88%) | low | 0.98% / 1.95% | 0 |
| Makueni North Candidate | Income | 0 / 0 / 0 | maize/common bean → maize/common bean → maize/common bean | 188 (36.72%) | low | 31.05% / 36.72% | 0 |
| Makueni North Candidate | Balanced | 0 / 0 / 0 | green gram/fallow → green gram/fallow → green gram/fallow | 86 (16.80%) | low | 1.17% / 2.73% | 0 |

All 36 threshold-specific sets were empty. No published baseline or alternative entered any set. There were zero consensus members to test for strict dominance, so dominance rates are **unavailable**. An empty dominance sample gives no evidence that the displayed rotations are undominated. A dominance event would require a feasible alternative to score strictly higher on all six normalized metrics in the same cell.

The four published alternatives are retained in every farm. At every threshold all four appear only in the displayed shortlist for every preset. The frequently occurring rotations above are descriptive results and do not fill the empty sets.

## Original winners and varying baselines

The original nominal winner uses P22's baseline-first ranking rule. The draw-winner membership fraction has the 512 original-only draws as its denominator. The last column follows the draw's current baseline, which can differ from the fixed published cycle in Telangana and Makueni.

| Farm | Preset | Original nominal winner | Nominal winner top one / top three | P18 label | Nominal in 50% set | Original draw winners in 50% set | Draw baseline top one / top three |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US High Plains B | Water Saver | fallow → sorghum → soybean | 7.03% / 18.85% | low | No | 0/512 | 0.00% / 0.68% |
| US High Plains B | Soil Builder | fallow → soybean → cereal rye cover | 21.58% / 31.93% | low | No | 0/512 | 0.00% / 0.39% |
| US High Plains B | Income | sorghum → soybean → sunflower | 7.13% / 13.65% | low | No | 0/512 | 0.00% / 0.39% |
| US High Plains B | Balanced | fallow → sorghum → soybean | 6.40% / 16.11% | low | No | 0/512 | 0.00% / 0.39% |
| Telangana A | Water Saver | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 21.09% / 21.29% | low | No | 0/512 | 0.00% / 0.00% |
| Telangana A | Soil Builder | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 22.27% / 22.27% | low | No | 0/512 | 0.00% / 0.00% |
| Telangana A | Income | pigeonpea/maize → pigeonpea/maize → pigeonpea/maize | 3.52% / 3.91% | low | No | 0/512 | 0.98% / 0.98% |
| Telangana A | Balanced | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 18.36% / 18.55% | low | No | 0/512 | 0.00% / 0.00% |
| Makueni North Candidate | Water Saver | green gram/fallow → green gram/fallow → green gram/fallow | 25.59% / 30.08% | low | No | 0/512 | 1.17% / 2.34% |
| Makueni North Candidate | Soil Builder | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 5.86% / 8.01% | low | No | 0/512 | 1.17% / 2.34% |
| Makueni North Candidate | Income | maize/green gram → maize/green gram → maize/green gram | 11.72% / 14.84% | low | No | 0/512 | 32.42% / 38.67% |
| Makueni North Candidate | Balanced | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 7.23% / 9.77% | low | No | 0/512 | 1.37% / 3.12% |

<details>
<summary>All four displayed alternatives by farm and preset</summary>

The following cycles missed the consensus cutoff at all three thresholds. Their shares describe the same variant-by-draw cells as the leading cycles above.

| Farm | Preset | Published strategy label | Canonical rotation | Top one / top three | P18 label |
| --- | --- | --- | --- | --- | --- |
| US High Plains B | Water Saver | Balanced | fallow → winter wheat → soybean | 6.03% / 11.62% | low |
| US High Plains B | Water Saver | Water Saver | fallow → sorghum → soybean | 7.03% / 18.85% | low |
| US High Plains B | Water Saver | Soil Builder | fallow → soybean → cereal rye cover | 6.45% / 12.74% | low |
| US High Plains B | Water Saver | Income | sorghum → soybean → sunflower | 0.00% / 0.00% | low |
| US High Plains B | Soil Builder | Balanced | fallow → winter wheat → soybean | 0.39% / 1.22% | low |
| US High Plains B | Soil Builder | Water Saver | fallow → sorghum → soybean | 2.34% / 7.23% | low |
| US High Plains B | Soil Builder | Soil Builder | fallow → soybean → cereal rye cover | 21.58% / 31.93% | low |
| US High Plains B | Soil Builder | Income | sorghum → soybean → sunflower | 0.39% / 1.56% | low |
| US High Plains B | Income | Balanced | fallow → winter wheat → soybean | 0.00% / 0.15% | low |
| US High Plains B | Income | Water Saver | fallow → sorghum → soybean | 0.10% / 0.29% | low |
| US High Plains B | Income | Soil Builder | fallow → soybean → cereal rye cover | 0.00% / 0.00% | low |
| US High Plains B | Income | Income | sorghum → soybean → sunflower | 7.13% / 13.65% | low |
| US High Plains B | Balanced | Balanced | fallow → winter wheat → soybean | 4.69% / 8.79% | low |
| US High Plains B | Balanced | Water Saver | fallow → sorghum → soybean | 6.40% / 16.11% | low |
| US High Plains B | Balanced | Soil Builder | fallow → soybean → cereal rye cover | 1.66% / 5.37% | low |
| US High Plains B | Balanced | Income | sorghum → soybean → sunflower | 2.93% / 5.47% | low |
| Telangana A | Water Saver | Soil Builder | soybean/fallow → pigeonpea/fallow → pigeonpea/fallow | 0.00% / 16.21% | low |
| Telangana A | Water Saver | Water Saver | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 21.09% / 21.29% | low |
| Telangana A | Water Saver | Balanced | pigeonpea/fallow → pigeonpea/fallow → pearl millet/fallow | 0.00% / 3.32% | low |
| Telangana A | Water Saver | Income | pigeonpea/maize → pigeonpea/maize → pigeonpea/maize | 0.00% / 0.00% | low |
| Telangana A | Soil Builder | Soil Builder | soybean/fallow → pigeonpea/fallow → pigeonpea/fallow | 0.00% / 20.12% | low |
| Telangana A | Soil Builder | Water Saver | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 22.27% / 22.27% | low |
| Telangana A | Soil Builder | Balanced | pigeonpea/fallow → pigeonpea/fallow → pearl millet/fallow | 0.00% / 0.20% | low |
| Telangana A | Soil Builder | Income | pigeonpea/maize → pigeonpea/maize → pigeonpea/maize | 0.00% / 0.00% | low |
| Telangana A | Income | Soil Builder | soybean/fallow → pigeonpea/fallow → pigeonpea/fallow | 0.00% / 0.00% | low |
| Telangana A | Income | Water Saver | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 0.00% / 0.00% | low |
| Telangana A | Income | Balanced | pigeonpea/fallow → pigeonpea/fallow → pearl millet/fallow | 0.00% / 0.00% | low |
| Telangana A | Income | Income | pigeonpea/maize → pigeonpea/maize → pigeonpea/maize | 3.52% / 3.91% | low |
| Telangana A | Balanced | Soil Builder | soybean/fallow → pigeonpea/fallow → pigeonpea/fallow | 0.00% / 13.09% | low |
| Telangana A | Balanced | Water Saver | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 18.36% / 18.55% | low |
| Telangana A | Balanced | Balanced | pigeonpea/fallow → pigeonpea/fallow → pearl millet/fallow | 0.00% / 2.34% | low |
| Telangana A | Balanced | Income | pigeonpea/maize → pigeonpea/maize → pigeonpea/maize | 0.00% / 0.00% | low |
| Makueni North Candidate | Water Saver | Income | maize/green gram → maize/green gram → maize/green gram | 0.00% / 0.00% | low |
| Makueni North Candidate | Water Saver | Water Saver | green gram/fallow → green gram/fallow → green gram/fallow | 25.59% / 30.08% | low |
| Makueni North Candidate | Water Saver | Balanced | green gram/fallow → green gram/pearl millet → green gram/pearl millet | 0.00% / 0.00% | low |
| Makueni North Candidate | Water Saver | Soil Builder | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 0.00% / 0.00% | low |
| Makueni North Candidate | Soil Builder | Income | maize/green gram → maize/green gram → maize/green gram | 0.00% / 0.00% | low |
| Makueni North Candidate | Soil Builder | Water Saver | green gram/fallow → green gram/fallow → green gram/fallow | 19.53% / 21.88% | low |
| Makueni North Candidate | Soil Builder | Balanced | green gram/fallow → green gram/pearl millet → green gram/pearl millet | 0.00% / 8.01% | low |
| Makueni North Candidate | Soil Builder | Soil Builder | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 5.86% / 8.01% | low |
| Makueni North Candidate | Income | Income | maize/green gram → maize/green gram → maize/green gram | 11.72% / 14.84% | low |
| Makueni North Candidate | Income | Water Saver | green gram/fallow → green gram/fallow → green gram/fallow | 0.98% / 6.05% | low |
| Makueni North Candidate | Income | Balanced | green gram/fallow → green gram/pearl millet → green gram/pearl millet | 0.00% / 0.59% | low |
| Makueni North Candidate | Income | Soil Builder | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 5.47% / 8.79% | low |
| Makueni North Candidate | Balanced | Income | maize/green gram → maize/green gram → maize/green gram | 0.39% / 0.39% | low |
| Makueni North Candidate | Balanced | Water Saver | green gram/fallow → green gram/fallow → green gram/fallow | 15.82% / 16.80% | low |
| Makueni North Candidate | Balanced | Balanced | green gram/fallow → green gram/pearl millet → green gram/pearl millet | 0.00% / 6.84% | low |
| Makueni North Candidate | Balanced | Soil Builder | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 7.23% / 9.77% | low |

</details>

## Evidence and publication scope

| P43 input | Evidence grade | Application grade | Source |
| --- | --- | --- | --- |
| Soybean N credit by successor | literature | assumption, validate locally | [K-State Research and Extension, MF2586, Previous Crop Adjustment tables, cool- and warm-season crops](https://www.brown.k-state.edu/crops-livestock/documents/Soiltestinterpretationsandfertilizerrecommenations.pdf) |
| Loss of starting water after legumes | literature | assumption, validate locally | [Holman et al. (2018), Crop Science, Table 5, Garden City trial, 0–1.8 m](https://acsess.onlinelibrary.wiley.com/doi/10.2135/cropsci2017.05.0324) |
| Sorghum break for wheat tan spot | literature | assumption, validate locally | [Bockus and Claassen (1992), Plant Disease, Tables 2–3 and discussion, pp. 634–635](https://www.apsnet.org/publications/PlantDisease/BackIssues/Documents/1992Articles/PlantDisease76n06_633.PDF) |

P18 labels describe the original crop, weather and farm inputs for each rotation. The P43 sources constrain selected inputs in Kansas and require assumptions to map them onto the score. Agreement within these scoring and assumption choices cannot establish how rotations will perform in fields.

The [README](../README.md) links this result. The [ledger](evidence_ledger.md) includes the empty sets. Published nominal shortlist, optimizer hit rates, and P22/P28b results in the README and [demo](demo.md) still refer to their original experiments. Any statement that the displayed four alternatives recur across variants should be replaced with the empty-set finding from P44.

Rebuild offline with `python -m src.consensus_shortlist`, then refresh the documentation ledger with `python -m src.evidence_ledger`.
