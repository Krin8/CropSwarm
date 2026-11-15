# Makueni bean-credit breakpoints (P51)

Makueni cropland is unverified. Results are illustrative and conditional on the assumed baseline.

Regional trials suggest an uncertain range of roughly 1–80 kg N/ha for bean credit. They estimate fertilizer equivalence for following maize in specific trial conditions. Transfer to this farm and to other successor crops is an assumption, validate locally.

Exact search evaluated 16,914 feasible canonical 3-year rotations at each of 10 tested credits. The 22 kg N/ha catalog leader held across the full grid in 0 of 4 presets. 4 of 4 observed flips met the near-tie rule. [Preregistration](p51_plan.md) · [Full-precision results](../data/processed/bean_credit_breakpoints_p51.json)

## Tested leader intervals

Each row covers consecutive tested credit settings. The exact search picks the first canonical row at an exact tie. The adjacent points bracket a change and leave its location between tested credits unresolved.

| Preset | Tested credit (kg N/ha) | Exact leader | Catalog leader at 22 |
| --- | --- | --- | --- |
| Water saver | 0.7–68 | green gram / fallow each year | Yes |
| Water saver | 80 | fallow / common bean each year | No |
| Soil builder | 0.7–30 | green gram / pearl millet each year | Yes |
| Soil builder | 44–80 | pearl millet / common bean each year | No |
| Income | 0.7–68 | maize / green gram each year | Yes |
| Income | 80 | maize / common bean each year | No |
| Balanced | 0.7–68 | green gram / pearl millet each year | Yes |
| Balanced | 80 | pearl millet / common bean each year | No |

## Breakpoints and top-two gaps

Near-tie means a gap of at most 0.01 weighted-score points at either endpoint (existing design choice). The table shows the flag at each endpoint. Scores and gaps use full precision for comparisons. Displayed gaps are rounded.

| Preset | Flip bracket (kg N/ha) | Flip is a near-tie | Before gap | Before close | After gap | After close |
| --- | --- | --- | --- | --- | --- | --- |
| Water saver | 68–80 | Yes | 0.001625 | Yes | 0.000820 | Yes |
| Soil builder | 30–44 | Yes | 0.000785 | Yes | 0.002401 | Yes |
| Income | 68–80 | Yes | 0.000139 | Yes | 0.000632 | Yes |
| Balanced | 68–80 | Yes | 0.002437 | Yes | 0.001000 | Yes |

### All nominal rankings

