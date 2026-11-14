"""Prepare the offline Streamlit data bundle and cache the map geography."""

import argparse
import json

from src.crops import load_crops
from src.localize import validate_locales
from src.precompute_cache import RequestCache, write_json
from src.scoring import METRICS, ROOT

MAP_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-map", action="store_true")
    args = parser.parse_args()
    config = ROOT / "config"
    farms = json.loads((config / "farms.json").read_text())
    settings = {"farms": farms, "crops": load_crops(ROOT / "data/crops.csv", farms=farms)}
    for name in ("weights_presets", "scoring", "uncertainty"):
        settings[name] = json.loads((config / f"{name}.json").read_text())
    # The app reads wording from the bundle so it needs no config directory at runtime.
    settings["locales"] = validate_locales(json.loads((config / "locales.json").read_text(encoding="utf-8")), farms,
                                           settings["crops"], METRICS, settings["weights_presets"]["presets"])
    write_json(ROOT / "data/processed/app_settings.json", settings)
    cache = RequestCache(ROOT / "data/raw/p11", offline=not args.fetch_map)
    geography = cache.fetch("natural_earth_land", MAP_URL)
    if geography:
        rings = []
        for feature in geography["features"]:
            geometry = feature["geometry"]
            for polygon in ([geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]):
                rings.append(polygon[0])
        write_json(ROOT / "data/processed/world_land.json", {"rings": rings, "source": MAP_URL})


if __name__ == "__main__":
    main()
