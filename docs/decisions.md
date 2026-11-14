# P2 Phase B decisions

All coordinates, climate values, and candidate farm inputs are illustrative and need local validation. These points are not verified farm parcels. Raw API responses and URLs are in [`data/raw/p2_evidence/`](../data/raw/p2_evidence/).

## Farm choices

| Farm | Choice and reason | Open flags |
|---|---|---|
| US High Plains B | User-selected point `37.940, -100.670`, tier 2. The saved USDA CDL point history reads 2019 fallow/idle cropland, 2020 winter wheat, 2021 sorghum, 2022 fallow/idle cropland, 2023 winter wheat. The config's three-year baseline is the requested illustrative `fallow → winter_wheat → sorghum`, supported as a type of rotation by [Kansas State Research and Extension](https://bookstore.ksre.ksu.edu/pubs/rotations-and-cultural-practices_MF2908.pdf). | CDL is not a verified management record. CDL says fallow in 2019 while MODIS NDVI shows spring peaks; inspect a 3×3 CDL neighborhood in P7. |
| Telangana A | User-selected point `17.845, 79.445`, tier 1. Phase A MCD12Q1 returned cropland class 12 and several years show seasonal NDVI peaks. The requested paddy–paddy baseline is an assumption. | Repeated paddy violates the same-crop hard rule. P4 filled the 2022 download gap. The second season remains tentative after quality screening. |
| Makueni North Candidate | Chosen at `-1.950, 37.640`, tier 1. NASA POWER 2004–2023 daily PRECTOTCORR shows April and November monthly rainfall maxima and a deeper dry-season trough relative to those peaks than the Machakos alternative. | MCD12Q1 returned class 10 (grassland) at both eastern Kenya test points. Exact-point cropland is **unverified**; do not present this as a confirmed farm. Rainfall is gridded climate evidence, not a field gauge. Maize–common bean and two growing seasons are assumptions. |

## Eastern Kenya rainfall comparison

Source: [NASA POWER daily point API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), parameter `PRECTOTCORR`, AG community, `20040101–20231231`; raw requests and responses in [`kenya_power.json`](../data/raw/p2_evidence/kenya_power.json). The 7,305 daily values per point had zero `-999` fill values. Monthly climatology is the mean of each calendar month's rainfall total over 20 years. The choice of a peak-to-dry-trough ratio as a clarity measure is a **design choice, not empirical**. All values below are illustrative and need local validation.

| Candidate | Monthly climatology Jan→Dec (mm/month) | Mar–May mean total (mm) | Oct–Dec mean total (mm) | Local maxima | MCD12Q1, one request |
|---|---|---:|---:|---|---|
| Machakos east `-1.580, 37.350` | 31.60, 27.65, 57.74, **116.07**, 62.05, 22.01, 17.34, 19.73, 19.23, 63.32, **112.67**, 78.93 | 235.86 | 254.92 | April and November | Class 10 grassland; cropland unverified |
| Makueni north `-1.950, 37.640` | 32.20, 31.29, 58.68, **103.89**, 53.70, 16.23, 12.15, 13.98, 14.40, 49.07, **100.19**, 77.45 | 216.27 | 226.71 | April and November | Class 10 grassland; cropland unverified |

Makueni's lower of its two peaks divided by the July minimum is approximately 8.2, versus approximately 6.5 for Machakos. Both show bimodality, so the instructed Kisii fallback condition was not met. Neither MCD12Q1 result verifies cultivation at the point. A later step must replace or validate this Kenya location before presenting it as cropland.

## Input format and irrigation change

The earlier flat `load_farm` format in the existing parent repository required `id`, `name`, a flat `baseline` list, and a `metrics` object. It was not suitable for years containing ordered seasons. The new repository's [`src/validation.py`](../src/validation.py) validates `farm_id`, location, tier, irrigation, nested `baseline_rotation_cycle`, season count, flags, and evidence references. `clean_power_value` (`-999` → missing) and `validate_metric` (numeric value with unit, source, and illustrative label) were copied into that module. The flat `load_farm` API was retired from this repository's active code; the parent repository file and its tests were left untouched, per the user's Git instruction. The new tests replace their three behaviors and cover the new schema.

The earlier proposed irrigation `available`/`max_mm_per_season` fields are replaced by `supply_fraction`, the assumed share of irrigation demand met: US 0.0, Telangana 0.6, Kenya 0.0. Each value has `basis: assumption, validate locally`. Season counts (US 1, Telangana 2, Kenya 2) are also assumptions pending P5. Preset weights are labeled `design choice, not empirical`.

## NDVI reliability and P4 fetch design