| Preset | Credit (kg N/ha) | Exact leader | Leader score | Runner-up | Runner-up score | Top-two gap | Near-tie |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Water saver | 0.7 | green gram / fallow each year | 0.746728 | fallow / green gram each year | 0.741017 | 0.005711 | Yes |
| Water saver | 5 | green gram / fallow each year | 0.746728 | fallow / green gram each year | 0.741017 | 0.005711 | Yes |
| Water saver | 10 | green gram / fallow each year | 0.746728 | fallow / green gram each year | 0.741017 | 0.005711 | Yes |
| Water saver | 16.4 | green gram / fallow each year | 0.746728 | fallow / green gram each year | 0.741017 | 0.005711 | Yes |
| Water saver | 22 | green gram / fallow each year | 0.746728 | fallow / green gram each year | 0.741017 | 0.005711 | Yes |
| Water saver | 30 | green gram / fallow each year | 0.746728 | fallow / green gram each year | 0.741017 | 0.005711 | Yes |
| Water saver | 44 | green gram / fallow each year | 0.739453 | common bean / fallow → green gram / fallow → green gram / fallow | 0.735006 | 0.004447 | Yes |
| Water saver | 56 | green gram / fallow each year | 0.731813 | common bean / fallow → green gram / fallow → green gram / fallow | 0.728874 | 0.002939 | Yes |
| Water saver | 68 | green gram / fallow each year | 0.725149 | common bean / fallow → green gram / fallow → green gram / fallow | 0.723524 | 0.001625 | Yes |
| Water saver | 80 | fallow / common bean each year | 0.720105 | green gram / fallow each year | 0.719285 | 0.000820 | Yes |
| Soil builder | 0.7 | green gram / pearl millet each year | 0.755802 | green gram / fallow → green gram / pearl millet → green gram / pearl millet | 0.755017 | 0.000785 | Yes |
| Soil builder | 5 | green gram / pearl millet each year | 0.755802 | green gram / fallow → green gram / pearl millet → green gram / pearl millet | 0.755017 | 0.000785 | Yes |
| Soil builder | 10 | green gram / pearl millet each year | 0.755802 | green gram / fallow → green gram / pearl millet → green gram / pearl millet | 0.755017 | 0.000785 | Yes |
| Soil builder | 16.4 | green gram / pearl millet each year | 0.755802 | green gram / fallow → green gram / pearl millet → green gram / pearl millet | 0.755017 | 0.000785 | Yes |
| Soil builder | 22 | green gram / pearl millet each year | 0.755802 | green gram / fallow → green gram / pearl millet → green gram / pearl millet | 0.755017 | 0.000785 | Yes |
| Soil builder | 30 | green gram / pearl millet each year | 0.755802 | green gram / fallow → green gram / pearl millet → green gram / pearl millet | 0.755017 | 0.000785 | Yes |
| Soil builder | 44 | pearl millet / common bean each year | 0.748682 | pearl millet / common bean → pearl millet / common bean → pearl millet / green gram | 0.746281 | 0.002401 | Yes |
| Soil builder | 56 | pearl millet / common bean each year | 0.745252 | common bean / pearl millet each year | 0.742613 | 0.002638 | Yes |
| Soil builder | 68 | pearl millet / common bean each year | 0.742260 | common bean / pearl millet each year | 0.739621 | 0.002638 | Yes |
| Soil builder | 80 | pearl millet / common bean each year | 0.739627 | common bean / pearl millet each year | 0.736988 | 0.002638 | Yes |
| Income | 0.7 | maize / green gram each year | 0.707399 | maize / green gram → maize / green gram → sunflower / green gram | 0.706376 | 0.001022 | Yes |
| Income | 5 | maize / green gram each year | 0.707399 | maize / green gram → maize / green gram → sunflower / green gram | 0.706376 | 0.001022 | Yes |
| Income | 10 | maize / green gram each year | 0.707399 | maize / green gram → maize / green gram → sunflower / green gram | 0.706376 | 0.001022 | Yes |
| Income | 16.4 | maize / green gram each year | 0.707399 | maize / green gram → maize / green gram → sunflower / green gram | 0.706376 | 0.001022 | Yes |
| Income | 22 | maize / green gram each year | 0.707399 | maize / green gram → maize / green gram → sunflower / green gram | 0.706376 | 0.001022 | Yes |
| Income | 30 | maize / green gram each year | 0.707399 | maize / green gram → maize / green gram → sunflower / green gram | 0.706376 | 0.001022 | Yes |
| Income | 44 | maize / green gram each year | 0.704924 | maize / green gram → maize / green gram → sunflower / green gram | 0.703539 | 0.001385 | Yes |
| Income | 56 | maize / green gram each year | 0.702326 | maize / common bean → maize / green gram → maize / green gram | 0.701310 | 0.001015 | Yes |
| Income | 68 | maize / green gram each year | 0.700059 | maize / common bean → maize / green gram → maize / green gram | 0.699920 | 0.000139 | Yes |
| Income | 80 | maize / common bean each year | 0.699961 | maize / common bean → maize / common bean → maize / green gram | 0.699329 | 0.000632 | Yes |
| Balanced | 0.7 | green gram / pearl millet each year | 0.739487 | green gram / sorghum → green gram / pearl millet → green gram / pearl millet | 0.735921 | 0.003566 | Yes |
| Balanced | 5 | green gram / pearl millet each year | 0.739487 | green gram / sorghum → green gram / pearl millet → green gram / pearl millet | 0.735921 | 0.003566 | Yes |
| Balanced | 10 | green gram / pearl millet each year | 0.739487 | green gram / sorghum → green gram / pearl millet → green gram / pearl millet | 0.735921 | 0.003566 | Yes |
| Balanced | 16.4 | green gram / pearl millet each year | 0.739487 | green gram / sorghum → green gram / pearl millet → green gram / pearl millet | 0.735921 | 0.003566 | Yes |
| Balanced | 22 | green gram / pearl millet each year | 0.739487 | green gram / sorghum → green gram / pearl millet → green gram / pearl millet | 0.735921 | 0.003566 | Yes |
| Balanced | 30 | green gram / pearl millet each year | 0.739487 | green gram / sorghum → green gram / pearl millet → green gram / pearl millet | 0.735921 | 0.003566 | Yes |
| Balanced | 44 | green gram / pearl millet each year | 0.732756 | green gram / sorghum → green gram / pearl millet → green gram / pearl millet | 0.729527 | 0.003229 | Yes |
| Balanced | 56 | green gram / pearl millet each year | 0.725688 | green gram / sorghum → green gram / pearl millet → green gram / pearl millet | 0.722812 | 0.002876 | Yes |
| Balanced | 68 | green gram / pearl millet each year | 0.719523 | common bean / pearl millet → green gram / pearl millet → green gram / pearl millet | 0.717086 | 0.002437 | Yes |
| Balanced | 80 | pearl millet / common bean each year | 0.715097 | green gram / pearl millet each year | 0.714097 | 0.001000 | Yes |

