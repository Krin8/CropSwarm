# Risk-aware swarm optimization (P28)

The **Robust pick** panel compares the nominal winner and three risk-objective picks per farm and priority preset. Its robustness refers to the assumption ranges sampled from P22. Field validation is still needed. The historical scoring engine, its weights and constraints, P9 rankings and all earlier saved results are unchanged.

## Assumptions and search space

Use the first **128** draws from the existing P22 joint stream, with seed **42** and the same input ordering and sampling rules. Use the first **256** for the Kansas sensitivity check. The cache records a SHA-256 digest for each prefix used. These sample sizes, ranges and distributions are design choices. This checks sensitivity to assumptions, using the cached NASA POWER daily record as in P22. P16 instead applies uniform weather shifts. [P22 ranges](sensitivity.md) · [P28 settings](../config/robust_optimization.json)

A fixed candidate must satisfy the nominal hard rules and uses the original three-year horizon. Search every nominally feasible canonical cycle, counting whole-year shifts once. In every draw, recompute each fixed candidate's metrics and hard-rule status using the existing scoring engine. A failed rule gives that candidate **zero realized weighted score** in the draw. This is an illustrative decision rule for P28. It does not edit any historical score or assume that crop failure produces zero yield. Report how many draws each fixed rotation remains feasible.

Regret uses a draw-specific benchmark. It compares with the best feasible canonical rotation available under that draw, including rotations whose eligibility emerged only in that draw. Following P22, the benchmark can also select the drawn baseline with any flags it carries. The baseline remains visible in the existing strategy comparison. Within P28, all fixed picks compete over the same nominally feasible space. The clairvoyant benchmark can adapt to a draw and a fixed pick cannot.

## Objectives

For draw `d`, let `s(r,d)` be the weighted score for rotation `r`, after the zero-score rule, and `B(d)` be the draw benchmark. Each score uses the existing normalized 0–1 metrics and the chosen preset.

- **Expected score.** Maximize the average of `s(r,d)` across all draws.
- **Lower-tail CVaR at 10%.** Maximize the mean score over exactly the worst 10% of the draw mass. Sort the scores, sum the first `floor(0.10 × n)` and include the next score fractionally before dividing by `0.10 × n`. For 128 draws this uses 12 full scores and 0.8 of the next. For 256 it uses 25 full scores and 0.6 of the next.
- **Minimax regret.** Minimize `max_d(max(0, B(d) − s(r,d)))`. The colony maximizes one minus this quantity, so its fitness stays nonnegative and the ordering is preserved.

The nominal best is the lexicographically first canonical cycle within the **0.000001** tolerance of the maximum nominal score. This tolerance is a design choice for float32 metrics. That score matches the saved P9 exact optimum within the tolerance. For risk objectives, keep the nominal pick if it is tied within the same tolerance. Otherwise select the lexicographically first tied cycle. A tie counts as an objective hit even when a colony returns another cycle. The price of robustness is nominal-best score minus selected nominal score. Positive changes in worst score or reductions in maximum regret favor the selected option. The result also records mean-score and lower-tail changes.

## Compute and verification

The exact method uses the existing six normalized score metrics as float32, with a separate boolean feasibility mask. These are computed once per fixed rotation and draw and stored in a temporary memory map. Regret benchmarks reuse those feasible rows, scoring only additional feasible rotations and the draw's baseline. Read the cache in chunks of **1,024 rotations**, weighting and accumulating in float64. The on-disk cache is temporary. The measured process high-water mark includes the Python environment, cached climate windows, enumeration and resident memory-map pages.

The table reports runtime for the main run and, for Kansas, the additional exact draw-count check. Exact references covered Kansas, Makueni and all **211,394** nominal Telangana rotations. Every farm finished well within the 30-minute-per-preset limit. No shortlist was used.

The P28 colonies use the existing ant counts, iterations, evaporation, elites and heuristic. The fitness callback derives the objective from each ant's canonical draw metrics, with memoization within a farm and preset. It does not look up the precomputed exact-objective table or seed starting rotations from it. Minimax uses the same draw benchmark that defines its objective. For each of 36 farm–preset–objective combinations, run 10 trials of five independent colonies. Trial `i` uses seeds `i + 10 × j` for restart `j = 0…4`. The single-run column uses the first colony of each trial. The gap is exact minus achieved utility, which equals the excess maximum regret for minimax. [P9 optimizer settings](../config/optimizer.json)

