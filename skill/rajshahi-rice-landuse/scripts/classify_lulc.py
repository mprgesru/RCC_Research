#!/usr/bin/env python3
"""Derive general land cover for transition attribution (protocol Step 5).

Builds a 9-class land-cover layer per target year from the seasonal composites
and the provisional rice products. Class codes follow the data dictionary:

    1 Boro rice, 2 Aus rice, 3 Aman rice
    4 other annual crop / fallow, 5 orchard / perennial
    6 other vegetation, 7 built-up, 8 water, 9 bare
    255 no data

Rule order is deliberate: rice first (from the seasonal products), then water,
built-up, bare, orchard, other cropland, other vegetation.

This is a derived, provisional product. It is not validated and must be replaced
or confirmed with reference samples before transitions are interpreted.

Outputs (runtime root)
----------------------
rasters/products/lulc_{YEAR}_30m.tif
manifests/lulc_{YEAR}.json

Repository output
-----------------
tables/lulc_class_fractions.csv

Usage
-----
    python classify_lulc.py --year 2020
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling

REPO_ROOT = Path(__file__).resolve().parents[3]
TABLE_DIR = REPO_ROOT / "tables"
SEASONS = ("BORO", "AUS", "AMAN")
MODEL_VERSION = "lulc-rules-0.1.0-provisional"
CLASS_NAMES = {
    1: "Boro", 2: "Aus", 3: "Aman",
    4: "Other annual crop", 5: "Orchard", 6: "Other vegetation",
    7: "Built-up", 8: "Water", 9: "Bare", 255: "No data",
}
PIXEL_HA = 0.09


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path, name: str) -> np.ndarray:
    with rasterio.open(path) as source:
        return source.read(source.descriptions.index(name) + 1)


def normalised_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        result = (a - b) / (a + b)
    return np.clip(result, -1.0, 1.0)


def write_lulc(path: Path, array: np.ndarray, profile: dict) -> None:
    profile = dict(profile)
    profile.update(
        driver="GTiff", count=1, dtype="uint8", nodata=255,
        compress="deflate", predictor=1, tiled=True,
        blockxsize=512, blockysize=512, BIGTIFF="IF_SAFER",
    )
    with rasterio.open(path, "w", **profile) as destination:
        destination.write(array.astype("uint8"), 1)
        destination.descriptions = ("lulc",)
        destination.build_overviews([2, 4, 8], Resampling.nearest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    composite_dir = data_root / "rasters" / "composites"
    product_dir = data_root / "rasters" / "products"
    manifest_dir = data_root / "manifests"
    product_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    lulc_path = product_dir / f"lulc_{args.year}_30m.tif"
    if lulc_path.exists() and not args.force:
        print(f"Refusing to overwrite existing land cover: {lulc_path}", file=sys.stderr)
        return 2

    # Annual spectral state from the median of the three seasonal medians.
    red, green, nir, swir16 = [], [], [], []
    profiles = []
    seasonal_ndvi = []
    valid_any = None
    for season in SEASONS:
        path = composite_dir / f"composite_{args.year}_{season}_30m.tif"
        if not path.exists():
            print(f"Missing composite: {path}", file=sys.stderr)
            return 3
        red.append(read(path, "red"))
        green.append(read(path, "green"))
        nir.append(read(path, "nir08"))
        swir16.append(read(path, "swir16"))
        seasonal_ndvi.append(read(path, "ndvi_median"))
        with rasterio.open(path) as source:
            profiles.append(source.profile.copy())

    red = np.nanmedian(np.stack(red), axis=0)
    green = np.nanmedian(np.stack(green), axis=0)
    nir = np.nanmedian(np.stack(nir), axis=0)
    swir16 = np.nanmedian(np.stack(swir16), axis=0)

    ndvi = normalised_difference(nir, red)
    ndwi = normalised_difference(green, nir)
    ndbi = normalised_difference(swir16, nir)
    ndvi_stack = np.stack(seasonal_ndvi)
    amplitude = np.nanmax(ndvi_stack, axis=0) - np.nanmin(ndvi_stack, axis=0)

    union_path = product_dir / f"rice_union_{args.year}_30m.tif"
    if not union_path.exists():
        print(f"Missing rice union: {union_path}", file=sys.stderr)
        return 4
    with rasterio.open(union_path) as source:
        union = source.read(1)
        profile = source.profile.copy()

    class_paths = {
        season: product_dir / f"rice_class_{season}_{args.year}_30m.tif" for season in SEASONS
    }
    prob_paths = {
        season: product_dir / f"rice_prob_{season}_{args.year}_30m.tif" for season in SEASONS
    }
    for path in list(class_paths.values()) + list(prob_paths.values()):
        if not path.exists():
            print(f"Missing seasonal product: {path}", file=sys.stderr)
            return 5

    rice_union = union == 1
    # Dominant season among seasons classified as rice, by probability.
    best_prob = np.full(union.shape, -1.0, dtype=np.float32)
    dominant = np.zeros(union.shape, dtype=np.uint8)
    for code, season in zip((1, 2, 3), SEASONS):
        classes = read(class_paths[season], f"rice_class_{season}")
        with rasterio.open(prob_paths[season]) as source:
            read_prob = source.read(1)
        selected = (classes == 1) & np.isfinite(read_prob) & (read_prob > best_prob)
        best_prob[selected] = read_prob[selected]
        dominant[selected] = code

    lulc = np.full(union.shape, 255, dtype=np.uint8)
    data = np.isfinite(ndvi)
    lulc[data] = 6

    water = data & (ndwi > 0.10) & (ndvi < 0.30)
    lulc[water] = 8
    built = data & ~water & (ndbi > 0.05) & (ndvi < 0.35)
    lulc[built] = 7
    bare = data & ~water & ~built & (ndvi < 0.25) & (ndbi <= 0.05)
    lulc[bare] = 9
    orchard = data & (lulc == 6) & (ndvi >= 0.50) & (amplitude < 0.25)
    lulc[orchard] = 5
    other_crop = data & (lulc == 6) & ~orchard & (amplitude >= 0.25)
    lulc[other_crop] = 4
    lulc[rice_union] = dominant[rice_union]
    lulc[rice_union & (dominant == 0)] = 1

    write_lulc(lulc_path, lulc, profile)

    counts = {code: int((lulc == code).sum()) for code in CLASS_NAMES}
    total_valid = int((lulc != 255).sum())
    manifest = {
        "artifact": "land_cover",
        "reference_year": args.year,
        "generated_utc": utc_now(),
        "model_version": MODEL_VERSION,
        "status": "provisional_unvalidated",
        "class_codes": CLASS_NAMES,
        "rules": {
            "water": "NDWI > 0.10 and NDVI < 0.30",
            "built_up": "NDBI > 0.05 and NDVI < 0.35",
            "bare": "NDVI < 0.25 and NDBI <= 0.05",
            "orchard": "NDVI >= 0.50 and seasonal NDVI amplitude < 0.25",
            "other_annual_crop": "seasonal NDVI amplitude >= 0.25",
            "other_vegetation": "remaining valid pixels",
            "rice": "seasonal rice union; dominant season by probability",
        },
        "valid_pixels": total_valid,
        "class_pixels": counts,
        "class_fractions": {
            CLASS_NAMES[code]: round(value / total_valid, 4) if total_valid else None
            for code, value in counts.items()
        },
        "output": {"path": str(lulc_path), "sha256": sha256_file(lulc_path)},
        "limitations": [
            "Derived from indices, not a trained classifier.",
            "Not validated against reference samples.",
            "Mango orchard separation is heuristic and unconfirmed.",
            "Rice classes come from the provisional rice products.",
        ],
    }
    manifest_dir.joinpath(f"lulc_{args.year}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    rows = []
    for code, value in counts.items():
        rows.append(
            {
                "reference_year": args.year,
                "class_code": code,
                "class_name": CLASS_NAMES[code],
                "pixels": value,
                "area_ha": round(value * PIXEL_HA, 3),
                "fraction_of_valid": round(value / total_valid, 4) if total_valid else None,
            }
        )
    frame = pd.DataFrame(rows)
    csv_path = TABLE_DIR / "lulc_class_fractions.csv"
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        existing = existing[existing.reference_year != args.year]
        frame = pd.concat([existing, frame], ignore_index=True)
    frame.sort_values(["reference_year", "class_code"]).to_csv(csv_path, index=False)

    print(f"valid pixels: {total_valid}")
    for code, value in counts.items():
        if value:
            print(f"  {code:3} {CLASS_NAMES[code]:20} {value:8} "
                  f"({100 * value / max(total_valid, 1):5.1f}%)")
    print(f"lulc: {lulc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
