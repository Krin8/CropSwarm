# Robustness check under weather shifts (P16)

This is a **sensitivity exercise, not a climate projection**. It uniformly adds `0–3 °C` to cached historical NASA POWER daily temperature in `0.5 °C` steps and scales daily precipitation by `−30% to +10%` in `10%` steps. These grid ranges, the lexicographic tie rule, and the normalized-distance definition of “smallest” are **design choices, not empirical estimates**. All results are illustrative and need local validation. No model parameters or crop values were tuned to produce the maps.

For each of the `35` grid cells per farm, the existing three-year baseline is retained, including any flags. The existing score components and median unmet-water feasibility screen are recomputed from cached daily climate. Every feasible three-year rotation is enumerated and scored exactly for all four presets; **ACO is not used**. Whole-year cyclic shifts are collapsed to their lexicographically smallest year shift; within-year season order remains distinct. The map label is the highest-scoring canonical feasible rotation or the baseline if it scores at least as high. **Exact-score tie rule:** the lexicographically first canonical maximizer wins, and an exactly equal baseline takes precedence. This rule is deterministic and independent of the feasible pool size. The nearest changed map label uses Euclidean distance in grid steps from `0 °C, 0%` rainfall; ties prefer the smaller temperature change, then smaller rainfall magnitude. See [scoring](scoring.md), [farm assumptions](decisions.md), and [stress-test configuration](../config/stress_test.json).

## Winner maps

Each map has four preset panels. The outlined grid cell is unchanged historical weather. Each color and `S` label identifies one rotation **within that panel**; the app panel gives full crop sequences on hover. The [Kansas map](charts/stress_us_high_plains_b.svg), [Telangana map](charts/stress_telangana_a.svg), and [Makueni map](charts/stress_kenya_makueni_north.svg) are standalone offline charts. The full source-tagged [Kansas](../data/processed/stress_test_us_high_plains_b.json), [Telangana](../data/processed/stress_test_telangana_a.json), and [Makueni](../data/processed/stress_test_kenya_makueni_north.json) grids record each cell's winner, exact feasible count, baseline score, optimum score and baseline flags.

| Farm | Preset | Cells with a different map label | Nearest changed map cell | Map-label change from unchanged weather |
|---|---|---:|---|---|
| Kansas | Water saver | 15 of 35 | +2 °C, 0% rain | Fallow → sorghum → soybean changes to fallow → soybean → pearl millet. |
| Kansas | Soil builder | 1 of 35 | +3 °C, +10% rain | Fallow → soybean → cereal rye cover changes to fallow → soybean → pearl millet. |
| Kansas | Income | 20 of 35 | +1.5 °C, 0% rain | Sorghum → soybean → sunflower changes to maize → soybean → sunflower. |
| Kansas | Balanced | 19 of 35 | +1 °C, +10% rain | Fallow → sorghum → soybean changes to fallow → soybean → pearl millet. |
| Telangana | Water saver | 0 of 35 | **No label change** | Pigeonpea then fallow remains the top repeated annual pattern throughout the grid. |
| Telangana | Soil builder | 2 of 35 | +3 °C, 0% rain | Soybean then fallow replaces pigeonpea then fallow as the top annual pattern. |
| Telangana | Income | 12 of 35 | +1 °C, +10% rain | Soybean then maize replaces pigeonpea then maize as the top annual pattern. |
| Telangana | Balanced | 1 of 35 | +3 °C, +10% rain | Soybean then fallow replaces pigeonpea then fallow as the top annual pattern. |
| Makueni | Water saver | 11 of 35 | 0 °C, −30% rain | Fallow then cowpea replaces green gram then fallow as the top annual pattern. |
| Makueni | Soil builder | 30 of 35 | 0 °C, −10% rain | Green gram then fallow replaces green gram then pearl millet as the top annual pattern. |
| Makueni | Income | 8 of 35 | 0 °C, −20% rain | The illustrative maize–common bean baseline becomes top, replacing maize then green gram. |
| Makueni | Balanced | 25 of 35 | 0 °C, +10% rain | Pearl millet then green gram replaces green gram then pearl millet; the within-year season order changes. |

## Margins around the reported flips (P16b)

The **near-tie tolerance is 0.01 normalized weighted-score points**, a **design choice, not empirical evidence**. A flip is flagged when the gap between the best two **distinct** rotations is at most that tolerance in either adjacent cell. Whole-year cyclic starting positions count as the same rotation. The “before” cell is one grid step from the reported changed cell toward unchanged weather. Where both axes can move, the predecessor farther from unchanged weather in normalized grid-step distance is used; a tie favors the temperature-axis step. This defines one reproducible path through a two-dimensional grid, not a continuous threshold. The grid, ranking scores and P16 parameters were not changed.