| Farm | Canonical rotations | Draw metrics and mask, MiB | Peak RSS, MiB | Draw prep + cache + benchmark, s | Longest exact preset, s | ACO, s | Total, s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kansas | 168 | 1.03 | 268 | 1.80 | 0.0002 | 18.68 | 20.51 |
| Telangana | 211,394 | 645.12 | 1271 | 15.15 | 0.1293 | 18.20 | 33.93 |
| Makueni | 16,914 | 51.62 | 347 | 2.54 | 0.0097 | 19.09 | 21.70 |

## Results for every farm and preset

Recorded cycles appear as crop IDs in slot order. A slash starts another year. ×3 marks a repeated two-slot year. All scores are weighted model points. All listed rotations have a low overall P18 evidence label. The cached JSON includes all six metric-level grades.

| Farm | Preset | Nominal best | Nominal score | Feasible draws | Worst-draw score | Maximum regret | Nominal ties |
|---|---|---|---:|---:|---:|---:|---:|
| Kansas | water saver | `fallow / sorghum / soybean` | 0.6837 | 71/128 | 0.0000 | 0.7285 | 2 |
| Kansas | soil builder | `fallow / soybean / cereal_rye_cover` | 0.7158 | 63/128 | 0.0000 | 0.7518 | 2 |
| Kansas | income | `sorghum / soybean / sunflower` | 0.6414 | 59/128 | 0.0000 | 0.7485 | 2 |
| Kansas | balanced | `fallow / sorghum / soybean` | 0.6781 | 71/128 | 0.0000 | 0.7366 | 2 |
| Telangana | water saver | `pigeonpea + fallow` ×3 | 0.8015 | 70/128 | 0.0000 | 0.8502 | 1 |
| Telangana | soil builder | `pigeonpea + fallow` ×3 | 0.7703 | 70/128 | 0.0000 | 0.8137 | 1 |
| Telangana | income | `pigeonpea + maize` ×3 | 0.6730 | 65/128 | 0.0000 | 0.7715 | 1 |
| Telangana | balanced | `pigeonpea + fallow` ×3 | 0.7419 | 70/128 | 0.0000 | 0.8017 | 1 |
| Makueni | water saver | `green_gram + fallow` ×3 | 0.7467 | 109/128 | 0.0000 | 0.7662 | 1 |
| Makueni | soil builder | `green_gram + pearl_millet` ×3 | 0.7558 | 82/128 | 0.0000 | 0.8007 | 1 |
| Makueni | income | `maize + green_gram` ×3 | 0.7074 | 61/128 | 0.0000 | 0.7477 | 1 |
| Makueni | balanced | `green_gram + pearl_millet` ×3 | 0.7395 | 82/128 | 0.0000 | 0.7783 | 1 |

The table below gives each exact pick and its changes relative to the nominal winner. Positive regret reduction means the pick improves maximum regret. A zero denotes no change at the listed precision.

