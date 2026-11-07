#!/usr/bin/env python3
"""Compute five-year land-cover transitions for rice (protocol Step 7).

For each consecutive target-year pair, cross-tabulates:

- all-rice union at the start year against land cover at the end year
  (rice persistence and rice loss, attributed to a destination class)
- land cover at the start year against all-rice union at the end year
  (rice gain, attributed to an origin class)
- each season at the start year against land cover at the end year

Areas are mapped pixel counts converted to hectares. They are NOT accuracy
adjusted: no validation samples exist. Every row carries `map_id` context in the
manifest and is marked provisional.

Outputs (runtime root)
----------------------
manifests/transitions.json
Database table transition_estimates

Repository output
-----------------
tables/transition_estimates_mapped.csv

Usage
-----
    python transitions.py
"""

from __future__ import annotations

import argparse
import json
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
PIXEL_HA = 0.09
SEASONS = ("BORO", "AUS", "AMAN")
YEARS = [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]
MODEL_VERSION = "rules-0.3.0-provisional"
CODE_TO_CLASS = {
    1: "BORO", 2: "AUS", 3: "AMAN",
    4: "OTHER_CROPLAND", 5: "ORCHARD", 6: "OTHER_VEG",
    7: "BUILT", 8: "WATER", 9: "BARE", 255: "NO_DATA",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_single(path: Path) -> np.ndarray:
    with rasterio.open(path) as source:
        return source.read(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    product_dir = data_root / "rasters" / "products"
    manifest_dir = data_root / "manifests"
    db_path = data_root / "db" / "rajshahi_rice.gpkg"
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    with rasterio.open(product_dir / "rice_union_1990_30m.tif") as source:
        transform = source.transform
        shape = (source.height, source.width)

    zone_masks = {}
    for _, zone in zones.iterrows():
        zone_masks[zone["zone_id"]] = geometry_mask(
            [zone.geometry], out_shape=shape, transform=transform, invert=True, all_touched=False
        )

    rows = []
    for start, end in zip(YEARS[:-1], YEARS[1:]):
        union_start = read_single(product_dir / f"rice_union_{start}_30m.tif") == 1
        union_end = read_single(product_dir / f"rice_union_{end}_30m.tif") == 1
        lulc_start = read_single(product_dir / f"lulc_{start}_30m.tif")
        lulc_end = read_single(product_dir / f"lulc_{end}_30m.tif")
        seasonal_start = {
            season: read_single(product_dir / f"rice_class_{season}_{start}_30m.tif") == 1
            for season in SEASONS
        }

        for zone_id, inside in zone_masks.items():
            inside_start = inside & (union_start | (lulc_start != 255))
            inside_end = inside & (union_end | (lulc_end != 255))

            def add(season_or_measure, from_class, to_class, mask):
                pixels = int((mask & inside).sum())
                if pixels == 0:
                    return
                rows.append(
                    {
                        "period_start": start,
                        "period_end": end,
                        "zone_id": zone_id,
                        "season_or_measure": season_or_measure,
                        "from_class": from_class,
                        "to_class": to_class,
                        "mapped_area_ha": round(pixels * PIXEL_HA, 3),
                        "validation_n": None,
                        "model_version": MODEL_VERSION,
                    }
                )

            # Union persistence, loss and gain.
            add("ALL_UNION", "ALL_RICE", "ALL_RICE", union_start & union_end)
            loss = union_start & ~union_end
            for code, name in CODE_TO_CLASS.items():
                if code == 255:
                    continue
                add("ALL_UNION", "ALL_RICE", name, loss & (lulc_end == code))
            gain = ~union_start & union_end
            for code, name in CODE_TO_CLASS.items():
                if code == 255:
                    continue
                add("ALL_UNION", name, "ALL_RICE", gain & (lulc_start == code))

            # Per-season persistence and loss.
            for season in SEASONS:
                rice_start = seasonal_start[season]
                add(season, season, season, rice_start & (lulc_end == SEASONS.index(season) + 1))
                for code, name in CODE_TO_CLASS.items():
                    if code in (1, 2, 3, 255):
                        continue
                    add(season, season, name, rice_start & (lulc_end == code))

        print(f"{start}->{end}: {len([r for r in rows if r['period_start'] == start])} rows")

    frame = pd.DataFrame(rows)
    csv_path = TABLE_DIR / "transition_estimates_mapped.csv"
    frame.drop(columns=["model_version"]).to_csv(csv_path, index=False)

    inserted = 0
    if db_path.exists():
        connection = sqlite3.connect(db_path)
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            for start, end in zip(YEARS[:-1], YEARS[1:]):
                connection.execute(
                    "DELETE FROM transition_estimates WHERE period_start = ? AND period_end = ?",
                    (start, end),
                )
            for row in rows:
                connection.execute(
                    """
                    INSERT INTO transition_estimates
                        (period_start, period_end, zone_id, season_or_measure,
                         from_class, to_class, mapped_area_ha, validation_n)
                    VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        row["period_start"], row["period_end"], row["zone_id"],
                        row["season_or_measure"], row["from_class"], row["to_class"],
                        row["mapped_area_ha"],
                    ),
                )
                inserted += 1
            connection.commit()
        finally:
            connection.close()

    manifest = {
        "artifact": "transitions",
        "generated_utc": utc_now(),
        "model_version": MODEL_VERSION,
        "status": "provisional_unvalidated",
        "class_mapping": CODE_TO_CLASS,
        "periods": [{"start": a, "end": b} for a, b in zip(YEARS[:-1], YEARS[1:])],
        "rows": len(rows),
        "database_rows_inserted": inserted,
        "limitations": [
            "Mapped areas only; no accuracy adjustment or confidence intervals.",
            "Land cover is a derived, unvalidated product.",
            "Rice classes come from the uncalibrated rule set.",
        ],
    }
    manifest_dir.joinpath("transitions.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"rows: {len(rows)}  database inserts: {inserted}")
    print(f"table: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
