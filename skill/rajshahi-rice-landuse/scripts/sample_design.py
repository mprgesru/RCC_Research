#!/usr/bin/env python3
"""Stratified reference-sample design following Olofsson et al. (2014).

Implements a probability sample for accuracy assessment and area estimation:

- strata: mapped land-cover class x zone group (RCC, 0-5 km, 5-10 km)
- sample size: Cochran (1977) Eq. 5.25 as presented in Olofsson et al. (2014),
  with S_h = sqrt(U_h (1 - U_h)) from conjectured user's accuracies
- allocation: minimum per stratum for rare strata, remainder proportional
- selection: random points, at most one per 1 km block, to reduce spatial
  autocorrelation between sample units

Outputs
-------
tables/sample_design.csv          Stratum weights, conjectured UA, allocation
tables/reference_sample_sheet.csv Blank label sheet
${DATA_ROOT}/db/rajshahi_rice.gpkg  Layer `reference_samples` populated

Usage
-----
    python sample_design.py --year 2020 --se 0.02
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

REPO_ROOT = Path(__file__).resolve().parents[3]
BOUNDARY_GPKG = REPO_ROOT / "boundaries" / "rcc_zones.gpkg"
TABLE_DIR = REPO_ROOT / "tables"
CRS = "EPSG:32645"

CLASS_NAMES = {
    1: "BORO", 2: "AUS", 3: "AMAN",
    4: "OTHER_CROPLAND", 5: "ORCHARD", 6: "OTHER_VEG",
    7: "BUILT", 8: "WATER", 9: "BARE",
}
# Conjectured user's accuracy by mapped class, used only for sample-size
# planning. They are replaced by observed values after interpretation.
CONJECTURED_UA = {
    1: 0.80, 2: 0.65, 3: 0.65,
    4: 0.70, 5: 0.60, 6: 0.75,
    7: 0.90, 8: 0.90, 9: 0.80,
}
ZONE_GROUPS = {"RCC": "RCC", "R0_5": "R0_5", "R5_10": "R5_10"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sample_size(strata: pd.DataFrame, target_se: float, total_pixels: int) -> int:
    weights = strata["W"].to_numpy()
    sds = strata["S"].to_numpy()
    numerator = (weights * sds).sum() ** 2
    denominator = target_se**2 + (1.0 / total_pixels) * (weights * sds**2).sum()
    return int(math.ceil(numerator / denominator))


def allocate(strata: pd.DataFrame, total: int, minimum: int) -> np.ndarray:
    n = len(strata)
    allocation = np.full(n, minimum, dtype=int)
    remaining = max(total - allocation.sum(), 0)
    if remaining:
        weights = strata["W"].to_numpy()
        weights = weights / weights.sum()
        allocation += np.floor(remaining * weights).astype(int)
    # Distribute rounding remainder to the largest strata.
    shortfall = total - allocation.sum()
    if shortfall > 0:
        order = np.argsort(-strata["W"].to_numpy())
        for position in order[:shortfall]:
            allocation[position] += 1
    counts = strata["pixels"].to_numpy()
    return np.minimum(allocation, counts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--se", type=float, default=0.02, help="target standard error of overall accuracy")
    parser.add_argument("--minimum", type=int, default=20, help="minimum sample per non-empty stratum")
    parser.add_argument("--max-samples", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=20261107)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    db_path = data_root / "db" / "rajshahi_rice.gpkg"
    lulc_path = data_root / "rasters" / "products" / f"lulc_{args.year}_30m.tif"
    union_path = data_root / "rasters" / "products" / f"rice_union_{args.year}_30m.tif"
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 2
    if not lulc_path.exists() or not union_path.exists():
        print("Missing land-cover or union product for the requested year", file=sys.stderr)
        return 3

    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(lulc_path) as source:
        lulc = source.read(1)
        transform = source.transform
        height, width = source.height, source.width

    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    zone_group = {}
    for _, zone in zones.iterrows():
        zone_group[zone["zone_id"]] = ZONE_GROUPS.get(zone["zone_id"])

    from rasterio.features import geometry_mask

    zone_stack = {}
    for zone_id, group in zone_group.items():
        if group is None:
            continue
        mask = geometry_mask(
            [zones[zones["zone_id"] == zone_id].geometry.iloc[0]],
            out_shape=(height, width), transform=transform, invert=True, all_touched=False,
        )
        zone_stack[group] = zone_stack.get(group, np.zeros((height, width), bool)) | mask

    rows = []
    for code, name in CLASS_NAMES.items():
        for group, mask in zone_stack.items():
            pixels = int(((lulc == code) & mask).sum())
            if pixels == 0:
                continue
            rows.append({"class_code": code, "map_class": name, "zone_group": group, "pixels": pixels})
    strata = pd.DataFrame(rows)
    total_pixels = int(strata["pixels"].sum())
    strata["W"] = strata["pixels"] / total_pixels
    strata["U"] = strata["class_code"].map(CONJECTURED_UA)
    strata["S"] = np.sqrt(strata["U"] * (1 - strata["U"]))

    planning = []
    for target in (0.01, 0.02, 0.03, 0.04):
        planning.append((target, sample_size(strata, target, total_pixels)))

    n = min(sample_size(strata, args.se, total_pixels), args.max_samples)
    strata["n"] = allocate(strata, n, args.minimum)
    strata["anticipated_se_ua"] = np.sqrt(strata["U"] * (1 - strata["U"]) / strata["n"])

    design = strata.copy()
    design["stratum"] = design["map_class"] + "|" + design["zone_group"]
    design.to_csv(TABLE_DIR / "sample_design.csv", index=False)

    # Random points, at most one per 1 km block within a stratum.
    rng = np.random.default_rng(args.seed)
    xmin = transform.c
    ymax = transform.f
    points = []
    for _, stratum in design.iterrows():
        code = stratum["class_code"]
        group = stratum["zone_group"]
        mask = (lulc == code) & zone_stack[group]
        rows_idx, cols_idx = np.nonzero(mask)
        if len(rows_idx) == 0:
            continue
        order = rng.permutation(len(rows_idx))
        used_blocks = set()
        selected = []
        for position in order:
            row, col = rows_idx[position], cols_idx[position]
            block = (int((xmin + col * 30) // 1000), int((ymax - row * 30) // 1000))
            if block in used_blocks:
                continue
            used_blocks.add(block)
            selected.append((row, col))
            if len(selected) >= int(stratum["n"]):
                break
        for row, col in selected:
            x = xmin + (col + 0.5) * 30
            y = ymax - (row + 0.5) * 30
            points.append(
                {
                    "sample_id": f"S{args.year}-{len(points) + 1:04d}",
                    "reference_year": args.year,
                    "season": "LULC",
                    "stratum": stratum["stratum"],
                    "map_class": stratum["map_class"],
                    "zone_id": group,
                    "reference_class": None,
                    "reference_source": None,
                    "reference_date": None,
                    "interpreter_id": None,
                    "confidence": None,
                    "split": "validation",
                    "notes": None,
                    "geometry": gpd.points_from_xy([x], [y])[0],
                }
            )

    samples = gpd.GeoDataFrame(points, crs=CRS)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("DELETE FROM reference_samples WHERE reference_year = ?", (args.year,))
        connection.commit()
    finally:
        connection.close()
    samples.to_file(db_path, layer="reference_samples", driver="GPKG", mode="a")

    sample_path = TABLE_DIR / "reference_sample_sheet.csv"
    samples.drop(columns="geometry").to_csv(sample_path, index=False)

    # Blinded sheet for interpreters: no map class, no stratum, no map-derived
    # information. The map key stays in reference_sample_sheet.csv for analysis.
    blinded = samples.drop(columns="geometry")[
        ["sample_id", "reference_year", "season", "zone_id"]
    ].copy()
    table = pd.DataFrame(
        {
            "sample_id": blinded["sample_id"],
            "reference_year": blinded["reference_year"],
            "season_or_lulc": blinded["season"],
            "zone_id": blinded["zone_id"],
        }
    )
    for label in ("BORO", "AMAN", "AUS"):
        table[f"chip_2020_{label}"] = [
            str(data_root / "chips" / str(args.year) / label / f"{sid}.png")
            for sid in blinded["sample_id"]
        ]
    for blank in (
        "reference_class", "reference_source", "reference_date", "confidence",
        "interpreter_id", "notes",
        "boro_rice", "boro_confidence",
        "aus_rice", "aus_confidence",
        "aman_rice", "aman_confidence",
        "season_notes",
    ):
        table[blank] = ""
    table.to_csv(TABLE_DIR / "interpretation_sheet.csv", index=False)

    # Reduced sheet for fast keyboard or spreadsheet entry. Provenance fields
    # (source, date, per-season confidence) are filled with defaults at import.
    quick_columns = [
        "sample_id", "reference_year", "zone_id",
        "chip_2020_BORO", "chip_2020_AMAN", "chip_2020_AUS",
        "reference_class", "boro_rice", "aus_rice", "aman_rice",
        "confidence", "interpreter_id", "notes",
    ]
    table[quick_columns].to_csv(TABLE_DIR / "interpretation_quick.csv", index=False)

    summary = {
        "artifact": "reference_sample_design",
        "reference_year": args.year,
        "generated_utc": utc_now(),
        "method": "Olofsson et al. (2014) stratified random sampling; Cochran (1977) sample size",
        "target_se": args.se,
        "minimum_per_stratum": args.minimum,
        "max_samples": args.max_samples,
        "seed": args.seed,
        "strata_count": int(len(design)),
        "total_pixels": total_pixels,
        "requested_samples": int(n),
        "realised_samples": int(len(samples)),
        "planning_curve": [{"target_se": se, "n": count} for se, count in planning],
        "strata": design.drop(columns=["pixels", "W", "U", "S", "anticipated_se_ua"]).to_dict(orient="records"),
    }
    (data_root / "manifests").mkdir(parents=True, exist_ok=True)
    (data_root / "manifests" / f"sample_design_{args.year}.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print("Sample-size planning (overall accuracy standard error):")
    for se, count in planning:
        print(f"  SE={se:.3f}  n={count}")
    print(f"\nChosen: SE={args.se}  n={n}  strata={len(design)}  points={len(samples)}")
    print(design[["stratum", "pixels", "W", "U", "n"]].to_string(index=False))
    print(f"\nlayer: {db_path}::reference_samples")
    print(f"sheet: {sample_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