## Baseline and displayed alternatives

The baseline and four displayed cycles are held fixed throughout. Baseline source: assumption, validate locally; long-rains maize and short-rains beans not verified at point. The baseline’s modeled raw nitrogen balance spans -69.65 to -30 kg N/ha per slot across the grid. All other raw metrics and the hard-rule flags are identical at every credit. The nitrogen score can change even for a cycle without common bean. Its raw nitrogen balance stays fixed, while the catalog-wide upper bound increases whenever the bean credit exceeds the highest credit among the other crops.

Absolute values for each unchanged metric are shown once. All deltas for these five metrics are zero. Source tags and evidence labels are in the [full results](../data/processed/bean_credit_breakpoints_p51.json).

| Published strategy | Cycle | Metric | Raw value | Normalized score | Source tag | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline | maize / common bean each year | Water | 230.77 mm unmet per slot | 0.491710 | NASA POWER · https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html · crop catalog and irrigation assumption | low |
| Baseline | maize / common bean each year | Erosion | 37.786 slope × rainfall proxy | 0.893664 | NASA SRTM · NASA POWER · crop cover assumptions | low |
| Baseline | maize / common bean each year | Climate fit | 0.53571 historical share | 0.535714 | NASA POWER · crop catalog | low |
| Baseline | maize / common bean each year | Income | 0.735 relative index | 0.735000 | Crop catalog · illustrative economic assumptions | low |
| Baseline | maize / common bean each year | Risk | 0 relative penalty | 1.000000 | Crop catalog · disease family and cover assumptions | low |
| Water saver | green gram / fallow each year | Water | 91.676 mm unmet per slot | 0.755530 | NASA POWER · https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html · crop catalog and irrigation assumption | low |
| Water saver | green gram / fallow each year | Erosion | 66.338 slope × rainfall proxy | 0.813315 | NASA SRTM · NASA POWER · crop cover assumptions | low |
| Water saver | green gram / fallow each year | Climate fit | 0.91429 historical share | 0.914286 | NASA POWER · crop catalog | low |
| Water saver | green gram / fallow each year | Income | 0.32 relative index | 0.320000 | Crop catalog · illustrative economic assumptions | low |
| Water saver | green gram / fallow each year | Risk | 0.25 relative penalty | 0.750000 | Crop catalog · disease family and cover assumptions | low |
| Soil builder | green gram / pearl millet each year | Water | 215.48 mm unmet per slot | 0.480414 | NASA POWER · https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html · crop catalog and irrigation assumption | low |
| Soil builder | green gram / pearl millet each year | Erosion | 43.481 slope × rainfall proxy | 0.877638 | NASA SRTM · NASA POWER · crop cover assumptions | low |
| Soil builder | green gram / pearl millet each year | Climate fit | 0.85546 historical share | 0.855462 | NASA POWER · crop catalog | low |
| Soil builder | green gram / pearl millet each year | Income | 0.58 relative index | 0.580000 | Crop catalog · illustrative economic assumptions | low |
| Soil builder | green gram / pearl millet each year | Risk | 0 relative penalty | 1.000000 | Crop catalog · disease family and cover assumptions | low |
| Income | maize / green gram each year | Water | 229.32 mm unmet per slot | 0.479984 | NASA POWER · https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html · crop catalog and irrigation assumption | low |
| Income | maize / green gram each year | Erosion | 38.336 slope × rainfall proxy | 0.892118 | NASA SRTM · NASA POWER · crop cover assumptions | low |
| Income | maize / green gram each year | Climate fit | 0.66807 historical share | 0.668067 | NASA POWER · crop catalog | low |
| Income | maize / green gram each year | Income | 0.72 relative index | 0.720000 | Crop catalog · illustrative economic assumptions | low |
| Income | maize / green gram each year | Risk | 0 relative penalty | 1.000000 | Crop catalog · disease family and cover assumptions | low |
| Balanced | green gram / fallow → green gram / pearl millet → green gram / pearl millet | Water | 174.21 mm unmet per slot | 0.572119 | NASA POWER · https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html · crop catalog and irrigation assumption | low |
| Balanced | green gram / fallow → green gram / pearl millet → green gram / pearl millet | Erosion | 51.1 slope × rainfall proxy | 0.856197 | NASA SRTM · NASA POWER · crop cover assumptions | low |
| Balanced | green gram / fallow → green gram / pearl millet → green gram / pearl millet | Climate fit | 0.87507 historical share | 0.875070 | NASA POWER · crop catalog | low |
| Balanced | green gram / fallow → green gram / pearl millet → green gram / pearl millet | Income | 0.49333 relative index | 0.493333 | Crop catalog · illustrative economic assumptions | low |
| Balanced | green gram / fallow → green gram / pearl millet → green gram / pearl millet | Risk | 0.083333 relative penalty | 0.916667 | Crop catalog · disease family and cover assumptions | low |

