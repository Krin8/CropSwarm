# P43 literature-informed variant

The [preregistration](p43_plan.md) was committed before any evaluation as `e1d966e`. This is an illustrative Kansas what-if that needs local validation. In Telangana and Makueni the original scorer applies. Their input rows show **no benchmark** for the Kansas corrections in this study. A later audit compared other regional benchmarks. [P45 regional audit](literature_check_p45.md) The [saved P43 results](../data/processed/literature_variant_p43.json) are a separate output. They contain every configuration, farm, preset, raw and normalized metric delta, feasibility flag and matched-draw comparison.

## Inputs and evidence

| Correction | Value | Input grade | Application grade | Publication |
| --- | --- | --- | --- | --- |
| Soybean N credit by successor | 0 before wheat, 45 kg N/ha before maize, sorghum or sunflower | literature | assumption, validate locally | [K-State Research and Extension, MF2586, Previous Crop Adjustment tables, cool- and warm-season crops](https://www.brown.k-state.edu/crops-livestock/documents/Soiltestinterpretationsandfertilizerrecommenations.pdf) |
| Loss of starting water after legumes | 43, 70, 97 mm after legumes | literature | assumption, validate locally | [Holman et al. (2018), Crop Science, Table 5, Garden City trial, 0–1.8 m](https://acsess.onlinelibrary.wiley.com/doi/10.2135/cropsci2017.05.0324) |
| Sorghum break for wheat tan spot | 79.3% proportional penalty reduction | literature | assumption, validate locally | [Bockus and Claassen (1992), Plant Disease, Tables 2–3 and discussion, pp. 634–635](https://www.apsnet.org/publications/PlantDisease/BackIssues/Documents/1992Articles/PlantDisease76n06_633.PDF) |

The Kansas soybean correction depends on the successor. The water calculation translates a measured deep-profile difference into an incremental shortfall around the same shallow bucket. It applies to winter wheat immediately after a legume and uses the published 201 mm fallow reference with 43, 70 and 97 mm reductions. The tan spot correction uses the median relative severity reduction (79.26%), within the four 1991 no-till measurements (74.95%–91.19%). For wheat after sorghum, the nominal per-transition penalty falls from 0.500 to 0.104 index points. Its penalty mapping is an assumption. The evidence does not quantify a similar effect for all crops, states or management practices. Every other transition retains its original scoring rules.

## Nominal rankings and near-ties

All 16 configurations used unchanged weights and exact enumeration of canonical cycles. N is nitrogen, W is the number of millimetres of starting water removed, and D is the tan spot correction. Feasible alternatives exclude repeated adjacent crops and apply the original calendar and water thresholds. The baseline remains visible as a fixed strategy for metric comparison. Kansas retained 168 eligible alternatives in all nominal configurations. Telangana retained 211,394 and Makueni 16,914. Rank correlation uses common eligible alternatives and average ranks for tied objectives. Near-top counts include the winner and all alternatives within 0.01 weighted-score points (design choice).

In Kansas the original winner lost optimality in 24 of 60 corrected configuration–preset comparisons. Nitrogen changed the water-saver and balanced winners, from fallow → sorghum → soybean to fallow → soybean → sorghum. Disease changed the income winner, to winter wheat → soybean → sorghum. Water alone changed some ranks and left all four top rotations in place. Using all three corrections produced the same three winner changes at each water level. Soil builder retained its winner throughout. Kansas rank correlations ranged from 0.97870 to 0.99973 across the corrected configurations, and all new top-two gaps remained within 0.01. In 24 comparisons the original two-way exact tie became a single maximizer with a small lead. No preset gained or lost its top-two near-tie status.

### Kansas, every configuration and preset

The original rotation in each preset is the entry in the first four rows. “Near top (in/out)” gives the number within tolerance followed by the count entering or leaving that set relative to the original. Exact ties use the numerical tolerance in the [tie settings](../config/tie_diagnosis.json). Each row also reports the P22 rate relative to the configuration's own nominal winner, with change from the original rate in percentage points. Paired disagreement compares the configuration against the original on the identical draw.

| Config | Preset | Variant top rotation | Score | Rank ρ | Top-two gap | Exact top ties | Near top (in/out) | P22 label change (Δ) | P22 material change (Δ) | Paired disagreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | Water Saver | fallow → sorghum → soybean | 0.683723 | 1.00000 | 0.000000 | 2 | 4 (+0/−0) | 85.94% (+0.00 pp) | 77.73% (+0.00 pp) | 0.00% |
| original | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 1.00000 | 0.000000 | 2 | 4 (+0/−0) | 76.37% (+0.00 pp) | 58.98% (+0.00 pp) | 0.00% |
| original | Income | sorghum → soybean → sunflower | 0.641364 | 1.00000 | 0.000000 | 2 | 2 (+0/−0) | 92.58% (+0.00 pp) | 86.52% (+0.00 pp) | 0.00% |
| original | Balanced | fallow → sorghum → soybean | 0.678125 | 1.00000 | 0.000000 | 2 | 2 (+0/−0) | 87.11% (+0.00 pp) | 79.10% (+0.00 pp) | 0.00% |
| D | Water Saver | fallow → sorghum → soybean | 0.683723 | 0.99715 | 0.000000 | 2 | 4 (+0/−0) | 85.94% (+0.00 pp) | 77.73% (+0.00 pp) | 0.20% |
| D | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.99698 | 0.000000 | 2 | 4 (+0/−0) | 76.37% (+0.00 pp) | 58.98% (+0.00 pp) | 0.20% |
| D | Income | winter wheat → soybean → sorghum | 0.646179 | 0.99580 | 0.004816 | 1 | 3 (+1/−0) | 96.48% (+3.91 pp) | 94.53% (+8.01 pp) | 6.25% |
| D | Balanced | fallow → sorghum → soybean | 0.678125 | 0.99458 | 0.000000 | 2 | 2 (+0/−0) | 87.30% (+0.20 pp) | 79.10% (+0.00 pp) | 0.78% |
| N | Water Saver | fallow → soybean → sorghum | 0.687295 | 0.99523 | 0.003571 | 1 | 2 (+0/−2) | 84.18% (-1.76 pp) | 75.00% (-2.73 pp) | 25.59% |
| N | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.99198 | 0.000000 | 2 | 5 (+1/−0) | 80.47% (+4.10 pp) | 62.11% (+3.12 pp) | 16.41% |
| N | Income | sorghum → soybean → sunflower | 0.643744 | 0.99933 | 0.000000 | 2 | 2 (+0/−0) | 92.58% (+0.00 pp) | 86.33% (-0.20 pp) | 16.80% |
| N | Balanced | fallow → soybean → sorghum | 0.682172 | 0.99476 | 0.004048 | 1 | 2 (+0/−0) | 84.57% (-2.54 pp) | 76.95% (-2.15 pp) | 26.95% |
| N_D | Water Saver | fallow → soybean → sorghum | 0.687295 | 0.99230 | 0.003571 | 1 | 2 (+0/−2) | 84.18% (-1.76 pp) | 75.00% (-2.73 pp) | 25.78% |
| N_D | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.98807 | 0.000000 | 2 | 5 (+1/−0) | 80.47% (+4.10 pp) | 62.11% (+3.12 pp) | 16.60% |
| N_D | Income | winter wheat → soybean → sorghum | 0.648560 | 0.99531 | 0.004816 | 1 | 3 (+1/−0) | 96.48% (+3.91 pp) | 94.34% (+7.81 pp) | 21.48% |
| N_D | Balanced | fallow → soybean → sorghum | 0.682172 | 0.98925 | 0.004048 | 1 | 2 (+0/−0) | 84.77% (-2.34 pp) | 76.95% (-2.15 pp) | 27.54% |
| W43 | Water Saver | fallow → sorghum → soybean | 0.683723 | 0.99748 | 0.000000 | 2 | 4 (+0/−0) | 85.94% (+0.00 pp) | 77.73% (+0.00 pp) | 0.20% |
| W43 | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.99973 | 0.000000 | 2 | 4 (+0/−0) | 76.37% (+0.00 pp) | 58.98% (+0.00 pp) | 0.00% |
| W43 | Income | sorghum → soybean → sunflower | 0.641364 | 0.99971 | 0.000000 | 2 | 2 (+0/−0) | 92.58% (+0.00 pp) | 86.52% (+0.00 pp) | 4.88% |
| W43 | Balanced | fallow → sorghum → soybean | 0.678125 | 0.99904 | 0.000000 | 2 | 2 (+0/−0) | 87.11% (+0.00 pp) | 79.10% (+0.00 pp) | 0.00% |
| W43_D | Water Saver | fallow → sorghum → soybean | 0.683723 | 0.99422 | 0.000000 | 2 | 4 (+0/−0) | 85.94% (+0.00 pp) | 77.73% (+0.00 pp) | 0.39% |
| W43_D | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.99660 | 0.000000 | 2 | 4 (+0/−0) | 76.37% (+0.00 pp) | 58.98% (+0.00 pp) | 0.20% |
| W43_D | Income | winter wheat → soybean → sorghum | 0.646179 | 0.99556 | 0.004816 | 1 | 3 (+1/−0) | 96.48% (+3.91 pp) | 94.34% (+7.81 pp) | 8.79% |
| W43_D | Balanced | fallow → sorghum → soybean | 0.678125 | 0.99318 | 0.000000 | 2 | 2 (+0/−0) | 87.30% (+0.20 pp) | 79.10% (+0.00 pp) | 0.78% |
| N_W43 | Water Saver | fallow → soybean → sorghum | 0.687295 | 0.99014 | 0.003571 | 1 | 2 (+0/−2) | 84.18% (-1.76 pp) | 75.00% (-2.73 pp) | 25.59% |
| N_W43 | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.98980 | 0.000000 | 2 | 5 (+1/−0) | 80.47% (+4.10 pp) | 62.11% (+3.12 pp) | 16.41% |
| N_W43 | Income | sorghum → soybean → sunflower | 0.643744 | 0.99898 | 0.000000 | 2 | 2 (+0/−0) | 92.58% (+0.00 pp) | 86.33% (-0.20 pp) | 19.34% |
| N_W43 | Balanced | fallow → soybean → sorghum | 0.682172 | 0.99060 | 0.004048 | 1 | 2 (+0/−0) | 84.57% (-2.54 pp) | 76.95% (-2.15 pp) | 26.95% |
| N_W43_D | Water Saver | fallow → soybean → sorghum | 0.687295 | 0.98692 | 0.003571 | 1 | 2 (+0/−2) | 84.18% (-1.76 pp) | 75.00% (-2.73 pp) | 25.78% |
| N_W43_D | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.98590 | 0.000000 | 2 | 5 (+1/−0) | 80.47% (+4.10 pp) | 62.11% (+3.12 pp) | 16.60% |
| N_W43_D | Income | winter wheat → soybean → sorghum | 0.648560 | 0.99483 | 0.004816 | 1 | 3 (+1/−0) | 96.48% (+3.91 pp) | 94.34% (+7.81 pp) | 22.66% |
| N_W43_D | Balanced | fallow → soybean → sorghum | 0.682172 | 0.98466 | 0.004048 | 1 | 2 (+0/−0) | 84.77% (-2.34 pp) | 76.95% (-2.15 pp) | 27.54% |
| W70 | Water Saver | fallow → sorghum → soybean | 0.683723 | 0.99278 | 0.000000 | 2 | 4 (+0/−0) | 85.94% (+0.00 pp) | 77.73% (+0.00 pp) | 0.20% |
| W70 | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.99956 | 0.000000 | 2 | 4 (+0/−0) | 76.37% (+0.00 pp) | 58.98% (+0.00 pp) | 0.00% |
| W70 | Income | sorghum → soybean → sunflower | 0.641364 | 0.99954 | 0.000000 | 2 | 2 (+0/−0) | 92.58% (+0.00 pp) | 86.52% (+0.00 pp) | 5.66% |
| W70 | Balanced | fallow → sorghum → soybean | 0.678125 | 0.99771 | 0.000000 | 2 | 2 (+0/−0) | 87.11% (+0.00 pp) | 79.10% (+0.00 pp) | 0.00% |
| W70_D | Water Saver | fallow → sorghum → soybean | 0.683723 | 0.98951 | 0.000000 | 2 | 4 (+0/−0) | 85.94% (+0.00 pp) | 77.73% (+0.00 pp) | 0.39% |
| W70_D | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.99626 | 0.000000 | 2 | 4 (+0/−0) | 76.37% (+0.00 pp) | 58.98% (+0.00 pp) | 0.20% |
| W70_D | Income | winter wheat → soybean → sorghum | 0.646179 | 0.99544 | 0.004816 | 1 | 3 (+1/−0) | 96.48% (+3.91 pp) | 94.34% (+7.81 pp) | 9.57% |
| W70_D | Balanced | fallow → sorghum → soybean | 0.678125 | 0.99181 | 0.000000 | 2 | 2 (+0/−0) | 87.30% (+0.20 pp) | 79.10% (+0.00 pp) | 0.78% |
| N_W70 | Water Saver | fallow → soybean → sorghum | 0.687295 | 0.98683 | 0.003571 | 1 | 2 (+0/−2) | 84.18% (-1.76 pp) | 75.00% (-2.73 pp) | 25.59% |
| N_W70 | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.98887 | 0.000000 | 2 | 5 (+1/−0) | 80.47% (+4.10 pp) | 62.11% (+3.12 pp) | 16.41% |
| N_W70 | Income | sorghum → soybean → sunflower | 0.643744 | 0.99873 | 0.000000 | 2 | 2 (+0/−0) | 92.58% (+0.00 pp) | 86.33% (-0.20 pp) | 19.53% |
| N_W70 | Balanced | fallow → soybean → sorghum | 0.682172 | 0.98859 | 0.004048 | 1 | 2 (+0/−0) | 84.57% (-2.54 pp) | 76.95% (-2.15 pp) | 26.95% |
| N_W70_D | Water Saver | fallow → soybean → sorghum | 0.687295 | 0.98384 | 0.003571 | 1 | 2 (+0/−2) | 84.18% (-1.76 pp) | 75.00% (-2.73 pp) | 25.78% |
| N_W70_D | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.98506 | 0.000000 | 2 | 5 (+1/−0) | 80.47% (+4.10 pp) | 62.11% (+3.12 pp) | 16.60% |
| N_W70_D | Income | winter wheat → soybean → sorghum | 0.648560 | 0.99463 | 0.004816 | 1 | 3 (+1/−0) | 96.48% (+3.91 pp) | 94.34% (+7.81 pp) | 22.85% |
| N_W70_D | Balanced | fallow → soybean → sorghum | 0.682172 | 0.98267 | 0.004048 | 1 | 2 (+0/−0) | 84.77% (-2.34 pp) | 76.95% (-2.15 pp) | 27.54% |
| W97 | Water Saver | fallow → sorghum → soybean | 0.683723 | 0.98905 | 0.000000 | 2 | 4 (+0/−0) | 85.94% (+0.00 pp) | 77.73% (+0.00 pp) | 0.20% |
| W97 | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.99924 | 0.000000 | 2 | 4 (+0/−0) | 76.37% (+0.00 pp) | 58.98% (+0.00 pp) | 0.00% |
| W97 | Income | sorghum → soybean → sunflower | 0.641364 | 0.99949 | 0.000000 | 2 | 2 (+0/−0) | 92.58% (+0.00 pp) | 86.52% (+0.00 pp) | 5.66% |
| W97 | Balanced | fallow → sorghum → soybean | 0.678125 | 0.99504 | 0.000000 | 2 | 2 (+0/−0) | 87.11% (+0.00 pp) | 79.10% (+0.00 pp) | 0.00% |
| W97_D | Water Saver | fallow → sorghum → soybean | 0.683723 | 0.98541 | 0.000000 | 2 | 4 (+0/−0) | 85.94% (+0.00 pp) | 77.73% (+0.00 pp) | 0.39% |
| W97_D | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.99598 | 0.000000 | 2 | 4 (+0/−0) | 76.37% (+0.00 pp) | 58.98% (+0.00 pp) | 0.20% |
| W97_D | Income | winter wheat → soybean → sorghum | 0.646179 | 0.99532 | 0.004816 | 1 | 3 (+1/−0) | 96.48% (+3.91 pp) | 94.34% (+7.81 pp) | 9.57% |
| W97_D | Balanced | fallow → sorghum → soybean | 0.678125 | 0.98913 | 0.000000 | 2 | 2 (+0/−0) | 87.30% (+0.20 pp) | 79.10% (+0.00 pp) | 0.78% |
| N_W97 | Water Saver | fallow → soybean → sorghum | 0.687295 | 0.98352 | 0.003571 | 1 | 2 (+0/−2) | 84.18% (-1.76 pp) | 75.00% (-2.73 pp) | 25.59% |
| N_W97 | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.98781 | 0.000000 | 2 | 5 (+1/−0) | 80.47% (+4.10 pp) | 62.11% (+3.12 pp) | 16.41% |
| N_W97 | Income | sorghum → soybean → sunflower | 0.643744 | 0.99816 | 0.000000 | 2 | 2 (+0/−0) | 92.58% (+0.00 pp) | 86.33% (-0.20 pp) | 19.53% |
| N_W97 | Balanced | fallow → soybean → sorghum | 0.682172 | 0.98448 | 0.004048 | 1 | 2 (+0/−0) | 84.57% (-2.54 pp) | 76.95% (-2.15 pp) | 26.95% |
| N_W97_D | Water Saver | fallow → soybean → sorghum | 0.687295 | 0.97953 | 0.003571 | 1 | 2 (+0/−2) | 84.18% (-1.76 pp) | 75.00% (-2.73 pp) | 25.78% |
| N_W97_D | Soil Builder | fallow → soybean → cereal rye cover | 0.715755 | 0.98412 | 0.000000 | 2 | 5 (+1/−0) | 80.47% (+4.10 pp) | 62.11% (+3.12 pp) | 16.60% |
| N_W97_D | Income | winter wheat → soybean → sorghum | 0.648560 | 0.99391 | 0.004816 | 1 | 3 (+1/−0) | 96.48% (+3.91 pp) | 94.34% (+7.81 pp) | 22.85% |
| N_W97_D | Balanced | fallow → soybean → sorghum | 0.682172 | 0.97870 | 0.004048 | 1 | 2 (+0/−0) | 84.77% (-2.34 pp) | 76.95% (-2.15 pp) | 27.54% |

### Telangana and Makueni, all configurations identical

Rank Spearman is 1.000 in every configuration, paired disagreement is zero, and none of the six metrics changed for any baseline or shortlist strategy. These results show the correction boundary. The literature was not transferred to these farms.

| Farm | Preset | Top rotation in every configuration | Score | Exact top ties | Top-two gap | Near top | P22 label change | P22 material change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Telangana A | Water Saver | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 0.801544 | 1 | 0.008222 | 3 | 78.91% | 71.09% |
| Telangana A | Soil Builder | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 0.770346 | 1 | 0.004286 | 3 | 77.73% | 66.41% |
| Telangana A | Income | pigeonpea/maize → pigeonpea/maize → pigeonpea/maize | 0.672979 | 1 | 0.000573 | 56 | 96.48% | 92.77% |
| Telangana A | Balanced | pigeonpea/fallow → pigeonpea/fallow → pigeonpea/fallow | 0.741856 | 1 | 0.008115 | 2 | 81.64% | 75.39% |
| Makueni North Candidate | Water Saver | green gram/fallow → green gram/fallow → green gram/fallow | 0.746728 | 1 | 0.005711 | 3 | 74.41% | 65.04% |
| Makueni North Candidate | Soil Builder | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 0.755802 | 1 | 0.000785 | 29 | 94.14% | 76.95% |
| Makueni North Candidate | Income | maize/green gram → maize/green gram → maize/green gram | 0.707399 | 1 | 0.001022 | 42 | 88.28% | 83.79% |
| Makueni North Candidate | Balanced | green gram/pearl millet → green gram/pearl millet → green gram/pearl millet | 0.739487 | 1 | 0.003566 | 12 | 92.77% | 82.23% |

## Original baseline and displayed shortlist

The Kansas baseline had zero change across all six metrics. The only nonzero metric in the fixed shortlist was the income alternative's nitrogen balance, +3.6667 kg N/ha per slot (+0.02381 normalized) in configurations with N. The other five metrics and all other fixed strategies had zero deltas. Water and disease can still change scores and ranks of other canonical rotations. Those two corrections do not target a transition in the published shortlist. The JSON and the app table report all six metric deltas, including zeros, for each fixed strategy and configuration.

## P22 replay and limits

Kansas used the identical 512 P22 assumption draws and seed 42. The original finite-run label and material-change fractions matched P22. The replay used the same input inventory, varied crop needs and season boundaries, and kept the baseline-first convention. For no-benchmark farms the correction is identically zero on every draw, so the original P22 fractions apply.

With all three changes at the middle water reduction, Kansas label-change rates shifted from 85.94% to 84.18% for water saver, 76.37% to 80.47% for soil builder, 92.58% to 96.48% for income, and 87.11% to 84.77% for balanced. Water alone left those rates equal to the original on every preset, although at least some individual draws selected different winners. Under the middle combined case, 16.60%–27.54% of identical draws selected a different rotation, depending on the preset. These are frequencies under the chosen assumption ranges. There is no sampling interval for the comparison.

The original published strategy scores, ACO checks, P22 sensitivity and weather-shift results remain the reference for the original scoring. P43 adds a Kansas-specific sensitivity result to the evidence ledger. Main demo outcomes and README numbers still describe their original experiments. A presentation that says Kansas crop order is irrelevant should limit that statement to the earlier formula and tested cycles. A presentation that claims the corrected winners are practical recommendations would exceed the evidence. This exercise does not establish the effect of a rotation on a farm.

Rebuild the separate result offline with `python -m src.literature_variant`. Refresh the documentation ledger with `python -m src.evidence_ledger`.
