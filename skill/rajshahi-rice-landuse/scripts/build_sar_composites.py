#!/usr/bin/env python3
"""Build Sentinel-1 SAR seasonal features on the study grid.

Reads Sentinel-1 RTC gamma0 (VV, VH) from Planetary Computer, reprojects to the
30 m study grid in EPSG:32645, converts to dB, and writes seasonal statistics.

Bands
-----
vv_db, vh_db, ratio_db (VH - VV), vh_min_db, vh_max_db, vh_std_db,
n_obs, low_vh_count (scenes with VH < -18 dB, a flooding heuristic)

Outputs (runtime root)
----------------------
rasters/sar/sar_{YEAR}_{SEASON}_30m.tif
manifests/sar_{YEAR}_{SEASON}.json

Repository output
-----------------
tables/sar_summary.csv

Usage
-----
    python build_sar_composites.py --year 2020 --season AMAN
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
TABLE_DIR = REPO_ROOT / "tables"
PC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"
PC_SAS = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-1-rtc"
CRS = "EPSG:32645"
RES = 30.0
SEASONS = {
    "BORO": ((11, 1), (4, 30), -1),
    "AUS": ((5, 1), (8, 31), 0),
    "AMAN": ((6, 1), (11, 30), 0),
}
FLOOD_DB = -18.0
AOI_BBOX_4326 = [88.4433, 24.2601, 88.7674, 24.5075]
OUT_BANDS = (
    "vv_db", "vh_db", "ratio_db", "vh_min_db", "vh_max_db", "vh_std_db",
    "n_obs", "low_vh_count",
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


def grid():
    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    bounds = zones[zones["zone_id"] == "RCC_10"].total_bounds
    xmin = math.floor(bounds[0] / RES) * RES
    ymin = math.floor(bounds[1] / RES) * RES
    xmax = math.ceil(bounds[2] / RES) * RES
    ymax = math.ceil(bounds[3] / RES) * RES
    width = int(round((xmax - xmin) / RES))
    height = int(round((ymax - ymin) / RES))
    return from_origin(xmin, ymax, RES, RES), width, height, (xmin, ymin, xmax, ymax)


def search(start: date, end: date, bbox) -> list[dict]:
    body = {
        "collections": ["sentinel-1-rtc"],
        "bbox": bbox,
        "datetime": f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T23:59:59Z",
        "limit": 200,
    }
    response = requests.post(f"{PC_API}/search", json=body, timeout=120)
    response.raise_for_status()
    payload = response.json()
    features = list(payload.get("features", []))
    while True:
        nxt = next((l for l in payload.get("links", []) if l.get("rel") == "next"), None)
        if not nxt:
            break
        if str(nxt.get("method", "GET")).upper() == "POST":
            body2 = dict(nxt.get("body") or {})
            response = requests.post(f"{PC_API}/search", json=body2, timeout=120)
        else:
            response = requests.get(nxt["href"], timeout=120)
        response.raise_for_status()
        payload = response.json()
        features.extend(payload.get("features", []))
    return features


def read_band(asset: dict, token: str, transform, width: int, height: int) -> np.ndarray:
    with rasterio.open(f"{asset['href']}{'&' if '?' in asset['href'] else '?'}{token}") as source:
        bounds = rasterio.transform.array_bounds(height, width, transform)
        window = from_bounds(*bounds, source.transform)
        data = source.read(1, window=window, boundless=True, fill_value=np.nan, masked=False)
        source_transform = source.window_transform(window)
        destination = np.full((height, width), np.nan, dtype=np.float32)
        reproject(
            source=data.astype(np.float32),
            destination=destination,
            src_transform=source_transform,
            src_crs=source.crs,
            dst_transform=transform,
            dst_crs=CRS,
            resampling=Resampling.average,
            src_nodata=-32768.0,
            dst_nodata=np.nan,
        )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--season", choices=sorted(SEASONS), required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    out_dir = data_root / "rasters" / "sar"
    manifest_dir = data_root / "manifests"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"sar_{args.year}_{args.season}_30m.tif"
    if out_path.exists() and not args.force:
        print(f"Refusing to overwrite existing SAR product: {out_path}", file=sys.stderr)
        return 2

    transform, width, height, bounds = grid()
    start, end = season_window(args.year, args.season)
    features = search(start, end, AOI_BBOX_4326)
    print(f"{args.year} {args.season}: {len(features)} Sentinel-1 RTC scenes")
    if not features:
        print("No scenes.", file=sys.stderr)
        return 3

    token = requests.get(PC_SAS, timeout=60).json()["token"]
    vv_stack, vh_stack = [], []
    used, failed = [], []
    for feature in features:
        try:
            vv = read_band(feature["assets"]["vv"], token, transform, width, height)
            vh = read_band(feature["assets"]["vh"], token, transform, width, height)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{feature['id']}: {exc}")
            continue
        vv[~np.isfinite(vv) | (vv <= 0)] = np.nan
        vh[~np.isfinite(vh) | (vh <= 0)] = np.nan
        vv_stack.append(10 * np.log10(vv))
        vh_stack.append(10 * np.log10(vh))
        used.append(feature["id"])
        if len(used) % 5 == 0:
            print(f"  {len(used)}/{len(features)}")

    if not used:
        print("No scenes could be read.", file=sys.stderr)
        return 4

    vv_stack = np.stack(vv_stack)
    vh_stack = np.stack(vh_stack)
    with np.errstate(invalid="ignore"):
        vv_median = np.nanmedian(vv_stack, axis=0)
        vh_median = np.nanmedian(vh_stack, axis=0)
        vh_min = np.nanmin(vh_stack, axis=0)
        vh_max = np.nanmax(vh_stack, axis=0)
        vh_std = np.nanstd(vh_stack, axis=0)
    n_obs = np.isfinite(vh_stack).sum(axis=0).astype(np.float32)
    low_vh = (vh_stack < FLOOD_DB).sum(axis=0).astype(np.float32)
    low_vh[n_obs == 0] = np.nan

    out = np.stack(
        [vv_median, vh_median, vh_median - vv_median, vh_min, vh_max, vh_std, n_obs, low_vh]
    )

    profile = {
        "driver": "GTiff", "height": height, "width": width, "count": len(OUT_BANDS),
        "dtype": "float32", "crs": CRS, "transform": transform, "nodata": np.nan,
        "compress": "deflate", "predictor": 2, "tiled": True,
        "blockxsize": 512, "blockysize": 512, "BIGTIFF": "IF_SAFER",
    }
    with rasterio.open(out_path, "w", **profile) as destination:
        destination.write(out.astype("float32"))
        destination.descriptions = OUT_BANDS
        destination.build_overviews([2, 4, 8], Resampling.average)

    summary = {
        "artifact": "sentinel1_features",
        "reference_year": args.year,
        "season": args.season,
        "generated_utc": utc_now(),
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "scene_count_requested": len(features),
        "scene_count_used": len(used),
        "scenes_failed": failed,
        "flood_threshold_db": FLOOD_DB,
        "valid_obs_summary": {
            "median": float(np.nanmedian(n_obs)),
            "max": float(np.nanmax(n_obs)),
            "zero_pixels": int((n_obs == 0).sum()),
        },
        "output": {"path": str(out_path), "sha256": sha256_file(out_path)},
        "note": "VH < -18 dB is a heuristic flooding indicator, not a calibrated threshold.",
    }
    manifest_dir.joinpath(f"sar_{args.year}_{args.season}.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    row = {
        "reference_year": args.year,
        "season": args.season,
        "scenes_used": len(used),
        "scenes_failed": len(failed),
        "obs_median": summary["valid_obs_summary"]["median"],
        "zero_pixels": summary["valid_obs_summary"]["zero_pixels"],
        "sar_path": str(out_path),
    }
    csv_path = TABLE_DIR / "sar_summary.csv"
    frame = pd.DataFrame([row])
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        existing = existing[~((existing.reference_year == args.year) & (existing.season == args.season))]
        frame = pd.concat([existing, frame], ignore_index=True)
    frame.sort_values(["reference_year", "season"]).to_csv(csv_path, index=False)

    print(f"used {len(used)}/{len(features)} scenes; median observations "
          f"{summary['valid_obs_summary']['median']}")
    print(f"sar: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
