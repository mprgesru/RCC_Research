#!/usr/bin/env python3
"""Create and verify the Rajshahi rice study database.

Canonical database is a GeoPackage containing two spatial layers (`zones`,
`reference_samples`) and the attribute tables from schema/rajshahi_rice.sql.
A geometry-free SQLite mirror is produced for analytics tools that cannot read
GeoPackage.

Outputs
-------
$RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/db/rajshahi_rice.gpkg
$RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/db/rajshahi_rice.sqlite
manifests/db_manifest.json

Usage
-----
    python make_db.py [--force] [--data-root PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import fiona
import geopandas as gpd

REPO_ROOT = Path(__file__).resolve().parents[3]
BOUNDARY_GPKG = REPO_ROOT / "boundaries" / "rcc_zones.gpkg"
DDL_PATH = REPO_ROOT / "schema" / "rajshahi_rice.sql"
MANIFEST_PATH = REPO_ROOT / "manifests" / "db_manifest.json"

ATTRIBUTE_TABLES = (
    "season_legend",
    "class_legend",
    "map_runs",
    "data_sources",
    "checksums",
    "area_estimates",
    "transition_estimates",
    "ward_summary",
)

SAMPLE_FIELDS = {
    "sample_id": "str",
    "reference_year": "int",
    "season": "str",
    "stratum": "str",
    "map_class": "str",
    "zone_id": "str",
    "reference_class": "str",
    "reference_source": "str",
    "reference_date": "str",
    "interpreter_id": "str",
    "confidence": "str",
    "split": "str",
    "notes": "str",
}

SQLITE_VIEWS = """
DROP VIEW IF EXISTS v_area_estimates_full;
CREATE VIEW v_area_estimates_full AS
SELECT a.reference_year, a.zone_id, z.zone_name, z.zone_type,
       a.season_or_measure, a.mapped_area_ha, a.adjusted_area_ha,
       a.ci95_lower_ha, a.ci95_upper_ha, a.valid_land_area_ha,
       a.sample_n, a.ua, a.pa, a.f1, a.map_id,
       m.sensors, m.low_support, m.window_start, m.window_end
FROM area_estimates a
LEFT JOIN zone_dim z    ON z.zone_id = a.zone_id
LEFT JOIN map_runs m    ON m.map_id  = a.map_id;

DROP VIEW IF EXISTS v_transition_full;
CREATE VIEW v_transition_full AS
SELECT t.period_start, t.period_end, t.zone_id, z.zone_name, z.zone_type,
       t.season_or_measure, t.from_class, t.to_class,
       t.mapped_area_ha, t.adjusted_area_ha, t.ci95_lower_ha,
       t.ci95_upper_ha, t.validation_n
FROM transition_estimates t
LEFT JOIN zone_dim z ON z.zone_id = t.zone_id;

DROP VIEW IF EXISTS v_map_runs_summary;
CREATE VIEW v_map_runs_summary AS
SELECT reference_year, season, COUNT(*) AS map_runs,
       SUM(low_support) AS low_support_runs,
       MIN(window_start) AS first_window_start,
       MAX(window_end) AS last_window_end
FROM map_runs
GROUP BY reference_year, season;
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"PASS: {message}")


def create_spatial_layers(gpkg: Path) -> None:
    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones")
    if len(zones) != 5:
        fail(f"expected 5 zones, found {len(zones)}")
    if str(zones.crs) != "EPSG:32645":
        fail(f"zones CRS is {zones.crs}, expected EPSG:32645")
    zones.to_file(gpkg, layer="zones", driver="GPKG")
    ok(f"zones layer: {len(zones)} features, EPSG:32645")

    schema = {"geometry": "Unknown", "properties": SAMPLE_FIELDS}
    with fiona.open(
        gpkg, "w", driver="GPKG", layer="reference_samples", schema=schema, crs="EPSG:32645"
    ):
        pass
    ok("reference_samples layer created (empty)")


def apply_ddl(connection: sqlite3.Connection) -> None:
    ddl = DDL_PATH.read_text(encoding="utf-8")
    connection.executescript(ddl)
    ok(f"applied DDL: {DDL_PATH.relative_to(REPO_ROOT)}")


def register_attribute_tables(connection: sqlite3.Connection) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    for table in ATTRIBUTE_TABLES:
        connection.execute(
            """
            INSERT OR REPLACE INTO gpkg_contents
                (table_name, data_type, identifier, description, last_change,
                 min_x, min_y, max_x, max_y, srs_id)
            VALUES (?, 'attributes', ?, ?, ?, NULL, NULL, NULL, NULL, NULL)
            """,
            (table, table, f"Rajshahi rice study: {table}", stamp),
        )
    ok(f"registered {len(ATTRIBUTE_TABLES)} attribute tables in gpkg_contents")


