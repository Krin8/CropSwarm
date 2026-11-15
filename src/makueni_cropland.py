"""P48 analysis of the cached land-cover rasters and existing farm context."""

from dataclasses import dataclass
import json
import math
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import convolve

from src.context import DEPTHS, SOILGRIDS, SOIL_LAYERS, SRTM, geo_tiff_value
from src.diagnostics import BARE_NDVI, MODIS
from src.precompute_cache import write_json

ROOT = Path(__file__).resolve().parents[1]
FARM_ID = "kenya_makueni_north"
REPORT = "makueni_cropland_p48.json"
RADIUS_M = 5000  # Design choice in docs/p48_plan.md.
MIN_PRODUCTS = 2  # Design choice in docs/p48_plan.md.
EARTH_M = 6371007.181  # NASA MODIS sinusoidal projection sphere.
SINUSOIDAL_SOURCE = ("https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/"
                    "Science%20Data%20Product%20Documentation/VIIRS_C2_BA_User_Guide_1.1.pdf")
POWER = "https://power.larc.nasa.gov/docs/methodology/"
MERRA2 = ("https://gmao.gsfc.nasa.gov/media/publications/zbly36ziNFDQeVqPhUoFbmYmvh/"
          "MERRA-2_GIO_File_Specification-Office_Note_v1.0__2Xts4xu.pdf")
IMERG = "https://gpm.nasa.gov/sites/default/files/document_files/IMERG_doc.pdf"
CERES = "https://ceres.larc.nasa.gov/documents/DQ_summaries/CERES_SYN1deg_Ed1A_DQS.pdf"
GEWEX = "https://asdc.larc.nasa.gov/documents/srb/SRB_Rel4-IP_Public_Release_Announcement.pdf"
MCD = "https://lpdaac.usgs.gov/documents/1409/MCD12_User_Guide_V61.pdf"
MCD_CACHE = f"data/raw/p7/land_cover/mcd12q1_{FARM_ID}_2023_1km.1.json"
CLIMATE_CACHE = f"data/processed/climate_{FARM_ID}.parquet"
COMMON_LIMIT = ("Products differ in year, class definition and accuracy. Map agreement describes their "
                "observation periods. Current field use, crop identity and management remain unverified.")

PRODUCTS = {
    "worldcover": {
        "name": "ESA WorldCover v200", "period": "2021", "resolution": "10 m nominal",
        "source": "https://esa-worldcover.org/en/data-access", "crop": 40,
        "legend": {10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
                   50: "Built-up", 60: "Bare/sparse vegetation", 70: "Snow and ice",
                   80: "Permanent water bodies", 90: "Herbaceous wetland",
                   95: "Mangroves", 100: "Moss and lichen"},
    },
    "glad": {
        "name": "UMD GLAD cropland extent", "period": "2016–2019",
        "resolution": "0.00025° (~30 m nominal)",
        "source": "https://glad.umd.edu/dataset/croplands", "crop": 1,
        "legend": {0: "No cropland or no data", 1: "Cropland"},
    },
    "worldcereal": {
        "name": "ESA WorldCereal v100", "period": "2021 product (zone 12048, Nov 2020–Nov 2021)",
        "resolution": "10 m nominal",
        "source": "https://docs.digitalearthafrica.org/en/latest/data_specs/ESA_World_Cereal_specs.html",
        "crop": 100, "legend": {0: "Outside temporary cropland", 100: "Temporary cropland"},
    },
}


def read_json(path):
    return json.loads(path.read_text())