For nitrogen, deltas are relative to 22 kg N/ha. Each preset column gives the weighted score and rank among the five published cycles, including the baseline. Exact ties in this table use published order. Overall exact ranks use the full canonical pool above. [Crop catalog](../data/crops.csv)

| Credit (kg N/ha) | Published strategy | N balance (kg N/ha per slot) | Change in N balance | N score | Change in N score | Water saver score (rank) | Soil builder score (rank) | Income score (rank) | Balanced score (rank) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.7 | Baseline | -69.65 | -10.65 | 0.326948 | -0.069156 | 0.614364 (5) | 0.647743 (5) | 0.687656 (3) | 0.659766 (5) |
| 0.7 | Water saver | 2.50 | +0.00 | 0.795455 | +0.000000 | 0.746728 (1) | 0.753447 (3) | 0.589407 (5) | 0.728559 (3) |
| 0.7 | Soil builder | -20.00 | +0.00 | 0.649351 | +0.000000 | 0.689631 (3) | 0.755802 (1) | 0.696178 (2) | 0.739487 (1) |
| 0.7 | Income | -57.50 | +0.00 | 0.405844 | +0.000000 | 0.640293 (4) | 0.681588 (4) | 0.707399 (1) | 0.691022 (4) |
| 0.7 | Balanced | -12.50 | +0.00 | 0.698052 | +0.000000 | 0.708663 (2) | 0.755017 (2) | 0.660587 (4) | 0.735844 (2) |
| 5 | Baseline | -67.50 | -8.50 | 0.340909 | -0.055195 | 0.616459 (5) | 0.651931 (5) | 0.689052 (3) | 0.662140 (5) |
| 5 | Water saver | 2.50 | +0.00 | 0.795455 | +0.000000 | 0.746728 (1) | 0.753447 (3) | 0.589407 (5) | 0.728559 (3) |
| 5 | Soil builder | -20.00 | +0.00 | 0.649351 | +0.000000 | 0.689631 (3) | 0.755802 (1) | 0.696178 (2) | 0.739487 (1) |
| 5 | Income | -57.50 | +0.00 | 0.405844 | +0.000000 | 0.640293 (4) | 0.681588 (4) | 0.707399 (1) | 0.691022 (4) |
| 5 | Balanced | -12.50 | +0.00 | 0.698052 | +0.000000 | 0.708663 (2) | 0.755017 (2) | 0.660587 (4) | 0.735844 (2) |
| 10 | Baseline | -65.00 | -6.00 | 0.357143 | -0.038961 | 0.618894 (5) | 0.656801 (5) | 0.690676 (3) | 0.664899 (5) |
| 10 | Water saver | 2.50 | +0.00 | 0.795455 | +0.000000 | 0.746728 (1) | 0.753447 (3) | 0.589407 (5) | 0.728559 (3) |
| 10 | Soil builder | -20.00 | +0.00 | 0.649351 | +0.000000 | 0.689631 (3) | 0.755802 (1) | 0.696178 (2) | 0.739487 (1) |
| 10 | Income | -57.50 | +0.00 | 0.405844 | +0.000000 | 0.640293 (4) | 0.681588 (4) | 0.707399 (1) | 0.691022 (4) |
| 10 | Balanced | -12.50 | +0.00 | 0.698052 | +0.000000 | 0.708663 (2) | 0.755017 (2) | 0.660587 (4) | 0.735844 (2) |
| 16.4 | Baseline | -61.80 | -2.80 | 0.377922 | -0.018182 | 0.622010 (5) | 0.663035 (5) | 0.692754 (3) | 0.668432 (5) |
| 16.4 | Water saver | 2.50 | +0.00 | 0.795455 | +0.000000 | 0.746728 (1) | 0.753447 (3) | 0.589407 (5) | 0.728559 (3) |
| 16.4 | Soil builder | -20.00 | +0.00 | 0.649351 | +0.000000 | 0.689631 (3) | 0.755802 (1) | 0.696178 (2) | 0.739487 (1) |
| 16.4 | Income | -57.50 | +0.00 | 0.405844 | +0.000000 | 0.640293 (4) | 0.681588 (4) | 0.707399 (1) | 0.691022 (4) |
| 16.4 | Balanced | -12.50 | +0.00 | 0.698052 | +0.000000 | 0.708663 (2) | 0.755017 (2) | 0.660587 (4) | 0.735844 (2) |
| 22 | Baseline | -59.00 | +0.00 | 0.396104 | +0.000000 | 0.624738 (5) | 0.668490 (5) | 0.694572 (3) | 0.671523 (5) |
| 22 | Water saver | 2.50 | +0.00 | 0.795455 | +0.000000 | 0.746728 (1) | 0.753447 (3) | 0.589407 (5) | 0.728559 (3) |
| 22 | Soil builder | -20.00 | +0.00 | 0.649351 | +0.000000 | 0.689631 (3) | 0.755802 (1) | 0.696178 (2) | 0.739487 (1) |
| 22 | Income | -57.50 | +0.00 | 0.405844 | +0.000000 | 0.640293 (4) | 0.681588 (4) | 0.707399 (1) | 0.691022 (4) |
| 22 | Balanced | -12.50 | +0.00 | 0.698052 | +0.000000 | 0.708663 (2) | 0.755017 (2) | 0.660587 (4) | 0.735844 (2) |
| 30 | Baseline | -55.00 | +4.00 | 0.422078 | +0.025974 | 0.628634 (5) | 0.676282 (5) | 0.697169 (2) | 0.675938 (5) |
| 30 | Water saver | 2.50 | +0.00 | 0.795455 | +0.000000 | 0.746728 (1) | 0.753447 (3) | 0.589407 (5) | 0.728559 (3) |
| 30 | Soil builder | -20.00 | +0.00 | 0.649351 | +0.000000 | 0.689631 (3) | 0.755802 (1) | 0.696178 (3) | 0.739487 (1) |
| 30 | Income | -57.50 | +0.00 | 0.405844 | +0.000000 | 0.640293 (4) | 0.681588 (4) | 0.707399 (1) | 0.691022 (4) |
| 30 | Balanced | -12.50 | +0.00 | 0.698052 | +0.000000 | 0.708663 (2) | 0.755017 (2) | 0.660587 (4) | 0.735844 (2) |
| 44 | Baseline | -48.00 | +11.00 | 0.439024 | +0.042920 | 0.631176 (5) | 0.681366 (4) | 0.698864 (2) | 0.678819 (5) |
| 44 | Water saver | 2.50 | +0.00 | 0.746951 | -0.048503 | 0.739453 (1) | 0.738896 (3) | 0.584557 (5) | 0.720314 (3) |
| 44 | Soil builder | -20.00 | +0.00 | 0.609756 | -0.039595 | 0.683691 (3) | 0.743924 (1) | 0.692218 (3) | 0.732756 (1) |
| 44 | Income | -57.50 | +0.00 | 0.381098 | -0.024747 | 0.636581 (4) | 0.674164 (5) | 0.704924 (1) | 0.686815 (4) |
| 44 | Balanced | -12.50 | +0.00 | 0.655488 | -0.042564 | 0.702278 (2) | 0.742248 (2) | 0.656331 (4) | 0.728609 (2) |
| 56 | Baseline | -42.00 | +17.00 | 0.443182 | +0.047078 | 0.631799 (5) | 0.682613 (4) | 0.699280 (2) | 0.679526 (5) |
| 56 | Water saver | 2.50 | +0.00 | 0.696023 | -0.099432 | 0.731813 (1) | 0.723617 (3) | 0.579464 (5) | 0.711656 (3) |
| 56 | Soil builder | -20.00 | +0.00 | 0.568182 | -0.081169 | 0.677455 (3) | 0.731452 (1) | 0.688061 (3) | 0.725688 (1) |
| 56 | Income | -57.50 | +0.00 | 0.355114 | -0.050731 | 0.632683 (4) | 0.666369 (5) | 0.702326 (1) | 0.682398 (4) |
| 56 | Balanced | -12.50 | +0.00 | 0.610795 | -0.087256 | 0.695575 (2) | 0.728840 (2) | 0.651862 (4) | 0.721011 (2) |
| 68 | Baseline | -36.00 | +23.00 | 0.446809 | +0.050705 | 0.632343 (4) | 0.683701 (4) | 0.699642 (2) | 0.680143 (4) |
| 68 | Water saver | 2.50 | +0.00 | 0.651596 | -0.143859 | 0.725149 (1) | 0.710289 (3) | 0.575021 (5) | 0.704103 (3) |
| 68 | Soil builder | -20.00 | +0.00 | 0.531915 | -0.117436 | 0.672015 (3) | 0.720572 (1) | 0.684434 (3) | 0.719523 (1) |
| 68 | Income | -57.50 | +0.00 | 0.332447 | -0.073397 | 0.629283 (5) | 0.659569 (5) | 0.700059 (1) | 0.678545 (5) |
| 68 | Balanced | -12.50 | +0.00 | 0.571809 | -0.126243 | 0.689727 (2) | 0.717144 (2) | 0.647963 (4) | 0.714383 (2) |
| 80 | Baseline | -30.00 | +29.00 | 0.450000 | +0.053896 | 0.632822 (4) | 0.684659 (4) | 0.699961 (1) | 0.680685 (4) |
| 80 | Water saver | 2.50 | +0.00 | 0.612500 | -0.182955 | 0.719285 (1) | 0.698560 (3) | 0.571112 (5) | 0.697457 (3) |
| 80 | Soil builder | -20.00 | +0.00 | 0.500000 | -0.149351 | 0.667228 (3) | 0.710997 (1) | 0.681243 (3) | 0.714097 (1) |
| 80 | Income | -57.50 | +0.00 | 0.312500 | -0.093344 | 0.626291 (5) | 0.653585 (5) | 0.698064 (2) | 0.675154 (5) |
| 80 | Balanced | -12.50 | +0.00 | 0.537500 | -0.160552 | 0.684580 (2) | 0.706851 (2) | 0.644532 (4) | 0.708551 (2) |

