#!/usr/bin/env python3
"""Load map runs, mapped areas and checksums into the study database.

Reads repository summary tables and runtime manifests produced by
build_composites.py and classify.py, and populates `map_runs`, `area_estimates`
and `checksums` in the canonical GeoPackage.

Idempotent per year: existing rows for a year are replaced.

Usage
-----
    python load_tables.py --year 2020
    python load_tables.py            # all years present in the summaries
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSITE_CSV = REPO_ROOT / "tables" / "composite_summary.csv"
AREA_CSV = REPO_ROOT / "tables" / "area_estimates_mapped.csv"
SEASONS = {
    "BORO": ((11, 1), (4, 30), -1),
    "AUS": ((5, 1), (8, 31), 0),
    "AMAN": ((6, 1), (11, 30), 0),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def code_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def season_window(year: int, season: str) -> tuple[str, str]:
    (sm, sd), (em, ed), offset = SEASONS[season]
    return date(year + offset, sm, sd).isoformat(), date(year, em, ed).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=0)
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

    if not COMPOSITE_CSV.exists() or not AREA_CSV.exists():
        print("Missing composite_summary.csv or area_estimates_mapped.csv", file=sys.stderr)
        return 3

    composites = pd.read_csv(COMPOSITE_CSV)
    areas = pd.read_csv(AREA_CSV)
    years = [args.year] if args.year else sorted(areas["reference_year"].unique())

    revision = code_revision()
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON")
    inserted_runs = inserted_areas = 0

    try:
        for year in years:
            year = int(year)
            connection.execute(
                "DELETE FROM area_estimates WHERE reference_year = ?", (year,)
            )
            connection.execute("DELETE FROM map_runs WHERE reference_year = ?", (year,))

            year_composites = composites[composites["reference_year"] == year]
            for _, row in year_composites.iterrows():
                season = row["season"]
                start, end = season_window(year, season)
                connection.execute(
                    """
                    INSERT OR REPLACE INTO map_runs
                        (map_id, reference_year, season, crop_year, window_start, window_end,
                         sensors, valid_obs_summary, model_name, model_version, threshold,
                         code_revision, output_path, low_support)
                    VALUES (?, ?, ?, ?, ?, ?, 'landsat', ?, 'median_composite', '0.1.0', NULL, ?, ?, ?)
                    """,
                    (
                        f"{year}_{season}_landsat",
                        year,
                        season,
                        year,
                        start,
                        end,
                        json.dumps(
                            {
                                "scenes_used": int(row["scenes_used"]),
                                "obs_median": float(row["obs_median"]),
                                "obs_mean": float(row["obs_mean"]),
                            }
                        ),
                        revision,
                        str(row["composite_path"]),
                        int(row["low_support"]),
                    ),
                )
                inserted_runs += 1

            for season in ("BORO", "AUS", "AMAN"):
                start, end = season_window(year, season)
                connection.execute(
                    """
                    INSERT OR REPLACE INTO map_runs
                        (map_id, reference_year, season, crop_year, window_start, window_end,
                         sensors, valid_obs_summary, model_name, model_version, threshold,
                         code_revision, output_path, low_support)
                    VALUES (?, ?, ?, ?, ?, ?, 'landsat', NULL, 'phenology_rules',
                            'rules-0.1.0-provisional', NULL, ?, ?, 0)
                    """,
                    (
                        f"{year}_{season}_rules-0.1.0-provisional",
                        year,
                        season,
                        year,
                        start,
                        end,
                        revision,
                        str(data_root / "rasters" / "products" / f"rice_class_{season}_{year}_30m.tif"),
                    ),
                )
                inserted_runs += 1

            for label, season_code, output in (
                ("ALL_UNION", "ALL_UNION", f"rice_union_{year}_30m.tif"),
                ("INTENSITY", "INTENSITY", f"rice_intensity_{year}_30m.tif"),
            ):
                connection.execute(
                    """
                    INSERT OR REPLACE INTO map_runs
                        (map_id, reference_year, season, crop_year, window_start, window_end,
                         sensors, valid_obs_summary, model_name, model_version, threshold,
                         code_revision, output_path, low_support)
                    VALUES (?, ?, ?, ?, ?, ?, 'landsat', NULL, 'phenology_rules',
                            'rules-0.1.0-provisional', NULL, ?, ?, 0)
                    """,
                    (
                        f"{year}_{label}_rules-0.1.0-provisional",
                        year,
                        season_code,
                        year,
                        f"{year}-01-01",
                        f"{year}-12-31",
                        revision,
                        str(data_root / "rasters" / "products" / output),
                    ),
                )
                inserted_runs += 1

            year_areas = areas[areas["reference_year"] == year]
            for _, row in year_areas.iterrows():
                connection.execute(
                    """
                    INSERT INTO area_estimates
                        (reference_year, zone_id, season_or_measure, mapped_area_ha,
                         valid_land_area_ha, map_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        year,
                        row["zone_id"],
                        row["season_or_measure"],
                        float(row["mapped_area_ha"]),
                        float(row["valid_land_area_ha"]),
                        row["map_id"],
                    ),
                )
                inserted_areas += 1

            manifest_path = data_root / "manifests" / f"classify_{year}.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                for output in manifest.get("outputs", []):
                    reference = Path(output["path"])
                    try:
                        relative = str(reference.relative_to(data_root))
                    except ValueError:
                        relative = str(reference)
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO checksums (artifact_path, sha256, bytes, stage)
                        VALUES (?, ?, NULL, ?)
                        """,
                        (relative, output["sha256"], "classify"),
                    )

        connection.commit()
    finally:
        connection.close()

    print(f"loaded years: {years}")
    print(f"map_runs rows: {inserted_runs}")
    print(f"area_estimates rows: {inserted_areas}")
    print(f"database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