@dataclass(frozen=True)
class Raster:
    values: np.ndarray
    west: float
    north: float
    dx: float
    dy: float

    def centers(self):
        lat = self.north - (np.arange(self.values.shape[0]) + 0.5) * self.dy
        lon = self.west + (np.arange(self.values.shape[1]) + 0.5) * self.dx
        return lat[:, None], lon[None, :]

    def sample(self, lat, lon):
        # Tie to the east/south at an exact cell edge. Round only to suppress
        # floating-point noise in decimal georeferencing.
        row = np.floor(np.round((self.north - lat) / self.dy, 8)).astype(int)
        col = np.floor(np.round((lon - self.west) / self.dx, 8)).astype(int)
        rows, cols = self.values.shape
        inside = (row >= 0) & (row < rows) & (col >= 0) & (col < cols)
        sampled = self.values[row.clip(0, rows-1), col.clip(0, cols-1)].astype(np.int16)
        return np.where(inside, sampled, -1)

    def touching_classes(self, lat, lon):
        epsilon = 1e-5  # Pixel fraction to expose a boundary independently of rounding noise.
        return sorted({int(self.sample(lat + y * epsilon * self.dy, lon + x * epsilon * self.dx))
                       for x in (-1, 1) for y in (-1, 1)})


def distance_m(lat, lon, center):
    phi, lam = np.radians(lat), np.radians(lon)
    orig_phi, orig_lam = map(math.radians, center)
    arc = np.sin((phi-orig_phi)/2)**2 + np.cos(phi)*math.cos(orig_phi)*np.sin((lam-orig_lam)/2)**2
    return 2 * EARTH_M * np.arcsin(np.sqrt(arc))


def map_summary(raster, crop, declared_nodata, point, ambiguous=()):
    lat, lon = raster.centers()
    in_disk = distance_m(lat, lon, point) <= RADIUS_M
    weights = np.broadcast_to(np.cos(np.radians(lat)), raster.values.shape)
    valid = in_disk & (raster.values != declared_nodata)
    classified = valid & ~np.isin(raster.values, ambiguous)
    crops = classified & (raster.values == crop)
    total, known, cropped = (float(weights[mask].sum()) for mask in (in_disk, classified, crops))
    codes, counts = np.unique(raster.values[in_disk], return_counts=True)
    return {
        "class_code": int(raster.sample(*point)),
        "touching_class_codes": raster.touching_classes(*point),
        "crop_pixels": int(crops.sum()), "disk_pixels": int(in_disk.sum()),
        "unresolved_pixels": int((in_disk & ~classified).sum()),
        "pixel_counts": dict(zip(map(int, codes), map(int, counts), strict=True)),
        "cropland_share": cropped / total if total else None,
        "classified_share": known / total if total else None,
    }


def grid_index(value, first_center, step):
    return np.floor(np.round((value - first_center) / step + 0.5, 10)).astype(int)


POWER_GRIDS = {
    "MERRA-2": {
        "parameters": ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "PRECTOTCORR_UTC", "GWETROOT", "RH2M"],
        "step": (0.5, 0.625), "first_center": (-90.0, -180.0), "sources": [POWER, MERRA2],
    },
    "Solar (SRB/CERES)": {
        "parameters": ["ALLSKY_SFC_SW_DWN"], "step": (1.0, 1.0),
        "first_center": (-89.5, -179.5), "sources": [POWER, CERES, GEWEX],
    },
    "GPM IMERG": {
        "parameters": ["IMERG_PRECTOT"], "step": (0.1, 0.1),
        "first_center": (-89.95, -179.95), "sources": [POWER, IMERG],
    },
}


def same_weather_grid(lat, lon, original, grid):
    return ((grid_index(lat, grid["first_center"][0], grid["step"][0])
             == grid_index(original[0], grid["first_center"][0], grid["step"][0]))
            & (grid_index(lon, grid["first_center"][1], grid["step"][1])
               == grid_index(original[1], grid["first_center"][1], grid["step"][1])))


