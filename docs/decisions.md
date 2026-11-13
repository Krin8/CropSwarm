# P2 Phase B decisions

All coordinates, climate values, and candidate farm inputs are illustrative and need local validation. These points are not verified farm parcels. Raw API responses and URLs are in [`data/raw/p2_evidence/`](../data/raw/p2_evidence/).

## Farm choices

| Farm | Choice and reason | Open flags |
|---|---|---|
| US High Plains B | User-selected point `37.940, -100.670`, tier 2. The saved USDA CDL point history reads 2019 fallow/idle cropland, 2020 winter wheat, 2021 sorghum, 2022 fallow/idle cropland, 2023 winter wheat. The config's three-year baseline is the requested illustrative `fallow → winter_wheat → sorghum`, supported as a type of rotation by [Kansas State Research and Extension](https://bookstore.ksre.ksu.edu/pubs/rotations-and-cultural-practices_MF2908.pdf). | CDL is not a verified management record. CDL says fallow in 2019 while MODIS NDVI shows spring peaks; inspect a 3×3 CDL neighborhood in P7. |
| Telangana A | User-selected point `17.845, 79.445`, tier 1. Phase A MCD12Q1 returned cropland class 12 and several years show seasonal NDVI peaks. The requested paddy–paddy baseline is an assumption. | Repeated paddy violates the same-crop hard rule; show the flag. No point-specific crop or irrigation history is verified. The 2022 MODIS record is incomplete. |
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
