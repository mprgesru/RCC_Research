#!/usr/bin/env python3
"""Benchmark our rice maps against published products (protocol Step 6).

Compares the study union map with externally downloaded products at overlapping
years, reporting agreement, intersection-over-union and rice fraction by zone.

File hosts for GCD-Rice, Zhao et al. and Singha et al. return HTTP 403 from the
build host, so the products must be downloaded manually. Put files under:

    ${RAJSHAHI_RICE_DATA_ROOT}/external/
        zhao/South and Southeast Asia Paddy Rice 2015.tif
        zhao/...
        singha/Boro_BGD_2017_V1.tif
        singha/...
        gcd_rice/<year>/<season>.tif

Products are benchmarks, not truth. Agreement is not accuracy.

Output
------
tables/benchmark_products.csv
manifests/benchmark.json

Usage
-----
    python benchmark_products.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject

REPO_ROOT = Path(__file__).resolve().parents[3]
BOUNDARY_GPKG = REPO_ROOT / "boundaries" / "rcc_zones.gpkg"
TABLE_DIR = REPO_ROOT / "tables"
CRS = "EPSG:32645"
AOI_BBOX = (88.4433, 24.2601, 88.7674, 24.5075)

PRODUCTS = [
    {"name": "Zhao 2026 (2015)", "file": "zhao/South and Southeast Asia Paddy Rice 2015.tif",
     "year": 2015, "rice_values": [1], "season": "ALL_UNION"},
    {"name": "Zhao 2026 (2005)", "file": "zhao/South and Southeast Asia Paddy Rice 2005.tif",
     "year": 2005, "rice_values": [1], "season": "ALL_UNION"},
    {"name": "Zhao 2026 (1995)", "file": "zhao/South and Southeast Asia Paddy Rice 1995.tif",
     "year": 1995, "rice_values": [1], "season": "ALL_UNION"},
    {"name": "Zhao 2026 (2024~2025)", "file": "zhao/South and Southeast Asia Paddy Rice 2024.tif",
     "year": 2025, "rice_values": [1], "season": "ALL_UNION"},
    {"name": "Singha 2017 Boro", "file": "singha/Boro_BGD_2017_V1.tif",
     "year": 2015, "rice_values": [1], "season": "BORO"},
    {"name": "Singha 2017 Aus", "file": "singha/Aus_BGD_2017_V1.tif",
     "year": 2015, "rice_values": [1], "season": "AUS"},
    {"name": "Singha 2017 Aman", "file": "singha/Aman_BGD_2017_V1.tif",
     "year": 2015, "rice_values": [1], "season": "AMAN"},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_on_grid(path: Path, reference: Path) -> np.ndarray:
    with rasterio.open(reference) as ref:
        transform, shape = ref.transform, (ref.height, ref.width)
    with rasterio.open(path) as source:
        window = rasterio.windows.from_bounds(*AOI_BBOX, source.transform)
        try:
            data = source.read(1, window=window, boundless=True, fill_value=0)
            src_transform = source.window_transform(window)
            destination = np.zeros(shape, dtype=np.float32)
            reproject(
                source=data.astype(np.float32), destination=destination,
                src_transform=src_transform, src_crs=source.crs,
                dst_transform=transform, dst_crs=CRS,
                resampling=Resampling.nearest,
            )
        except Exception:
            # Fall back to a full read and reproject.
            data = source.read(1).astype(np.float32)
            destination = np.zeros(shape, dtype=np.float32)
            reproject(
                source=data, destination=destination,
                src_transform=source.transform, src_crs=source.crs,
                dst_transform=transform, dst_crs=CRS,
                resampling=Resampling.nearest,
            )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    runtime = Path(args.data_root).expanduser().resolve()
    external = runtime / "external"
    products_dir = runtime / "rasters" / "products"
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    reference = products_dir / "rice_union_2020_30m.tif"
    with rasterio.open(reference) as source:
        transform, shape = source.transform, (source.height, source.width)
    masks = {
        row["zone_id"]: geometry_mask(
            [row.geometry], out_shape=shape, transform=transform, invert=True, all_touched=False
        )
        for _, row in zones.iterrows()
    }

    rows = []
    missing = []
    for spec in PRODUCTS:
        path = external / spec["file"]
        if not path.exists():
            missing.append(spec["file"])
            continue
        product = load_on_grid(path, reference)
        product_rice = np.isin(product.astype(np.int64), spec["rice_values"])

        union_path = products_dir / f"rice_union_{spec['year']}_30m.tif"
        if spec["season"] != "ALL_UNION":
            union_path = products_dir / f"rice_class_{spec['season']}_{spec['year']}_30m.tif"
        if not union_path.exists():
            missing.append(f"our {union_path.name}")
            continue
        with rasterio.open(union_path) as source:
            ours = source.read(1) == 1

        for zone_id, mask in masks.items():
            a, b = ours & mask, product_rice & mask
            if not mask.any():
                continue
            inter = int((a & b).sum())
            union = int((a | b).sum())
            rows.append(
                {
                    "product": spec["name"],
                    "product_year": spec["year"],
                    "our_year": spec["year"],
                    "season": spec["season"],
                    "zone_id": zone_id,
                    "our_rice_fraction": round(float(a.sum() / mask.sum()), 4),
                    "product_rice_fraction": round(float(b.sum() / mask.sum()), 4),
                    "agreement": round(float(((a == b) & mask).sum() / mask.sum()), 4),
                    "iou": round(inter / union, 4) if union else None,
                }
            )
        print(f"compared: {spec['name']}")

    if not rows:
        print("No products found. Download them into:", file=sys.stderr)
        print(f"  {external}", file=sys.stderr)
        for item in missing[:10]:
            print(f"  missing: {item}", file=sys.stderr)
        return 0

    frame = pd.DataFrame(rows)
    path = TABLE_DIR / "benchmark_products.csv"
    frame.to_csv(path, index=False)
    (runtime / "manifests").mkdir(parents=True, exist_ok=True)
    (runtime / "manifests" / "benchmark.json").write_text(
        json.dumps({"generated_utc": utc_now(), "rows": len(frame),
                    "missing": missing, "note": "Agreement is not accuracy."}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"rows: {len(frame)}  ->  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
