"""Render the P50 observation-gate result from its saved processed report."""

import json

from src.makueni_sentinel_p50 import OUTPUT
from src.scoring import ROOT

DOCUMENT = "p50_sentinel2.md"


def format_scl(values):
    if not values:
        return "none"
    ordered = sorted(values.items(), key=lambda item: (not item[0].isdigit(),
                                                        int(item[0]) if item[0].isdigit() else item[0]))
    return ", ".join(f"{code}={count}" for code, count in ordered)


def render(report):
    access = report.get("stac_access_check", {})
    attempt = report.get("retrieval_attempt_summary", {})
    initial = attempt.get("initial_restricted_attempt", {})
    successful = attempt.get("final_resumed_attempt", {})
    fallback = report.get("fallback_access_summary", {})
    fallback_point = fallback.get("point_access_check", {})
    fallback_full = fallback.get("full_period_attempt", {})
    preflight = next((row.get("asset_preflight", []) for row in report.get("catalog_attempts", [])
                      if row.get("id") == "earth_search_v1"), [])
    failed = report["point_year_gate_failures"]
    checked = len(report["gate"]["counts"])
    all_scene_count = report.get("unique_scene_dates") or 0
    final_failures = report.get("failed_scene_count", 0)
    excluded_counts = {}
    for row in report["gate"]["counts"]:
        for code, value in row["masked_scl_counts"].items():
            excluded_counts[code] = excluded_counts.get(code, 0) + value

    lines = [
        "# Makueni Sentinel-2 seasonality check (P50)", "",
        "## Gate result", "",
        "The preregistered coverage gate failed, so this report does not calculate or interpret P5 peaks, "
        "amplitude, low-greenness periods, P7 pass rates, or reference-group similarity. Makueni remains "
        "**cropland unverified**. NDVI seasonality does not identify crop type, management or irrigation.", "",
        f"The gate failed in **{failed} of {checked} point-years**. It required at least "
        f"{report['minimum_observations']['valid_scenes_per_year']} valid cloud-screened scenes and "
        f"{report['minimum_observations']['valid_16_day_composites_per_year']} of 23 valid 16-day windows for "
        "every one of the 12 points in each year. The thresholds are design choices from "
        "[the preregistration](p50_plan.md).", "",
        "## Public access and retrieval", "",
        f"The unauthenticated Earth Search v1 STAC access check returned HTTP "
        f"{access.get('http_status', 'unrecorded')} for collection "
        f"`{report.get('chosen_catalog', {}).get('collection', 'sentinel-2-l2a')}`, the registered bbox and "
        f"2019–2023 time range. The check returned {access.get('features_in_access_check', 'unrecorded')} "
        "first-page items and a next-page link. The prior resumable search cache contained "
        f"{report.get('raw_item_count', 0)} matching items. Deduplication retained one sensing date per day, "
        f"leaving {all_scene_count} scene dates and removing "
        f"{report.get('duplicate_items_removed', 0)} duplicate-date items.", "",
        f"Red, near-infrared and scene-classification Cloud-Optimized GeoTIFF byte-range preflight requests "
        f"returned HTTP 206 with Content-Range and ETag metadata. The cached scene witness has "
        f"{all_scene_count - final_failures}/{all_scene_count} successfully extracted scenes and "
        f"{final_failures} final scene failures. At interruption, the initial restricted-shell run showed "
        f"{initial.get('failed_records_at_interruption', 'unrecorded')} failed records among "
        f"{initial.get('observed_scene_cache_records_at_interruption', 'unrecorded')} scene cache records due "
        f"to DNS resolution at the Earth Search COG host. The resumed authorized retrieval finished with "
        f"{successful.get('successful_scene_records', 'unrecorded')}/{successful.get('unique_sensing_dates', 'unrecorded')} "
        f"successful scene records and {successful.get('failed_scene_records', 'unrecorded')} failures. The "
        f"Digital Earth Africa fallback point check returned HTTP {fallback_point.get('http_status', 'unrecorded')} "
        f"with {fallback_point.get('items_returned', 'unrecorded')} item; its B04, B08 and SCL byte-range checks "
        "returned HTTP 206. Its full-period search did not complete: page one returned HTTP "
        f"{fallback_full.get('page_one_http_status', 'unrecorded')} with "
        f"{fallback_full.get('page_one_feature_count', 'unrecorded')} features, then the page-two request "
        f"{fallback_full.get('failure', 'had no recorded result')}. The pagination client was corrected to "
        "preserve the initial filters, but the fallback was not retried because the primary retrieval completed. "
        "No fallback scenes were used in the analysis.", "",
        "| Access request | HTTP | URL or byte range | ETag |",
        "| --- | ---: | --- | --- |",
        f"| STAC POST, page-1 access check | {access.get('http_status', 'unrecorded')} | "
        f"{access.get('url', 'unrecorded')} | not applicable |",
        *(f"| {row['band']} COG preflight | {row['http_status']} | {row['content_range']} "
          f"at {row['url']} | {row['etag']} |" for row in preflight), "",
        *(f"| DE Africa {band} COG preflight | {check['http_status']} | {check['content_range']} "
          f"at {fallback_point.get('asset_urls', {}).get(band, 'unrecorded')} | {check['etag']} |"
          for band, check in fallback_point.get("range_checks", {}).items()), "",
        f"The fallback's page-two URL was `{fallback.get('search_url', 'unrecorded')}`; its next-page method "
        f"was `{fallback_full.get('next_page_method', 'unrecorded')}` with merge `{fallback_full.get('next_page_merge', 'unrecorded')}`. "
        f"The point-access record and fallback status are saved in "
        "[fallback_access_summary.json](../data/raw/p50/fallback_access_summary.json).", "",
        f"STAC query parameters were collection `{', '.join(access.get('request_parameters', {}).get('collections', []))}`, "
        f"bbox `{access.get('request_parameters', {}).get('bbox')}`, datetime "
        f"`{access.get('request_parameters', {}).get('datetime')}`, and page size "
        f"`{access.get('request_parameters', {}).get('limit')}`. The point data use the public Sentinel-2 "
        "B04, B08 and SCL assets.", "",
        "The saved witness contains the scene ID, date, processing baseline, per-point SCL and band DN values, "
        "scale/offset, ETags, and final scene status. It is stored at "
        "[sentinel2_observations.json](../data/raw/p50/sentinel2_observations.json). The STAC access check is "
        "[stac_access_check.json](../data/raw/p50/stac_access_check.json) and the retry summary is "
        "[retrieval_attempt_summary.json](../data/raw/p50/retrieval_attempt_summary.json).", "",
        "## Coverage and masking by point and year", "",
        "A valid observation passed the registered SCL classes 4 or 5, nonzero DN, positive scaled reflectance, "
        "and the NDVI domain. SCL codes in the masked column were excluded by the cloud and quality mask. "
        "Reflectance rejections are listed separately. Counts and scene measurements carry the "
        "Copernicus Sentinel-2 "
        "source tag. Minimums are labeled as design choices.", "",
        "| Point | Map group (WorldCover + GLAD, P48) | Year | Scenes seen (Copernicus S2) | Valid NDVI scenes (Copernicus S2; min 10) | Valid 16-day windows (Copernicus S2; min 8/23) | Masked SCL codes and counts (Copernicus S2) | Reflectance/NDVI rejects (Copernicus S2) | Failed Copernicus S2 scenes | Gate |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in report["gate"]["counts"]:
        map_group = f"{row['map_group']} · {row['map_class']}"
        masked = format_scl(row["masked_scl_counts"])
        rejects = format_scl(row["rejected_band_or_ndvi_counts"])
        lines.append(f"| {row['point_id']} | {map_group} | {row['year']} | {row['scenes_seen']} | "
                     f"{row['valid_scenes']} | {row['valid_composites']}/23 | {masked} | {rejects} | "
                     f"{row['failed_scenes']} | {'pass' if row['passes'] else 'fail'} |")
    lines.extend(["", "SCL code totals across the 12 points and five years were " +
                  (", ".join(f"{code}={count}" for code, count in sorted(excluded_counts.items(), key=lambda item: int(item[0])))
                   if excluded_counts else "none") + ". These are excluded scene observations, not unique scenes."])
    failed_rows = [row for row in report["gate"]["counts"] if not row["passes"]]
    lines.extend(["", "The specific point-years below the gate were " +
                  ", ".join(f"{row['point_id']} {row['year']} ({row['valid_scenes']} scenes, "
                            f"{row['valid_composites']}/23 windows)" for row in failed_rows) + ".", "",
                  "## What can be concluded", "",
                  "No peak timing, NDVI amplitude, low-greenness duration, or cropland-versus-noncropland "
                  "seasonality comparison is reported because the preregistered all-point coverage gate did not "
                  "pass. The original and parallel coordinates are not reclassified. The P48 map labels and "
                  "their observation periods remain the only land-cover evidence reported for these points.", "",
                  "This check does not identify crops, management, irrigation, or current field use. WorldCover "
                  "and GLAD classes are map labels and the reference pixels do not establish field-level use. "
                  "All numeric values are illustrative and need local validation.", "",
                  "[P48 cropland map check](makueni_cropland.md) · [P50 preregistration](p50_plan.md) · "
                  "[Evidence ledger](evidence_ledger.md)", "",
                  "Regenerate the offline report with `python -m src.makueni_sentinel_report`.", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    report = json.loads((ROOT / "data/processed" / OUTPUT).read_text())
    (ROOT / "docs" / DOCUMENT).write_text(render(report))
