#!/usr/bin/env python3
"""Stratified accuracy and area estimation following Olofsson et al. (2014).

Reads interpreted samples from the `reference_samples` layer and reports:

- error matrix expressed as proportions of area
- overall, user's and producer's accuracy with standard errors
- class area estimates with 95% confidence intervals

Strata weights are recomputed from the map, not taken from the sample, so the
estimator stays consistent with the sampling design.

If no interpreted samples exist, the script reports the shortfall and exits
without producing numbers. It never fabricates labels.

Outputs
-------
tables/validation_{YEAR}.csv        Metrics and area estimates
manifests/validation_{YEAR}.json    Design and result record

Usage
-----
    python validate.py --year 2020
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
TABLE_DIR = REPO_ROOT / "tables"
CRS = "EPSG:32645"
CLASS_NAMES = {
    1: "BORO", 2: "AUS", 3: "AMAN",
    4: "OTHER_CROPLAND", 5: "ORCHARD", 6: "OTHER_VEG",
    7: "BUILT", 8: "WATER", 9: "BARE",
}
ALIASES = {
    "RICE": "RICE", "NON_RICE": "NON_RICE", "NONRICE": "NON_RICE",
    "BORO": "BORO", "AUS": "AUS", "AMAN": "AMAN",
    "OTHER_CROPLAND": "OTHER_CROPLAND", "ORCHARD": "ORCHARD",
    "OTHER_VEG": "OTHER_VEG", "BUILT": "BUILT", "WATER": "WATER", "BARE": "BARE",
    "BUILT-UP": "BUILT", "BUILTUP": "BUILT", "OTHER VEGETATION": "OTHER_VEG",
    "OTHER ANNUAL CROP": "OTHER_CROPLAND", "FALLOW": "OTHER_CROPLAND",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalise(value: str) -> str:
    key = str(value).strip().upper().replace(" ", "_")
    return ALIASES.get(key, key)


def strata_weights(data_root: Path, year: int):
    lulc_path = data_root / "rasters" / "products" / f"lulc_{year}_30m.tif"
    with rasterio.open(lulc_path) as source:
        lulc = source.read(1)
        transform = source.transform
        shape = (source.height, source.width)

    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    groups = {"RCC": "RCC", "R0_5": "R0_5", "R5_10": "R5_10"}
    masks = {}
    for zone_id, group in groups.items():
        masks[group] = geometry_mask(
            [zones[zones["zone_id"] == zone_id].geometry.iloc[0]],
            out_shape=shape, transform=transform, invert=True, all_touched=False,
        )

    weights = {}
    total = 0
    for code, name in CLASS_NAMES.items():
        for group, mask in masks.items():
            pixels = int(((lulc == code) & mask).sum())
            if pixels:
                weights[f"{name}|{group}"] = pixels
                total += pixels
    return {key: value / total for key, value in weights.items()}, total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--measure", default="ALL_UNION")
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    db_path = data_root / "db" / "rajshahi_rice.gpkg"
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 2

    connection = sqlite3.connect(db_path)
    try:
        samples = pd.read_sql_query(
            "SELECT sample_id, stratum, map_class, reference_class, confidence, split "
            "FROM reference_samples WHERE reference_year = ?",
            connection, params=(args.year,),
        )
    finally:
        connection.close()

    labelled = samples[samples["reference_class"].notna() & (samples["reference_class"].astype(str) != "")]
    print(f"samples in design: {len(samples)}")
    print(f"interpreted samples: {len(labelled)}")
    if labelled.empty:
        print()
        print("No interpreted samples. Nothing can be estimated.")
        print("Label reference_class in the reference_samples layer, then rerun.")
        return 0

    if len(labelled) < len(samples):
        print(f"WARNING: {len(samples) - len(labelled)} samples are unlabelled; "
              "estimates will be biased if missingness is not random.", file=sys.stderr)

    labelled = labelled.copy()
    labelled["map_class"] = labelled["map_class"].map(normalise)
    labelled["reference_class"] = labelled["reference_class"].map(normalise)
    labelled["stratum"] = labelled["map_class"] + "|" + labelled["stratum"].str.split("|").str[-1]

    weights, total_pixels = strata_weights(data_root, args.year)
    missing = sorted(set(labelled["stratum"]) - set(weights))
    if missing:
        print(f"ERROR: strata absent from the map: {missing}", file=sys.stderr)
        return 3

    map_classes = sorted(labelled["map_class"].unique())
    ref_classes = sorted(labelled["reference_class"].unique())
    p = pd.DataFrame(0.0, index=map_classes, columns=ref_classes)

    for stratum, group in labelled.groupby("stratum"):
        weight = weights[stratum]
        counts = group.groupby(["map_class", "reference_class"]).size()
        n_h = len(group)
        for (map_class, ref_class), count in counts.items():
            p.loc[map_class, ref_class] += weight * count / n_h

    # Normalise in case a stratum's sample does not cover all cells.
    p = p / p.to_numpy().sum()

    overall = float(np.trace(p.to_numpy()))
    map_totals = p.sum(axis=1)
    ref_totals = p.sum(axis=0)
    ua = {c: (p.loc[c, c] / map_totals[c]) if map_totals[c] else np.nan for c in map_classes}
    pa = {c: (p.loc[c, c] / ref_totals[c]) if ref_totals[c] else np.nan for c in ref_classes}
    f1 = {
        c: (2 * ua[c] * pa[c] / (ua[c] + pa[c]))
        if c in ua and c in pa and ua[c] and pa[c] and not math.isnan(ua[c]) and not math.isnan(pa[c])
        else np.nan
        for c in p.columns
    }

    # Standard error of each reference-class area proportion.
    se = {}
    for ref_class in ref_classes:
        variance = 0.0
        for stratum, group in labelled.groupby("stratum"):
            weight = weights[stratum]
            n_h = len(group)
            if n_h < 2:
                continue
            n_hj = int((group["reference_class"] == ref_class).sum())
            proportion = n_hj / n_h
            variance += weight**2 * proportion * (1 - proportion) / (n_h - 1)
        se[ref_class] = math.sqrt(max(variance, 0.0))

    # Standard error of overall accuracy: treat correctness as a binary
    # variable within each stratum (Olofsson et al. 2014, Eq. 5).
    overall_variance = 0.0
    for stratum, group in labelled.groupby("stratum"):
        weight = weights[stratum]
        n_h = len(group)
        if n_h < 2:
            continue
        correct = float((group["map_class"] == group["reference_class"]).mean())
        overall_variance += weight**2 * correct * (1 - correct) / (n_h - 1)
    overall_se = math.sqrt(max(overall_variance, 0.0))

    total_area_ha = total_pixels * 0.09
    rows = []
    for ref_class in ref_classes:
        rows.append(
            {
                "class": ref_class,
                "mapped_pixels": int(labelled["map_class"].eq(ref_class).sum()),
                "sample_n": int(labelled["reference_class"].eq(ref_class).sum()),
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
    metrics_path = TABLE_DIR / f"validation_{args.year}.csv"
    metrics.to_csv(metrics_path, index=False)

    matrix_path = TABLE_DIR / f"error_matrix_{args.year}.csv"
    p.round(6).to_csv(matrix_path)

    manifest = {
        "artifact": "validation",
        "reference_year": args.year,
        "measure": args.measure,
        "generated_utc": utc_now(),
        "method": "Olofsson et al. (2014) stratified estimator, area proportions",
        "design_samples": int(len(samples)),
        "interpreted_samples": int(len(labelled)),
        "strata": int(len(weights)),
        "total_area_ha": round(total_area_ha, 1),
        "overall_accuracy": round(overall, 4),
        "overall_accuracy_se": round(overall_se, 4),
        "overall_accuracy_ci95": [round(max(overall - 1.96 * overall_se, 0), 4),
                                  round(min(overall + 1.96 * overall_se, 1), 4)],
        "class_metrics": rows,
        "outputs": [str(metrics_path), str(matrix_path)],
        "warning": (
            None
            if len(labelled) == len(samples)
            else f"{len(samples) - len(labelled)} unlabelled samples; estimates may be biased"
        ),
    }
    (data_root / "manifests").mkdir(parents=True, exist_ok=True)
    (data_root / "manifests" / f"validation_{args.year}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print()
    print(f"overall accuracy: {overall:.4f} (SE {overall_se:.4f})")
    print(metrics.to_string(index=False))
    print(f"\nmetrics: {metrics_path}")
    print(f"matrix:  {matrix_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
