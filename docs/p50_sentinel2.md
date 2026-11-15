# Makueni Sentinel-2 seasonality check (P50)

## Gate result

The preregistered coverage gate failed, so this report does not calculate or interpret P5 peaks, amplitude, low-greenness periods, P7 pass rates, or reference-group similarity. Makueni remains **cropland unverified**. NDVI seasonality does not identify crop type, management or irrigation.

The gate failed in **6 of 60 point-years**. It required at least 10 valid cloud-screened scenes and 8 of 23 valid 16-day windows for every one of the 12 points in each year. The thresholds are design choices from [the preregistration](p50_plan.md).

## Public access and retrieval

The unauthenticated Earth Search v1 STAC access check returned HTTP 200 for collection `sentinel-2-l2a`, the registered bbox and 2019–2023 time range. The check returned 100 first-page items and a next-page link. The prior resumable search cache contained 571 matching items. Deduplication retained one sensing date per day, leaving 359 scene dates and removing 212 duplicate-date items.

Red, near-infrared and scene-classification Cloud-Optimized GeoTIFF byte-range preflight requests returned HTTP 206 with Content-Range and ETag metadata. The cached scene witness has 359/359 successfully extracted scenes and 0 final scene failures. At interruption, the initial restricted-shell run showed 64 failed records among 66 scene cache records due to DNS resolution at the Earth Search COG host. The resumed authorized retrieval finished with 359/359 successful scene records and 0 failures. The Digital Earth Africa fallback point check returned HTTP 200 with 1 item; its B04, B08 and SCL byte-range checks returned HTTP 206. Its full-period search did not complete: page one returned HTTP 200 with 100 features, then the page-two request ReadTimeout after 30 seconds on the second STAC page. The pagination client was corrected to preserve the initial filters, but the fallback was not retried because the primary retrieval completed. No fallback scenes were used in the analysis.

| Access request | HTTP | URL or byte range | ETag |
| --- | ---: | --- | --- |
| STAC POST, page-1 access check | 200 | https://earth-search.aws.element84.com/v1/search | not applicable |
| scl COG preflight | 206 | bytes 0-65535/5062003 at https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/37/M/CT/2019/1/S2B_37MCT_20190104_0_L2A/SCL.tif | "8f13710f1621c1ec3d40299dea51a40d" |
| red COG preflight | 206 | bytes 0-65535/221768324 at https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/37/M/CT/2019/1/S2B_37MCT_20190104_0_L2A/B04.tif | "8a49b1e3fc8bfd80d507ecf576d57736-27" |
| nir COG preflight | 206 | bytes 0-65535/215283496 at https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/37/M/CT/2019/1/S2B_37MCT_20190104_0_L2A/B08.tif | "282cb6aaf69df2a8b9acee0cc3cce99d-26" |

| DE Africa B04 COG preflight | 206 | bytes 0-65535/221768324 at https://deafrica-sentinel-2.s3.af-south-1.amazonaws.com/sentinel-s2-l2a-cogs/37/M/CT/2019/1/S2B_37MCT_20190104_0_L2A/B04.tif | "f7efcc61db753af4da188f46b1cf1472" |
| DE Africa B08 COG preflight | 206 | bytes 0-65535/215283496 at https://deafrica-sentinel-2.s3.af-south-1.amazonaws.com/sentinel-s2-l2a-cogs/37/M/CT/2019/1/S2B_37MCT_20190104_0_L2A/B08.tif | "e94c2b0a38af3717c8d0a72b76b5ed78" |
| DE Africa SCL COG preflight | 206 | bytes 0-65535/5062003 at https://deafrica-sentinel-2.s3.af-south-1.amazonaws.com/sentinel-s2-l2a-cogs/37/M/CT/2019/1/S2B_37MCT_20190104_0_L2A/SCL.tif | "8f13710f1621c1ec3d40299dea51a40d" |

The fallback's page-two URL was `https://explorer.digitalearth.africa/stac/search`; its next-page method was `POST` with merge `True`. The point-access record and fallback status are saved in [fallback_access_summary.json](../data/raw/p50/fallback_access_summary.json).