| Farm | Preset | Objective | Exact pick | Feasible draws | Differs | Nominal cost | Δ worst | Regret reduction | Δ mean | Δ CVaR | Ties |
|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| Kansas | water saver | Expected score | `fallow / common_bean / sunflower` | 92/128 | Yes | 0.0435 | 0.0000 | -0.0138 | 0.0955 | 0.0000 | 2 |
| Kansas | water saver | CVaR 10% | `fallow / sorghum / soybean` | 71/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 168 |
| Kansas | water saver | Minimax regret | `fallow / sorghum / soybean` | 71/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 2 |
| Kansas | soil builder | Expected score | `fallow / common_bean / sunflower` | 92/128 | Yes | 0.0453 | 0.0000 | -0.0075 | 0.1333 | 0.0000 | 2 |
| Kansas | soil builder | CVaR 10% | `fallow / soybean / cereal_rye_cover` | 63/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 168 |
| Kansas | soil builder | Minimax regret | `fallow / common_bean / soybean` | 82/128 | Yes | 0.0129 | 0.0000 | 0.0067 | 0.1045 | 0.0000 | 2 |
| Kansas | income | Expected score | `fallow / common_bean / sunflower` | 92/128 | Yes | 0.0878 | 0.0000 | 0.0258 | 0.1135 | 0.0000 | 2 |
| Kansas | income | CVaR 10% | `sorghum / soybean / sunflower` | 59/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 168 |
| Kansas | income | Minimax regret | `fallow / common_bean / sunflower` | 92/128 | Yes | 0.0878 | 0.0000 | 0.0258 | 0.1135 | 0.0000 | 2 |
| Kansas | balanced | Expected score | `fallow / common_bean / sunflower` | 92/128 | Yes | 0.0469 | 0.0000 | -0.0049 | 0.0947 | 0.0000 | 2 |
| Kansas | balanced | CVaR 10% | `fallow / sorghum / soybean` | 71/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 168 |
| Kansas | balanced | Minimax regret | `fallow / soybean / sunflower` | 80/128 | Yes | 0.0360 | 0.0000 | 0.0057 | 0.0465 | 0.0000 | 2 |
| Telangana | water saver | Expected score | `green_gram + fallow` ×3 | 117/128 | Yes | 0.0347 | 0.0000 | 0.0406 | 0.2757 | 0.1007 | 1 |
| Telangana | water saver | CVaR 10% | `fallow + paddy` ×3 | 118/128 | Yes | 0.1549 | 0.0000 | 0.0130 | 0.1738 | 0.1360 | 1 |
| Telangana | water saver | Minimax regret | `green_gram + fallow` ×3 | 117/128 | Yes | 0.0347 | 0.0000 | 0.0406 | 0.2757 | 0.1007 | 1 |
| Telangana | soil builder | Expected score | `green_gram + fallow` ×3 | 117/128 | Yes | 0.0309 | 0.0000 | 0.0410 | 0.2621 | 0.0985 | 1 |
| Telangana | soil builder | CVaR 10% | `fallow + paddy` ×3 | 118/128 | Yes | 0.1803 | 0.0000 | 0.0133 | 0.1320 | 0.1239 | 1 |
| Telangana | soil builder | Minimax regret | `green_gram + fallow` ×3 | 117/128 | Yes | 0.0309 | 0.0000 | 0.0410 | 0.2621 | 0.0985 | 1 |
| Telangana | income | Expected score | `green_gram + paddy` ×3 | 108/128 | Yes | 0.0272 | 0.0000 | 0.0145 | 0.2110 | 0.0000 | 1 |
| Telangana | income | CVaR 10% | `fallow + paddy` ×3 | 118/128 | Yes | 0.1503 | 0.0000 | 0.0145 | 0.1453 | 0.1058 | 1 |
| Telangana | income | Minimax regret | `fallow + sunflower` ×3 | 117/128 | Yes | 0.1652 | 0.0000 | 0.0399 | 0.1324 | 0.0654 | 1 |
| Telangana | balanced | Expected score | `green_gram + fallow` ×3 | 117/128 | Yes | 0.0360 | 0.0000 | 0.0514 | 0.2522 | 0.0935 | 1 |
| Telangana | balanced | CVaR 10% | `fallow + paddy` ×3 | 118/128 | Yes | 0.1416 | 0.0000 | 0.0153 | 0.1608 | 0.1264 | 1 |
| Telangana | balanced | Minimax regret | `green_gram + fallow` ×3 | 117/128 | Yes | 0.0360 | 0.0000 | 0.0514 | 0.2522 | 0.0935 | 1 |
| Makueni | water saver | Expected score | `green_gram + fallow` ×3 | 109/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1 |
| Makueni | water saver | CVaR 10% | `green_gram + fallow` ×3 | 109/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 16,914 |
| Makueni | water saver | Minimax regret | `green_gram + fallow` ×3 | 109/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1 |
| Makueni | soil builder | Expected score | `green_gram + fallow` ×3 | 109/128 | Yes | 0.0024 | 0.0000 | 0.0209 | 0.1584 | 0.0000 | 1 |
| Makueni | soil builder | CVaR 10% | `green_gram + pearl_millet` ×3 | 82/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 16,914 |
| Makueni | soil builder | Minimax regret | `cowpea + fallow` ×3 | 108/128 | Yes | 0.0311 | 0.0000 | 0.0255 | 0.1433 | 0.0000 | 1 |
| Makueni | income | Expected score | `green_gram + fallow` ×3 | 109/128 | Yes | 0.1180 | 0.0000 | 0.0018 | 0.1551 | 0.0000 | 1 |
| Makueni | income | CVaR 10% | `maize + green_gram` ×3 | 61/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 16,914 |
| Makueni | income | Minimax regret | `fallow + green_gram` ×3 | 96/128 | Yes | 0.1232 | 0.0000 | 0.0138 | 0.1017 | 0.0000 | 1 |
| Makueni | balanced | Expected score | `green_gram + fallow` ×3 | 109/128 | Yes | 0.0109 | 0.0000 | 0.0182 | 0.1479 | 0.0000 | 1 |
| Makueni | balanced | CVaR 10% | `green_gram + pearl_millet` ×3 | 82/128 | No | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 16,914 |
| Makueni | balanced | Minimax regret | `cowpea + fallow` ×3 | 108/128 | Yes | 0.0683 | 0.0000 | 0.0261 | 0.1196 | 0.0000 | 1 |

