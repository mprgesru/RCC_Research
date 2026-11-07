#!/usr/bin/env python3
"""Summarise valid observation support by zone (protocol Step 2).

Reads the seasonal observation-support rasters and reports, per target year,
season and zone, the median valid observations per pixel, the 10th percentile
and the share of pixels with no valid observation.

Output
------
tables/observation_support_by_zone.csv

Usage
-----
    python support_summary.py
"""

from __future__ import annotations

import os
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
YEARS = (1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025)
SEASONS = ("BORO", "AUS", "AMAN")


def main() -> int:
    runtime = Path(
        os.environ.get("RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice")
    ).expanduser()
    composite_dir = runtime / "rasters" / "composites"
    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    first = composite_dir / f"obs_support_{SEASONS[0]}_{YEARS[0]}_30m.tif"
    with rasterio.open(first) as source:
        transform = source.transform
        shape = (source.height, source.width)

    masks = {
        row["zone_id"]: geometry_mask(
            [row.geometry], out_shape=shape, transform=transform, invert=True, all_touched=False
        )
        for _, row in zones.iterrows()
    }

    rows = []
    for year in YEARS:
        for season in SEASONS:
            path = composite_dir / f"obs_support_{season}_{year}_30m.tif"
            if not path.exists():
                continue
            with rasterio.open(path) as source:
                support = source.read(1)
            for zone_id, mask in masks.items():
                values = support[mask]
                if values.size == 0:
                    continue
                rows.append(
                    {
                        "reference_year": year,
                        "season": season,
                        "zone_id": zone_id,
                        "pixels": int(values.size),
                        "obs_median": float(np.median(values)),
                        "obs_mean": round(float(values.mean()), 2),
                        "obs_p10": float(np.percentile(values, 10)),
                        "zero_pixels": int((values == 0).sum()),
                        "zero_fraction": round(float((values == 0).mean()), 4),
                        "low_support": int(np.median(values) < 3),
                    }
                )

    frame = pd.DataFrame(rows)
    path = TABLE_DIR / "observation_support_by_zone.csv"
    frame.to_csv(path, index=False)
    print(f"rows: {len(frame)}  ->  {path}")

    pivot = frame.pivot_table(index="reference_year", columns="season", values="obs_median", aggfunc="mean")
    print(pivot.round(1).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
