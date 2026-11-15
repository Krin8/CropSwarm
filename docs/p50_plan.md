# P50 Makueni Sentinel-2 seasonality preregistration

Evaluate 10 m Sentinel-2 Level-2A (L2A) surface-reflectance NDVI seasonality across `2019–2023` at the original Makueni point (`-1.950, 37.640`), the P48 parallel cropland-map point `makueni_alt` (`-1.950125, 37.639875`), five reference pixels classified cropland by both ESA WorldCover v200 (2021, 10 m) and UMD GLAD cropland extent (2016–2019, ~30 m) within the 5 km study disk, and five reference pixels classified non-cropland (tree cover or grassland) by both products within the same 5 km disk. The original `config/farms.json`, `config/makueni_alt.json`, scorer, crop parameters, saved results and existing Makueni outputs are read-only. All numeric outputs are illustrative and need local validation.

## Catalog, collection and public access

- **Primary STAC catalog and collection**: Element 84 Earth Search v1 (`https://earth-search.aws.element84.com/v1/search`), collection `sentinel-2-l2a` (Copernicus Sentinel-2 L2A Cloud-Optimized GeoTIFFs hosted on AWS Open Data, MGRS tile `37MCT`, UTM Zone 37S `EPSG:32737`).
- **Fallback STAC catalog and collection**: Digital Earth Africa STAC (`https://explorer.digitalearth.africa/stac/search`), collection `s2_l2a` (public Sentinel-2 L2A Cloud-Optimized GeoTIFFs over Africa in `EPSG:32737`), used only if the primary STAC search or public COG byte-range access fails.
- **No credentials**: Only unauthenticated HTTPS requests are permitted. If an endpoint requires credentials or redirects to an authentication login, skip it and record the failure.
- **Deduplication**: Query `2019-01-01T00:00:00Z/2023-12-31T23:59:59Z` intersecting the 5 km disk (`bbox = [37.59, -2.00, 37.69, -1.90]`) in MGRS tile `37MCT`. When multiple STAC items exist for the same sensing calendar date (`YYYY-MM-DD`) and MGRS tile, retain one item per sensing date by selecting the highest `s2:processing_baseline`, breaking ties by latest `s2:generation_time` (or `created`) and lexical item ID.
- **Resumable, cached, bounded backoff**: Cache STAC search pages and byte-range blocks on disk (`data/cache/p50/`), validate `206 Partial Content` and `ETag` consistency, and use bounded exponential backoff (at most 3 attempts per request, `2**attempt` seconds delay, 30 s timeout). Check in a compact extracted pixel-observation witness (`data/raw/p50/`) so `python -m src.makueni_sentinel_p50` and the test suite rebuild offline without network access.

## Study points and deterministic reference pixel selection

All 12 points lie within the 5 km disk centered on `original` (`-1.950, 37.640`) and are derived deterministically from the checked-in P48 rasters (`data/raw/p48/worldcover.npz` and `data/raw/p48/glad.npz`):

1. **Study points (2)**:
   - `original`: `(-1.950000, 37.640000)` — P48 WorldCover class `30` (Grassland, touching `30` and `40` on a grid corner), GLAD class `1` (Cropland).
   - `makueni_alt`: `(-1.950125, 37.639875)` — 19.7 m southwest of `original`, P48 WorldCover class `40` (Cropland), GLAD class `1` (Cropland).
2. **Candidate grid and interior homogeneity screen**:
   - Candidate coordinates are native pixel centers of the cached GLAD grid (`dx = 0.00025°, dy = 0.00025°`) within the 5 km disk (`0 < distance_m <= 5000`), ordered by ascending distance to `original`, breaking exact ties by latitude then longitude (same ordering convention as P48).
   - To avoid mixed map edges and registration boundaries between the 10 m and ~30 m grids, require 3×3 neighborhood homogeneity in both maps around the candidate center: all 9 native GLAD cells in the 3×3 GLAD window and all 9 native 10 m WorldCover cells in the 3×3 WorldCover window (`lat ± dy_wc`, `lon ± dx_wc`) must share the required class.
   - Require a minimum pairwise separation of **250 m** (one nominal MODIS 250 m pixel width) from `original`, `makueni_alt`, and all previously selected reference points.
