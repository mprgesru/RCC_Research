#!/usr/bin/env python3
"""Build seasonal Landsat composites and observation-support layers.

For a target year and season, reads windowed Landsat Collection 2 Level-2
surface-reflectance bands from Planetary Computer, applies the Collection 2
QA_PIXEL and QA_RADSAT masks, and writes a median composite plus phenology
metrics and a valid-observation count on a fixed 30 m grid in EPSG:32645.

Outputs (runtime root)
----------------------
rasters/composites/composite_{YEAR}_{SEASON}_30m.tif
rasters/composites/obs_support_{SEASON}_{YEAR}_30m.tif
manifests/composite_{YEAR}_{SEASON}.json

Repository output
-----------------
tables/composite_summary.csv   One row appended per completed composite

Usage
-----
    python build_composites.py --year 2020 --season BORO
    python build_composites.py --year 2020 --season BORO --max-scenes 6
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.windows import from_bounds

REPO_ROOT = Path(__file__).resolve().parents[3]
BOUNDARY_GPKG = REPO_ROOT / "boundaries" / "rcc_zones.gpkg"
SCENE_CSV = REPO_ROOT / "tables" / "scene_inventory_scenes.csv"
TABLE_DIR = REPO_ROOT / "tables"

PC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"
PC_SAS = "https://planetarycomputer.microsoft.com/api/sas/v1/token/landsat-c2-l2"
CRS = "EPSG:32645"
RES = 30.0
BANDS = ("blue", "green", "red", "nir08", "swir16", "swir22")
SEASONS = {
    "BORO": ((11, 1), (4, 30), -1),
    "AUS": ((5, 1), (8, 31), 0),
    "AMAN": ((6, 1), (11, 30), 0),
}
REFLECTANCE_SCALE = 0.0000275
REFLECTANCE_OFFSET = -0.2
OUT_BANDS = (
    "blue", "green", "red", "nir08", "swir16", "swir22",
    "ndvi_median", "lswi_median", "ndvi_max", "ndvi_min", "ndvi_amplitude", "lswi_max",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def season_window(year: int, season: str) -> tuple[date, date]:
    (sm, sd), (em, ed), offset = SEASONS[season]
    return date(year + offset, sm, sd), date(year, em, ed)


def grid() -> tuple[object, int, int, tuple[float, float, float, float]]:
    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    bounds = zones[zones["zone_id"] == "RCC_10"].total_bounds
    xmin = math.floor(bounds[0] / RES) * RES
    ymin = math.floor(bounds[1] / RES) * RES
    xmax = math.ceil(bounds[2] / RES) * RES
    ymax = math.ceil(bounds[3] / RES) * RES
    width = int(round((xmax - xmin) / RES))
    height = int(round((ymax - ymin) / RES))
    return from_origin(xmin, ymax, RES, RES), width, height, (xmin, ymin, xmax, ymax)


def get_token() -> str:
    response = requests.get(PC_SAS, timeout=60)
    response.raise_for_status()
    return response.json()["token"]


def sign(href: str, token: str) -> str:
    separator = "&" if "?" in href else "?"
    return f"{href}{separator}{token}"


def fetch_items(scene_ids: list[str], token: str) -> dict[str, dict]:
    items: dict[str, dict] = {}
    for start in range(0, len(scene_ids), 50):
        chunk = scene_ids[start : start + 50]
        response = requests.post(
            f"{PC_API}/search",
            json={"collections": ["landsat-c2-l2"], "ids": chunk, "limit": len(chunk)},
            timeout=120,
        )
        response.raise_for_status()
        for feature in response.json().get("features", []):
            items[feature["id"]] = feature
    return items


def read_band(asset: dict, token: str, transform, width: int, height: int, fill: int) -> np.ndarray:
    with rasterio.open(sign(asset["href"], token)) as src:
        bounds = rasterio.transform.array_bounds(height, width, transform)
        window = from_bounds(*bounds, src.transform)
        data = src.read(
            1, window=window, boundless=True, fill_value=fill, masked=False
        )
        src_transform = src.window_transform(window)
        destination = np.full((height, width), fill, dtype=data.dtype)
        reproject(
            source=data,
            destination=destination,
            src_transform=src_transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=CRS,
            resampling=Resampling.nearest,
            src_nodata=fill,
            dst_nodata=fill,
        )
    return destination


def index(red, nir, swir16, blue=None):
    with np.errstate(divide="ignore", invalid="ignore"):
        denominator_ndvi = nir + red
        denominator_lswi = nir + swir16
        ndvi = np.where(np.abs(denominator_ndvi) > 1e-6, (nir - red) / denominator_ndvi, np.nan)
        lswi = np.where(np.abs(denominator_lswi) > 1e-6, (nir - swir16) / denominator_lswi, np.nan)
    return np.clip(ndvi, -1.0, 1.0), np.clip(lswi, -1.0, 1.0)


def process_scene(item: dict, token: str, transform, width: int, height: int) -> np.ndarray:
    qa = read_band(item["assets"]["qa_pixel"], token, transform, width, height, fill=1)
    radsat = read_band(item["assets"]["qa_radsat"], token, transform, width, height, fill=1)
    invalid = (qa & 1) | (qa & 2) | (qa & 4) | (qa & 8) | (qa & 16) | (qa & 32)
    mask = (invalid == 0) & (radsat == 0)

    stack = np.full((len(BANDS), height, width), np.nan, dtype=np.float32)
    for position, band in enumerate(BANDS):
        raw = read_band(item["assets"][band], token, transform, width, height, fill=0).astype(np.float32)
        reflectance = raw * REFLECTANCE_SCALE + REFLECTANCE_OFFSET
        good = mask & (raw > 0)
        reflectance[~good] = np.nan
        stack[position] = reflectance
    return stack


def write_raster(path: Path, array: np.ndarray, transform, count: int, dtype: str, nodata, descriptions):
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": array.shape[1],
        "width": array.shape[2],
        "count": count,
        "dtype": dtype,
        "crs": CRS,
        "transform": transform,
        "nodata": nodata,
        "compress": "deflate",
        "predictor": 2 if dtype == "float32" else 1,
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "BIGTIFF": "IF_SAFER",
    }
    with rasterio.open(path, "w", **profile) as destination:
        destination.write(array.astype(dtype))
        destination.descriptions = tuple(descriptions)
        destination.build_overviews([2, 4, 8], Resampling.average)
        destination.update_tags(ns="rio_overview", resampling="average")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--season", choices=sorted(SEASONS), required=True)
    parser.add_argument("--max-scenes", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    raster_dir = data_root / "rasters" / "composites"
    manifest_dir = data_root / "manifests"
    raster_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    composite_path = raster_dir / f"composite_{args.year}_{args.season}_30m.tif"
    support_path = raster_dir / f"obs_support_{args.season}_{args.year}_30m.tif"
    by_pixel_manifest = manifest_dir / f"composite_{args.year}_{args.season}.json"
    if composite_path.exists() and not args.force:
        print(f"Refusing to overwrite existing composite: {composite_path}", file=sys.stderr)
        return 2

    scenes = pd.read_csv(SCENE_CSV)
    scenes = scenes[
        (scenes["collection"] == "landsat-c2-l2")
        & (scenes["reference_year"] == args.year)
        & (scenes["season"] == args.season)
    ].sort_values("datetime")
    if args.max_scenes:
        scenes = scenes.head(args.max_scenes)
    if scenes.empty:
        print("No scenes found for this year and season.", file=sys.stderr)
        return 3
    scene_ids = scenes["scene_id"].tolist()

    transform, width, height, bounds = grid()
    print(f"Grid {width} x {height} px, EPSG:32645")
    print(f"Scenes: {len(scene_ids)}  ({scene_ids[0]} .. {scene_ids[-1]})")

    token = get_token()
    items = fetch_items(scene_ids, token)
    print(f"Resolved {len(items)} of {len(scene_ids)} items on Planetary Computer")

    accum: list[np.ndarray] = []
    ndvi_max = np.full((height, width), np.nan, dtype=np.float32)
    ndvi_min = np.full((height, width), np.nan, dtype=np.float32)
    lswi_max = np.full((height, width), np.nan, dtype=np.float32)
    valid_obs = np.zeros((height, width), dtype=np.uint16)
    used = []
    failed = []

    for position, scene_id in enumerate(scene_ids):
        item = items.get(scene_id)
        if item is None:
            failed.append(scene_id)
            continue
        try:
            stack = process_scene(item, token, transform, width, height)
        except Exception as exc:  # noqa: BLE001 - log and continue
            failed.append(f"{scene_id}: {exc}")
            print(f"  WARN {scene_id}: {exc}", file=sys.stderr)
            continue
        accum.append(stack)
        ndvi, lswi = index(stack[2], stack[3], stack[4])
        with np.errstate(invalid="ignore"):
            ndvi_max = np.fmax(ndvi_max, ndvi)
            ndvi_min = np.fmin(ndvi_min, ndvi)
            lswi_max = np.fmax(lswi_max, lswi)
        valid_obs += np.isfinite(stack[0]).astype(np.uint16)
        used.append(scene_id)
        if (position + 1) % 5 == 0 or position == len(scene_ids) - 1:
            print(f"  {position + 1}/{len(scene_ids)} scenes processed")

    if not used:
        print("No scenes could be read.", file=sys.stderr)
        return 4

    count = len(used)
    with np.errstate(invalid="ignore"):
        median = np.nanmedian(np.stack(accum), axis=0)
    ndvi_median, lswi_median = index(median[2], median[3], median[4])

    out = np.concatenate(
        [
            median,
            np.stack([ndvi_median, lswi_median, ndvi_max, ndvi_min, ndvi_max - ndvi_min, lswi_max]),
        ],
        axis=0,
    )
    out[~np.isfinite(out)] = np.nan

    write_raster(composite_path, out, transform, len(OUT_BANDS), "float32", np.nan, OUT_BANDS)
    write_raster(
        support_path,
        valid_obs[np.newaxis, :, :],
        transform,
        1,
        "uint16",
        0,
        ["valid_observations"],
    )

    start, end = season_window(args.year, args.season)
    map_id = f"{args.year}_{args.season}_landsat"
    summary = {
        "map_id": map_id,
        "reference_year": args.year,
        "season": args.season,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "sensors": "landsat",
        "scene_count_requested": len(scene_ids),
        "scene_count_used": count,
        "scenes_used": used,
        "scenes_failed": failed,
        "grid": {"crs": CRS, "resolution_m": RES, "width": width, "height": height, "bounds": bounds},
        "valid_obs_summary": {
            "min": int(valid_obs.min()),
            "median": float(np.median(valid_obs)),
            "mean": round(float(valid_obs.mean()), 2),
            "max": int(valid_obs.max()),
            "zero_pixels": int((valid_obs == 0).sum()),
        },
        "low_support": bool(np.median(valid_obs) < 3),
        "outputs": {
            str(composite_path): sha256_file(composite_path),
            str(support_path): sha256_file(support_path),
        },
        "generated_utc": utc_now(),
    }
    by_pixel_manifest.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    row = {
        "reference_year": args.year,
        "season": args.season,
        "map_id": map_id,
        "scenes_used": count,
        "scenes_failed": len(failed),
        "obs_median": summary["valid_obs_summary"]["median"],
        "obs_mean": summary["valid_obs_summary"]["mean"],
        "obs_zero_pixels": summary["valid_obs_summary"]["zero_pixels"],
        "low_support": int(summary["low_support"]),
        "composite_path": str(composite_path),
    }
    summary_csv = TABLE_DIR / "composite_summary.csv"
    frame = pd.DataFrame([row])
    if summary_csv.exists():
        existing = pd.read_csv(summary_csv)
        existing = existing[~((existing.reference_year == args.year) & (existing.season == args.season))]
        frame = pd.concat([existing, frame], ignore_index=True).sort_values(["reference_year", "season"])
    frame.to_csv(summary_csv, index=False)

    print()
    print(f"used scenes: {count}/{len(scene_ids)}  failed: {len(failed)}")
    print(f"valid obs: min={summary['valid_obs_summary']['min']} "
          f"median={summary['valid_obs_summary']['median']} "
          f"max={summary['valid_obs_summary']['max']} "
          f"zero_pixels={summary['valid_obs_summary']['zero_pixels']}")
    print(f"low_support: {summary['low_support']}")
    print(f"composite: {composite_path}")
    print(f"support:   {support_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