def verify(connection: sqlite3.Connection) -> dict:
    tables = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    expected = set(ATTRIBUTE_TABLES) | {"zones", "reference_samples"}
    missing = expected - tables
    if missing:
        fail(f"missing tables: {sorted(missing)}")
    ok(f"all {len(expected)} expected tables present")

    counts = {}
    for table in sorted(expected):
        counts[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if counts["zones"] != 5:
        fail(f"zones table has {counts['zones']} rows, expected 5")
    if counts["reference_samples"] != 0:
        fail("reference_samples should be empty at schema stage")
    ok(f"zone rows: {counts['zones']}; reference samples: {counts['reference_samples']}")

    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        fail(f"foreign key violations: {violations}")
    ok("no foreign key violations")

    legend = connection.execute("SELECT COUNT(*) FROM class_legend").fetchone()[0]
    if legend != 10:
        fail(f"class_legend has {legend} rows, expected 10")
    sources = connection.execute("SELECT COUNT(*) FROM data_sources").fetchone()[0]
    ok(f"class legend rows: {legend}; data sources seeded: {sources}")

    # Negative tests: constraints must reject invalid rows.
    checks = [
        (
            "invalid year",
            "INSERT INTO map_runs (map_id, reference_year, season, crop_year, window_start, window_end, sensors) "
            "VALUES ('__bad__', 1991, 'BORO', 1990, '2020-01-01', '2020-01-02', 'landsat')",
        ),
        (
            "invalid season",
            "INSERT INTO map_runs (map_id, reference_year, season, crop_year, window_start, window_end, sensors) "
            "VALUES ('__bad__', 1990, 'WINTER', 1990, '2020-01-01', '2020-01-02', 'landsat')",
        ),
        (
            "unknown zone foreign key",
            "INSERT INTO area_estimates (reference_year, zone_id, season_or_measure, mapped_area_ha) "
            "VALUES (2020, 'NOPE', 'BORO', 10.0)",
        ),
        (
            "negative area",
            "INSERT INTO area_estimates (reference_year, zone_id, season_or_measure, mapped_area_ha) "
            "VALUES (2020, 'RCC', 'BORO', -1.0)",
        ),
    ]
    for label, statement in checks:
        connection.execute("SAVEPOINT bad_insert")
        try:
            connection.execute(statement)
        except sqlite3.IntegrityError:
            connection.execute("ROLLBACK TO bad_insert")
            connection.execute("RELEASE bad_insert")
            ok(f"constraint rejected: {label}")
        else:
            connection.execute("ROLLBACK TO bad_insert")
            connection.execute("RELEASE bad_insert")
            fail(f"constraint did not reject: {label}")

    return counts


def build_mirror(gpkg: Path, sqlite_path: Path) -> None:
    if sqlite_path.exists():
        sqlite_path.unlink()
    connection = sqlite3.connect(sqlite_path)
    try:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute(f"ATTACH DATABASE '{gpkg}' AS g")
        for table in ATTRIBUTE_TABLES:
            connection.execute(f"CREATE TABLE {table} AS SELECT * FROM g.{table}")
        connection.execute(
            "CREATE TABLE zone_dim AS SELECT zone_id, zone_name, zone_type, "
            "distance_min_km, distance_max_km, area_km2, boundary_version, "
            "boundary_status, source_url FROM g.zones"
        )
        connection.execute(
            "CREATE TABLE reference_samples AS SELECT "
            + ", ".join(SAMPLE_FIELDS)
            + " FROM g.reference_samples"
        )
        connection.execute("DETACH DATABASE g")
        connection.executescript(SQLITE_VIEWS)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_area_year_zone ON area_estimates (reference_year, zone_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_transition_zone ON transition_estimates (zone_id)")
        connection.commit()
    finally:
        connection.close()
    ok(f"sqlite mirror written: {sqlite_path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rebuild an existing database")
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    db_dir = data_root / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    gpkg = db_dir / "rajshahi_rice.gpkg"
    sqlite_path = db_dir / "rajshahi_rice.sqlite"

    if gpkg.exists() and not args.force:
        print(f"Refusing to overwrite existing database: {gpkg}", file=sys.stderr)
        print("Re-run with --force to rebuild.", file=sys.stderr)
        return 2
    if gpkg.exists():
        gpkg.unlink()

    create_spatial_layers(gpkg)

    connection = sqlite3.connect(gpkg)
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        apply_ddl(connection)
        register_attribute_tables(connection)
        counts = verify(connection)
        connection.commit()
    finally:
        connection.close()

    build_mirror(gpkg, sqlite_path)

    manifest = {
        "artifact": "study_database",
        "generated_utc": utc_now(),
        "engine": "SQLite 3 / GeoPackage",
        "inputs": {
            "ddl": str(DDL_PATH.relative_to(REPO_ROOT)),
            "ddl_sha256": sha256_file(DDL_PATH),
            "zones_source": str(BOUNDARY_GPKG.relative_to(REPO_ROOT)),
        },
        "outputs": {
            "gpkg": {
                "path": str(gpkg),
                "sha256": sha256_file(gpkg),
                "bytes": gpkg.stat().st_size,
            },
            "sqlite": {
                "path": str(sqlite_path),
                "sha256": sha256_file(sqlite_path),
                "bytes": sqlite_path.stat().st_size,
            },
        },
        "row_counts": counts,
        "tables": sorted(list(ATTRIBUTE_TABLES) + ["zones", "reference_samples"]),
        "checks": [
            "expected tables present",
            "zone rows == 5",
            "reference_samples empty",
            "no foreign key violations",
            "class legend rows == 10",
            "constraints reject invalid year, season, zone and negative area",
        ],
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    ok(f"manifest written: {MANIFEST_PATH.relative_to(REPO_ROOT)}")

    print()
    print(f"GeoPackage: {gpkg}")
    print(f"SQLite:     {sqlite_path}")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
