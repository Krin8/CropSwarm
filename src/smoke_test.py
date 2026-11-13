"""Live, reproducible API smoke checks; never used at demo runtime.

Run from the repository root: python -m src.smoke_test
All coordinates and spacing are approximate API test inputs, not farm locations.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/smoke"
POINTS = {"us": (37.97, -100.87), "india": (17.98, 79.59)}
POWER_PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,GWETROOT,ALLSKY_SFC_SW_DWN,RH2M"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "CropSwarm-hackathon-smoke/0.1 (research prototype)"


def call(name: str, url: str, *, params: dict | None = None, method: str = "GET",
         data: dict | None = None, alternative: tuple[str, dict | None] | None = None,
         refresh: bool = False) -> dict:
    saved = OUT / f"{name}.json"
    previous = json.loads(saved.read_text(encoding="utf-8")) if saved.exists() else None
    if previous and previous["status"] == "PASS" and not refresh:
        print(f"{name}: PASS (saved; no new request)")
        return previous
    attempts = [(url, params)]
    if alternative:
        attempts.append(alternative)
    record = {"name": name, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "attempts": previous["attempts"] if previous else []}
    for target, query in attempts:
        start = time.monotonic()
        try:
            response = SESSION.request(method, target, params=query, data=data, timeout=30)
            elapsed = round(time.monotonic() - start, 3)
            try:
                body = response.json()
            except ValueError:
                body = response.text if name.startswith("soilgrids_wcs") else response.text[:4000]
            attempt = {"url": response.url, "method": method, "http_status": response.status_code,
                       "latency_s": elapsed, "response_keys": list(body) if isinstance(body, dict) else [],
                       "body": body}
            record["attempts"].append(attempt)
            if response.ok and ((isinstance(body, dict) and not body.get("error")) or
                                (name == "appeears_docs" and isinstance(body, str) and
                                 "AppEEARS API Documentation" in body) or
                                (name == "cdl_us_projected" and isinstance(body, str) and
                                 "GetCDLValueResponse" in body and "value:" in body) or
                                (name.startswith("soilgrids_wcs") and isinstance(body, str) and
                                 "Capabilities" in body)):
                record["status"] = "PASS"
                break
        except requests.RequestException as exc:
            record["attempts"].append({"url": target + ("?" + urlencode(query) if query else ""),
                                       "method": method, "http_status": None,
                                       "latency_s": round(time.monotonic() - start, 3), "error": str(exc)})
    else:
        record["status"] = "FAIL"
    OUT.mkdir(parents=True, exist_ok=True)
    saved.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{name}: {record['status']} ({record['attempts'][-1].get('http_status')})")
    return record


def main() -> None:
    for label, (lat, lon) in POINTS.items():
        base = "https://power.larc.nasa.gov/api/temporal/daily/point"
        call(f"power_{label}", base, params={"parameters": POWER_PARAMS, "community": "AG",
             "longitude": lon, "latitude": lat, "start": "20230101", "end": "20231231", "format": "JSON"})
        # ORNL DAAC documents a maximum of ten MODIS dates per subset request.
        for part, (start, end) in enumerate(((1, 145), (161, 305), (321, 353)), 1):
            call(f"modis_{label}_{part}", "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset",
                 params={"latitude": lat, "longitude": lon, "startDate": f"A2023{start:03d}",
                         "endDate": f"A2023{end:03d}", "kmAboveBelow": 0, "kmLeftRight": 0})
        call(f"soilgrids_{label}", "https://rest.isric.org/soilgrids/v2.0/properties/query",
             params=[("lon", lon), ("lat", lat), ("property", "clay"), ("property", "sand"),
                     ("property", "soc"), ("depth", "0-5cm"), ("depth", "5-15cm"),
                     ("depth", "15-30cm"), ("value", "mean")])
    call("power_parameters", "https://power.larc.nasa.gov/api/system/manager/parameters",
         params={"community": "AG", "temporal": "daily"})
    call("modis_bands", "https://modis.ornl.gov/rst/api/v1/MOD13Q1/bands")
    # ISRIC documents WCS as the stable alternative while REST is paused.
    call("soilgrids_wcs_clay", "https://maps.isric.org/mapserv",
         params={"map": "/map/clay.map", "SERVICE": "WCS", "VERSION": "2.0.0",
                 "REQUEST": "GetCapabilities"})
    lat, lon = POINTS["us"]
    # Roughly 90 m offsets; approximate API testing only.
    offsets = [-0.00081, 0, 0.00081]
    grid = "|".join(f"{lat + dy:.5f},{lon + dx:.5f}" for dy in offsets for dx in offsets)
    call("srtm_us_point", "https://api.opentopodata.org/v1/srtm90m", params={"locations": f"{lat},{lon}"})
    call("srtm_us_grid", "https://api.opentopodata.org/v1/srtm90m", params={"locations": grid})
    lat, lon = POINTS["india"]
    call("srtm_india_point", "https://api.opentopodata.org/v1/srtm90m", params={"locations": f"{lat},{lon}"})
    call("srtm_india_grid", "https://api.opentopodata.org/v1/srtm90m",
         params={"locations": "|".join(f"{lat + dy:.5f},{lon + dx:.5f}" for dy in offsets for dx in offsets)})
    lat, lon = POINTS["us"]
    query = f"SELECT TOP 1 mukey, muname FROM mapunit WHERE mukey IN (SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('POINT({lon} {lat})'))"
    call("ssurgo_us", "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest",
         method="POST", data={"query": query, "format": "JSON"})
    # USDA documents CDL coordinates in EPSG:5070 meters. Converted from
    # the user-supplied test point with PROJ cs2cs (EPSG:4326 -> EPSG:5070).
    call("cdl_us_projected", "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue",
         params={"year": 2022, "x": -423585.797, "y": 1670318.167})
    call("nwis_us_levels", "https://waterservices.usgs.gov/nwis/gwlevels/",
         params={"format": "json", "bBox": "-100.97,37.87,-100.77,38.07"})
    call("appeears_docs", "https://appeears.earthdatacloud.nasa.gov/api/")
    write_manifest()


def write_manifest() -> None:
    """Summarize saved responses without making another network request."""
    entries = []
    bands_file = OUT / "modis_bands.json"
    bands = json.loads(bands_file.read_text())["attempts"][-1]["body"]["bands"] if bands_file.exists() else []
    ndvi_meta = next((b for b in bands if b.get("band") == "250m_16_days_NDVI"), {})
    for path in sorted(OUT.glob("*.json")):
        if path.name == "manifest.json":
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        attempt = record["attempts"][-1]
        body = attempt.get("body")
        name = record["name"]
        summary = {"source": name, "status": record["status"], "url": attempt.get("url"),
                   "http_status": attempt.get("http_status"), "latency_s": attempt.get("latency_s"),
                   "response_keys": attempt.get("response_keys", []), "units": None,
                   "fill_missing": None, "sample_row": None}
        if name.startswith("power_") and name != "power_parameters" and isinstance(body, dict):
            values = body["properties"]["parameter"]
            fill = body["header"].get("fill_value")
            summary["units"] = {k: v["units"] for k, v in body["parameters"].items()}
            summary["fill_missing"] = {"fill_value": fill,
                                       "counts": {k: sum(x == fill or x is None for x in series.values())
                                                  for k, series in values.items()}}
            summary["sample_row"] = {"date": "20230101", **{k: v.get("20230101") for k, v in values.items()}}
        elif name.startswith("modis_") and name != "modis_bands" and isinstance(body, dict):
            ndvi = [row for row in body["subset"] if row["band"] == "250m_16_days_NDVI"]
            summary["units"] = {"NDVI": ndvi_meta.get("units"), "scale_factor": ndvi_meta.get("scale_factor")}
            summary["fill_missing"] = {"fill_value": ndvi_meta.get("fill_value"),
                                       "count": sum(v == int(ndvi_meta.get("fill_value", -3000))
                                                    for row in ndvi for v in row["data"])}
            summary["sample_row"] = {"date": ndvi[0]["modis_date"], "NDVI_raw": ndvi[0]["data"][0]} if ndvi else None
        elif name.startswith("srtm_") and isinstance(body, dict):
            summary["units"] = "meters elevation"
            summary["fill_missing"] = {"null_elevations": sum(row["elevation"] is None for row in body["results"])}
            summary["sample_row"] = body["results"][0]
        elif name.startswith("soilgrids_"):
            summary["units"] = {"clay": "g/kg -> % divide by 10", "sand": "g/kg -> % divide by 10",
                                "soc": "dg/kg -> g/kg divide by 10"}
            summary["fill_missing"] = "unavailable: REST failed; WCS capabilities have no pixel data"
        elif name == "cdl_us_projected" and isinstance(body, str):
            summary["units"] = "categorical CDL class code"
            summary["sample_row"] = body
        elif name == "ssurgo_us" and isinstance(body, dict):
            summary["units"] = {"mukey": "identifier", "muname": "text"}
            summary["sample_row"] = body.get("Table", [None])[0]
        entries.append(summary)
    (OUT / "manifest.json").write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