def power_grid_detail(original, candidate):
    output = {}
    for name, grid in POWER_GRIDS.items():
        first, step = grid["first_center"], grid["step"]
        center = [round(start + int(grid_index(coord, start, delta)) * delta, 6)
                  for coord, start, delta in zip(original, first, step, strict=True)]
        bounds = [[round(mid - delta/2, 6), round(mid + delta/2, 6)]
                  for mid, delta in zip(center, step, strict=True)]
        phi, lam = map(math.radians, original)
        nearest_lat = min(abs(phi - math.radians(edge)) for edge in bounds[0])
        nearest_lon = min(abs(math.sin(lam - math.radians(edge))) for edge in bounds[1])
        edge_distance = EARTH_M * min(nearest_lat, math.asin(math.cos(phi) * nearest_lon))
        output[name] = grid | {"original_center": center, "original_bounds": bounds,
                               "nearest_cell_edge_m": edge_distance,
                               "full_disk_shares_cell": edge_distance > RADIUS_M,
                               "alternate_same_cell": None if candidate is None else
                               bool(same_weather_grid(*candidate, original, grid))}
    return output


def nearest_candidate(rasters, crop_codes, origin):
    if len(rasters) < MIN_PRODUCTS:
        return None
    coarsest = max(rasters, key=lambda name: rasters[name].dx * rasters[name].dy)
    lat, lon = rasters[coarsest].centers()
    votes = sum((raster.sample(lat, lon) == crop_codes[name]).astype(np.uint8)
                for name, raster in rasters.items())
    agreement = votes >= MIN_PRODUCTS
    neighboring = convolve(agreement.astype(np.uint8), np.ones((3, 3), dtype=np.uint8),
                           mode="constant") > 1
    distance = distance_m(lat, lon, origin)
    same_weather = np.logical_and.reduce([same_weather_grid(lat, lon, origin, grid)
                                         for grid in POWER_GRIDS.values()])
    rows, cols = np.where(agreement & neighboring & same_weather & (distance <= RADIUS_M) & (distance > 0))
    if not len(rows):
        return None
    order = np.lexsort((lon[0, cols], lat[rows, 0], distance[rows, cols]))
    row, col = rows[order[0]], cols[order[0]]
    point = (float(lat[row, 0]), float(lon[0, col]))
    return {"lat": round(point[0], 9), "lon": round(point[1], 9), "distance_m": float(distance[row, col]),
            "candidate_grid": coarsest, "eligible_centers": len(rows),
            "supporting_products": [name for name, raster in rasters.items()
                                    if raster.sample(*point) == crop_codes[name]]}


def sinusoidal(lat, lon):
    phi, lam = map(math.radians, (lat, lon))
    return EARTH_M * lam * math.cos(phi), EARTH_M * phi


def modis_position(body, point):
    x, y = sinusoidal(*point)
    cell = body["cellsize"]
    col = math.floor((x - float(body["xllcorner"])) / cell)
    row = body["nrows"] - 1 - math.floor((y - float(body["yllcorner"])) / cell)
    if 0 <= row < body["nrows"] and 0 <= col < body["ncols"]:
        return row, col
    return None


def modis_land_cover(root, original, candidate):
    body = read_json(root / MCD_CACHE)
    values = next(block["data"] for block in body["subset"] if block["band"] == "LC_Type1")
    classes = np.asarray(values).reshape(body["nrows"], body["ncols"])
    x, y = sinusoidal(*original)
    cell = body["cellsize"]
    delta_x = float(body["xllcorner"]) + (np.arange(body["ncols"])+0.5)*cell - x
    delta_y = float(body["yllcorner"]) + (np.arange(body["nrows"])+0.5)*cell - y
    mask = np.hypot(delta_y[::-1, None], delta_x[None, :]) <= RADIUS_M
    valid = classes[mask & (classes != 255)]
    original_index = modis_position(body, original)
    if original_index is None:
        raise ValueError("Original coordinate is outside the recorded MCD12Q1 subset")
    alt_index = None if candidate is None else modis_position(body, candidate)
    return {
        "name": "NASA MODIS MCD12Q1 IGBP", "period": "2023", "resolution": "500 m nominal",
        "source": MCD, "access": "Existing ORNL cache; partial disk",
        "point_class": "Grassland" if classes[original_index] == 10 else f"IGBP class {classes[original_index]}",
        "class_code": int(classes[original_index]),
        "alternate_class_code": None if alt_index is None else int(classes[alt_index]),
        "crop_pixels": int((valid == 12).sum()), "mosaic_pixels": int((valid == 14).sum()),
        "sample_pixels": int(valid.size),
        "classified_share": float(valid.size * cell**2 / (math.pi * RADIUS_M**2)),
        "cropland_share": None, "evidence_ref": MCD_CACHE,
    }


