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

Run `python -m src.robust_optimization` from the repository. Add `--farm` followed by a farm ID to refresh one site. The build writes only the P28 reports. The P28b panel uses the separate files described below. Exact-search and process timing values vary by run.

[Kansas report](../data/processed/robust_optimization_us_high_plains_b.json) · [Telangana report](../data/processed/robust_optimization_telangana_a.json) · [Makueni report](../data/processed/robust_optimization_kenya_makueni_north.json)

## P28b feasible-tail and draw-count check

The P28 tables above preserve the original zero-score CVaR results and swarm trial counts. P28b uses the same canonical candidate sets, P22 assumptions, scoring inputs and draw-specific regret benchmarks. The 128-, 256- and 512-draw sets are nested prefixes of the original seed-42 P22 stream. They are illustrative design choices. The P28b builder writes separate outputs.

**Conditional CVaR** averages the lowest 10% of each candidate's feasible scores with the original fractional-boundary rule. A rotation with no feasible draws has an undefined conditional CVaR. Feasibility share is the number of feasible draws divided by the full draw count and is reported independently. This objective can favor a rotation that performs well in the few scenarios where it is feasible. Expected score and minimax regret retain the P28 zero-score rule on infeasible draws. Unconditional CVaR is also recomputed for each prefix and shown with its objective tie count.

Each objective lists the top three canonical candidates and their gaps to the best objective value. At the existing 0.000001-point tolerance, the nominal winner is preferred when it ties, then the first canonical tied cycle. Runners-up sort by utility, then canonical crop order. The near-tie flag compares the displayed winner and runner-up at the same tolerance. For minimax regret, a gap is the excess regret over the optimum.

For each objective and farm–preset, pool the top three candidates from each draw count. Within each prefix, use 500 paired bootstrap resamples of the draw indices, with seed 2028. All finalists see the same resampled indices and tied winners split credit. Exclude resamples where every finalist has undefined conditional CVaR. The resulting win shares describe reselection **among these finalists**, so they do not measure the probability of winning a fresh full-space search or the probability of field success. Resampling cannot expose scenarios outside the original draws, including unseen regret extremes.

For the Telangana ACO check, replay the original 128-draw unconditional objective and seeds 0–49 to audit search coverage and the prevalence of zero fitness. Evaluate conditional CVaR on the fixed 512-draw set with paired, held-out seeds 10000–10049. Compare the original 40 iterations with a single prespecified exploration variant using 160 iterations and a 20% uniform mixture over legal crop transitions. Both use five restarts per trial and 10 trials per preset. Candidates with no feasible draws have undefined conditional CVaR in exact search and receive zero fitness if sampled by ACO. The variant tests both changes together, so their individual contributions cannot be isolated. Exact results are used to score hits and gaps, never to seed or guide a colony. [P28b settings](../config/robust_stability.json)

### Exact results

All three farms finished full canonical search. The original zero-score rule produced an all-candidate zero tie in Kansas and Makueni at every draw count and preset. The conditional objective breaks those global ties. Close alternatives remain, including all twelve Kansas feasible-tail comparisons. The expected-score, minimax and original-CVaR winners, objective values and tie counts match the archived P28 comparisons at overlapping draw counts.

| Objective | Same cycle, Kansas | Telangana | Makueni | Same cycle overall | Near-ties at 128 / 256 / 512 |
| --- | --- | --- | --- | --- | --- |
| Expected score | 0/4 | 4/4 | 4/4 | 8/12 | 4/12 / 4/12 / 4/12 |
| Conditional CVaR | 2/4 | 1/4 | 3/4 | 6/12 | 8/12 / 8/12 / 8/12 |
| Minimax regret | 1/4 | 0/4 | 1/4 | 2/12 | 4/12 / 4/12 / 6/12 |

Makueni’s 512-draw income pick for conditional CVaR is feasible in 108 of 512 draws (21.1%). It is within the existing near-tie tolerance of its runner-up and takes 25.9% of the split bootstrap wins among finalists. The feasibility column matters when reading a feasible-only tail score. For all 12 Kansas preset–objective combinations at 512 draws, the runner-up is within the near-tie tolerance. These ties can make the displayed cycle look less stable across counts than its score.

### Top three by farm, preset, draw count and objective

Scores and gaps are weighted points. Each cycle is shown with its gap to the exact maximum in brackets. A slash advances the year and an arrow advances the season. For minimax regret, the objective-value column shows maximum regret of the displayed pick and smaller is better. Feasibility and paired-bootstrap win share refer to the displayed pick. All numbers are illustrative and need local validation.

<details>
<summary>Kansas · all 36 comparisons</summary>

