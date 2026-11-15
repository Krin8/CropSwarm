"""Cache P48 source byte ranges and extract native-pixel windows.

Run from the repository root with python -m scripts.cache_p48_rasters.
Only the listed public classification assets are contacted. The window evidence
can subsequently be analyzed offline with python -m src.makueni_cropland.
"""

import argparse
import io
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, TiffImagePlugin
import requests


CACHE = Path("data/cache/p48")
WITNESSES = Path("data/raw/p48")
WORLDCOVER = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
              "ESA_WorldCover_10m_2021_v200_S03E036_Map.tif")
GLAD = "https://gladxfer.umd.edu/Potapov/Global_Crop/Data/Global_cropland_SE_2019.tif"
WORLDCEREAL = ("https://deafrica-input-datasets.s3.af-south-1.amazonaws.com/esa_worldcereal/"
               "temporarycrops/tc-annual/12048/2021/"
               "12048_tc-annual_temporarycrops_2020-11-05_2021-11-05_classification.tif")
ASSETS = {"worldcover": WORLDCOVER, "glad": GLAD, "worldcereal": WORLDCEREAL}
# Bounding box padded beyond the 5 km study disk.
BBOX = (37.59, -2.0, 37.69, -1.9)
BLOCK_SIZE = 256 * 1024