Phase A requested each year 2019–2023 as three inclusive MOD13Q1 date windows: `Ayyyy001–Ayyyy145` (10 composites), `Ayyyy161–Ayyyy305` (10), and `Ayyyy321–Ayyyy353` (3). The [ORNL DAAC service documentation](https://modis.ornl.gov/data/modis_webservice.html) caps the subset endpoint at **10 MODIS dates per request**. Some requests timed out, so a peak count was left incomplete rather than interpreting missing windows as zero peaks.

September 30 is day 273, within the second request window and away from both its endpoints (days 161 and 305); it is not a chunk-edge or year-edge peak under the current merged-series method. It can still be affected by 16-day compositing, quality flags, or a nearby missing composite. Peak dates should be checked against adjacent composites and `VI_Quality`/`pixel_reliability` before use.

P4 should query available composite dates first, split into chunks of at most 10 dates, save each successful raw chunk atomically with point/product/window keys, and resume only missing or invalid chunks. Use bounded retries with deterministic backoff, then mark unresolved windows incomplete. Validate expected date coverage and NDVI fill/quality values; merge all chunks and neighboring-year edge composites before peak detection. Preserve raw scaled values, scale factor, quality fields, and source URL for every derived metric.

## P3 soil, terrain, and groundwater

- Kansas soil uses the dominant major SSURGO component in the intersecting map unit. Organic matter and texture fractions use thickness weighting over 0–30 cm. Available water storage integrates representative available water capacity over that depth. The selected component lists no restrictive layer. Field depth and texture need local validation. [SSURGO column descriptions](https://www.nrcs.usda.gov/sites/default/files/2022-08/SSURGO-Metadata-Table-Column-Descriptions-Report.pdf)
- Telangana and Makueni use native SoilGrids median pixels from WCS. The three standard depth intervals retain texture fractions, soil organic carbon, and water pH. Available water in the sampled layer is a proxy from modeled retention at 33 and 1,500 kPa. [ISRIC layer units](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html)
- Terrain uses the mean of four absolute center-to-neighbor gradients from an SRTM 90 m cross. The Kansas cross reports a higher slope than the SSURGO map unit. The absolute SRTM elevation accuracy specification of 16 m at 90% confidence does not quantify the error of these short-baseline slope estimates. [SRTM mission summary](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-srtm-mission-summary)
- The modern USGS field-measurements endpoint returned a record in the bounded Kansas check. Groundwater output uses published regional context for all three sites. Field groundwater trends and irrigation availability remain unverified. [USGS migration documentation](https://api.waterdata.usgs.gov/docs/ogcapi/migration/)

Run `python -m src.context --offline` to rebuild the three context files from `data/raw/p3/manifest.json` and its payloads. Live SoilGrids precompute uses the PROJ command `proj`.

## P5 climate diagnostics and proposed seasons

- Rainfall windows use contiguous months with mean precipitation at least half the site's wettest month. This threshold is an assumption, validate locally. It gives April–August in Kansas, June–September in Telangana, and March–May plus November–December in Makueni. Kansas retains one annual rotation slot with warm and cool alternatives. The October–June wheat window is an assumption, validate locally.
- Telangana has a tentative November–March window around its February quality-screened monthly NDVI median peak. The Jan–Apr search, neighbor contrast of 0.08, and month offsets are assumptions, validate locally. Individual quality-screened years do not consistently show two clear peaks. The proposed counts match the configured counts and no edit to the farm calendars is proposed.
- MODIS peak settings are assumptions, validate locally. Use summary reliability 0 with good or absent detailed QA, one isolated gap interpolation for smoothing, a five-composite quadratic Savitzky–Golay filter, three-composite minimum separation, prominence sensitivity at 0.08, 0.12 and 0.16, and low cover below 0.25. Low NDVI does not establish bare soil. [NASA MOD13Q1 QA](https://ladsweb.modaps.eosdis.nasa.gov/filespec/MODIS/61/MOD13Q1)
- A dry day uses rainfall below 1 mm and a frost-free day uses minimum temperature above 0 °C. These screening thresholds are assumptions, validate locally. Significance uses two-sided Kendall rank testing against time at an illustrative 0.05 threshold and assumes independent annual observations. Rainfall agreement pairs the UTC products. K-means standardizes annual rainfall, mean temperature and mean daily maximum temperature. Three clusters, seed 42, and ten initializations are design choices, assumption, validate locally. [Theil–Sen documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html)

## P7 farm validity

All three locations receive **pass with flags** for illustrative demo use. The processed validity files carry the evidence and visible flags. Run `python -m src.farm_validity` to rebuild them offline. App displays must read the flags, including `cropland unverified` for Makueni North. The farm coordinates and baselines remain as configured.

- **Kansas:** The center matches all eight surrounding CDL pixels in every sampled year. All nine pixels were classified as fallow/idle cropland in 2019, winter wheat in 2020, sorghum in 2021, fallow/idle cropland in 2022, and winter wheat in 2023. The center represents this three-by-three sample. The 2019 MODIS April 7 composite peak survives quality screening. Its approximately 250 m footprint extends beyond the approximately 90 m-wide CDL sample, and greenness can include vegetation such as weeds or volunteers on idle land. The evidence supports the 2019 CDL label at neighborhood scale. It does not identify the spring vegetation or verify field management. [USDA NASS CDL resolution and classification](https://www.nass.usda.gov/research-and-science/cropland/sarsfaqs2), [NASA MOD13Q1](https://lpdaac.usgs.gov/documents/621/MOD13_User_Guide_V61.pdf)
- **Telangana:** The P4 2022 coverage gap is filled. All 23 expected NDVI composites are present in each study year. Only six in 2022, and six to ten per year overall, meet the P5 quality screen. No annual series supports two clear peaks under that screen. A sensitivity check admitting marginal reliability with usable MODLAND bits and no flagged adjacent clouds, mixed clouds, snow or shadow returns one early-year peak per year at 0.12 prominence. P2 MCD12Q1 class 12 supports mapped cropland at the point. The assumed two-season calendar stays provisional. [NASA MOD13 vegetation quality bits](https://lpdaac.usgs.gov/documents/621/MOD13_User_Guide_V61.pdf), [NASA MCD12Q1 land-cover legend](https://modis-land.gsfc.nasa.gov/pdf/MCD12Q1_C6_Userguide04042018.pdf)
- **Kenya:** Makueni North has zero of five years with a qualifying peak after each of the typical April and November rainfall maxima. Its 2023 MCD12Q1 IGBP window contains 25 class-10 (grassland) pixels. The two alternative KALRO trial points in Katumani and Kampi ya Mawe also return 25 class-10 pixels each, so neither meets the required cropland/mosaic gate. Additional candidate NDVI was unnecessary after the land-cover result. Partial candidate NDVI chunks fetched during the land-cover retry remain in cache. The rule retains Makueni North with `cropland unverified`. MCD12Q1's mapped class does not establish land use at the scale of a research plot. [KALRO trial source audit](citation_audit.md) (original direct PDF host timed out), [NASA MCD12Q1 land-cover legend](https://modis-land.gsfc.nasa.gov/pdf/MCD12Q1_C6_Userguide04042018.pdf)

The Kenya decision rule requires at least two rain-aligned peaks in at least three of the five core years and cropland or cropland/natural vegetation mosaic in the center and a majority of the immediate MODIS land-cover neighborhood. Rain alignment screens April–July and November–December vegetation dates within the same calendar year, using the selected observation date within each MODIS composite when available. The within-year windows, spatial majority, and 0.12 prominence are assumptions, validate locally. The spatial sample uses the smallest documented nonzero integer half-width (1 km in each direction). The failed half-kilometer requests are retained in the raw manifest. [ORNL subset API](https://modis.ornl.gov/rst/globalsubset_ui/)

## P13 submission checks

US B's reference uses a rainfed assumption with zero irrigation supplied. The 2019 spring NDVI peak remains unexplained after the CDL neighborhood check. Makueni cropland is unverified and Telangana's second season is tentative. Five independent seeded ACO restarts run per trial, and their results are compared against exact enumeration. [Claim changes](claim_audit.md) · [ACO results](optimizer.md)

## P22 field-check priorities

Use exact canonical search under each trial so eligibility changes can introduce or remove contenders. The app ranks the effects of one-at-a-time tests and shows joint rank associations separately. Keep the existing 0.01 near-tie tolerance as a design choice. Use cited crop water ranges, one-sided irrigation tests from a zero reference and one-slot substitutions for assumed baseline identities. These choices set the scope of the sensitivity experiment. [Ranges and results](sensitivity.md)

## P17 opportunity window screen

Use strict P19 QA and the existing P5 low-NDVI cutoff of 0.25, with sensitivity at 0.20 and 0.30. Require consecutive valid composites and at least three supporting years with a majority or half of assessable pairs to call a window recurrent. Score the modeled addition only for passing years, using a paired uncovered and planted gap and the existing score engine. The fit screen and crop category, frost exception and wetness proxy are illustrative design choices. Site flags cap confidence. [Methods, results and limits](opportunity_windows.md)

## P25 county climate-yield study

Use the published non-irrigated yield when both practices are available for a county-year and tag every all-practice fallback. Use Census geographic centroids and the existing P20 wheat window with a fixed mapped storage proxy. Fit county trends and select model settings entirely inside training folds. Hold out years and counties separately. [Methods and results](ml_model.md)


## P28 risk-aware picks

Use fixed, nominally feasible three-year cycles and the first 128 P22 draws. Assign zero realized score on draw-specific infeasibility and report the count alongside score results. Retain the nominal pick when a risk objective ties. Use exact enumeration for all three reference farms and separately test how often stochastic ACO reaches those objective references. [Methods and results](robust_optimization.md)


## P28b feasible-tail and draw-count checks

Retain P28 as the unconditional reference and compute CVaR separately on each candidate's feasible draws. Report feasibility beside the conditional score. Use the same nested P22 prefixes for expected score, regret and both CVaR definitions. Preserve the original swarm settings for controls and test more exploration on independent evaluation seeds. [P28b report](robust_optimization.md#p28b-feasible-tail-and-draw-count-check)
