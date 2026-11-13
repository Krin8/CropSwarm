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
         data: dict | None = None, alternative: tuple[str, dict | None] | None = None) -> dict:
    attempts = [(url, params)]
    if alternative:
        attempts.append(alternative)
    record = {"name": name, "checked_at_utc": datetime.now(timezone.utc).isoformat(), "attempts": []}
    for target, query in attempts:
        start = time.monotonic()
        try:
            response = SESSION.request(method, target, params=query, data=data, timeout=30)
            elapsed = round(time.monotonic() - start, 3)
            try:
                body = response.json()
            except ValueError:
                body = response.text[:4000]
            attempt = {"url": response.url, "method": method, "http_status": response.status_code,
                       "latency_s": elapsed, "response_keys": list(body) if isinstance(body, dict) else [],
                       "body": body}
            record["attempts"].append(attempt)
            if response.ok and isinstance(body, dict) and not body.get("error"):
                record["status"] = "PASS"
                break
        except requests.RequestException as exc:
            record["attempts"].append({"url": target + ("?" + urlencode(query) if query else ""),
                                       "method": method, "http_status": None,
                                       "latency_s": round(time.monotonic() - start, 3), "error": str(exc)})
    else:
        record["status"] = "FAIL"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{name}: {record['status']} ({record['attempts'][-1].get('http_status')})")
    return record


def main() -> None:
    for label, (lat, lon) in POINTS.items():
        base = "https://power.larc.nasa.gov/api/temporal/daily/point"
        call(f"power_{label}", base, params={"parameters": POWER_PARAMS, "community": "AG",
             "longitude": lon, "latitude": lat, "start": "20230101", "end": "20231231", "format": "JSON"})
        call(f"modis_{label}", "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset",
             params={"latitude": lat, "longitude": lon, "startDate": "A2023001",
                     "endDate": "A2023365", "kmAboveBelow": 0, "kmLeftRight": 0})
        call(f"soilgrids_{label}", "https://rest.isric.org/soilgrids/v2.0/properties/query",
             params={"lon": lon, "lat": lat, "property": ["clay", "sand", "soc"],
                     "depth": ["0-5cm", "5-15cm", "15-30cm"], "value": "mean"})
    call("power_parameters", "https://power.larc.nasa.gov/api/system/manager/parameters",
         params={"community": "AG"})
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
    call("cdl_us", "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLValue",
         params={"year": 2022, "x": lon, "y": lat})
    call("nwis_us", "https://waterservices.usgs.gov/nwis/site/",
         params={"format": "rdb", "siteType": "GW", "bBox": "-100.97,37.87,-100.77,38.07"})
    call("appeears_docs", "https://appeears.earthdatacloud.nasa.gov/api/")


if __name__ == "__main__":
    main()