Expected-score optima differ from the nominal cycle in 11 of 12 combinations. Minimax picks differ in 10 of 12, and CVaR picks differ in four. Those four are all in Telangana. All nominal and selected rotations have a worst score of zero, so no pick improves the worst single draw. Minimax reduces maximum regret by up to 0.0514 points. Some expected-score picks increase maximum regret. Every nominal candidate in Kansas and Makueni ties at zero on CVaR. Their nominal picks are shown for that objective.

## ACO against the exact reference

| Farm | Preset | Objective | Single hits | Single gap mean / worst | Best-of-five hits | Best-of-five gap mean / worst |
|---|---|---|---:|---:|---:|---:|
| Kansas | water saver | Expected score | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | water saver | CVaR 10% | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | water saver | Minimax regret | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | soil builder | Expected score | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | soil builder | CVaR 10% | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | soil builder | Minimax regret | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | income | Expected score | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | income | CVaR 10% | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | income | Minimax regret | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | balanced | Expected score | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | balanced | CVaR 10% | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Kansas | balanced | Minimax regret | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Telangana | water saver | Expected score | 7/10 | 0.01324 / 0.08381 | 9/10 | 0.00183 / 0.01831 |
| Telangana | water saver | CVaR 10% | 0/10 | 0.13604 / 0.13604 | 0/10 | 0.11719 / 0.13604 |
| Telangana | water saver | Minimax regret | 4/10 | 0.00734 / 0.01533 | 10/10 | 0.00000 / 0.00000 |
| Telangana | soil builder | Expected score | 9/10 | 0.00306 / 0.03056 | 10/10 | 0.00000 / 0.00000 |
| Telangana | soil builder | CVaR 10% | 0/10 | 0.12392 / 0.12392 | 0/10 | 0.12392 / 0.12392 |
| Telangana | soil builder | Minimax regret | 3/10 | 0.00270 / 0.01033 | 9/10 | 0.00011 / 0.00110 |
| Telangana | income | Expected score | 2/10 | 0.04093 / 0.09717 | 9/10 | 0.00191 / 0.01908 |
| Telangana | income | CVaR 10% | 0/10 | 0.10577 / 0.10577 | 0/10 | 0.10577 / 0.10577 |
| Telangana | income | Minimax regret | 0/10 | 0.02187 / 0.02461 | 0/10 | 0.02149 / 0.02156 |
| Telangana | balanced | Expected score | 7/10 | 0.02352 / 0.08678 | 10/10 | 0.00000 / 0.00000 |
| Telangana | balanced | CVaR 10% | 0/10 | 0.12643 / 0.12643 | 0/10 | 0.11832 / 0.12643 |
| Telangana | balanced | Minimax regret | 1/10 | 0.01316 / 0.02181 | 9/10 | 0.00123 / 0.01234 |
| Makueni | water saver | Expected score | 6/10 | 0.03198 / 0.10181 | 10/10 | 0.00000 / 0.00000 |
| Makueni | water saver | CVaR 10% | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Makueni | water saver | Minimax regret | 7/10 | 0.00074 / 0.00248 | 10/10 | 0.00000 / 0.00000 |
| Makueni | soil builder | Expected score | 7/10 | 0.03490 / 0.15841 | 10/10 | 0.00000 / 0.00000 |
| Makueni | soil builder | CVaR 10% | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Makueni | soil builder | Minimax regret | 2/10 | 0.00353 / 0.01316 | 7/10 | 0.00088 / 0.00292 |
| Makueni | income | Expected score | 0/10 | 0.05940 / 0.09774 | 0/10 | 0.05514 / 0.05514 |
| Makueni | income | CVaR 10% | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Makueni | income | Minimax regret | 0/10 | 0.01870 / 0.02359 | 0/10 | 0.01381 / 0.01381 |
| Makueni | balanced | Expected score | 9/10 | 0.00683 / 0.06831 | 10/10 | 0.00000 / 0.00000 |
| Makueni | balanced | CVaR 10% | 10/10 | 0.00000 / 0.00000 | 10/10 | 0.00000 / 0.00000 |
| Makueni | balanced | Minimax regret | 1/10 | 0.00723 / 0.00814 | 2/10 | 0.00638 / 0.00798 |

