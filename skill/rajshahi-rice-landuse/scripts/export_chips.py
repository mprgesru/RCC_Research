#!/usr/bin/env python3
"""Export interpretation chips for the reference sample.

For each sample point, finds the least cloudy Sentinel-2 L2A scene in the chosen
season window and writes a three-panel image: true colour, false colour
(NIR-R-G) and NDVI. Also writes an index CSV so interpreters can work through
points systematically.

Chips are evidence for labelling only. They are not training data by themselves.

Outputs
-------
${DATA_ROOT}/chips/{YEAR}/{SEASON}/{sample_id}.png
tables/chip_index.csv

Usage
-----
    python export_chips.py --year 2020 --season AMAN --limit 20
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.windows import Window

REPO_ROOT = Path(__file__).resolve().parents[3]
TABLE_DIR = REPO_ROOT / "tables"
PC_SEARCH = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
PC_SAS = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a"
SEASONS = {
    "BORO": ((11, 1), (4, 30), -1),
    "AUS": ((5, 1), (8, 31), 0),
    "AMAN": ((6, 1), (11, 30), 0),
}
CHIP_PIXELS = 100  # 1 km at 10 m


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def window(year: int, season: str) -> tuple[date, date]:
    (sm, sd), (em, ed), offset = SEASONS[season]
    return date(year + offset, sm, sd), date(year, em, ed)


def get_token() -> str:
    response = requests.get(PC_SAS, timeout=60)
    response.raise_for_status()
    return response.json()["token"]


def sign(href: str, token: str) -> str:
    return f"{href}{'&' if '?' in href else '?'}{token}"


def best_scene(lon: float, lat: float, start: date, end: date) -> dict | None:
    body = {
        "collections": ["sentinel-2-l2a"],
        "intersects": {"type": "Point", "coordinates": [lon, lat]},
        "datetime": f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T23:59:59Z",
        "limit": 50,
    }
    response = requests.post(PC_SEARCH, json=body, timeout=120)
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        return None
    features.sort(key=lambda f: f.get("properties", {}).get("eo:cloud_cover", 100))
    return features[0]


def read_chip(asset: dict, token: str, x: float, y: float) -> np.ndarray | None:
    from pyproj import Transformer

    with rasterio.open(sign(asset["href"], token)) as source:
        if source.crs is not None and source.crs.to_string() != "EPSG:4326":
            transformer = Transformer.from_crs("EPSG:4326", source.crs, always_xy=True)
            x, y = transformer.transform(x, y)
        row, col = source.index(x, y)
        half = CHIP_PIXELS // 2
        window = Window(col - half, row - half, CHIP_PIXELS, CHIP_PIXELS)
        data = source.read(1, window=window, boundless=True, fill_value=0).astype(np.float32)
    data[data <= 0] = np.nan
    return data / 10000.0


def stretch(array: np.ndarray) -> np.ndarray:
    valid = array[np.isfinite(array)]
    if valid.size == 0:
        return np.zeros_like(array)
    low, high = np.percentile(valid, [2, 98])
    if high <= low:
        return np.zeros_like(array)
    return np.clip((array - low) / (high - low), 0, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--season", choices=sorted(SEASONS), default="AMAN")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    db_path = data_root / "db" / "rajshahi_rice.gpkg"
    out_dir = data_root / "chips" / str(args.year) / args.season
    out_dir.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        samples = pd.read_sql_query(
            "SELECT sample_id, map_class, zone_id FROM reference_samples WHERE reference_year = ?",
            connection, params=(args.year,),
        )
    finally:
        connection.close()
    if samples.empty:
        print("No samples for this year. Run sample_design.py first.", file=sys.stderr)
        return 2

    import geopandas as gpd

    samples_geo = gpd.read_file(db_path, layer="reference_samples")
    samples_geo = samples_geo[samples_geo["reference_year"] == args.year].to_crs(4326)
    samples_geo = samples_geo.iloc[args.offset : args.offset + args.limit]

    token = get_token()
    start, end = window(args.year, args.season)
    index_rows = []

    for position, (_, sample) in enumerate(samples_geo.iterrows(), start=1):
        lon, lat = sample.geometry.x, sample.geometry.y
        try:
            scene = best_scene(lon, lat, start, end)
            if scene is None:
                print(f"  {sample['sample_id']}: no scene")
                continue
            assets = scene["assets"]
            red = read_chip(assets["B04"], token, lon, lat)
            green = read_chip(assets["B03"], token, lon, lat)
            blue = read_chip(assets["B02"], token, lon, lat)
            nir = read_chip(assets["B08"], token, lon, lat)
            if any(a is None for a in (red, green, blue, nir)):
                continue

            figure, axes = plt.subplots(1, 3, figsize=(12, 4.4))
            true = np.dstack([stretch(red), stretch(green), stretch(blue)])
            false = np.dstack([stretch(nir), stretch(red), stretch(green)])
            with np.errstate(divide="ignore", invalid="ignore"):
                ndvi = np.clip((nir - red) / (nir + red), -1, 1)
            axes[0].imshow(true)
            axes[0].set_title("True colour")
            axes[1].imshow(false)
            axes[1].set_title("False colour (NIR-R-G)")
            image = axes[2].imshow(ndvi, cmap="RdYlGn", vmin=-0.2, vmax=0.8)
            axes[2].set_title("NDVI")
            figure.colorbar(image, ax=axes[2], fraction=0.046, pad=0.04)
            stamp = scene["properties"].get("datetime", "")[:10]
            cloud = scene["properties"].get("eo:cloud_cover")
            figure.suptitle(
                f"{sample['sample_id']}  zone {sample['zone_id']}  {stamp}  cloud {cloud}%"
            )
            for axis in axes:
                axis.axis("off")
            figure.tight_layout()
            png = out_dir / f"{sample['sample_id']}.png"
            figure.savefig(png, dpi=110, bbox_inches="tight")
            plt.close(figure)

            index_rows.append(
                {
                    "sample_id": sample["sample_id"],
                    "map_class": sample["map_class"],
                    "zone_id": sample["zone_id"],
                    "lon": round(lon, 6),
                    "lat": round(lat, 6),
                    "scene_id": scene["id"],
                    "scene_datetime": scene["properties"].get("datetime"),
                    "cloud_cover": cloud,
                    "png": str(png),
                }
            )
            if position % 5 == 0:
                print(f"  {position}/{len(samples_geo)}")
        except Exception as exc:  # noqa: BLE001 - continue through failures
            print(f"  {sample['sample_id']}: {exc}", file=sys.stderr)

    index_path = TABLE_DIR / "chip_index.csv"
    frame = pd.DataFrame(index_rows)
    if index_path.exists():
        existing = pd.read_csv(index_path)
        existing = existing[~existing["sample_id"].isin(frame["sample_id"])]
        frame = pd.concat([existing, frame], ignore_index=True)
    frame.to_csv(index_path, index=False)

    print(f"chips written: {len(index_rows)}  ->  {out_dir}")
    print(f"index: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
