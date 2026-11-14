# Historical back-test: does modeled stress move with vegetation?

This is a **descriptive check**, not a crop-yield validation. We fixed the existing scoring inputs and compared modeled crop-window water deficit and heat days with observed, QA-filtered MODIS NDVI peak and amplitude for 2019–2023. No parameters were tuned to improve these results. The farm points and crop parameters are illustrative; validate locally.

The [Kansas chart](charts/backtest_us_high_plains_b.svg), [Telangana chart](charts/backtest_telangana_a.svg), and [Makueni chart](charts/backtest_kenya_makueni_north.svg) show deficit share against NDVI peak. The app's **Validation** panel shows the same interactive plots and all four correlation pairs per season. The [Kansas](../data/processed/backtest_us_high_plains_b.json), [Telangana](../data/processed/backtest_telangana_a.json), and [Makueni](../data/processed/backtest_kenya_makueni_north.json) JSON files include every year, crop, season, source tag and statistic.

## What was compared

- Kansas uses saved USDA CDL point classes: 2019 fallow, 2020 winter wheat, 2021 sorghum, 2022 fallow, 2023 winter wheat. Winter wheat is assigned to the **harvest year** and its climate and NDVI window starts in the previous October. Fallow has no crop water or heat stress indicator. CDL is a mapped class, not verified management.
- Telangana uses the assumed paddy–paddy baseline; Makueni uses the assumed long-rains maize and short-rains bean baseline for each year. Telangana's second season is tentative, and Makueni's exact point is not verified cropland.
- NASA POWER `PRECTOTCORR` and `T2M_MAX` feed the scoring engine's daily water bucket and crop heat threshold. Crop demand, threshold, soil storage and irrigation share retain their existing sources and assumptions. A MODIS composite passes only with good pixel reliability, good or absent detailed QA, and valid NDVI. Each NDVI peak and amplitude requires at least three good composites in the crop window. These screening thresholds and 2019–2023 comparison range are design choices, not empirical calibrations.
- Spearman rank correlation is computed **within each season**, so different crops and windows are not pooled. A fixed-seed, 1,000-draw paired bootstrap provides a descriptive 95% interval. All samples are small (`n < 8`), and intervals are not calibrated confidence statements. Tied heat counts can produce deceptively narrow bootstrap intervals. Directional agreement counts assessable years whose stress and NDVI peak lie on opposite sides of their season medians; ties and fallow are excluded.

## Results

Each cell is `Spearman ρ [bootstrap interval]; n`. “Unavailable” means fewer than three nonconstant pairs. A negative sign is the expected direction if more stress coincides with lower greenness. The numeric model indicators are illustrative and require local validation.

| Farm and season | Water deficit vs NDVI peak | Water deficit vs amplitude | Heat days vs NDVI peak | Heat days vs amplitude | Directionally consistent years |
|---|---|---|---|---|---|
| Kansas cool (wheat) | Unavailable; n=2 | Unavailable; n=2 | Unavailable; n=2 | Unavailable; n=2 | 0 of 0 assessable |
| Kansas warm (sorghum) | Unavailable; n=1 | Unavailable; n=1 | Unavailable; n=1 | Unavailable; n=1 | 0 of 0 assessable |
| Telangana monsoon | Unavailable; n=1 | Unavailable; n=1 | Unavailable; n=1 | Unavailable; n=1 | 0 of 0 assessable |
| Telangana post-monsoon | −0.50 [−1.00, 1.00]; n=3 | −0.50 [−1.00, 1.00]; n=3 | −0.50 [−1.00, 1.00]; n=3 | −0.50 [−1.00, 1.00]; n=3 | 1 of 1 assessable |
| Makueni long rains | −0.40 [−1.00, 1.00]; n=5 | −0.20 [−1.00, 1.00]; n=5 | −0.71 [−1.00, −0.71]; n=5 | −0.71 [−1.00, −0.71]; n=5 | 2 of 3 assessable |
| Makueni short rains | −0.20 [−1.00, 1.00]; n=5 | **+0.90 [+0.11, 1.00]; n=5, wrong sign** | 0.00 [−1.00, 1.00]; n=5 | **+0.95 [+0.75, 1.00]; n=5, wrong sign** | 2 of 3 assessable |

The water-deficit/NDVI-peak direction is weakly negative where estimable, but every interval spans both signs. The positive short-rains amplitude results are contrary to the simple stress hypothesis and are reported unchanged. Kansas and Telangana cannot support a meaningful within-season correlation from these years. The 2019 Kansas spring NDVI peak over CDL-mapped fallow remains unexplained.

## What this does not prove

MODIS NDVI measures vegetation greenness in a mixed point pixel; it does not identify the planted crop, yield, irrigation or management. MODIS and CDL have different footprints and sensor resolutions. The simplified bucket omits local irrigation timing, soil depth and management; the assumed crop identities in India and Kenya may be wrong. Small and QA-sparse samples, multiple comparisons, bootstrap ties and weather confounding prevent a causal or predictive claim. No soil nitrogen or soil organic carbon was directly measured by these data. Consult local records and field experts before using any strategy.