| Preset | Draws | Objective | Pick value | Feasible | Finalist bootstrap wins | Near-tie | Pick [gap] | Runner-up [gap] | Third [gap] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| water saver | 128 | Expected score | 0.469996 | 71.9% | 36.5% | Yes | `fallow / common_bean / sunflower` [0.00000000] | `fallow / sunflower / common_bean` [0.00000000] | `fallow / maize / common_bean` [0.01941106] |
| water saver | 128 | Conditional CVaR | 0.625063 | 64.1% | 31.5% | Yes | `fallow / common_bean / soybean` [0.00000000] | `fallow / soybean / common_bean` [0.00000000] | `fallow / soybean / sunflower` [0.00318447] |
| water saver | 128 | Minimax regret | 0.728546 | 55.5% | 32.2% | Yes | `fallow / sorghum / soybean` [0.00000000] | `fallow / soybean / sorghum` [0.00000000] | `fallow / sorghum / cereal_rye_cover` [0.00736310] |
| water saver | 256 | Expected score | 0.438518 | 68.0% | 25.1% | Yes | `fallow / maize / common_bean` [0.00000000] | `fallow / common_bean / maize` [0.00000000] | `fallow / common_bean / sunflower` [0.00254040] |
| water saver | 256 | Conditional CVaR | 0.623982 | 60.5% | 36.5% | Yes | `fallow / common_bean / soybean` [0.00000000] | `fallow / soybean / common_bean` [0.00000000] | `fallow / soybean / sunflower` [0.00324281] |
| water saver | 256 | Minimax regret | 0.728546 | 56.2% | 47.8% | Yes | `fallow / sorghum / soybean` [0.00000000] | `fallow / soybean / sorghum` [0.00000000] | `fallow / sorghum / common_bean` [0.02627425] |
| water saver | 512 | Expected score | 0.431429 | 66.8% | 27.3% | Yes | `fallow / maize / common_bean` [0.00000000] | `fallow / common_bean / maize` [0.00000000] | `fallow / common_bean / sunflower` [0.00156619] |
| water saver | 512 | Conditional CVaR | 0.624281 | 48.6% | 22.2% | Yes | `fallow / winter_wheat / soybean` [0.00000000] | `fallow / soybean / winter_wheat` [0.00000000] | `fallow / common_bean / soybean` [0.00037488] |
| water saver | 512 | Minimax regret | 0.745991 | 59.4% | 45.4% | Yes | `fallow / sorghum / soybean` [0.00000000] | `fallow / soybean / sorghum` [0.00000000] | `fallow / sorghum / common_bean` [0.00882915] |
| soil builder | 128 | Expected score | 0.489651 | 71.9% | 37.6% | Yes | `fallow / common_bean / sunflower` [0.00000000] | `fallow / sunflower / common_bean` [0.00000000] | `fallow / common_bean / soybean` [0.02879388] |
| soil builder | 128 | Conditional CVaR | 0.703887 | 49.2% | 50.0% | Yes | `fallow / soybean / cereal_rye_cover` [0.00000000] | `fallow / cereal_rye_cover / soybean` [0.00000000] | `fallow / common_bean / soybean` [0.01326935] |
| soil builder | 128 | Minimax regret | 0.745093 | 64.1% | 37.2% | Yes | `fallow / common_bean / soybean` [0.00000000] | `fallow / soybean / common_bean` [0.00000000] | `fallow / sorghum / common_bean` [0.00035591] |
| soil builder | 256 | Expected score | 0.454593 | 66.8% | 31.7% | Yes | `fallow / common_bean / sunflower` [0.00000000] | `fallow / sunflower / common_bean` [0.00000000] | `fallow / maize / common_bean` [0.00980173] |
| soil builder | 256 | Conditional CVaR | 0.701544 | 52.7% | 50.0% | Yes | `fallow / soybean / cereal_rye_cover` [0.00000000] | `fallow / cereal_rye_cover / soybean` [0.00000000] | `fallow / common_bean / soybean` [0.01111505] |
| soil builder | 256 | Minimax regret | 0.749556 | 56.2% | 43.9% | Yes | `fallow / sorghum / soybean` [0.00000000] | `fallow / soybean / sorghum` [0.00000000] | `fallow / sorghum / pearl_millet` [0.00845103] |
| soil builder | 512 | Expected score | 0.453498 | 63.3% | 30.6% | Yes | `fallow / common_bean / soybean` [0.00000000] | `fallow / soybean / common_bean` [0.00000000] | `fallow / common_bean / sunflower` [0.00635445] |
| soil builder | 512 | Conditional CVaR | 0.700033 | 53.7% | 50.0% | Yes | `fallow / soybean / cereal_rye_cover` [0.00000000] | `fallow / cereal_rye_cover / soybean` [0.00000000] | `fallow / common_bean / soybean` [0.01031696] |
| soil builder | 512 | Minimax regret | 0.760642 | 59.4% | 33.2% | Yes | `fallow / sorghum / soybean` [0.00000000] | `fallow / soybean / sorghum` [0.00000000] | `fallow / sorghum / common_bean` [0.00069462] |
| income | 128 | Expected score | 0.406762 | 71.9% | 28.4% | Yes | `fallow / common_bean / sunflower` [0.00000000] | `fallow / sunflower / common_bean` [0.00000000] | `fallow / maize / common_bean` [0.00452846] |
| income | 128 | Conditional CVaR | 0.593992 | 50.8% | 35.7% | Yes | `maize / soybean / sunflower` [0.00000000] | `maize / sunflower / soybean` [0.00000000] | `soybean / pearl_millet / sunflower` [0.00313675] |
| income | 128 | Minimax regret | 0.722727 | 71.9% | 45.9% | Yes | `fallow / common_bean / sunflower` [0.00000000] | `fallow / sunflower / common_bean` [0.00000000] | `fallow / common_bean / soybean` [0.01291685] |
| income | 256 | Expected score | 0.392075 | 68.0% | 36.7% | Yes | `fallow / maize / common_bean` [0.00000000] | `fallow / common_bean / maize` [0.00000000] | `fallow / common_bean / sunflower` [0.01365340] |
| income | 256 | Conditional CVaR | 0.596988 | 47.3% | 49.8% | Yes | `maize / soybean / sunflower` [0.00000000] | `maize / sunflower / soybean` [0.00000000] | `maize / common_bean / soybean` [0.01691850] |
| income | 256 | Minimax regret | 0.727988 | 66.8% | 44.6% | Yes | `fallow / common_bean / sunflower` [0.00000000] | `fallow / sunflower / common_bean` [0.00000000] | `fallow / common_bean / soybean` [0.00765572] |
| income | 512 | Expected score | 0.385634 | 66.8% | 42.6% | Yes | `fallow / maize / common_bean` [0.00000000] | `fallow / common_bean / maize` [0.00000000] | `fallow / common_bean / sunflower` [0.01232206] |
| income | 512 | Conditional CVaR | 0.598888 | 50.8% | 50.0% | Yes | `maize / soybean / sunflower` [0.00000000] | `maize / sunflower / soybean` [0.00000000] | `winter_wheat / soybean / sunflower` [0.01442211] |
| income | 512 | Minimax regret | 0.737214 | 62.3% | 33.6% | Yes | `fallow / soybean / sunflower` [0.00000000] | `fallow / sunflower / soybean` [0.00000000] | `fallow / common_bean / soybean` [0.00356548] |
| balanced | 128 | Expected score | 0.465201 | 71.9% | 37.1% | Yes | `fallow / common_bean / sunflower` [0.00000000] | `fallow / sunflower / common_bean` [0.00000000] | `fallow / maize / common_bean` [0.02051062] |
| balanced | 128 | Conditional CVaR | 0.624950 | 51.6% | 30.9% | Yes | `fallow / soybean / pearl_millet` [0.00000000] | `fallow / pearl_millet / soybean` [0.00000000] | `fallow / soybean / sunflower` [0.00215383] |
| balanced | 128 | Minimax regret | 0.730860 | 62.5% | 34.8% | Yes | `fallow / soybean / sunflower` [0.00000000] | `fallow / sunflower / soybean` [0.00000000] | `fallow / sorghum / soybean` [0.00571459] |
| balanced | 256 | Expected score | 0.433182 | 68.0% | 23.7% | Yes | `fallow / maize / common_bean` [0.00000000] | `fallow / common_bean / maize` [0.00000000] | `fallow / common_bean / sunflower` [0.00100499] |
| balanced | 256 | Conditional CVaR | 0.622351 | 60.5% | 32.3% | Yes | `fallow / common_bean / soybean` [0.00000000] | `fallow / soybean / common_bean` [0.00000000] | `fallow / soybean / sunflower` [0.00110355] |
| balanced | 256 | Minimax regret | 0.736575 | 56.2% | 35.4% | Yes | `fallow / sorghum / soybean` [0.00000000] | `fallow / soybean / sorghum` [0.00000000] | `fallow / sorghum / common_bean` [0.01368477] |
| balanced | 512 | Expected score | 0.425981 | 65.4% | 25.0% | Yes | `fallow / common_bean / sunflower` [0.00000000] | `fallow / sunflower / common_bean` [0.00000000] | `fallow / maize / common_bean` [0.00018038] |
| balanced | 512 | Conditional CVaR | 0.622997 | 62.3% | 34.2% | Yes | `fallow / soybean / sunflower` [0.00000000] | `fallow / sunflower / soybean` [0.00000000] | `fallow / common_bean / soybean` [0.00076187] |
| balanced | 512 | Minimax regret | 0.750260 | 63.3% | 16.0% | Yes | `fallow / common_bean / soybean` [0.00000000] | `fallow / common_bean / sunflower` [0.00000000] | `fallow / soybean / common_bean` [0.00000000] |