3. **Cropland-agreed reference group (5 points)**:
   - Require 3×3 GLAD class `1` (Cropland) and 3×3 WorldCover class `40` (Cropland). Greedy selection in ascending distance from `original` yields:
     - `crop_ref_1`: `(-1.951625, 37.641625)` — 255.5 m from `original` (WC `40`, GLAD `1`)
     - `crop_ref_2`: `(-1.950125, 37.637625)` — 264.3 m from `original` (WC `40`, GLAD `1`)
     - `crop_ref_3`: `(-1.947625, 37.639875)` — 264.5 m from `original` (WC `40`, GLAD `1`)
     - `crop_ref_4`: `(-1.953375, 37.639875)` — 375.5 m from `original` (WC `40`, GLAD `1`)
     - `crop_ref_5`: `(-1.947125, 37.637625)` — 414.6 m from `original` (WC `40`, GLAD `1`)
4. **Non-cropland-agreed reference group (5 points: 3 grassland + 2 tree cover)**:
   - Require 3×3 GLAD class `0` (No cropland or no data; WorldCover is 100% classified across the disk) and 3×3 WorldCover uniformly class `30` (Grassland) or uniformly class `10` (Tree cover). To represent both non-cropland classes named in the study design (tree or grass), select the first 3 eligible grassland centers and the first 2 eligible tree-cover centers in ascending distance from `original` with ≥ 250 m pairwise separation across all selected points:
     - `noncrop_ref_1` (grassland): `(-1.948125, 37.644625)` — 554.7 m from `original` (WC `30`, GLAD `0`)
     - `noncrop_ref_2` (grassland): `(-1.954625, 37.637875)` — 565.9 m from `original` (WC `30`, GLAD `0`)
     - `noncrop_ref_3` (grassland): `(-1.945875, 37.643875)` — 629.2 m from `original` (WC `30`, GLAD `0`)
     - `noncrop_ref_4` (tree cover): `(-1.947625, 37.632375)` — 887.6 m from `original` (WC `10`, GLAD `0`)
     - `noncrop_ref_5` (tree cover): `(-1.944125, 37.650625)` — 1,349.4 m from `original` (WC `10`, GLAD `0`)

## Scene-classification cloud masking and 10 m NDVI

- Project each point's WGS84 `(lat, lon)` coordinate to UTM Zone 37S (`EPSG:32737`) and sample the containing native 10 m pixel of the red (`B04` / `red`) and near-infrared (`B08` / `nir`) bands and the containing native 20 m pixel of the Scene Classification Layer (`SCL` / `scl`).
- **Cloud and quality mask**: Accept a scene observation at a point only when `SCL` is in `{4, 5}` (`4 = Vegetation`, `5 = Not-vegetated`). Exclude `0` (No Data), `1` (Saturated or defective), `2` (Dark area / cast shadows), `3` (Cloud shadows), `6` (Water), `7` (Unclassified / low-probability cloud), `8` (Cloud medium probability), `9` (Cloud high probability), `10` (Thin cirrus) and `11` (Snow or ice). Record excluded observation counts by `SCL` code for every point and year.
- **Surface reflectance and NDVI**: Convert raw unsigned 16-bit digital numbers (`DN`, where `0` is nodata) to bottom-of-atmosphere reflectance using the STAC asset `scale` and `offset` metadata (`reflectance = DN * scale + offset`; for ESA Processing Baseline `< 04.00`, `scale = 0.0001, offset = 0.0`; for Processing Baseline `>= 04.00`, `scale = 0.0001, offset = -0.1`, equivalent to `(DN - 1000) / 10000`). Reject observations with `DN == 0`, `red <= 0`, `nir <= 0`, or `nir + red <= 0`. Compute `NDVI = (nir - red) / (nir + red)` and require `NDVI` within the P5 valid domain `[-0.2, 1.0]`.

## P5 peak method, P7 decision rule and minimum observation gate

