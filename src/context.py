"""Precompute the soil, terrain and regional water context for a farm."""

import argparse
import io
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from src.precompute_cache import RequestCache, write_json

ROOT = Path(__file__).resolve().parents[1]
ASSUMPTION = "assumption, validate locally"
SDA = "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest"
SSURGO = "https://www.nrcs.usda.gov/sites/default/files/2022-08/SSURGO-Metadata-Table-Column-Descriptions-Report.pdf"
SOILGRIDS = "https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html"
WCS = "https://maps.isric.org/mapserv"
SRTM = "https://www.opentopodata.org/datasets/srtm/"
SRTM_ACCURACY = "https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-srtm-mission-summary"
DEPTHS = ((0, 5), (5, 15), (15, 30))
SOIL_LAYERS = {
    "clay": ("clay", "% by mass"), "sand": ("sand", "% by mass"),
    "silt": ("silt", "% by mass"), "soc": ("soil_organic_carbon", "g/kg"),
    "phh2o": ("ph_water", "pH"), "wv0033": ("water_at_33_kpa", "vol %"),
    "wv1500": ("water_at_1500_kpa", "vol %"),
}
GROUNDWATER = {
    "us_high_plains_b": (
        "The High Plains aquifer supplies irrigated agriculture in western Kansas.",
        "https://kgs.ku.edu/sites/kgs/files/files/PICpdfs/PIC18HighPlainsAquifer2023revision.pdf",
    ),
    "telangana_a": (
        "The Central Ground Water Board reports both rises and falls across Telangana during the 2023 monsoon.",
        "https://gwdata.cgwb.gov.in/download/Yearbook/Telangana_GWYB_23-24.pdf",
    ),
    "kenya_makueni_north": (
        "Makueni County's water strategy reports that groundwater availability varies across the county.",
        "https://makueni.go.ke/sandbox/site/files/2025/10/Approved-Makueni-CWSSIP-30th-May-2025.pdf",
    ),
}


def field(value, unit, source, resolution, uncertainty_note, evidence=()):
    return {"value": value, "unit": unit, "source": source, "resolution": resolution,
            "uncertainty_note": uncertainty_note, "evidence_refs": list(evidence)}


def terrain_cross(lat, lon):
    # Sample about one nominal SRTM90m cell from the center in each direction.
    offset = 1 / 1200  # Three arc-seconds, per SRTM product documentation.
    east = offset / math.cos(math.radians(lat))
    return [(lat, lon), (lat + offset, lon), (lat - offset, lon),
            (lat, lon + east), (lat, lon - east)]


def terrain_fields(rows):
    note = "Coarse elevation. SRTM mission absolute vertical accuracy specification is 16 m at 90% confidence."
    note += " This is not an error bound for the derived slope."
    rows = rows or []
    elevation = rows[0]["elevation"] if rows else None
    slope = None
    if len(rows) == 5 and all(row["elevation"] is not None for row in rows):
        # WGS84 equatorial radius (m). The spherical approximation is adequate for this cross.
        center = rows[0]["location"]
        distances = []
        for row in rows[1:]:
            point = row["location"]
            distance = 6378137 * math.hypot(math.radians(point["lat"] - center["lat"]),
                                           math.radians(point["lng"] - center["lng"]) *
                                           math.cos(math.radians(center["lat"])))
            distances.append(distance)
        slope = sum(abs(row["elevation"] - elevation) / distance for row, distance
                    in zip(rows[1:], distances, strict=True)) * 25
    category = None if slope is None else "gentle" if slope < 2 else "moderate" if slope < 5 else "steep"
    return {
        "elevation_m": field(elevation, "m", SRTM, "3 arc-seconds (~90 m)", note, [SRTM_ACCURACY]),
        "mean_slope_pct": field(None if slope is None else round(slope, 3), "% rise",
                                SRTM, "5-point cross on ~90 m grid", note, [SRTM_ACCURACY]),
        "slope_class": field(category, "class", ASSUMPTION, "5-point cross on ~90 m grid",
                             "Illustrative classes: gentle <2%, moderate 2–<5%, steep ≥5%.", [SRTM]),
    }


def ssurgo_query(lat, lon):
    return f"""
WITH ranked AS (
    SELECT mu.mukey, mu.muname, c.cokey, c.compname, c.comppct_r, c.hydgrp, c.drainagecl,
           ROW_NUMBER() OVER (PARTITION BY mu.mukey ORDER BY c.comppct_r DESC, c.cokey) AS rank
    FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('POINT({lon} {lat})') AS hit
    JOIN mapunit AS mu ON mu.mukey = hit.mukey
    JOIN component AS c ON c.mukey = mu.mukey
    WHERE c.comppct_r IS NOT NULL AND c.majcompflag = 'Yes'
)
SELECT c.mukey, c.muname, c.compname, c.comppct_r, c.hydgrp, c.drainagecl,
       h.hzdept_r, h.hzdepb_r, h.om_r, h.awc_r, h.claytotal_r, h.sandtotal_r, h.silttotal_r,
       tex.texture, restriction.reskind, restriction.resdept_r
FROM ranked AS c
LEFT JOIN chorizon AS h ON h.cokey = c.cokey AND h.hzdept_r < 30
OUTER APPLY (
    SELECT TOP 1 t.texture FROM chtexturegrp AS t
    WHERE t.chkey = h.chkey AND t.rvindicator = 'Yes' ORDER BY t.chtgkey
) AS tex
OUTER APPLY (
    SELECT TOP 1 r.reskind, r.resdept_r FROM corestrictions AS r
    WHERE r.cokey = c.cokey AND r.resdept_r IS NOT NULL ORDER BY r.resdept_r, r.corestrictkey
) AS restriction
WHERE c.rank = 1
ORDER BY c.mukey, h.hzdept_r
"""