Best of five reached the objective reference in **275 of 360** trials. By objective, it hit 108/120 expected-score, 80/120 CVaR and 87/120 minimax references. All 80 Kansas and Makueni CVaR hits correspond to an all-candidate tie. Excluding those ties, 195 of 280 trials hit the reference. Telangana CVaR had 0/40 hits and the largest recorded best-of-five gap, about 0.1360. The app shows exact results, while the table records swarm failures in full.

## Kansas draw-count check

At 256 draws, 7/12 exact displayed cycles match the 128-draw cycles. The distinction from the nominal choice agrees in 11/12 cases. A design tolerance of 0.01 weighted points gives agreement on nominal cost in 10/12 comparisons, worst-score change in 12/12, and regret reduction in 7/12. The CVaR tie and zero worst-score finding persist. The exact rotations and regret magnitudes show sample sensitivity.

| Preset | Objective | 128-draw cycle | 256-draw cycle | Nominal cost, 128 → 256 | Regret reduction, 128 → 256 |
|---|---|---|---|---:|---:|
| water saver | Expected score | `fallow / common_bean / sunflower` | `fallow / maize / common_bean` | 0.0435 → 0.0512 | -0.0138 → -0.0321 |
| water saver | CVaR 10% | `fallow / sorghum / soybean` | `fallow / sorghum / soybean` | 0.0000 → 0.0000 | 0.0000 → 0.0000 |
| water saver | Minimax regret | `fallow / sorghum / soybean` | `fallow / sorghum / soybean` | 0.0000 → 0.0000 | 0.0000 → 0.0000 |
| soil builder | Expected score | `fallow / common_bean / sunflower` | `fallow / common_bean / sunflower` | 0.0453 → 0.0453 | -0.0075 → 0.0033 |
| soil builder | CVaR 10% | `fallow / soybean / cereal_rye_cover` | `fallow / soybean / cereal_rye_cover` | 0.0000 → 0.0000 | 0.0000 → 0.0000 |
| soil builder | Minimax regret | `fallow / common_bean / soybean` | `fallow / sorghum / soybean` | 0.0129 → 0.0117 | 0.0067 → 0.0151 |
| income | Expected score | `fallow / common_bean / sunflower` | `fallow / maize / common_bean` | 0.0878 → 0.0774 | 0.0258 → -0.0011 |
| income | CVaR 10% | `sorghum / soybean / sunflower` | `sorghum / soybean / sunflower` | 0.0000 → 0.0000 | 0.0000 → 0.0000 |
| income | Minimax regret | `fallow / common_bean / sunflower` | `fallow / common_bean / sunflower` | 0.0878 → 0.0878 | 0.0258 → 0.0205 |
| balanced | Expected score | `fallow / common_bean / sunflower` | `fallow / maize / common_bean` | 0.0469 → 0.0565 | -0.0049 → -0.0364 |
| balanced | CVaR 10% | `fallow / sorghum / soybean` | `fallow / sorghum / soybean` | 0.0000 → 0.0000 | 0.0000 → 0.0000 |
| balanced | Minimax regret | `fallow / soybean / sunflower` | `fallow / sorghum / soybean` | 0.0360 → 0.0000 | 0.0057 → 0.0000 |

## Reproduce offline

Run `python -m src.robust_optimization` from the repository. Add `--farm` followed by a farm ID to refresh one site. The build writes only the P28 reports. The app displays their saved picks and applies the selected named preset to its reference inputs. Exact-search and process timing values vary by run.

[Kansas report](../data/processed/robust_optimization_us_high_plains_b.json) · [Telangana report](../data/processed/robust_optimization_telangana_a.json) · [Makueni report](../data/processed/robust_optimization_kenya_makueni_north.json)
