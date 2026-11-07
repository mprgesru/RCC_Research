#!/usr/bin/env python3
"""Apply the provisional phenology rule set to seasonal composites.

Reads the seasonal composite and observation-support rasters, computes a rice
probability proxy and a binary rice class per season, then derives the all-rice
union and cropping intensity for the year. Writes mapped (unadjusted) areas per
zone.

This is a rule-based baseline. It is NOT a validated classifier: thresholds are
uncalibrated placeholders until reference samples exist. Every output is labelled
with `model_version = rules-0.1.0-provisional`.

Outputs (runtime root)
----------------------
rasters/products/rice_prob_{SEASON}_{YEAR}_30m.tif
rasters/products/rice_class_{SEASON}_{YEAR}_30m.tif
rasters/products/rice_union_{YEAR}_30m.tif
rasters/products/rice_intensity_{YEAR}_30m.tif
manifests/classify_{YEAR}.json

Repository output
-----------------
tables/area_estimates_mapped.csv

Usage
-----
    python classify.py --year 2020
"""

from __future__ import annotations

import argparse
import hashlib
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

REPO_ROOT = Path(__file__).resolve().parents[3]
THRESHOLDS_PATH = REPO_ROOT / "skill" / "rajshahi-rice-landuse" / "references" / "classification-thresholds.json"
BOUNDARY_GPKG = REPO_ROOT / "boundaries" / "rcc_zones.gpkg"
TABLE_DIR = REPO_ROOT / "tables"
CRS = "EPSG:32645"
PIXEL_HA = 0.09  # 30 m x 30 m
SEASONS = ("BORO", "AUS", "AMAN")
MODEL_VERSION = "rules-0.3.0-provisional"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_band(path: Path, description: str) -> np.ndarray:
    with rasterio.open(path) as source:
        index = source.descriptions.index(description) + 1
        return source.read(index)


def scaled(value: np.ndarray, floor: float, span: float) -> np.ndarray:
    return np.clip((value - floor) / span, 0.0, 1.0)