def json_table(body):
    rows = json.loads(body).get("Table")
    if not rows:
        raise ValueError("SDA returned no soil horizons")
    return rows


def ssurgo_fields(rows):
    resolution = "SSURGO map unit, dominant major component"
    note = "Mapped representative component and horizons. Field sampling is needed for parcel conditions."
    if not rows or len({row[0] for row in rows}) != 1:
        note = "Missing or ambiguous SSURGO map unit. No component selected."
        rows = []

    def metric(value, unit):
        return field(value, unit, SSURGO, resolution, note, [SDA])

    def weighted(column, scale=1):
        thickness = 0
        total = 0
        for row in rows:
            if row[6] is None or row[7] is None or row[column] is None:
                continue
            overlap = max(0, min(30, float(row[7])) - max(0, float(row[6])))
            thickness += overlap
            total += float(row[column]) * overlap
        return round(total * scale / thickness, 3) if thickness == 30 else None

    top = rows[0] if rows else [None] * 16
    result = {
        "map_unit": metric(top[1], "name"),
        "component": metric(top[2], "name"),
        "component_share_pct": metric(float(top[3]) if top[3] is not None else None, "%"),
        "hydrologic_group": metric(top[4], "USDA hydrologic soil group"),
        "drainage": metric(top[5], "USDA drainage class"),
        "organic_matter_pct": metric(weighted(8), "% mass, 0–30 cm"),
        "available_water_mm_0_30": metric(weighted(9, scale=300), "mm in 0–30 cm"),
        "clay_pct": metric(weighted(10), "% mass, 0–30 cm"),
        "sand_pct": metric(weighted(11), "% mass, 0–30 cm"),
        "silt_pct": metric(weighted(12), "% mass, 0–30 cm"),
        "texture_class": metric(top[13], "representative surface texture code"),
        "restrictive_layer": metric(top[14], "kind"),
        "restrictive_depth_cm": metric(float(top[15]) if top[15] is not None else None, "cm"),
    }
    if rows and top[15] is None:
        for key in ("restrictive_layer", "restrictive_depth_cm"):
            result[key]["uncertainty_note"] += " No restrictive layer was listed for this component."
    return result


def geo_tiff_value(data, x, y):
    with Image.open(io.BytesIO(data)) as raster:
        scale_x, scale_y, *_ = raster.tag_v2[33550]
        col0, row0, _, east, north, _ = raster.tag_v2[33922]
        pixel = (math.floor(col0 + (x - east) / scale_x),
                 math.floor(row0 + (north - y) / scale_y))
        value = raster.getpixel(pixel)
        nodata = raster.tag_v2.get(42113)
        if nodata is not None and float(nodata.strip("\x00")) == value:
            raise ValueError("SoilGrids pixel has no data")
        if not isinstance(value, int) or value < 0:
            raise ValueError("Invalid SoilGrids sample")
        return value / 10


