#!/usr/bin/env python3
"""Inventory satellite scenes and benchmark products for the study area.

Queries public STAC catalogs (anonymous) for Landsat C2 L2, Sentinel-2 L2A and
Sentinel-1 GRD over the RCC + 10 km footprint, per target year and season.
Records scene counts, platforms, cloud statistics and date ranges.
Checks availability of the two benchmark products.

Outputs
-------
tables/scene_inventory.csv          One row per year x season x collection
tables/scene_inventory_scenes.csv   One row per scene
manifests/scene_inventory.json      Full record with product availability

Usage
-----
    python stac_inventory.py [--data-root PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
TABLE_DIR = REPO_ROOT / "tables"
MANIFEST_DIR = REPO_ROOT / "manifests"

STAC_ENDPOINTS = {
    "earth-search": "https://earth-search.aws.element84.com/v1/search",
    "planetary-computer": "https://planetarycomputer.microsoft.com/api/stac/v1/search",
}
ZENODO_RECORD = "https://zenodo.org/api/records/21349862"

# RCC + 10 km footprint, EPSG:4326 (from boundaries/rcc_zones.gpkg, layer zones)
AOI_BBOX = [88.4433, 24.2601, 88.7674, 24.5075]
LANDSAT_PATH, LANDSAT_ROW = 138, 43

YEARS = [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]
SEASONS = {
    "BORO": ((11, 1), (4, 30), -1),   # Nov (year-1) to Apr (year); harvest-year label
    "AUS": ((5, 1), (8, 31), 0),
    "AMAN": ((6, 1), (11, 30), 0),
}
COLLECTIONS = {
    "landsat-c2-l2": {"label": "Landsat C2 L2", "first_year": 1982, "endpoint": "earth-search"},
    "sentinel-2-l2a": {"label": "Sentinel-2 L2A", "first_year": 2016, "endpoint": "planetary-computer"},
    "sentinel-1-grd": {"label": "Sentinel-1 GRD", "first_year": 2014, "endpoint": "earth-search"},
}
MAX_PAGES = 80


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def season_window(year: int, season: str) -> tuple[date, date]:
    (sm, sd), (em, ed), offset = SEASONS[season]
    return date(year + offset, sm, sd), date(year, em, ed)


def search(endpoint: str, collection: str, start: date, end: date, bbox=AOI_BBOX) -> list[dict]:
    url = STAC_ENDPOINTS[endpoint]
    body = {
        "collections": [collection],
        "bbox": bbox,
        "datetime": f"{start.isoformat()}T00:00:00Z/{end.isoformat()}T23:59:59Z",
        "limit": 250,
    }
    response = requests.post(url, json=body, timeout=120)
    response.raise_for_status()
    payload = response.json()
    features = list(payload.get("features", []))
    pages = 1
    while pages < MAX_PAGES:
        nxt = next((link for link in payload.get("links", []) if link.get("rel") == "next"), None)
        if not nxt:
            break
        if str(nxt.get("method", "GET")).upper() == "POST":
            next_body = dict(nxt.get("body") or {})
            next_body.setdefault("collections", [collection])
            next_body.setdefault("bbox", bbox)
            response = requests.post(url, json=next_body, timeout=120)
        else:
            response = requests.get(nxt["href"], timeout=120)
        response.raise_for_status()
        payload = response.json()
        features.extend(payload.get("features", []))
        pages += 1
    return features


def summarise(features: list[dict], collection: str) -> dict:
    clouds, dates, platforms = [], [], []
    cloud_applicable = collection != "sentinel-1-grd"
    kept = []
    for feature in features:
        props = feature.get("properties", {})
        if collection == "landsat-c2-l2":
            path = props.get("landsat:wrs_path")
            row = props.get("landsat:wrs_row")
            if path is not None and row is not None:
                if int(path) != LANDSAT_PATH or int(row) != LANDSAT_ROW:
                    continue
        kept.append(feature)
        cloud = props.get("eo:cloud_cover")
        if cloud is not None and cloud_applicable:
            clouds.append(float(cloud))
        stamp = props.get("datetime")
        if stamp:
            dates.append(stamp)
        platform = props.get("platform")
        if platform:
            platforms.append(str(platform).lower())

    return {
        "collection": collection,
        "n_scenes": len(kept),
        "platforms": sorted(set(platforms)),
        "cloud_metric": "scene_cloud_cover" if cloud_applicable else "not_applicable_sar",
        "cloud_min": round(min(clouds), 2) if clouds else None,
        "cloud_median": round(statistics.median(clouds), 2) if clouds else None,
        "cloud_max": round(max(clouds), 2) if clouds else None,
        "n_cloud_lt_20": sum(1 for c in clouds if c < 20) if cloud_applicable else None,
        "n_cloud_lt_50": sum(1 for c in clouds if c < 50) if cloud_applicable else None,
        "date_min": min(dates)[:10] if dates else None,
        "date_max": max(dates)[:10] if dates else None,
        "scenes": [
            {
                "scene_id": f.get("id"),
                "collection": collection,
                "datetime": f.get("properties", {}).get("datetime"),
                "platform": str(f.get("properties", {}).get("platform")).lower()
                if f.get("properties", {}).get("platform")
                else None,
                "cloud_cover": f.get("properties", {}).get("eo:cloud_cover"),
                "wrs_path": f.get("properties", {}).get("landsat:wrs_path"),
                "wrs_row": f.get("properties", {}).get("landsat:wrs_row"),
            }
            for f in kept
        ],
    }


def check_zhao() -> dict:
    try:
        response = requests.get(ZENODO_RECORD, timeout=60)
        response.raise_for_status()
        record = response.json()
    except Exception as exc:  # noqa: BLE001 - availability check should not abort
        return {"status": "unreachable", "error": str(exc)}
    files = record.get("files", [])
    return {
        "status": "available",
        "title": record.get("metadata", {}).get("title"),
        "doi": record.get("doi"),
        "n_files": len(files),
        "files": [{"key": f.get("key"), "bytes": f.get("size")} for f in files],
        "overlapping_years": [1995, 2005, 2015],
        "nearest_recent_year": 2024,
        "access": "anonymous HTTP range reads recommended; whole rasters are ~0.5 GB each",
    }


def check_gcd_rice() -> dict:
    return {
        "status": "manual-download-required",
        "title": "Global Crop Dataset - Rice, 1990-2023",
        "doi": "10.57760/sciencedb.21665",
        "landing_page": "https://www.scidb.cn/en/detail?dataSetId=68ea15cf08d7469f8c1a653f5589701a",
        "n_files_total": 918,
        "note": "Bulk download host returned HTTP 403 from the build host; browser download of the Bangladesh folder required.",
    }


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
    (data_root / "manifests").mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    scene_rows = []
    warnings = []

    for year in YEARS:
        for season in SEASONS:
            start, end = season_window(year, season)
            for collection, meta in COLLECTIONS.items():
                if year < meta["first_year"]:
                    continue
                try:
                    features = search(meta["endpoint"], collection, start, end)
                except Exception as exc:  # noqa: BLE001 - record and continue
                    warnings.append(f"{collection} {year} {season}: {exc}")
                    print(f"WARN {collection} {year} {season}: {exc}", file=sys.stderr)
                    continue
                summary = summarise(features, collection)
                row = {
                    "reference_year": year,
                    "season": season,
                    "catalog": meta["endpoint"],
                    "window_start": start.isoformat(),
                    "window_end": end.isoformat(),
                    **{k: v for k, v in summary.items() if k != "scenes"},
                }
                records.append(row)
                for scene in summary["scenes"]:
                    scene_rows.append(
                        {
                            "reference_year": year,
                            "season": season,
                            **scene,
                        }
                    )
                clear = summary["n_cloud_lt_20"]
                clear_text = f"{clear:3}" if clear is not None else "  -"
                print(
                    f"{year} {season:4} {collection:16} "
                    f"scenes={summary['n_scenes']:4} "
                    f"clear<20={clear_text} "
                    f"platforms={','.join(summary['platforms']) or '-'}"
                )

    landsat_years = sorted({r["reference_year"] for r in records if r["collection"] == "landsat-c2-l2"})
    for year in landsat_years:
        total = sum(
            r["n_scenes"]
            for r in records
            if r["collection"] == "landsat-c2-l2" and r["reference_year"] == year
        )
        if total == 0:
            warnings.append(f"no Landsat scenes for {year}")
    for year in (2005, 2010):
        if any(
            r["collection"] == "landsat-c2-l2"
            and r["reference_year"] == year
            and "landsat-7" in r["platforms"]
            for r in records
        ):
            warnings.append(
                f"{year}: Landsat 7 SLC-off scenes present; protocol excludes L7 2003-2011 from the baseline"
            )

    s2_2015 = sum(
        r["n_scenes"]
        for r in records
        if r["collection"] == "sentinel-2-l2a" and r["reference_year"] == 2015
    )
    if s2_2015 == 0:
        warnings.append(
            "2015: no Sentinel-2 L2A scenes over the AOI in either catalog; "
            "the protocol's 2015 Sentinel-enhanced comparison cannot use S2. "
            "Use Sentinel-1 only for 2015, or restrict the sensor comparison to 2020 and 2025."
        )

    zhao = check_zhao()
    gcd = check_gcd_rice()

    manifest = {
        "artifact": "scene_inventory",
        "generated_utc": utc_now(),
        "catalog": STAC_ENDPOINTS,
        "aoi": {
            "bbox_4326": AOI_BBOX,
            "landsat_path_row": f"{LANDSAT_PATH}/{LANDSAT_ROW}",
        },
        "season_windows": {
            season: {
                "start": f"{sm:02d}-{sd:02d}",
                "end": f"{em:02d}-{ed:02d}",
                "year_offset_start": offset,
                "status": "provisional; confirm against BRRI/DAE calendars",
            }
            for season, ((sm, sd), (em, ed), offset) in SEASONS.items()
        },
        "collections": COLLECTIONS,
        "records": records,
        "products": {"zhao_2026": zhao, "gcd_rice": gcd},
        "warnings": warnings,
    }

    MANIFEST_DIR.joinpath("scene_inventory.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    import csv

    summary_fields = [
        "reference_year", "season", "catalog", "collection", "window_start", "window_end",
        "n_scenes", "n_cloud_lt_20", "n_cloud_lt_50", "cloud_min", "cloud_median",
        "cloud_max", "cloud_metric", "date_min", "date_max", "platforms",
    ]
    with (TABLE_DIR / "scene_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary_fields, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            row = dict(row)
            row["platforms"] = ";".join(row.get("platforms") or [])
            writer.writerow({k: row.get(k) for k in summary_fields})

    scene_fields = [
        "reference_year", "season", "collection", "scene_id", "datetime",
        "platform", "cloud_cover", "wrs_path", "wrs_row",
    ]
    with (TABLE_DIR / "scene_inventory_scenes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=scene_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(scene_rows)

    print()
    print(f"records: {len(records)}  scenes: {len(scene_rows)}")
    print(f"zhao_2026: {zhao.get('status')}  gcd_rice: {gcd.get('status')}")
    if warnings:
        print(f"warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