class RangeFile:
    """A seekable reader for these public GeoTIFFs with on-disk range caching."""

    def __init__(self, session, url, directory):
        self.session, self.url, self.directory = session, url, directory
        self.offset = 0
        directory.mkdir(parents=True, exist_ok=True)
        manifest = directory / "asset.json"
        if manifest.exists():
            self.metadata = json.loads(manifest.read_text())
            if self.metadata["url"] != url:
                raise ValueError(f"Cached URL mismatch for {directory}")
        else:
            with session.head(url, timeout=30) as response:
                response.raise_for_status()
                self.metadata = {
                    "url": response.url, "bytes": int(response.headers["Content-Length"]),
                    "etag": response.headers["ETag"],
                    "last_modified": response.headers.get("Last-Modified"),
                }
            manifest.write_text(json.dumps(self.metadata, indent=2) + "\n")

    def tell(self):
        return self.offset

    def seek(self, offset, whence=io.SEEK_SET):
        start = {io.SEEK_SET: 0, io.SEEK_CUR: self.offset, io.SEEK_END: self.metadata["bytes"]}[whence]
        self.offset = start + offset
        return self.offset

    def block(self, start):
        end = min(start + BLOCK_SIZE, self.metadata["bytes"]) - 1
        block = self.directory / str(start)
        if block.exists() and block.stat().st_size == end + 1 - start:
            return block.read_bytes()
        expected = f"bytes {start}-{end}/{self.metadata['bytes']}"
        for attempt in range(3):
            try:
                with self.session.get(self.url, headers={"Range": f"bytes={start}-{end}",
                                      "If-Match": self.metadata["etag"], "Accept-Encoding": "identity"},
                                      timeout=30, stream=True) as response:
                    response.raise_for_status()
                    if (response.status_code != 206 or response.headers.get("Content-Range") != expected or
                            response.headers.get("ETag") != self.metadata["etag"]):
                        raise ValueError(f"Range response does not match pinned asset: {expected}")
                    data = response.content
                if len(data) != end + 1 - start:
                    raise ValueError(f"Truncated range: {expected}")
                temporary = block.with_suffix(".part")
                temporary.write_bytes(data)
                temporary.replace(block)
                return data
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)

    def read(self, size=-1):
        if size < 0:
            raise ValueError("An explicit read length is required")
        end = min(self.offset + size, self.metadata["bytes"])
        pieces = []
        while self.offset < end:
            start = (self.offset // BLOCK_SIZE) * BLOCK_SIZE
            offset = self.offset - start
            part = self.block(start)[offset:offset + end - self.offset]
            pieces.append(part)
            self.offset += len(part)
        return b"".join(pieces)


def decode_block(source, tags, offset, size, width, height):
    source.seek(offset)
    payload = source.read(size)
    # Rewrap a compressed tile or strip as a small grayscale TIFF. Palette
    # entries are deliberately omitted so Pillow returns the raw class index.
    header = b"II*\x00\x08\x00\x00\x00"
    directory = TiffImagePlugin.ImageFileDirectory_v2(header)
    for key, value in {256: width, 257: height, 258: (8,), 262: 1, 273: (0,),
                       277: 1, 278: height, 279: (size,), 284: 1, 339: (1,)}.items():
        directory[key] = value
    for key in (259, 266, 317):
        if key in tags:
            directory[key] = tags[key]
    with Image.open(io.BytesIO(header + directory.tobytes(8) + payload)) as pixels:
        return np.array(pixels)


def extract(source, bbox):
    # Metadata-only open of very large source rasters. Only the small clip is
    # allocated. The original resolution and pixel centers are preserved.
    original_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = None
    try:
        with Image.open(source) as raster:
            tags = raster.tag_v2
            if tags[258] != (8,) or tags.get(277, 1) != 1 or tags.get(339, (1,)) != (1,):
                raise ValueError("Expected a single unsigned 8-bit classification band")
            geokeys = tags[34735]
            keys = {geokeys[i]: tuple(geokeys[i+1:i+4]) for i in range(4, len(geokeys), 4)}
            if keys.get(1024) != (0, 1, 2) or keys.get(2048) != (0, 1, 4326) or keys.get(1025) != (0, 1, 1):
                raise ValueError(f"Expected WGS84 geographic pixel-area grid: {keys}")
            dx, dy, _ = tags[33550]
            col, row, _, east, north, _ = tags[33922]
            west, top = east - col * dx, north + row * dy
            minimum_x, minimum_y, maximum_x, maximum_y = bbox
            x0, x1 = math.floor((minimum_x - west) / dx), math.ceil((maximum_x - west) / dx)
            y0, y1 = math.floor((top - maximum_y) / dy), math.ceil((top - minimum_y) / dy)
            if not (0 <= x0 < x1 <= raster.width and 0 <= y0 < y1 <= raster.height):
                raise ValueError("Requested extent falls outside source raster")
            tiled = 324 in tags
            width, height = (tags[322], tags[323]) if tiled else (raster.width, tags[278])
            offsets, counts = (tags[324], tags[325]) if tiled else (tags[273], tags[279])
            columns = math.ceil(raster.width / width)
            missing = tags.get(42113)
            nodata = -1 if missing is None else int(missing.rstrip("\x00"))
            values = np.empty((y1 - y0, x1 - x0), dtype=np.uint8)
            for block_y in range(y0 // height, (y1 - 1) // height + 1):
                for block_x in range(x0 // width, (x1 - 1) // width + 1):
                    index = block_y * columns + block_x
                    start_x, start_y = block_x * width, block_y * height
                    left, right = max(x0, start_x), min(x1, start_x + width)
                    upper, lower = max(y0, start_y), min(y1, start_y + height)
                    if counts[index]:
                        rows = height if tiled else min(height, raster.height - start_y)
                        block = decode_block(source, tags, offsets[index], counts[index], width, rows)
                        window = block[upper-start_y:lower-start_y, left-start_x:right-start_x]
                    elif nodata >= 0:
                        window = nodata
                    else:
                        raise ValueError("Unallocated source block has no declared fill code")
                    values[upper-y0:lower-y0, left-x0:right-x0] = window
            return values, np.array([west + x0 * dx, top - y0 * dy, dx, dy]), nodata
    finally:
        Image.MAX_IMAGE_PIXELS = original_limit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", choices=ASSETS)
    parser.add_argument("--local-tiff", type=Path, help="Use an already cached complete GeoTIFF")
    args = parser.parse_args()
    with requests.Session() as session:
        asset = RangeFile(session, ASSETS[args.asset], CACHE / args.asset)
        if args.local_tiff:
            if args.local_tiff.stat().st_size != asset.metadata["bytes"]:
                raise ValueError("Local TIFF size does not match the source")
            with args.local_tiff.open("rb") as file:
                values, grid, nodata = extract(file, BBOX)
        else:
            values, grid, nodata = extract(asset, BBOX)
    WITNESSES.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(WITNESSES / f"{args.asset}.npz", values=values, grid=grid, nodata=nodata)
    meta = asset.metadata | {"bbox_lonlat": BBOX, "shape": values.shape,
                              "west_north_dx_dy": grid.tolist(), "tiff_nodata": nodata}
    (WITNESSES / f"{args.asset}.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(args.asset, values.shape, np.unique(values, return_counts=True), grid.tolist(), nodata)


if __name__ == "__main__":
    main()
