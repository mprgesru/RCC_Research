#!/usr/bin/env python3
"""Stratified accuracy and area estimation following Olofsson et al. (2014).

Supports two measurement modes:

- `--measure LULC`      validates the nine-class land-cover map
- `--measure BORO|AUS|AMAN` validates a seasonal rice map (rice / non-rice)

Labels are read from `tables/interpretation_sheet.csv`; the design key (map class,
stratum, coordinates) comes from the `reference_samples` layer. The estimator uses
the design strata weights, so the sample remains a probability sample.

If no labels are present the script reports the shortfall and exits without
producing numbers. It never fabricates labels.

Outputs
-------
tables/validation_{MEASURE}_{YEAR}.csv
tables/error_matrix_{MEASURE}_{YEAR}.csv
manifests/validation_{MEASURE}_{YEAR}.json

Usage
-----
    python validate.py --year 2020 --measure LULC
    python validate.py --year 2020 --measure AMAN
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask

REPO_ROOT = Path(__file__).resolve().parents[3]
BOUNDARY_GPKG = REPO_ROOT / "boundaries" / "rcc_zones.gpkg"
SHEET = REPO_ROOT / "tables" / "interpretation_sheet.csv"
TABLE_DIR = REPO_ROOT / "tables"
CRS = "EPSG:32645"
CLASS_NAMES = {
    1: "BORO", 2: "AUS", 3: "AMAN",
    4: "OTHER_CROPLAND", 5: "ORCHARD", 6: "OTHER_VEG",
    7: "BUILT", 8: "WATER", 9: "BARE",
}
TRUTHY = {"Y", "YES", "1", "TRUE", "T", "RICE"}
FALSY = {"N", "NO", "0", "FALSE", "F", "NON_RICE", "NONRICE"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalise_class(value: str) -> str:
    return str(value).strip().upper().replace(" ", "_")


def parse_rice(value) -> int | None:
    text = str(value).strip().upper().replace(" ", "_")
    if text in TRUTHY:
        return 1
    if text in FALSY:
        return 0
    return None


def design_weights(data_root: Path, year: int) -> tuple[dict, int]:
    lulc_path = data_root / "rasters" / "products" / f"lulc_{year}_30m.tif"
    with rasterio.open(lulc_path) as source:
        lulc = source.read(1)
        transform = source.transform
        shape = (source.height, source.width)

    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    groups = {"RCC": "RCC", "R0_5": "R0_5", "R5_10": "R5_10"}
    masks = {
        group: geometry_mask(
            [zones[zones["zone_id"] == zone_id].geometry.iloc[0]],
            out_shape=shape, transform=transform, invert=True, all_touched=False,
        )
        for zone_id, group in groups.items()
    }

    weights, total = {}, 0
    for code, name in CLASS_NAMES.items():
        for group, mask in masks.items():
            pixels = int(((lulc == code) & mask).sum())
            if pixels:
                weights[f"{name}|{group}"] = pixels
                total += pixels
    return {key: value / total for key, value in weights.items()}, total


def sample_points(data_root: Path, year: int) -> gpd.GeoDataFrame:
    db_path = data_root / "db" / "rajshahi_rice.gpkg"
    connection = sqlite3.connect(db_path)
    try:
        keys = pd.read_sql_query(
            "SELECT sample_id, stratum, map_class, zone_id FROM reference_samples "
            "WHERE reference_year = ?",
            connection, params=(year,),
        )
    finally:
        connection.close()
    geometry = gpd.read_file(db_path, layer="reference_samples")
    geometry = geometry[geometry["reference_year"] == year][["sample_id", "geometry"]].to_crs(CRS)
    merged = geometry.merge(keys.drop_duplicates("sample_id"), on="sample_id", how="left")
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--measure", default="LULC", choices=("LULC", "BORO", "AUS", "AMAN"))
    parser.add_argument("--sheet", default=str(SHEET))
    parser.add_argument("--out-dir", default=str(TABLE_DIR))
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    sheet = Path(args.sheet)
    if not sheet.exists():
        print(f"Interpretation sheet not found: {sheet}", file=sys.stderr)
        return 2

    points = sample_points(data_root, args.year)
    labels = pd.read_csv(sheet, dtype=str).fillna("")
    labels = labels[labels["reference_year"].astype(str) == str(args.year)]
    frame = points.merge(labels, on="sample_id", how="left", suffixes=("", "_label"))
    print(f"samples in design: {len(frame)}")

    if args.measure == "LULC":
        frame["reference"] = frame["reference_class"].map(normalise_class)
        frame = frame[frame["reference"].isin(set(CLASS_NAMES.values()))]
        frame["map_value"] = frame["map_class"].map(normalise_class)
    else:
        column = f"{args.measure.lower()}_rice"
        frame["reference_value"] = frame[column].map(parse_rice)
        frame = frame[frame["reference_value"].notna()]
        class_path = data_root / "rasters" / "products" / f"rice_class_{args.measure}_{args.year}_30m.tif"
        if not class_path.exists():
            print(f"Missing seasonal class raster: {class_path}", file=sys.stderr)
            return 3
        with rasterio.open(class_path) as source:
            values = np.array(
                [next(source.sample([(geom.x, geom.y)]))[0] for geom in frame.geometry],
                dtype=np.int16,
            )
        frame["map_value"] = np.where(values == 1, "RICE", "NON_RICE")
        frame.loc[values == 255, "map_value"] = None
        frame["reference"] = np.where(frame["reference_value"] == 1, "RICE", "NON_RICE")
        frame = frame[frame["map_value"].notna()]

    print(f"interpreted samples for {args.measure}: {len(frame)}")
    if frame.empty:
        print()
        print("No interpreted samples for this measure. Nothing can be estimated.")
        print("Fill the sheet and rerun.")
        return 0
    if len(frame) < len(points):
        print(f"WARNING: {len(points) - len(frame)} samples unlabelled or not applicable; "
              "estimates may be biased if missingness is not random.", file=sys.stderr)

    weights, total_pixels = design_weights(data_root, args.year)
    frame["stratum_key"] = frame["map_class"].map(normalise_class) + "|" + frame["zone_id"]
    missing = sorted(set(frame["stratum_key"]) - set(weights))
    if missing:
        print(f"ERROR: strata absent from the map: {missing}", file=sys.stderr)
        return 4

    map_classes = sorted(frame["map_value"].dropna().unique())
    ref_classes = sorted(frame["reference"].dropna().unique())
    p = pd.DataFrame(0.0, index=map_classes, columns=ref_classes)
    for stratum, group in frame.groupby("stratum_key"):
        weight = weights[stratum]
        n_h = len(group)
        for (map_value, reference), count in group.groupby(["map_value", "reference"]).size().items():
            p.loc[map_value, reference] += weight * count / n_h
    p = p / p.to_numpy().sum()

    overall = float(np.trace(p.to_numpy()))
    map_totals = p.sum(axis=1)
    ref_totals = p.sum(axis=0)
    ua = {c: (p.loc[c, c] / map_totals[c]) if map_totals[c] else np.nan for c in map_classes}
    pa = {c: (p.loc[c, c] / ref_totals[c]) if ref_totals[c] else np.nan for c in ref_classes}
    f1 = {
        c: (2 * ua[c] * pa[c] / (ua[c] + pa[c]))
        if c in ua and c in pa and ua[c] and pa[c]
        else np.nan
        for c in ref_classes
    }

    variance_overall = 0.0
    for stratum, group in frame.groupby("stratum_key"):
        weight = weights[stratum]
        n_h = len(group)
        if n_h < 2:
            continue
        correct = float((group["map_value"] == group["reference"]).mean())
        variance_overall += weight**2 * correct * (1 - correct) / (n_h - 1)
    overall_se = math.sqrt(max(variance_overall, 0.0))

    se = {}
    for ref_class in ref_classes:
        variance = 0.0
        for stratum, group in frame.groupby("stratum_key"):
            weight = weights[stratum]
            n_h = len(group)
            if n_h < 2:
                continue
            n_hj = int((group["reference"] == ref_class).sum())
            proportion = n_hj / n_h
            variance += weight**2 * proportion * (1 - proportion) / (n_h - 1)
        se[ref_class] = math.sqrt(max(variance, 0.0))

    total_area_ha = total_pixels * 0.09
    rows = []
    for ref_class in ref_classes:
        rows.append(
            {
                "measure": args.measure,
                "class": ref_class,
                "sample_n": int((frame["reference"] == ref_class).sum()),
                "mapped_n": int((frame["map_value"] == ref_class).sum()),
                "p_area": round(float(ref_totals[ref_class]), 6),
                "area_ha": round(float(ref_totals[ref_class]) * total_area_ha, 1),
                "ci95_lower_ha": round(max(float(ref_totals[ref_class]) - 1.96 * se[ref_class], 0) * total_area_ha, 1),
                "ci95_upper_ha": round((float(ref_totals[ref_class]) + 1.96 * se[ref_class]) * total_area_ha, 1),
                "se_p": round(se[ref_class], 6),
                "ua": None if pd.isna(ua.get(ref_class)) else round(float(ua[ref_class]), 4),
                "pa": None if pd.isna(pa.get(ref_class)) else round(float(pa[ref_class]), 4),
                "f1": None if pd.isna(f1.get(ref_class)) else round(float(f1[ref_class]), 4),
            }
        )

    metrics = pd.DataFrame(rows)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = out_dir / f"validation_{args.measure}_{args.year}.csv"
    metrics.to_csv(metrics_path, index=False)
    matrix_path = out_dir / f"error_matrix_{args.measure}_{args.year}.csv"
    p.round(6).to_csv(matrix_path)

    manifest = {
        "artifact": "validation",
        "reference_year": args.year,
        "measure": args.measure,
        "generated_utc": utc_now(),
        "method": "Olofsson et al. (2014) stratified estimator, area proportions",
        "design_samples": int(len(points)),
        "interpreted_samples": int(len(frame)),
        "strata": int(len(weights)),
        "total_area_ha": round(total_area_ha, 1),
        "overall_accuracy": round(overall, 4),
        "overall_accuracy_se": round(overall_se, 4),
        "overall_accuracy_ci95": [
            round(max(overall - 1.96 * overall_se, 0), 4),
            round(min(overall + 1.96 * overall_se, 1), 4),
        ],
        "class_metrics": rows,
        "outputs": [str(metrics_path), str(matrix_path)],
        "warning": (
            None if len(frame) == len(points)
            else f"{len(points) - len(frame)} samples unlabelled or not applicable"
        ),
    }
    (data_root / "manifests").mkdir(parents=True, exist_ok=True)
    (data_root / "manifests" / f"validation_{args.measure}_{args.year}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print()
    print(f"overall accuracy: {overall:.4f} (SE {overall_se:.4f})")
    print(metrics.to_string(index=False))
    print(f"\nmetrics: {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