def soilgrids_fields(cache, farm):
    farm_id = farm["farm_id"]
    projection = shutil.which("proj")
    if projection is None and not cache.offline:
        raise RuntimeError("SoilGrids WCS precompute requires the PROJ command 'proj'")
    coordinates = cache.directory / f"{farm_id}_projection.json"
    if coordinates.exists():
        x, y = json.loads(coordinates.read_text())["value"]
    elif projection:
        result = subprocess.run([projection, "-f", "%.3f", "+proj=igh", "+datum=WGS84"],
                                input=f"{farm['lon']} {farm['lat']}\n", check=True,
                                capture_output=True, text=True)
        x, y = map(float, result.stdout.split())
        if not cache.offline:
            write_json(coordinates, {"value": [x, y], "unit": "m",
                                    "source": "https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html"})
    else:
        x = y = None
    crs = "http://www.opengis.net/def/crs/EPSG/0/152160"
    soils = {}
    water = 0
    water_complete = True
    texture_complete = True
    for top, bottom in DEPTHS:
        depth = f"{top}-{bottom}cm"
        points = {}
        for prop, (name, unit) in SOIL_LAYERS.items():
            key = f"{farm_id}_{prop}_{depth}"
            params = [("map", f"/map/{prop}.map"), ("SERVICE", "WCS"), ("VERSION", "2.0.1"),
                      ("REQUEST", "GetCoverage"), ("COVERAGEID", f"{prop}_{depth}_Q0.5"),
                      ("FORMAT", "GEOTIFF_INT16"), ("SUBSETTINGCRS", crs), ("OUTPUTCRS", crs)]
            value = None
            if x is not None:
                params += [("SUBSET", f"X({x-250},{x+250})"), ("SUBSET", f"Y({y-250},{y+250})")]
                value = cache.fetch(key, WCS, params=params, suffix="tif", attempts=2,
                                    parse=lambda data: geo_tiff_value(data, x, y))
            points[name] = field(value, unit, SOILGRIDS, f"250 m grid, {depth}",
                                 "SoilGrids median model prediction. Local soil sampling is needed."
                                 if value is not None else "incomplete: WCS did not supply a valid pixel.",
                                 [f"data/raw/p3/manifest.json#{key}"])
        soils[depth] = points
        texture_complete &= all(points[prop]["value"] is not None for prop in ("clay", "sand", "silt"))
        wet, dry = (points[name]["value"] for name in ("water_at_33_kpa", "water_at_1500_kpa"))
        if wet is None or dry is None or wet <= dry:
            water_complete = False
        else:
            water += (wet - dry) * (bottom - top) / 10
    result = {"depths": soils}
    if not texture_complete:
        result["texture_class"] = field("loam", "coarse texture class", ASSUMPTION,
                                        "generic fallback", "incomplete: SoilGrids texture retrieval failed.")
    result["available_water_mm_0_30"] = field(
        round(water, 3) if water_complete else None, "mm in 0–30 cm", SOILGRIDS, "250 m grid",
        "Difference between predicted volumetric water retention at 33 and 1500 kPa, integrated by depth."
        if water_complete else "incomplete: water retention pair unavailable or inconsistent.")
    return result


def build_context(cache, farm):
    farm_id = farm["farm_id"]
    lat, lon = farm["lat"], farm["lon"]
    locations = "|".join(f"{y:.8f},{x:.8f}" for y, x in terrain_cross(lat, lon))
    terrain_key = f"{farm_id}_srtm"

    def elevations(body):
        response = json.loads(body)
        rows = response.get("results", [])
        if response.get("status") != "OK" or len(rows) != 5:
            raise ValueError("SRTM returned an incomplete cross")
        return rows

    terrain = terrain_fields(cache.fetch(terrain_key, "https://api.opentopodata.org/v1/srtm90m",
                                         params={"locations": locations}, parse=elevations, interval=1.1))
    for metric in terrain.values():
        metric["evidence_refs"].append(f"data/raw/p3/manifest.json#{terrain_key}")
    alternative = None
    if farm["tier"] == 2:
        soil_key = f"{farm_id}_ssurgo"
        soil = ssurgo_fields(cache.fetch(soil_key, SDA, data={"query": ssurgo_query(lat, lon),
                                                             "format": "JSON"}, parse=json_table))
        for metric in soil.values():
            metric["evidence_refs"].append(f"data/raw/p3/manifest.json#{soil_key}")
        alternative = cache.fetch(f"{farm_id}_usgs_ogc",
                                  "https://api.waterdata.usgs.gov/ogcapi/v1/collections/field-measurements/items",
                                  params={"f": "json", "parameter_code": "72019", "limit": 1,
                                          "bbox": f"{lon-.05},{lat-.05},{lon+.05},{lat+.05}"},
                                  attempts=1)
    else:
        soil = soilgrids_fields(cache, farm)
    summary, source = GROUNDWATER.get(farm_id, ("groundwater trend: not verified", ASSUMPTION))
    groundwater = {"regional_context": field(summary, "text", source, "region",
                                              "Groundwater trend and availability at this field are unverified.")}
    if alternative is not None:
        groundwater["regional_context"]["evidence_refs"].append(
            f"data/raw/p3/manifest.json#{farm_id}_usgs_ogc")
    flags = list(farm["validation_flags"])
    if "depths" in soil and "texture_class" in soil:
        flags.append("SoilGrids texture retrieval incomplete. The coarse texture default is an assumption.")
    if soil["available_water_mm_0_30"]["value"] is None:
        flags.append("Available water capacity in 0–30 cm is incomplete.")
    if terrain["mean_slope_pct"]["value"] is None:
        flags.append("SRTM cross incomplete. Slope is unavailable.")
    if farm_id == "us_high_plains_b" and terrain["slope_class"]["value"] in {"moderate", "steep"}:
        flags.append("The coarse SRTM slope is higher than the SSURGO map-unit slope class. Validate local slope.")
    return {"farm_id": farm_id, "label": "illustrative; validate locally", "soil": soil,
            "terrain": terrain, "groundwater": groundwater, "validation_flags": flags,
            "limitations": ["Satellites do not directly measure soil nitrogen or organic carbon.",
                            "SoilGrids is a model prediction. POWER soil wetness is modelled."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    cache = RequestCache(ROOT / "data/raw/p3", offline=args.offline)
    farms = json.loads((ROOT / "config/farms.json").read_text())
    for farm in farms:
        context = build_context(cache, farm)
        write_json(ROOT / f"data/processed/context_{farm['farm_id']}.json", context)
        print(f"{farm['farm_id']}: soil and terrain context saved", flush=True)


if __name__ == "__main__":
    main()