STAC query parameters were collection `sentinel-2-l2a`, bbox `[37.59, -2.0, 37.69, -1.9]`, datetime `2019-01-01T00:00:00Z/2023-12-31T23:59:59Z`, and page size `100`. The point data use the public Sentinel-2 B04, B08 and SCL assets.

The saved witness contains the scene ID, date, processing baseline, per-point SCL and band DN values, scale/offset, ETags, and final scene status. It is stored at [sentinel2_observations.json](../data/raw/p50/sentinel2_observations.json). The STAC access check is [stac_access_check.json](../data/raw/p50/stac_access_check.json) and the retry summary is [retrieval_attempt_summary.json](../data/raw/p50/retrieval_attempt_summary.json).

## Coverage and masking by point and year

A valid observation passed the registered SCL classes 4 or 5, nonzero DN, positive scaled reflectance, and the NDVI domain. SCL codes in the masked column were excluded by the cloud and quality mask. Reflectance rejections are listed separately. Counts and scene measurements carry the Copernicus Sentinel-2 source tag. Minimums are labeled as design choices.

| Point | Map group (WorldCover + GLAD, P48) | Year | Scenes seen (Copernicus S2) | Valid NDVI scenes (Copernicus S2; min 10) | Valid 16-day windows (Copernicus S2; min 8/23) | Masked SCL codes and counts (Copernicus S2) | Reflectance/NDVI rejects (Copernicus S2) | Failed Copernicus S2 scenes | Gate |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| original | study · Grassland | 2019 | 72 | 20 | 12/23 | 3=2, 7=4, 8=5, 9=27, 10=4 | nonpositive_reflectance=10 | 0 | pass |
| original | study · Grassland | 2020 | 72 | 6 | 5/23 | 3=6, 8=11, 9=28, 10=3 | nonpositive_reflectance=18 | 0 | fail |
| original | study · Grassland | 2021 | 73 | 15 | 10/23 | 3=3, 8=8, 9=35, 10=2 | nonpositive_reflectance=10 | 0 | pass |
| original | study · Grassland | 2022 | 70 | 22 | 13/23 | 3=1, 7=1, 8=10, 9=26, 10=4 | nonpositive_reflectance=6 | 0 | pass |
| original | study · Grassland | 2023 | 72 | 17 | 11/23 | 3=3, 7=1, 8=6, 9=28, 10=2 | nonpositive_reflectance=15 | 0 | pass |
| makueni_alt | study · Cropland | 2019 | 72 | 25 | 15/23 | 3=2, 7=3, 8=7, 9=26, 10=4 | nonpositive_reflectance=5 | 0 | pass |
| makueni_alt | study · Cropland | 2020 | 72 | 13 | 9/23 | 3=6, 8=12, 9=27, 10=3 | nonpositive_reflectance=11 | 0 | pass |
| makueni_alt | study · Cropland | 2021 | 73 | 18 | 13/23 | 3=4, 8=7, 9=35, 10=2 | nonpositive_reflectance=7 | 0 | pass |
| makueni_alt | study · Cropland | 2022 | 70 | 23 | 13/23 | 3=1, 7=1, 8=12, 9=25, 10=4 | nonpositive_reflectance=4 | 0 | pass |
| makueni_alt | study · Cropland | 2023 | 72 | 21 | 12/23 | 3=3, 7=1, 8=6, 9=28, 10=2 | nonpositive_reflectance=11 | 0 | pass |
| crop_ref_1 | cropland_ref · Cropland | 2019 | 72 | 25 | 16/23 | 3=4, 8=10, 9=26, 10=5 | nonpositive_reflectance=2 | 0 | pass |
| crop_ref_1 | cropland_ref · Cropland | 2020 | 72 | 16 | 11/23 | 3=6, 7=1, 8=17, 9=21, 10=5 | nonpositive_reflectance=6 | 0 | pass |
| crop_ref_1 | cropland_ref · Cropland | 2021 | 73 | 17 | 10/23 | 3=2, 8=6, 9=36, 10=2 | nonpositive_reflectance=10 | 0 | pass |
| crop_ref_1 | cropland_ref · Cropland | 2022 | 70 | 17 | 10/23 | 3=2, 7=1, 8=11, 9=28, 10=2 | nonpositive_reflectance=9 | 0 | pass |
| crop_ref_1 | cropland_ref · Cropland | 2023 | 72 | 12 | 8/23 | 3=3, 7=1, 8=12, 9=28, 10=1 | nonpositive_reflectance=15 | 0 | pass |
| crop_ref_2 | cropland_ref · Cropland | 2019 | 72 | 21 | 12/23 | 2=1, 3=3, 7=3, 8=10, 9=24, 10=4 | nonpositive_reflectance=6 | 0 | pass |
| crop_ref_2 | cropland_ref · Cropland | 2020 | 72 | 14 | 10/23 | 3=4, 8=10, 9=29, 10=4 | nonpositive_reflectance=11 | 0 | pass |
| crop_ref_2 | cropland_ref · Cropland | 2021 | 73 | 18 | 15/23 | 3=4, 8=6, 9=36, 10=2 | nonpositive_reflectance=7 | 0 | pass |
| crop_ref_2 | cropland_ref · Cropland | 2022 | 70 | 23 | 13/23 | 3=1, 7=1, 8=10, 9=30, 10=1 | nonpositive_reflectance=4 | 0 | pass |
| crop_ref_2 | cropland_ref · Cropland | 2023 | 72 | 24 | 14/23 | 3=3, 7=3, 8=6, 9=24, 10=2 | nonpositive_reflectance=10 | 0 | pass |
| crop_ref_3 | cropland_ref · Cropland | 2019 | 72 | 24 | 14/23 | 7=2, 8=12, 9=24, 10=4 | nonpositive_reflectance=6 | 0 | pass |
| crop_ref_3 | cropland_ref · Cropland | 2020 | 72 | 15 | 10/23 | 3=4, 8=17, 9=27, 10=2 | nonpositive_reflectance=7 | 0 | pass |
| crop_ref_3 | cropland_ref · Cropland | 2021 | 73 | 15 | 11/23 | 3=6, 8=7, 9=36, 10=3 | nonpositive_reflectance=6 | 0 | pass |
| crop_ref_3 | cropland_ref · Cropland | 2022 | 70 | 24 | 13/23 | 3=4, 7=1, 8=12, 9=23, 10=2 | nonpositive_reflectance=4 | 0 | pass |
| crop_ref_3 | cropland_ref · Cropland | 2023 | 72 | 17 | 10/23 | 3=5, 8=10, 9=27, 10=2 | nonpositive_reflectance=11 | 0 | pass |
| crop_ref_4 | cropland_ref · Cropland | 2019 | 72 | 23 | 14/23 | 3=1, 7=1, 8=13, 9=24, 10=5 | nonpositive_reflectance=5 | 0 | pass |
| crop_ref_4 | cropland_ref · Cropland | 2020 | 72 | 11 | 7/23 | 3=7, 8=13, 9=23, 10=5 | nonpositive_reflectance=13 | 0 | fail |
| crop_ref_4 | cropland_ref · Cropland | 2021 | 73 | 14 | 10/23 | 3=6, 7=1, 8=6, 9=35, 10=2 | nonpositive_reflectance=9 | 0 | pass |
| crop_ref_4 | cropland_ref · Cropland | 2022 | 70 | 19 | 11/23 | 3=3, 8=11, 9=29, 10=3 | nonpositive_reflectance=5 | 0 | pass |
| crop_ref_4 | cropland_ref · Cropland | 2023 | 72 | 22 | 12/23 | 3=5, 8=7, 9=26, 10=1 | nonpositive_reflectance=11 | 0 | pass |
| crop_ref_5 | cropland_ref · Cropland | 2019 | 72 | 22 | 15/23 | 2=2, 3=1, 7=1, 8=6, 9=27, 10=5 | nonpositive_reflectance=8 | 0 | pass |
| crop_ref_5 | cropland_ref · Cropland | 2020 | 72 | 12 | 10/23 | 3=5, 7=1, 8=16, 9=26, 10=2 | nonpositive_reflectance=10 | 0 | pass |
| crop_ref_5 | cropland_ref · Cropland | 2021 | 73 | 15 | 10/23 | 3=4, 7=1, 8=5, 9=37, 10=3 | nonpositive_reflectance=8 | 0 | pass |
| crop_ref_5 | cropland_ref · Cropland | 2022 | 70 | 21 | 12/23 | 3=2, 7=2, 8=9, 9=29, 10=2 | nonpositive_reflectance=5 | 0 | pass |
| crop_ref_5 | cropland_ref · Cropland | 2023 | 72 | 19 | 11/23 | 3=4, 7=3, 8=7, 9=25, 10=1 | nonpositive_reflectance=13 | 0 | pass |
| noncrop_ref_1 | noncropland_ref · Grassland | 2019 | 72 | 24 | 15/23 | 3=3, 7=2, 8=6, 9=28, 10=4 | nonpositive_reflectance=5 | 0 | pass |
| noncrop_ref_1 | noncropland_ref · Grassland | 2020 | 72 | 14 | 10/23 | 3=4, 7=1, 8=13, 9=26, 10=3 | nonpositive_reflectance=11 | 0 | pass |
| noncrop_ref_1 | noncropland_ref · Grassland | 2021 | 73 | 20 | 14/23 | 3=2, 8=8, 9=34, 10=3 | nonpositive_reflectance=6 | 0 | pass |
| noncrop_ref_1 | noncropland_ref · Grassland | 2022 | 70 | 24 | 14/23 | 3=3, 7=2, 8=8, 9=25, 10=3 | nonpositive_reflectance=5 | 0 | pass |
| noncrop_ref_1 | noncropland_ref · Grassland | 2023 | 72 | 21 | 11/23 | 3=6, 7=2, 8=5, 9=29, 10=2 | nonpositive_reflectance=7 | 0 | pass |
| noncrop_ref_2 | noncropland_ref · Grassland | 2019 | 72 | 22 | 14/23 | 2=1, 3=4, 8=7, 9=28, 10=7 | nonpositive_reflectance=3 | 0 | pass |
| noncrop_ref_2 | noncropland_ref · Grassland | 2020 | 72 | 13 | 9/23 | 3=7, 8=12, 9=24, 10=5 | nonpositive_reflectance=11 | 0 | pass |
| noncrop_ref_2 | noncropland_ref · Grassland | 2021 | 73 | 18 | 14/23 | 3=5, 8=3, 9=37, 10=3 | nonpositive_reflectance=7 | 0 | pass |
| noncrop_ref_2 | noncropland_ref · Grassland | 2022 | 70 | 18 | 12/23 | 3=2, 8=13, 9=28, 10=5 | nonpositive_reflectance=4 | 0 | pass |
| noncrop_ref_2 | noncropland_ref · Grassland | 2023 | 72 | 24 | 14/23 | 3=2, 8=3, 9=30, 10=1 | nonpositive_reflectance=12 | 0 | pass |
| noncrop_ref_3 | noncropland_ref · Grassland | 2019 | 72 | 27 | 17/23 | 2=1, 3=3, 7=2, 8=10, 9=23, 10=5 | nonpositive_reflectance=1 | 0 | pass |
| noncrop_ref_3 | noncropland_ref · Grassland | 2020 | 72 | 22 | 16/23 | 3=3, 7=1, 8=12, 9=30, 10=2 | nonpositive_reflectance=2 | 0 | pass |
| noncrop_ref_3 | noncropland_ref · Grassland | 2021 | 73 | 20 | 14/23 | 3=4, 8=8, 9=36, 10=3 | nonpositive_reflectance=2 | 0 | pass |
| noncrop_ref_3 | noncropland_ref · Grassland | 2022 | 70 | 28 | 16/23 | 3=1, 7=3, 8=7, 9=27, 10=2 | nonpositive_reflectance=2 | 0 | pass |
| noncrop_ref_3 | noncropland_ref · Grassland | 2023 | 72 | 30 | 17/23 | 3=3, 7=3, 8=4, 9=30, 10=2 | none | 0 | pass |
| noncrop_ref_4 | noncropland_ref · Tree cover | 2019 | 72 | 18 | 11/23 | 3=2, 7=1, 8=12, 9=25, 10=4 | nonpositive_reflectance=10 | 0 | pass |
| noncrop_ref_4 | noncropland_ref · Tree cover | 2020 | 72 | 4 | 4/23 | 3=8, 7=1, 8=17, 9=19, 10=2 | nonpositive_reflectance=21 | 0 | fail |
| noncrop_ref_4 | noncropland_ref · Tree cover | 2021 | 73 | 3 | 2/23 | 3=4, 7=1, 8=5, 9=37, 10=3 | nonpositive_reflectance=20 | 0 | fail |
| noncrop_ref_4 | noncropland_ref · Tree cover | 2022 | 70 | 11 | 7/23 | 3=4, 7=2, 8=6, 9=32, 10=3 | nonpositive_reflectance=12 | 0 | fail |
| noncrop_ref_4 | noncropland_ref · Tree cover | 2023 | 72 | 9 | 7/23 | 3=4, 7=2, 8=7, 9=27, 10=2 | nonpositive_reflectance=21 | 0 | fail |
| noncrop_ref_5 | noncropland_ref · Tree cover | 2019 | 72 | 24 | 14/23 | 3=5, 8=8, 9=23, 10=5 | nonpositive_reflectance=7 | 0 | pass |
| noncrop_ref_5 | noncropland_ref · Tree cover | 2020 | 72 | 12 | 10/23 | 3=5, 7=1, 8=9, 9=30, 10=2 | nonpositive_reflectance=13 | 0 | pass |
| noncrop_ref_5 | noncropland_ref · Tree cover | 2021 | 73 | 19 | 11/23 | 3=4, 8=6, 9=31, 10=3 | nonpositive_reflectance=10 | 0 | pass |
| noncrop_ref_5 | noncropland_ref · Tree cover | 2022 | 70 | 18 | 11/23 | 3=5, 8=8, 9=26, 10=2 | nonpositive_reflectance=11 | 0 | pass |
| noncrop_ref_5 | noncropland_ref · Tree cover | 2023 | 72 | 17 | 12/23 | 3=2, 8=4, 9=35, 10=3 | nonpositive_reflectance=11 | 0 | pass |