- **16-day composite alignment for P5 and P7**: Because the P5 smoothing and peak detector (`src/diagnostics.py:vegetation`) and P7 decision rule (`src/farm_validity.py:rainfall_consistent_peaks`) are parameterized on the 23 annual 16-day composite steps (`DOY 1, 17, 33, ..., 353`, where a 5-step Savitzky–Golay filter spans 80 days and a 3-step peak separation spans 48 days), aggregate valid cloud-screened Sentinel-2 observations into the 23 standard 16-day windows in each calendar year `2019–2023`. Within each 16-day window, take the median valid Sentinel-2 NDVI (recording the date of the observation attaining or nearest the median as `composite_date`, `pixel_reliability = 0`, `vi_quality = 0`). Windows with zero valid cloud-free observations receive `pixel_reliability = 3`, `vi_quality = 2062` (masked by P5's `good` filter) and placeholder `ndvi = 0.0` so all 23 annual slots are indexed as received (`status = "complete"`) while only windows with valid cloud-free Sentinel-2 observations count toward `good_composites` and enter smoothing and peak detection.
- **P5 peak and low-greenness rules**: Run the unchanged `src/diagnostics.py:vegetation` and `src/farm_validity.py:rainfall_consistent_peaks` functions on each point's 2019–2023 composite table:
  - Single-step internal gap interpolation for smoothing only; no bridging across multi-window gaps or gaps > 17 days; 5-window quadratic Savitzky–Golay filter (`savgol_filter(segment, 5, 2)`); `find_peaks` with minimum separation `distance = 3` windows and prominence `0.12` (with sensitivity reported at `0.08` and `0.16`), counted only where the uninterpolated window is valid.
  - Low-greenness ("bare") periods use the P5 threshold `NDVI < 0.25` (`BARE_NDVI = 0.25`, with sensitivity counts at `0.20` and `0.30`). Report both low-greenness composite counts/dates and unbinned valid scene counts with `NDVI < 0.25`. Low greenness can reflect dry grass, senescent canopy, residue or bare soil and does not establish tilled bare ground.
  - Report annual NDVI amplitude per point-year both on the valid 16-day composites (`max - min`) and on unbinned valid scenes (`max - min` and `P90 - P10`).
- **P7 decision rule**: A year qualifies under P7 when it has **at least 2 clear rain-aligned peaks** at `0.12` prominence—at least one peak in the long-rains response window (`April–July`, months 4–7) and at least one peak in the short-rains response window (`November–December`, months 11–12)—using `composite_date`. Also report the unconstrained P5 two-peak year count (`peak_count >= 2` at `0.12` prominence regardless of calendar month). A point passes the P7 seasonality rule if **at least 3 of the 5 years (`2019–2023`)** qualify.
- **Minimum valid observations per year and GATE**:
  - Preregistered minimum: **at least 10 valid cloud-screened Sentinel-2 observations per year** and **at least 8 of 23 16-day windows with valid observations per year** in each year `2019–2023` for `original`, `makueni_alt`, and the reference points.
  - **GATE**: If public unauthenticated STAC/COG access fails, or if valid observations per year fall below the preregistered minimum for the points, stop, report every observed count and failure, and leave Makueni flagged as `cropland unverified`. Even if the observation gate and seasonality check pass, `config/farms.json`, `config/makueni_alt.json`, the scorer, parameters, saved results and existing Makueni outputs remain unchanged.

## Reporting rules and group comparison

1. Report per-point and per-year (`2019–2023`) valid scene counts, valid 16-day composite counts (`good_composites` of 23), excluded scene counts by `SCL` class, P5 peak counts at `0.08 / 0.12 / 0.16` prominence, peak dates and months, rain-aligned peak counts (`Apr–Jul` and `Nov–Dec`), qualifying years under P7 (and unconstrained `>= 2` peak years), annual NDVI amplitude (`max - min` and `P90 - P10`), and low-greenness (`NDVI < 0.25`) periods.
2. Compare the 5-pixel **cropland-agreed group** against the 5-pixel **non-cropland group** (and its grassland and tree-cover subgroups) using group summaries (median, min–max range, mean peak count/amplitude, low-greenness share, and number of points meeting the P7 rule).
3. Compare `original` and `makueni_alt` against both reference distributions across peak counts, amplitude, minimum/low-greenness NDVI, and P7 pass rates, stating plainly whether `original` and `makueni_alt` look more like the cropland-agreed group or the non-cropland group (or where they overlap).
4. State explicitly in the report, app Validation panel and evidence ledger that **NDVI seasonality does not identify crop type, management or irrigation**, and report all failed requests, masked scenes or gate shortfalls.

## Supplemental descriptive comparison rule

Before downloading the remaining scene tiles or calculating NDVI, compare original and alternate against the cropland-agreed and non-cropland reference distributions on five point-level summaries: mean annual P5 peak count at 0.12 prominence, median annual valid-composite NDVI amplitude, median annual minimum valid-scene NDVI, overall valid-scene low-greenness share, and count of P7-qualified years. A point is described as closer to one reference group when more of its five values fall within that group's observed min–max interval. A tie is reported as overlap. This is a descriptive range-count rule, not a statistical classifier. The five reference pixels in each group are nearby and are not independent samples. This supplement was fixed after the two-scene unauthenticated access check and before processing scene reflectance or the remaining series.