</details>

<details>
<summary>Telangana · all 36 comparisons</summary>

| Preset | Draws | Objective | Pick value | Feasible | Finalist bootstrap wins | Near-tie | Pick [gap] | Runner-up [gap] | Third [gap] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| water saver | 128 | Expected score | 0.701201 | 91.4% | 69.2% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.01831405] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.03030998] |
| water saver | 128 | Conditional CVaR | 0.750201 | 50.0% | 54.0% | — | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00017898] | `soybean → fallow / pigeonpea → fallow / pigeonpea → fallow` [0.00221843] |
| water saver | 128 | Minimax regret | 0.809591 | 91.4% | 90.8% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `fallow → common_bean / fallow → common_bean / fallow → common_bean` [0.00914627] | `fallow → common_bean / fallow → common_bean / green_gram → common_bean` [0.00914627] |
| water saver | 256 | Expected score | 0.697705 | 90.6% | 62.4% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.00878692] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.02558913] |
| water saver | 256 | Conditional CVaR | 0.751171 | 73.8% | 78.1% | — | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00087969] | `soybean → fallow / pigeonpea → fallow / pigeonpea → fallow` [0.00317449] |
| water saver | 256 | Minimax regret | 0.825744 | 87.5% | 67.3% | — | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.00000000] | `fallow → green_gram / fallow → green_gram / soybean → green_gram` [0.00514822] | `fallow → green_gram / soybean → fallow / soybean → green_gram` [0.00514822] |
| water saver | 512 | Expected score | 0.701835 | 91.0% | 84.4% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.01551005] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.02022038] |
| water saver | 512 | Conditional CVaR | 0.751948 | 69.7% | 52.0% | — | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00000141] | `soybean → fallow / pigeonpea → fallow / pigeonpea → fallow` [0.00296139] |
| water saver | 512 | Minimax regret | 0.825744 | 89.8% | 88.2% | — | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.00000000] | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00674675] | `fallow → green_gram / fallow → green_gram / soybean → green_gram` [0.00794726] |
| soil builder | 128 | Expected score | 0.674633 | 91.4% | 65.6% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.01326118] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.03056495] |
| soil builder | 128 | Conditional CVaR | 0.729857 | 50.0% | 51.4% | — | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00003478] | `soybean → fallow / soybean → fallow / cowpea → fallow` [0.00208251] |
| soil builder | 128 | Minimax regret | 0.772660 | 91.4% | 73.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `fallow → sunflower / fallow → sunflower / fallow → sunflower` [0.00109923] | `fallow → sunflower / fallow → sunflower / green_gram → sunflower` [0.00109923] |
| soil builder | 256 | Expected score | 0.672325 | 90.6% | 55.2% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.00335711] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.02665696] |
| soil builder | 256 | Conditional CVaR | 0.730717 | 73.8% | 58.2% | — | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00029143] | `soybean → fallow / soybean → fallow / cowpea → fallow` [0.00182960] |
| soil builder | 256 | Minimax regret | 0.783397 | 87.5% | 82.3% | — | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.00000000] | `fallow → green_gram / fallow → green_gram / soybean → green_gram` [0.00512934] | `fallow → green_gram / soybean → fallow / soybean → green_gram` [0.00512934] |
| soil builder | 512 | Expected score | 0.676544 | 91.0% | 77.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.01008973] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.02136162] |
| soil builder | 512 | Conditional CVaR | 0.732529 | 46.3% | 63.0% | — | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00051738] | `soybean → fallow / pigeonpea → fallow / pigeonpea → fallow` [0.00306884] |
| soil builder | 512 | Minimax regret | 0.791755 | 89.8% | 29.2% | Yes | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.00000000] | `fallow → green_gram / fallow → green_gram / soybean → green_gram` [0.00000000] | `fallow → green_gram / soybean → fallow / soybean → green_gram` [0.00000000] |
| income | 128 | Expected score | 0.547087 | 84.4% | 60.2% | — | `green_gram → paddy / green_gram → paddy / green_gram → paddy` [0.00000000] | `common_bean → paddy / common_bean → paddy / common_bean → paddy` [0.01894349] | `green_gram → maize / green_gram → maize / green_gram → maize` [0.01908381] |
| income | 128 | Conditional CVaR | 0.628707 | 40.6% | 15.2% | Yes | `soybean → maize / soybean → maize / pigeonpea → sunflower` [0.00000000] | `soybean → maize / soybean → sunflower / pigeonpea → maize` [0.00000000] | `soybean → maize / pigeonpea → maize / soybean → sunflower` [0.00000000] |
| income | 128 | Minimax regret | 0.731608 | 91.4% | 96.6% | — | `fallow → sunflower / fallow → sunflower / fallow → sunflower` [0.00000000] | `sunflower → fallow / sunflower → fallow / sunflower → fallow` [0.00760437] | `fallow → sunflower / fallow → sunflower / soybean → sunflower` [0.02084171] |
| income | 256 | Expected score | 0.538064 | 82.4% | 53.8% | — | `green_gram → paddy / green_gram → paddy / green_gram → paddy` [0.00000000] | `green_gram → maize / green_gram → maize / green_gram → maize` [0.00717504] | `cowpea → paddy / cowpea → paddy / cowpea → paddy` [0.02043670] |
| income | 256 | Conditional CVaR | 0.628897 | 39.8% | 30.7% | Yes | `soybean → paddy / soybean → maize / pigeonpea → maize` [0.00000000] | `soybean → paddy / pigeonpea → maize / soybean → maize` [0.00000000] | `soybean → maize / soybean → maize / pigeonpea → paddy` [0.00000000] |
| income | 256 | Minimax regret | 0.760148 | 88.3% | 46.1% | — | `fallow → cowpea / fallow → cowpea / fallow → cowpea` [0.00000000] | `fallow → cowpea / fallow → cowpea / soybean → cowpea` [0.00123808] | `fallow → cowpea / soybean → fallow / soybean → cowpea` [0.00123808] |
| income | 512 | Expected score | 0.548049 | 83.8% | 60.6% | — | `green_gram → paddy / green_gram → paddy / green_gram → paddy` [0.00000000] | `green_gram → maize / green_gram → maize / green_gram → maize` [0.00447461] | `common_bean → paddy / common_bean → paddy / common_bean → paddy` [0.01679510] |
| income | 512 | Conditional CVaR | 0.628413 | 39.5% | 29.9% | Yes | `soybean → paddy / soybean → maize / pigeonpea → maize` [0.00000000] | `soybean → paddy / pigeonpea → maize / soybean → maize` [0.00000000] | `soybean → maize / soybean → maize / pigeonpea → paddy` [0.00000000] |
| income | 512 | Minimax regret | 0.764137 | 90.4% | 48.4% | Yes | `fallow → sunflower / fallow → sunflower / fallow → sunflower` [0.00000000] | `fallow → sunflower / fallow → sunflower / sorghum → sunflower` [0.00000000] | `fallow → sunflower / sorghum → fallow / sorghum → sunflower` [0.00000000] |
| balanced | 128 | Expected score | 0.646003 | 91.4% | 75.4% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.02259469] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.03172364] |
| balanced | 128 | Conditional CVaR | 0.689812 | 50.0% | 55.0% | — | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00015575] | `soybean → fallow / soybean → fallow / green_gram → fallow` [0.00297299] |
| balanced | 128 | Minimax regret | 0.750254 | 91.4% | 90.4% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `fallow → sunflower / fallow → sunflower / fallow → sunflower` [0.01036608] | `fallow → sunflower / fallow → sunflower / green_gram → sunflower` [0.01036608] |
| balanced | 256 | Expected score | 0.644094 | 90.6% | 76.6% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.01443915] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.02803698] |
| balanced | 256 | Conditional CVaR | 0.690039 | 48.4% | 49.6% | — | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00007314] | `soybean → fallow / soybean → fallow / green_gram → fallow` [0.00246322] |
| balanced | 256 | Minimax regret | 0.768069 | 87.5% | 74.9% | — | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.00000000] | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00926221] | `fallow → green_gram / fallow → green_gram / soybean → green_gram` [0.01120122] |
| balanced | 512 | Expected score | 0.648539 | 91.0% | 92.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.02103083] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.02381450] |
| balanced | 512 | Conditional CVaR | 0.692938 | 46.3% | 91.0% | — | `soybean → fallow / soybean → fallow / pigeonpea → fallow` [0.00000000] | `soybean → fallow / soybean → fallow / soybean → fallow` [0.00163723] | `soybean → fallow / pigeonpea → fallow / pigeonpea → fallow` [0.00450887] |
| balanced | 512 | Minimax regret | 0.773346 | 89.8% | 88.0% | — | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.00000000] | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00594395] | `fallow → green_gram / fallow → green_gram / soybean → green_gram` [0.00695689] |