SCL code totals across the 12 points and five years were 2=5, 3=215, 7=58, 8=534, 9=1705, 10=179. These are excluded scene observations, not unique scenes.

The specific point-years below the gate were original 2020 (6 scenes, 5/23 windows), crop_ref_4 2020 (11 scenes, 7/23 windows), noncrop_ref_4 2020 (4 scenes, 4/23 windows), noncrop_ref_4 2021 (3 scenes, 2/23 windows), noncrop_ref_4 2022 (11 scenes, 7/23 windows), noncrop_ref_4 2023 (9 scenes, 7/23 windows).

## What can be concluded

No peak timing, NDVI amplitude, low-greenness duration, or cropland-versus-noncropland seasonality comparison is reported because the preregistered all-point coverage gate did not pass. The original and parallel coordinates are not reclassified. The P48 map labels and their observation periods remain the only land-cover evidence reported for these points.

This check does not identify crops, management, irrigation, or current field use. WorldCover and GLAD classes are map labels and the reference pixels do not establish field-level use. All numeric values are illustrative and need local validation.

[P48 cropland map check](makueni_cropland.md) · [P50 preregistration](p50_plan.md) · [Evidence ledger](evidence_ledger.md)

Regenerate the offline report with `python -m src.makueni_sentinel_report`.
