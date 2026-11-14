# Tipping-point climate stress test

This is a **sensitivity exercise, not a climate projection**. It uniformly adds `0–3 °C` to cached historical NASA POWER daily temperature in `0.5 °C` steps and scales daily precipitation by `−30% to +10%` in `10%` steps. These grid ranges, a fixed tie-breaking seed of `42`, and the normalized-distance definition of “smallest” are **design choices, not empirical estimates**. All results are illustrative and need local validation. No model parameters or crop values were tuned to produce a tipping point.

For each of the `35` grid cells per farm, the existing three-year baseline is retained, including any flags. The existing score components and median unmet-water feasibility screen are recomputed from cached daily climate. Every feasible three-year rotation is enumerated and scored exactly for all four presets; **ACO is not used**. The winner is the highest-scoring feasible rotation or the baseline if it scores at least as high. Exactly equal feasible scores use a fixed-seed order. Whole-year cyclic shifts of the same rotation share one strategy label; season order within each year remains distinct. The first tip is the changed winner at minimum Euclidean distance measured in grid steps from `0 °C, 0%` rainfall; ties prefer the smaller temperature change, then smaller rainfall magnitude. See [scoring](scoring.md), [farm assumptions](decisions.md), and [stress-test configuration](../config/stress_test.json).

## Winner maps

Each map has four preset panels. The outlined grid cell is unchanged historical weather. Each color and `S` label identifies one rotation **within that panel**; the app panel gives full crop sequences on hover. The [Kansas map](charts/stress_us_high_plains_b.svg), [Telangana map](charts/stress_telangana_a.svg), and [Makueni map](charts/stress_kenya_makueni_north.svg) are standalone offline charts. The full source-tagged [Kansas](../data/processed/stress_test_us_high_plains_b.json), [Telangana](../data/processed/stress_test_telangana_a.json), and [Makueni](../data/processed/stress_test_kenya_makueni_north.json) grids record each cell's winner, exact feasible count, baseline score, optimum score and baseline flags.

| Farm | Preset | Nearest tip in this grid | Plain-language change from the unchanged-weather winner |
|---|---|---|---|
| Kansas | Water saver | +2 °C, 0% rain | Fallow → soybean → sorghum changes to fallow → soybean → pearl millet. |
| Kansas | Soil builder | 0 °C, +10% rain | Fallow → cereal rye cover → soybean changes to fallow → soybean → cereal rye cover. |
| Kansas | Income | 0 °C, +10% rain | Sorghum → soybean → sunflower changes to sorghum → sunflower → soybean. |
| Kansas | Balanced | +1 °C, +10% rain | Fallow → soybean → sorghum changes to fallow → soybean → pearl millet. |
| Telangana | Water saver | **No tip** | Pigeonpea then fallow remains the top repeated annual pattern throughout the grid. |
| Telangana | Soil builder | +3 °C, 0% rain | Soybean then fallow replaces pigeonpea then fallow as the top annual pattern. |
| Telangana | Income | +1 °C, +10% rain | Soybean then maize replaces pigeonpea then maize as the top annual pattern. |
| Telangana | Balanced | +3 °C, +10% rain | Soybean then fallow replaces pigeonpea then fallow as the top annual pattern. |
| Makueni | Water saver | 0 °C, −30% rain | Fallow then cowpea replaces green gram then fallow as the top annual pattern. |
| Makueni | Soil builder | 0 °C, −10% rain | Green gram then fallow replaces green gram then pearl millet as the top annual pattern. |
| Makueni | Income | 0 °C, −20% rain | The illustrative maize–common bean baseline becomes top, replacing maize then green gram. |
| Makueni | Balanced | 0 °C, +10% rain | Pearl millet then green gram replaces green gram then pearl millet; the within-year season order changes. |

## Limits and interpretation

“First” means nearest **tested grid cell**, not a precise physical threshold. A winner can change because scores cross or the existing water-screen constraint changes; the JSON records feasible counts for each cell. The simple uniform shifts leave solar radiation, humidity, soil-water capacity, planting dates, crop water need, prices and management unchanged. They do not represent a climate model, future probability or forecast. No confidence interval is assigned to tipping locations. The baseline may carry hard-rule flags; the app continues to display those flags elsewhere. Kansas is modeled as rainfed, Telangana's second season is tentative, and Makueni cropland remains unverified. Local crop, soil and farmer evidence could change every map.