def terrain_proxy(rows, candidate):
    """Interpolate inside the cached cross. Use the gradient of the containing triangle."""
    center = rows[0]["location"]
    phi = math.radians(center["lat"])

    def local(lat, lon):
        return np.array([EARTH_M * math.radians(lon - center["lng"]) * math.cos(phi),
                         EARTH_M * math.radians(lat - center["lat"])])

    p = local(*candidate)
    z = rows[0]["elevation"]
    if z is None:
        return None
    for north_south in rows[1:3]:
        for east_west in rows[3:5]:
            samples = [north_south, east_west]
            if any(row["elevation"] is None for row in samples):
                continue
            matrix = np.array([local(row["location"]["lat"], row["location"]["lng"]) for row in samples])
            weights = np.linalg.solve(matrix.T, p)
            if (weights >= -1e-10).all() and weights.sum() <= 1 + 1e-10:
                differences = np.array([row["elevation"] - z for row in samples])
                gradient = np.linalg.solve(matrix, differences)
                return {"slope_pct": round(100 * float(np.linalg.norm(gradient)), 3),
                        "interpolated_elevation_m": round(float(z + weights @ differences), 3),
                        "support": [rows[0], *samples], "source": SRTM,
                        "method": "Piecewise planar gradient in the containing triangle of the original SRTM90m cross"}
    return None


def projection(root, point):
    witness = root / "data/raw/p48/alternate_soil_projection.json"
    if witness.exists():
        record = read_json(witness)
        if record["latlon"] != list(point):
            raise ValueError("Cached SoilGrids projection is for a different point")
        return record["projected_xy_m"]
    result = subprocess.run(["proj", "-f", "%.3f", "+proj=igh", "+datum=WGS84"],
                            input=f"{point[1]} {point[0]}\n", text=True, capture_output=True, check=True)
    coords = list(map(float, result.stdout.split()))
    write_json(witness, {"latlon": list(point), "projected_xy_m": coords,
                         "projection": "+proj=igh +datum=WGS84", "source": SOILGRIDS})
    return coords


def soil_at_point(root, xy):
    layers = {}
    for top, bottom in DEPTHS:
        layer = {}
        depth = f"{top}-{bottom}cm"
        for key, (label, unit) in SOIL_LAYERS.items():
            path = f"data/raw/p3/{FARM_ID}_{key}_{depth}.1.tif"
            data = (root / path).read_bytes()
            with Image.open(root / path) as image:
                scale_x, scale_y, *_ = image.tag_v2[33550]
                col, row, _, west, north, _ = image.tag_v2[33922]
                pixel = (math.floor(col + (xy[0]-west)/scale_x), math.floor(row + (north-xy[1])/scale_y))
                inside = 0 <= pixel[0] < image.width and 0 <= pixel[1] < image.height
            try:
                value = geo_tiff_value(data, *xy) if inside else None
            except ValueError:
                value = None
            layer[label] = {"value": value, "unit": unit, "source": SOILGRIDS,
                            "pixel_col_row": list(pixel) if inside else None, "evidence_ref": path}
        layers[depth] = layer
    water = 0
    for top, bottom in DEPTHS:
        layer = layers[f"{top}-{bottom}cm"]
        wet = layer["water_at_33_kpa"]["value"]
        dry = layer["water_at_1500_kpa"]["value"]
        if wet is None or dry is None or wet <= dry:
            water = None
            break
        water += (wet - dry) * (bottom - top) / 10
    return {"depths": layers, "source": SOILGRIDS, "available_water_mm_0_30": None if water is None else round(water, 3)}


