#!/usr/bin/env python3
"""Build the Rajshahi rice study zones from the RCC ward service.

Source
------
ArcGIS FeatureServer:
    https://services.arcgis.com/5T5nSi527N4F7luB/arcgis/rest/services/
    Rajshahi_Wards_data/FeatureServer/0
Portal item: bfdf7c83715a4b0781e113fb16fd2ab7 (modified 2024-10-15)

Outputs (all under the repository, except the runtime tree)
----------------------------------------------------------
boundaries/rcc_boundary.shp        RCC outline, EPSG:32645
boundaries/rcc_boundary.geojson    RCC outline, EPSG:4326
boundaries/rcc_zones.gpkg          layers: rcc, zones, wards (EPSG:32645)
tables/zones.csv                   Zone summary table
manifests/boundary_manifest.json   Provenance, areas and SHA-256 checksums

Runtime
-------
Creates the runtime directory tree at $RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/.

Usage
-----
    python build_zones.py [--force] [--data-root PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely import make_valid

SERVICE_URL = (
    "https://services.arcgis.com/5T5nSi527N4F7luB/arcgis/rest/services/"
    "Rajshahi_Wards_data/FeatureServer/0"
)
QUERY_URL = f"{SERVICE_URL}/query"
PORTAL_ITEM = "bfdf7c83715a4b0781e113fb16fd2ab7"
BOUNDARY_VERSION = "2024-10-15"
BOUNDARY_STATUS = "official_operational"
LICENCE = "unstated"
ATTRIBUTION = (
    "WHO/UNICEF EPI Digital Microplanning - Rajshahi City Corporation (2024)"
)

ANALYSIS_CRS = "EPSG:32645"
INTERCHANGE_CRS = "EPSG:4326"
EXPECTED_WARDS = 30
EXPECTED_RCC_KM2 = 46.23
RCC_TOLERANCE = 0.01  # 1 percent
PART_UNION_TOLERANCE_KM2 = 0.05
RING_OVERLAP_TOLERANCE_KM2 = 0.01

REPO_ROOT = Path(__file__).resolve().parents[3]
BOUNDARY_DIR = REPO_ROOT / "boundaries"
TABLE_DIR = REPO_ROOT / "tables"
MANIFEST_DIR = REPO_ROOT / "manifests"

ZONE_DEFS = [
    ("RCC", "City Corporation", "core", 0.0, 0.0),
    ("R0_5", "Inner peri-urban ring", "ring", 0.0, 5.0),
    ("R5_10", "Outer peri-urban ring", "ring", 5.0, 10.0),
    ("RCC_5", "City plus 5 km", "cumulative", 0.0, 5.0),
    ("RCC_10", "City plus 10 km", "cumulative", 0.0, 10.0),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_wards() -> gpd.GeoDataFrame:
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    response = requests.get(
        QUERY_URL,
        params=params,
        timeout=90,
        headers={"User-Agent": "rajshahi-rice-landuse/0.1"},
    )
    response.raise_for_status()
    wards = gpd.read_file(io.StringIO(response.text))
    if wards.crs is None:
        wards = wards.set_crs(INTERCHANGE_CRS)
    return wards


def repair_geometry(frame: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, int]:
    invalid = ~frame.geometry.is_valid
    repaired = int(invalid.sum())
    if repaired:
        frame = frame.copy()
        frame.loc[invalid, "geometry"] = frame.loc[invalid, "geometry"].apply(make_valid)
    return frame, repaired


def build_zones(rcc, ring_05, ring_5_10) -> gpd.GeoDataFrame:
    geometries = {
        "RCC": rcc,
        "R0_5": ring_05,
        "R5_10": ring_5_10,
        "RCC_5": rcc.union(ring_05),
        "RCC_10": rcc.union(ring_05).union(ring_5_10),
    }
    rows = []
    for zone_id, zone_name, zone_type, dmin, dmax in ZONE_DEFS:
        geom = geometries[zone_id]
        rows.append(
            {
                "zone_id": zone_id,
                "zone_name": zone_name,
                "zone_type": zone_type,
                "distance_min_km": dmin,
                "distance_max_km": dmax,
                "area_km2": round(geom.area / 1e6, 4),
                "boundary_version": BOUNDARY_VERSION,
                "boundary_status": BOUNDARY_STATUS,
                "source_url": SERVICE_URL,
                "geometry": geom,
            }
        )
    return gpd.GeoDataFrame(rows, crs=ANALYSIS_CRS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite existing outputs")
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
        help="runtime data root (outside the repository)",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    for sub in ("raw", "curated", "rasters", "db", "manifests", "logs"):
        (data_root / sub).mkdir(parents=True, exist_ok=True)

    manifest_path = MANIFEST_DIR / "boundary_manifest.json"
    if manifest_path.exists() and not args.force:
        print(f"Refusing to overwrite existing manifest: {manifest_path}", file=sys.stderr)
        print("Re-run with --force to rebuild.", file=sys.stderr)
        return 2

    BOUNDARY_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching wards from {SERVICE_URL}")
    wards = fetch_wards()
    print(f"  features: {len(wards)}")

    if len(wards) != EXPECTED_WARDS:
        print(
            f"ERROR: expected {EXPECTED_WARDS} wards, got {len(wards)}",
            file=sys.stderr,
        )
        return 3

    wards, repaired = repair_geometry(wards)
    print(f"  repaired invalid geometries: {repaired}")

    wards_utm = wards.to_crs(ANALYSIS_CRS)
    parts_sum = float(wards_utm.area.sum() / 1e6)
    rcc = wards_utm.union_all()
    rcc_area = float(rcc.area / 1e6)
    part_gap = abs(parts_sum - rcc_area)
    print(f"  ward area sum: {parts_sum:.4f} km2")
    print(f"  dissolved RCC: {rcc_area:.4f} km2")
    print(f"  part/union difference: {part_gap:.4f} km2")

    if part_gap > PART_UNION_TOLERANCE_KM2:
        print("ERROR: ward parts and union differ beyond tolerance", file=sys.stderr)
        return 4

    relative_error = abs(rcc_area - EXPECTED_RCC_KM2) / EXPECTED_RCC_KM2
    if relative_error > RCC_TOLERANCE:
        print(
            f"ERROR: RCC area {rcc_area:.4f} km2 differs from "
            f"{EXPECTED_RCC_KM2} km2 by {relative_error:.2%}",
            file=sys.stderr,
        )
        return 5

    buffer_05 = rcc.buffer(5000.0)
    buffer_10 = rcc.buffer(10000.0)
    ring_05 = buffer_05.difference(rcc)
    ring_5_10 = buffer_10.difference(buffer_05)

    overlap_rcc_ring = float(rcc.intersection(ring_05).area / 1e6)
    overlap_rings = float(ring_05.intersection(ring_5_10).area / 1e6)
    print(f"  RCC/ring overlap: {overlap_rcc_ring:.6f} km2")
    print(f"  ring/ring overlap: {overlap_rings:.6f} km2")
    if max(overlap_rcc_ring, overlap_rings) > RING_OVERLAP_TOLERANCE_KM2:
        print("ERROR: zone overlap exceeds tolerance", file=sys.stderr)
        return 6

    zones = build_zones(rcc, ring_05, ring_5_10)

    rcc_frame = zones[zones["zone_id"] == "RCC"].copy()

    # Shapefile: DBF field names are limited to 10 characters.
    shp_frame = rcc_frame[["zone_id", "zone_name", "area_km2", "boundary_version", "geometry"]].copy()
    shp_frame = shp_frame.rename(columns={"boundary_version": "boundary_v"})
    shp_path = BOUNDARY_DIR / "rcc_boundary.shp"
    shp_frame.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")

    geojson_path = BOUNDARY_DIR / "rcc_boundary.geojson"
    rcc_frame.to_crs(INTERCHANGE_CRS).to_file(geojson_path, driver="GeoJSON")

    gpkg_path = BOUNDARY_DIR / "rcc_zones.gpkg"
    if gpkg_path.exists():
        gpkg_path.unlink()
    rcc_frame.to_file(gpkg_path, layer="rcc", driver="GPKG")
    zones.to_file(gpkg_path, layer="zones", driver="GPKG", mode="a")
    wards_utm[["Ward_No", "Ward_Name", "Zone_Name", "geometry"]].to_file(
        gpkg_path, layer="wards", driver="GPKG", mode="a"
    )

    csv_path = TABLE_DIR / "zones.csv"
    zones.drop(columns="geometry").to_csv(csv_path, index=False)

    outputs = [shp_path, geojson_path, gpkg_path, csv_path]
    for candidate in list(outputs):
        for sidecar in sorted(BOUNDARY_DIR.glob(f"{candidate.stem}.*")):
            if sidecar not in outputs:
                outputs.append(sidecar)
    # Sidecars only apply to the shapefile.
    outputs = [
        p
        for p in outputs
        if p.suffix.lower() in {".shp", ".shx", ".dbf", ".prj", ".cpg", ".geojson", ".gpkg", ".csv"}
    ]

    zone_records = zones.drop(columns="geometry").to_dict(orient="records")
    manifest = {
        "artifact": "study_boundaries",
        "generated_utc": utc_now(),
        "source": {
            "service_url": SERVICE_URL,
            "portal_item": PORTAL_ITEM,
            "portal_title": "Rajshahi City Corporation EPI Digital Microplanning",
            "owner": "digital_micplan",
            "item_modified": BOUNDARY_VERSION,
            "licence": LICENCE,
            "attribution": ATTRIBUTION,
        },
        "parameters": {
            "analysis_crs": ANALYSIS_CRS,
            "interchange_crs": INTERCHANGE_CRS,
            "ward_count": int(len(wards)),
            "repaired_geometries": repaired,
            "buffer_inner_m": 5000,
            "buffer_outer_m": 10000,
        },
        "checks": {
            "ward_area_sum_km2": round(parts_sum, 4),
            "dissolved_rcc_km2": round(rcc_area, 4),
            "expected_rcc_km2": EXPECTED_RCC_KM2,
            "relative_error": round(relative_error, 6),
            "part_union_difference_km2": round(part_gap, 6),
            "rcc_ring_overlap_km2": round(overlap_rcc_ring, 6),
            "ring_ring_overlap_km2": round(overlap_rings, 6),
        },
        "zones": zone_records,
        "outputs": [
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(set(outputs))
        ],
        "runtime_root": str(data_root),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("\nZones")
    print(zones.drop(columns="geometry").to_string(index=False))
    print(f"\nWrote {len(set(outputs))} files under {BOUNDARY_DIR.relative_to(REPO_ROOT)}/")
    print(f"Manifest: {manifest_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