| Farm | Preset | Before cell: °C, rain; top-two gap | First changed cell: °C, rain; top-two gap | Near-tie? |
|---|---|---|---|---|
| Kansas | Water saver | +1.5, 0%; **0** | +2, 0%; **0** | Yes; exact ties on both sides |
| Kansas | Soil builder | +3, 0%; **0** | +3, +10%; **0** | Yes; exact ties on both sides |
| Kansas | Income | +1, 0%; **0** | +1.5, 0%; **0** | Yes; exact ties on both sides |
| Kansas | Balanced | +1, 0%; **0** | +1, +10%; **0** | Yes; exact ties on both sides |
| Telangana | Water saver | No reported tip | No reported tip | Not applicable |
| Telangana | Soil builder | +2.5, 0%; 0.00142840 | +3, 0%; 0.00000017 | Yes |
| Telangana | Income | +1, 0%; 0.00057279 | +1, +10%; 0.00038725 | Yes |
| Telangana | Balanced | +3, 0%; 0.00082907 | +3, +10%; 0.00080211 | Yes |
| Makueni | Water saver | 0, −20%; 0.00492650 | 0, −30%; 0.00116940 | Yes |
| Makueni | Soil builder | 0, 0%; 0.00078521 | 0, −10%; 0.00139570 | Yes |
| Makueni | Income | 0, −10%; 0.00127225 | 0, −20%; 0.00022166 | Yes |
| Makueni | Balanced | 0, 0%; 0.00356581 | 0, +10%; 0.00068979 | Yes |

**All eleven reported flips are near-ties by this rule.** The four Kansas flips have zero gap between different rotation strategies on both sides, so their displayed winner labels are especially sensitive to exact tie-breaking. These are close model rankings, not evidence of abrupt farm outcomes. Full-precision scores, both top rotations, source tags and the predecessor rule are in the [Kansas](../data/processed/stress_margins_us_high_plains_b.json), [Telangana](../data/processed/stress_margins_telangana_a.json), and [Makueni](../data/processed/stress_margins_kenya_makueni_north.json) margin files.

## What the ties mean (P16c)

The app's **Robustness check under weather shifts (P16)** reports the changed-label counts above. These are label counts, not probabilities of a crop outcome. The nearest reported changes are all between near-equal options. In the previous grid, Kansas soil-builder and income could switch labels within unchanged exact-tied pairs. Canonical year shifts and lexicographic tie-breaking remove those two earlier label artifacts; their new nearest changed cells involve different crop sets, though crop order is still tied within each cell.

The [metric-by-metric tie diagnosis](tie_diagnosis.md) lists both strategies at the adjacent cells for every near-tie. Kansas's zero gaps arise from crop order having no effect on any of the six modeled metric scores for those compared rotations, even after whole-year shifts are collapsed. In Telangana and Makueni, distinct crop mixes have small weighted trade-offs: some metric scores improve while others decline. Nitrogen, relative income and family/cover risk are **climate-insensitive for a fixed rotation** in this sweep; they can still differ between rotations and are not by themselves the cause of the nonzero ties. Recomputed full-precision gaps agree with the refreshed P16b calculation. P23 refreshed the grid with the sourced cowpea water-use input. The climate grid, scoring definitions and near-tie tolerance were preserved. See the [P23 comparison](p23_changes.md).

The four alternatives displayed for each reference farm now form **four meaningfully different metric profiles**, each also different from the baseline, under a maximum absolute difference of `0.05` across the six normalized metric scores. This threshold is a **design choice, not empirical evidence**. No reference alternative is a near-duplicate. The app recomputes distinctness for edited comparisons and shows fewer alternatives if no further canonical candidate clears the threshold; it never pads the list with a near-duplicate. See [tie-diagnosis settings](../config/tie_diagnosis.json).

## Limits and interpretation

The nearest changed label means the nearest **tested grid cell**, not a precise physical threshold. A label can change because scores cross, the existing water-screen constraint changes, or an exact tie selects a different label. The JSON records feasible counts for each cell. The simple uniform shifts leave solar radiation, humidity, soil-water capacity, planting dates, crop water need, prices and management unchanged. They do not represent a climate model, future probability or forecast. No confidence interval is assigned to changed-cell locations. The baseline may carry hard-rule flags; the app continues to display those flags elsewhere. Kansas is modeled as rainfed, Telangana's second season is tentative, and Makueni cropland remains unverified. Local crop, soil and farmer evidence could change every map.