## Matched P22 draws

Each of the three fixed-credit cases uses the same 512 draws and seed 42 (P22 design choices). Within each draw, only the bean credit changes between cases. P22 can vary the assumed baseline and include it as an exception to the usual feasibility rules. The change rate uses each credit’s own P22 reference winner. Material changes additionally require that the reference becomes ineligible or that its score is more than 0.01 points lower. The paired column compares winners from the same draw at the catalog credit. P22’s published original sampled the credit along with its other assumptions. It is included separately for context.

| Preset | Fixed credit (kg N/ha) | Own nominal P22 reference | Changes vs own reference | Material changes | Paired differences vs fixed 22 | Draw top-score range | Most frequent rotation | Share of draws it wins |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Water saver | 22 | green gram / fallow each year | 74.61% | 64.84% | 0/512 (0.00%) | 0.555–0.787 | green gram / fallow each year | 25.39% |
| Water saver | 44 | green gram / fallow each year | 78.12% | 70.70% | 50/512 (9.77%) | 0.562–0.791 | common bean / fallow each year | 22.27% |
| Water saver | 80 | fallow / common bean each year | 79.30% | 66.21% | 116/512 (22.66%) | 0.563–0.782 | common bean / fallow each year | 29.10% |
| Soil builder | 22 | green gram / pearl millet each year | 94.34% | 77.34% | 0/512 (0.00%) | 0.631–0.802 | green gram / fallow each year | 19.73% |
| Soil builder | 44 | pearl millet / common bean each year | 89.45% | 78.32% | 178/512 (34.77%) | 0.644–0.788 | common bean / fallow each year | 21.29% |
| Soil builder | 80 | pearl millet / common bean each year | 79.69% | 64.65% | 355/512 (69.34%) | 0.647–0.778 | common bean / fallow each year | 24.22% |
| Income | 22 | maize / green gram each year | 88.28% | 83.98% | 0/512 (0.00%) | 0.569–0.803 | maize / common bean each year | 30.86% |
| Income | 44 | maize / green gram each year | 89.45% | 84.38% | 41/512 (8.01%) | 0.564–0.808 | maize / common bean each year | 34.77% |
| Income | 80 | maize / common bean each year | 61.72% | 51.76% | 74/512 (14.45%) | 0.552–0.808 | maize / common bean each year | 38.28% |
| Balanced | 22 | green gram / pearl millet each year | 92.77% | 82.23% | 0/512 (0.00%) | 0.599–0.781 | green gram / fallow each year | 15.43% |
| Balanced | 44 | green gram / pearl millet each year | 93.95% | 84.77% | 80/512 (15.62%) | 0.607–0.774 | green gram / fallow each year | 12.30% |
| Balanced | 80 | pearl millet / common bean each year | 91.41% | 82.42% | 173/512 (33.79%) | 0.608–0.770 | common bean / fallow each year | 12.89% |