</details>

<details>
<summary>Makueni · all 36 comparisons</summary>

| Preset | Draws | Objective | Pick value | Feasible | Finalist bootstrap wins | Near-tie | Pick [gap] | Runner-up [gap] | Third [gap] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| water saver | 128 | Expected score | 0.617282 | 85.2% | 74.4% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.01507316] | `green_gram → fallow / green_gram → fallow / cowpea → fallow` [0.06483920] |
| water saver | 128 | Conditional CVaR | 0.698961 | 50.8% | 41.7% | Yes | `fallow → common_bean / fallow → green_gram / fallow → cowpea` [0.00000000] | `fallow → common_bean / fallow → cowpea / fallow → green_gram` [0.00000000] | `fallow → common_bean / fallow → cowpea / fallow → cowpea` [0.00413828] |
| water saver | 128 | Minimax regret | 0.766217 | 85.2% | 91.7% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `sorghum → fallow / sorghum → fallow / sorghum → fallow` [0.00247745] | `sorghum → fallow / sorghum → fallow / green_gram → fallow` [0.00247745] |
| water saver | 256 | Expected score | 0.635574 | 87.9% | 97.8% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.03785894] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.06223398] |
| water saver | 256 | Conditional CVaR | 0.698431 | 50.4% | 40.4% | Yes | `fallow → common_bean / fallow → green_gram / fallow → cowpea` [0.00000000] | `fallow → common_bean / fallow → cowpea / fallow → green_gram` [0.00000000] | `fallow → common_bean / fallow → green_gram / fallow → green_gram` [0.00172003] |
| water saver | 256 | Minimax regret | 0.766217 | 87.9% | 98.4% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.01229325] | `fallow → common_bean / fallow → common_bean / fallow → common_bean` [0.01595653] |
| water saver | 512 | Expected score | 0.642473 | 88.9% | 100.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.04868674] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.06289094] |
| water saver | 512 | Conditional CVaR | 0.698702 | 45.1% | 49.7% | Yes | `fallow → common_bean / fallow → green_gram / fallow → cowpea` [0.00000000] | `fallow → common_bean / fallow → cowpea / fallow → green_gram` [0.00000000] | `fallow → common_bean / fallow → cowpea / fallow → cowpea` [0.00483830] |
| water saver | 512 | Minimax regret | 0.767127 | 88.9% | 100.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.01138337] | `fallow → common_bean / fallow → common_bean / fallow → common_bean` [0.01504665] |
| soil builder | 128 | Expected score | 0.631705 | 85.2% | 74.6% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.01507399] | `green_gram → fallow / green_gram → fallow / cowpea → fallow` [0.06618923] |
| soil builder | 128 | Conditional CVaR | 0.716408 | 54.7% | 44.5% | — | `fallow → common_bean / fallow → green_gram / fallow → green_gram` [0.00000000] | `fallow → green_gram / fallow → cowpea / fallow → cowpea` [0.00012889] | `fallow → green_gram / fallow → green_gram / fallow → cowpea` [0.00113860] |
| soil builder | 128 | Minimax regret | 0.775192 | 84.4% | 72.1% | — | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.00000000] | `maize → fallow / maize → fallow / maize → fallow` [0.00292301] | `maize → fallow / maize → fallow / cowpea → fallow` [0.00292301] |
| soil builder | 256 | Expected score | 0.651259 | 87.9% | 98.2% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.04021432] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.06671515] |
| soil builder | 256 | Conditional CVaR | 0.716448 | 57.0% | 55.4% | — | `fallow → common_bean / fallow → green_gram / fallow → green_gram` [0.00000000] | `fallow → green_gram / fallow → green_gram / fallow → cowpea` [0.00052467] | `fallow → green_gram / fallow → cowpea / fallow → cowpea` [0.00066562] |
| soil builder | 256 | Minimax regret | 0.775192 | 83.6% | 77.2% | — | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.00000000] | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00464331] | `green_gram → fallow / green_gram → fallow / cowpea → fallow` [0.00464331] |
| soil builder | 512 | Expected score | 0.658315 | 88.9% | 100.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.05137398] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.06754831] |
| soil builder | 512 | Conditional CVaR | 0.715937 | 51.6% | 63.1% | — | `fallow → common_bean / fallow → green_gram / fallow → green_gram` [0.00000000] | `fallow → green_gram / fallow → green_gram / fallow → cowpea` [0.00076339] | `fallow → common_bean / fallow → green_gram / fallow → cowpea` [0.00084347] |
| soil builder | 512 | Minimax regret | 0.779836 | 88.9% | 95.8% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `green_gram → fallow / green_gram → fallow / sunflower → fallow` [0.00645017] | `green_gram → fallow / sunflower → fallow / sunflower → fallow` [0.00645017] |
| income | 128 | Expected score | 0.482186 | 85.2% | 92.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.03441033] | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.05331718] |
| income | 128 | Conditional CVaR | 0.642212 | 25.0% | 26.7% | Yes | `sorghum → common_bean / maize → green_gram / sunflower → green_gram` [0.00000000] | `sorghum → common_bean / sunflower → green_gram / maize → green_gram` [0.00000000] | `sorghum → green_gram / maize → common_bean / sunflower → green_gram` [0.00000000] |
| income | 128 | Minimax regret | 0.733855 | 75.0% | 94.0% | — | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.00000000] | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.01196527] | `fallow → green_gram / fallow → green_gram / maize → green_gram` [0.01381182] |
| income | 256 | Expected score | 0.496810 | 87.9% | 99.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.04826390] | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.04902637] |
| income | 256 | Conditional CVaR | 0.638265 | 24.2% | 27.3% | Yes | `sorghum → common_bean / pearl_millet → green_gram / sunflower → green_gram` [0.00000000] | `sorghum → common_bean / sunflower → green_gram / pearl_millet → green_gram` [0.00000000] | `sorghum → green_gram / pearl_millet → common_bean / sunflower → green_gram` [0.00000000] |
| income | 256 | Minimax regret | 0.736152 | 78.5% | 99.8% | — | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.00000000] | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.02183599] | `fallow → green_gram / fallow → green_gram / sorghum → green_gram` [0.02639631] |
| income | 512 | Expected score | 0.502057 | 88.9% | 100.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.04950991] | `pearl_millet → fallow / pearl_millet → fallow / pearl_millet → fallow` [0.06122968] |
| income | 512 | Conditional CVaR | 0.635966 | 21.1% | 25.9% | Yes | `sorghum → common_bean / pearl_millet → green_gram / sunflower → green_gram` [0.00000000] | `sorghum → common_bean / sunflower → green_gram / pearl_millet → green_gram` [0.00000000] | `sorghum → green_gram / pearl_millet → common_bean / sunflower → green_gram` [0.00000000] |
| income | 512 | Minimax regret | 0.761037 | 88.9% | 81.2% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `sorghum → fallow / sorghum → fallow / sorghum → fallow` [0.01245859] | `sorghum → fallow / sorghum → fallow / green_gram → fallow` [0.01245859] |
| balanced | 128 | Expected score | 0.600259 | 85.2% | 85.4% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.02830844] | `green_gram → fallow / green_gram → fallow / cowpea → fallow` [0.06705610] |
| balanced | 128 | Conditional CVaR | 0.673521 | 51.6% | 31.4% | Yes | `fallow → common_bean / fallow → green_gram / fallow → pearl_millet` [0.00000000] | `fallow → common_bean / fallow → pearl_millet / fallow → green_gram` [0.00000000] | `common_bean → fallow / pearl_millet → common_bean / pearl_millet → fallow` [0.00159197] |
| balanced | 128 | Minimax regret | 0.752147 | 84.4% | 97.4% | — | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.00000000] | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00797503] | `green_gram → fallow / green_gram → fallow / cowpea → fallow` [0.00797503] |
| balanced | 256 | Expected score | 0.618140 | 87.9% | 99.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.05082828] | `fallow → green_gram / fallow → green_gram / fallow → green_gram` [0.06254221] |
| balanced | 256 | Conditional CVaR | 0.673559 | 53.1% | 37.7% | Yes | `fallow → common_bean / fallow → green_gram / fallow → pearl_millet` [0.00000000] | `fallow → common_bean / fallow → pearl_millet / fallow → green_gram` [0.00000000] | `fallow → common_bean / fallow → green_gram / fallow → green_gram` [0.00143924] |
| balanced | 256 | Minimax regret | 0.756295 | 83.6% | 92.7% | — | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.00000000] | `sorghum → fallow / sorghum → fallow / sorghum → fallow` [0.00399704] | `sorghum → fallow / sorghum → fallow / pearl_millet → fallow` [0.00399704] |
| balanced | 512 | Expected score | 0.624762 | 88.9% | 100.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `cowpea → fallow / cowpea → fallow / cowpea → fallow` [0.06111567] | `common_bean → fallow / common_bean → fallow / common_bean → fallow` [0.06517050] |
| balanced | 512 | Conditional CVaR | 0.671446 | 46.1% | 28.6% | Yes | `fallow → common_bean / fallow → green_gram / fallow → pearl_millet` [0.00000000] | `fallow → common_bean / fallow → pearl_millet / fallow → green_gram` [0.00000000] | `fallow → common_bean / fallow → green_gram / fallow → cowpea` [0.00081925] |
| balanced | 512 | Minimax regret | 0.760830 | 88.9% | 66.0% | — | `green_gram → fallow / green_gram → fallow / green_gram → fallow` [0.00000000] | `sorghum → fallow / sorghum → fallow / sorghum → fallow` [0.00159315] | `sorghum → fallow / sorghum → fallow / green_gram → fallow` [0.00159315] |