def vegetation_context(root, original, candidate):
    paths = sorted((root / f"data/raw/p4/{FARM_ID}").glob("modis_*.json"))
    keys = ("xllcorner", "yllcorner", "cellsize", "nrows", "ncols")
    geometry = set()
    successful = 0
    for path in paths:
        entry = read_json(path)
        body = entry.get("body")
        if entry["status"] == 200:
            successful += 1
            geometry.add(tuple(body[key] for key in keys))
    sample = dict(zip(keys, next(iter(geometry)), strict=True)) if len(geometry) == 1 else None
    shared = (candidate is not None and sample is not None and
              modis_position(sample, original) == (0, 0) == modis_position(sample, candidate))
    data = root / "data/processed"
    validity = read_json(data / f"validity_{FARM_ID}.json")["current"]
    seasons = read_json(data / f"seasons_{FARM_ID}.json")
    windows = read_json(data / f"opportunity_windows_{FARM_ID}.json")
    long = pd.read_csv(data / f"ndvi_long_{FARM_ID}.csv", usecols=["ndvi"])
    results = {
        "source": MODIS, "period": [windows["years"][0], windows["years"][-1]],
        "qa_composites": windows["qa_composites"], "received_composites": int(long.ndvi.count()),
        "annual_p7": {year: {"peaks": row["peak_count"], "peak_dates": row["peaks"]["0.12"],
                            "qa": row["good_composites"], "received": row["received_composites"]}
                      for year, row in validity["annual"].items()},
        "two_rain_aligned_years": validity["qualifying_years"],
        "greenness_peak_months": seasons["ndvi_peak_months"],
        "rain_windows": {name: [v["onset_month"], v["cessation_month"]]
                         for name, v in seasons["season_windows"].items()},
        "low_greenness": [
            {"threshold": row["threshold"], "runs": row["run_count"],
             "windows": [{key: window[key] for key in ("start_doy", "typical_days", "supporting_years",
                                                       "assessable_years", "qa_composites", "status")}
                         for window in row["windows"]]}
            for row in windows["sensitivity"]
        ],
        "reference_threshold": BARE_NDVI, "threshold_source": windows["threshold_source"],
        "evidence_refs": [f"data/processed/{name}_{FARM_ID}.{suffix}"
                          for name, suffix in (("ndvi_long", "csv"), ("validity", "json"),
                                               ("seasons", "json"), ("opportunity_windows", "json"))],
    }
    return {"original": results, "alternate": results if shared else None, "shared_native_pixel": shared,
            "georeferencing": sample, "successful_chunks": successful,
            "geometry_source": SINUSOIDAL_SOURCE}