def write_raster(path: Path, array: np.ndarray, profile: dict, dtype: str, nodata, description: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = dict(profile)
    profile.update(
        driver="GTiff",
        count=1,
        dtype=dtype,
        nodata=nodata,
        compress="deflate",
        predictor=2 if dtype == "float32" else 1,
        tiled=True,
        blockxsize=512,
        blockysize=512,
        BIGTIFF="IF_SAFER",
    )
    with rasterio.open(path, "w", **profile) as destination:
        destination.write(array.astype(dtype), 1)
        destination.descriptions = (description,)
        destination.build_overviews([2, 4, 8], Resampling.average)


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

    thresholds = json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))
    weights = thresholds["score_weights"]
    scaling = thresholds["score_scaling"]

    union_path = product_dir / f"rice_union_{args.year}_30m.tif"
    if union_path.exists() and not args.force:
        print(f"Refusing to overwrite existing products: {union_path}", file=sys.stderr)
        return 2

    seasonal_classes = {}
    seasonal_valid = {}
    maps = []
    outputs = []

    for season in SEASONS:
        composite_path = composite_dir / f"composite_{args.year}_{season}_30m.tif"
        support_path = composite_dir / f"obs_support_{season}_{args.year}_30m.tif"
        if not composite_path.exists() or not support_path.exists():
            print(f"Missing composite for {args.year} {season}: {composite_path}", file=sys.stderr)
            return 3

        with rasterio.open(composite_path) as source:
            template = source
            lswi_max = source.read(source.descriptions.index("lswi_max") + 1)
            ndvi_amplitude = source.read(source.descriptions.index("ndvi_amplitude") + 1)
            ndvi_max = source.read(source.descriptions.index("ndvi_max") + 1)
            flood_obs = source.read(source.descriptions.index("flood_obs") + 1)
            profile = source.profile.copy()

        with rasterio.open(support_path) as source:
            support = source.read(1)

        valid = (
            (support > 0)
            & np.isfinite(lswi_max)
            & np.isfinite(ndvi_amplitude)
            & np.isfinite(ndvi_max)
            & np.isfinite(flood_obs)
        )
        flood_frac = np.divide(flood_obs, np.maximum(support, 1))

        score = (
            weights["flood_frac"] * scaled(flood_frac, scaling["flood_frac_floor"], scaling["flood_frac_span"])
            + weights["lswi_max"] * scaled(lswi_max, scaling["lswi_max_floor"], scaling["lswi_max_span"])
            + weights["ndvi_amplitude"] * scaled(ndvi_amplitude, scaling["ndvi_amplitude_floor"], scaling["ndvi_amplitude_span"])
            + weights["ndvi_max"] * scaled(ndvi_max, scaling["ndvi_max_floor"], scaling["ndvi_max_span"])
        )
        score = np.clip(np.nan_to_num(score, nan=0.0), 0.0, 1.0)
        score[~valid] = np.nan

        rule = thresholds["seasons"][season]
        rice = (
            valid
            & (flood_frac >= rule["flood_frac_min"])
            & (lswi_max >= rule["lswi_max"])
            & (ndvi_amplitude >= rule["ndvi_amplitude"])
            & (ndvi_max >= rule["ndvi_max"])
        )
        classes = np.full(rice.shape, 255, dtype=np.uint8)
        classes[valid] = 0
        classes[rice] = 1

        prob_path = product_dir / f"rice_prob_{season}_{args.year}_30m.tif"
        class_path = product_dir / f"rice_class_{season}_{args.year}_30m.tif"
        write_raster(prob_path, score, profile, "float32", np.nan, f"rice_prob_{season}")
        write_raster(class_path, classes, profile, "uint8", 255, f"rice_class_{season}")
        outputs.extend([prob_path, class_path])

        seasonal_classes[season] = rice
        seasonal_valid[season] = valid

        pixels_valid = int(valid.sum())
        pixels_rice = int(rice.sum())
        maps.append(
            {
                "map_id": f"{args.year}_{season}_{MODEL_VERSION}",
                "reference_year": args.year,
                "season": season,
                "model_name": "phenology_rules",
                "model_version": MODEL_VERSION,
                "thresholds": rule,
                "valid_pixels": pixels_valid,
                "rice_pixels": pixels_rice,
                "rice_fraction_of_valid": round(pixels_rice / pixels_valid, 4) if pixels_valid else None,
                "probability_median_where_valid": round(float(np.nanmedian(score)), 4),
            }
        )
        print(f"{season}: valid={pixels_valid} rice={pixels_rice} "
              f"({100 * pixels_rice / pixels_valid:.1f}% of valid)" if pixels_valid else f"{season}: no valid pixels")

    any_valid = np.logical_or.reduce([seasonal_valid[s] for s in SEASONS])
    union_rice = np.logical_or.reduce([seasonal_classes[s] for s in SEASONS]) & any_valid
    intensity = np.zeros(any_valid.shape, dtype=np.uint8)
    for season in SEASONS:
        intensity += (seasonal_classes[season] & seasonal_valid[season]).astype(np.uint8)
    intensity[~any_valid] = 255

    union_out = np.full(any_valid.shape, 255, dtype=np.uint8)
    union_out[any_valid] = 0
    union_out[union_rice] = 1

    union_path_out = product_dir / f"rice_union_{args.year}_30m.tif"
    intensity_path = product_dir / f"rice_intensity_{args.year}_30m.tif"
    write_raster(union_path_out, union_out, profile, "uint8", 255, "rice_union")
    write_raster(intensity_path, intensity, profile, "uint8", 255, "rice_intensity")
    outputs.extend([union_path_out, intensity_path])

    # Mapped area per zone and measure.
    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    with rasterio.open(union_path_out) as source:
        transform = source.transform
        shape = (source.height, source.width)

    rows = []
    for _, zone in zones.iterrows():
        inside = geometry_mask(
            [zone.geometry], out_shape=shape, transform=transform, invert=True, all_touched=False
        )
        for season in SEASONS:
            rice = seasonal_classes[season] & inside & seasonal_valid[season]
            rows.append(
                {
                    "reference_year": args.year,
                    "zone_id": zone["zone_id"],
                    "season_or_measure": season,
                    "mapped_area_ha": round(int(rice.sum()) * PIXEL_HA, 3),
                    "valid_land_area_ha": round(int((seasonal_valid[season] & inside).sum()) * PIXEL_HA, 3),
                    "map_id": f"{args.year}_{season}_{MODEL_VERSION}",
                }
            )
        rows.append(
            {
                "reference_year": args.year,
                "zone_id": zone["zone_id"],
                "season_or_measure": "ALL_UNION",
                "mapped_area_ha": round(int((union_rice & inside).sum()) * PIXEL_HA, 3),
                "valid_land_area_ha": round(int((any_valid & inside).sum()) * PIXEL_HA, 3),
                "map_id": f"{args.year}_ALL_UNION_{MODEL_VERSION}",
            }
        )
        for level in range(4):
            rows.append(
                {
                    "reference_year": args.year,
                    "zone_id": zone["zone_id"],
                    "season_or_measure": f"INTENSITY_{level}",
                    "mapped_area_ha": round(int(((intensity == level) & inside).sum()) * PIXEL_HA, 3),
                    "valid_land_area_ha": round(int((any_valid & inside).sum()) * PIXEL_HA, 3),
                    "map_id": f"{args.year}_INTENSITY_{MODEL_VERSION}",
                }
            )

    frame = pd.DataFrame(rows)
    csv_path = TABLE_DIR / "area_estimates_mapped.csv"
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        existing = existing[existing.reference_year != args.year]
        frame = pd.concat([existing, frame], ignore_index=True)
    frame.sort_values(["reference_year", "zone_id", "season_or_measure"]).to_csv(csv_path, index=False)

    manifest = {
        "artifact": "provisional_classification",
        "reference_year": args.year,
        "generated_utc": utc_now(),
        "model_name": "phenology_rules",
        "model_version": MODEL_VERSION,
        "status": "provisional_uncalibrated",
        "thresholds_file": str(THRESHOLDS_PATH.relative_to(REPO_ROOT)),
        "thresholds_version": thresholds["version"],
        "seasons": maps,
        "union_rice_pixels": int(union_rice.sum()),
        "valid_pixels": int(any_valid.sum()),
        "intensity_counts": {str(level): int((intensity == level).sum()) for level in range(4)},
        "outputs": [{"path": str(path), "sha256": sha256_file(path)} for path in outputs],
        "limitations": [
            "Thresholds are uncalibrated placeholders.",
            "No independent validation; do not report accuracy from this run.",
            "No land-cover classification yet, so transitions cannot be attributed.",
            "Sentinel comparison not included.",
        ],
    }
    manifest_dir.joinpath(f"classify_{args.year}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print()
    print(f"union rice pixels: {int(union_rice.sum())} "
          f"({100 * union_rice.sum() / max(int(any_valid.sum()), 1):.1f}% of valid)")
    print(f"intensity counts: {manifest['intensity_counts']}")
    print(f"areas written: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