</details>

### Original unconditional CVaR, recomputed

Each entry gives the best unconditional CVaR and the number of candidates tied at the existing tolerance. The P28 picks and trial results remain above.

| Farm | Preset | 128 score · ties | 256 score · ties | 512 score · ties |
| --- | --- | --- | --- | --- |
| Kansas | water saver | 0.000000 · 168 | 0.000000 · 168 | 0.000000 · 168 |
| Kansas | soil builder | 0.000000 · 168 | 0.000000 · 168 | 0.000000 · 168 |
| Kansas | income | 0.000000 · 168 | 0.000000 · 168 | 0.000000 · 168 |
| Kansas | balanced | 0.000000 · 168 | 0.000000 · 168 | 0.000000 · 168 |
| Telangana | water saver | 0.136038 · 1 | 0.063003 · 1 | 0.135443 · 1 |
| Telangana | soil builder | 0.123922 · 1 | 0.057413 · 1 | 0.123927 · 1 |
| Telangana | income | 0.105769 · 1 | 0.049058 · 1 | 0.105804 · 1 |
| Telangana | balanced | 0.126434 · 1 | 0.058598 · 1 | 0.126038 · 1 |
| Makueni | water saver | 0.000000 · 16,914 | 0.000000 · 16,914 | 0.000000 · 16,914 |
| Makueni | soil builder | 0.000000 · 16,914 | 0.000000 · 16,914 | 0.000000 · 16,914 |
| Makueni | income | 0.000000 · 16,914 | 0.000000 · 16,914 | 0.000000 · 16,914 |
| Makueni | balanced | 0.000000 · 16,914 | 0.000000 · 16,914 | 0.000000 · 16,914 |