The full winner counts are available in the [saved replay](../data/processed/bean_credit_breakpoints_p51.json) and in the Validation panel. These are frequencies under modeled assumptions. Field suitability needs local evidence.

| Preset | Earlier P22 sampled-credit change rate | Earlier P22 material-change rate |
| --- | --- | --- |
| Water saver | 74.41% | 65.04% |
| Soil builder | 94.14% | 76.95% |
| Income | 88.28% | 83.79% |
| Balanced | 92.77% | 82.23% |

## Provenance

| Credit (kg N/ha) | Source |
| --- | --- |
| 0.7 | P49 Machakos field-yield fit, Chui p. 156 |
| 5 | design choice |
| 10 | design choice |
| 16.4 | P49 recalculation of Kimutwa yield fit, Chui Table 37b and Appendix Table 21 |
| 22 | Crop catalog, assumption, validate locally |
| 30 | design choice |
| 44 | P45 Katumani field-yield fit, Nadar and Faught Figure 2 and Tables II–VI |
| 56 | P49 Machakos field-yield fit, Chui p. 156 |
| 68 | design choice |
| 80 | P45 Katumani field-yield fit, Nadar and Faught Figure 2 and Tables II–VI |

[P45 Katumani trial](literature_check_p45.md#nadar) · [P49 Machakos estimates](literature_check_p49.md) · [P22 draw design](sensitivity.md) · [Original strategy evidence](../data/processed/strategies_kenya_makueni_north.json)

Regenerate the new results and report offline with `python -m src.bean_credit_breakpoints` and `python -m src.bean_credit_report`.