def make_study(root=ROOT):
    farm = next(row for row in read_json(root / "config/farms.json") if row["farm_id"] == FARM_ID)
    original = farm["lat"], farm["lon"]
    rasters, products = {}, {}
    for name, details in PRODUCTS.items():
        path = root / f"data/raw/p48/{name}"
        with np.load(path.with_suffix(".npz"), allow_pickle=False) as source:
            raster = Raster(source["values"], *source["grid"])
            values = map_summary(raster, details["crop"], int(source["nodata"]), original,
                                 ambiguous=(0,) if name == "glad" else ())
        rasters[name] = raster
        products[name] = details | values | {
            "point_class": details["legend"].get(values["class_code"], "Unclassified"),
            "access": "Public TIFF, cached", "asset": read_json(path.with_suffix(".json")),
        }
    alt = nearest_candidate(rasters, {name: spec["crop"] for name, spec in PRODUCTS.items()}, original)
    point = None if alt is None else (alt["lat"], alt["lon"])
    for name, product in products.items():
        code = None if point is None else int(rasters[name].sample(*point))
        product["alternate_class_code"] = code
        product["alternate_class"] = product["legend"].get(code, "Unavailable")
    products["mcd12q1"] = modis_land_cover(root, original, point)
    products["mcd12q1"]["alternate_class"] = {10: "Grassland"}.get(products["mcd12q1"]["alternate_class_code"], "Unavailable")
    products["gfsad"] = {
        **read_json(root / "data/raw/p48/gfsad_access.json"), "name": "NASA MEaSUREs GFSAD30AFCE v001",
        "source": "https://www.usgs.gov/apps/croplands/downloadLPDAAC", "period": "Nominal 2015",
        "resolution": "30 m nominal", "point_class": "Unavailable", "alternate_class": "Unavailable",
        "cropland_share": None, "classified_share": None,
    }
    original_context = read_json(root / f"data/processed/context_{FARM_ID}.json")
    cross = read_json(root / f"data/raw/p3/{FARM_ID}_srtm.1.json")["results"]
    original_xy = read_json(root / f"data/raw/p3/{FARM_ID}_projection.json")["value"]
    vegetation = vegetation_context(root, original, point)
    soil = {"original": soil_at_point(root, original_xy),
            "alternate": None if point is None else soil_at_point(root, projection(root, point))}
    terrain = {"original": original_context["terrain"], "alternate": None if point is None else terrain_proxy(cross, point),
               "evidence_ref": f"data/raw/p3/{FARM_ID}_srtm.1.json"}
    point_votes = sum(products[name]["class_code"] == details["crop"] for name, details in PRODUCTS.items())
    point_votes += int(products["mcd12q1"]["class_code"] == 12)
    return {
        "farm_id": FARM_ID, "label": "illustrative; validate locally",
        "design": {"radius_m": RADIUS_M, "minimum_products": MIN_PRODUCTS, "source": "docs/p48_plan.md"},
        "original": {"lat": original[0], "lon": original[1], "crop_votes": point_votes,
                     "meets_rule": point_votes >= MIN_PRODUCTS},
        "alternate": alt, "products": products, "limit": COMMON_LIMIT,
        "weather": {"native_grids": power_grid_detail(original, point), "data_ref": CLIMATE_CACHE,
                    "source": POWER,
                    "qualification": "Same cells inferred from source grids. Daily point API equivalence was not queried."},
        "vegetation": vegetation, "terrain": terrain, "soil": soil,
    }


def parallel_entry(study):
    point = study["alternate"]
    if point is None:
        return None
    return {
        "farm_id": "makueni_alt", "name": "Makueni parallel cropland-map point",
        "parent_farm_id": study["farm_id"], "lat": point["lat"], "lon": point["lon"],
        "region": "Semi-arid eastern Kenya", "tier": 1, "label": "illustrative representative farm",
        "coordinate_source": "P48 nearest agreeing native pixel center; validate locally",
        "status": "parallel context only",
        "baseline_source": "assumption, validate locally; no point-specific rotation assigned",
        "weather_ref": study["weather"]["data_ref"],
        "context_ref": f"data/processed/{REPORT}",
        "validation_flags": [
            "Two map products classify the point as cropland. Current field use and crop history are unverified.",
            "Shares the original MODIS NDVI pixel. Seasonal greenness is a mixed-pixel observation.",
            "Slope is a gradient within the original cached SRTM triangle. A separate point-centered cross is unavailable.",
            "SoilGrids values are model predictions sampled from a cached WCS raster.",
        ],
        "evidence_refs": ["docs/p48_plan.md", f"data/processed/{REPORT}"],
    }


def main():
    study = make_study()
    write_json(ROOT / "data/processed" / REPORT, study)
    candidate = parallel_entry(study)
    if candidate is not None:
        write_json(ROOT / "config/makueni_alt.json", candidate)


if __name__ == "__main__":
    main()