### Telangana ACO diagnosis and held-out result

The original 128-draw objective assigned exactly zero to 211,391 of 211,394 rotations under every preset. The replay visited about 17,800–18,300 distinct candidates per best-of-five trial on average. At least 99.9988% of those visited had zero fitness in each preset average, and no trial visited any exact winner. This is consistent with a nearly flat objective that gives the swarm little useful fitness feedback. The fixed draw set already made the original fitness deterministic.

On the separate seed set, the unchanged search reached the 512-draw conditional CVaR reference in 36/40 single runs and 40/40 best-of-five trials. The exploration variant reached it in 40/40 single runs and 40/40 best-of-five trials. Thus extra exploration helped single runs in this seed set. Best of five already reached the reference with conditional CVaR. Both new arms are evaluated on the same objective and draw count. The original replay uses a different objective, draw count and seed set, so comparisons across the replay and held-out arms cannot isolate the effect of changing draw count.

| Preset | Run | Single hits | Best-of-five hits | Trial visited an exact winner | Mean distinct candidates per trial | Mean / worst best-of-five gap |
| --- | --- | --- | --- | --- | --- | --- |
| water saver | Original replay | 0/10 | 0/10 | 0/10 | 17,782 | 0.117190 / 0.136038 |
| water saver | Conditional control | 7/10 | 10/10 | 10/10 | 3,497 | 0.000000 / 0.000000 |
| water saver | Conditional + exploration | 10/10 | 10/10 | 10/10 | 17,745 | 0.000000 / 0.000000 |
| soil builder | Original replay | 0/10 | 0/10 | 0/10 | 18,319 | 0.123922 / 0.123922 |
| soil builder | Conditional control | 9/10 | 10/10 | 10/10 | 4,363 | 0.000000 / 0.000000 |
| soil builder | Conditional + exploration | 10/10 | 10/10 | 10/10 | 21,413 | 0.000000 / 0.000000 |
| income | Original replay | 0/10 | 0/10 | 0/10 | 18,010 | 0.105769 / 0.105769 |
| income | Conditional control | 10/10 | 10/10 | 10/10 | 4,886 | 0.000000 / 0.000000 |
| income | Conditional + exploration | 10/10 | 10/10 | 10/10 | 21,323 | 0.000000 / 0.000000 |
| balanced | Original replay | 0/10 | 0/10 | 0/10 | 18,224 | 0.118325 / 0.126434 |
| balanced | Conditional control | 10/10 | 10/10 | 10/10 | 4,023 | 0.000000 / 0.000000 |
| balanced | Conditional + exploration | 10/10 | 10/10 | 10/10 | 20,291 | 0.000000 / 0.000000 |

### Runtime and reproduction

Each farm writes one temporary draw-major float32 metric cache and a Boolean feasibility mask. The builder reads 1,024 rotations per exact evaluation chunk and reuses the metrics for all presets. The cache and the process peak resident memory are different measurements. The timings below come from this run and are machine dependent.

| Farm | Exact candidates | Temporary cache (MiB) | Peak RSS (MiB) | Metric cache (s) | Draw oracle (s) | Exact + bootstrap per preset (s) | All work (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kansas | 168 | 2.1 | 341.5 | 0.03 | 0.08 | 0.09–0.11 | 3.81 |
| Telangana | 211,394 | 2,580.5 | 3,759.9 | 31.27 | 20.64 | 3.27–3.31 | 107.19 |
| Makueni | 16,914 | 206.5 | 552.7 | 2.43 | 2.11 | 0.32–0.33 | 10.57 |

Telangana’s total includes about nine seconds of ACO per preset. To rebuild offline, run `python -m src.robust_stability` from the repository. Use `--farm` with one farm ID to rebuild just that report. The JSON also records each finalist’s win share and the objective gap and feasibility for all three candidates.

[Kansas P28b JSON](../data/processed/robust_stability_us_high_plains_b.json) · [Telangana P28b JSON](../data/processed/robust_stability_telangana_a.json) · [Makueni P28b JSON](../data/processed/robust_stability_kenya_makueni_north.json)
