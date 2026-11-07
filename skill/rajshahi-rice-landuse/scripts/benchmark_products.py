#!/usr/bin/env python3
"""Benchmark our rice maps against Zhao et al. (2026) and Singha et al. (2019).

This is the final benchmark set for the study. GCD-Rice and the BBS yearbooks are
documented as unavailable (see reports/BENCHMARKS.md) and are not required.

The script locates the downloaded GeoTIFFs by file name, so they do not have to
sit in one exact folder. It searches, in order:

1. `--external-dir` if given
2. `<data-root>/external`
3. `<data-root>`
4. the current directory
5. the repository root
6. `~/Downloads`
7. the home directory

Shallow, name-based discovery only; nothing is moved or modified.

Outputs
-------
tables/benchmark_products.csv
manifests/benchmark.json

Usage
-----
    python benchmark_products.py --data-root /path/to/rajshahi-rice
    python benchmark_products.py --external-dir ~/Downloads
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject

REPO_ROOT = Path(__file__).resolve().parents[3]
BOUNDARY_GPKG = REPO_ROOT / "boundaries" / "rcc_zones.gpkg"
TABLE_DIR = REPO_ROOT / "tables"
CRS = "EPSG:32645"
AOI_BBOX = (88.4433, 24.2601, 88.7674, 24.5075)

# Final benchmark set. `tokens` must all appear in the normalised file name.
PRODUCTS = [
    {"name": "Zhao 2026 1995", "tokens": ("southandsoutheastasiapaddyrice", "1995"), "exclude": (),
     "product_year": 1995, "our_years": (1995,), "season": "ALL_UNION"},
    {"name": "Zhao 2026 2005", "tokens": ("southandsoutheastasiapaddyrice", "2005"), "exclude": (),
     "product_year": 2005, "our_years": (2005,), "season": "ALL_UNION"},
    {"name": "Zhao 2026 2015", "tokens": ("southandsoutheastasiapaddyrice", "2015"), "exclude": (),
     "product_year": 2015, "our_years": (2015,), "season": "ALL_UNION"},
    {"name": "Zhao 2026 2024", "tokens": ("southandsoutheastasiapaddyrice", "2024"), "exclude": (),
     "product_year": 2024, "our_years": (2025,), "season": "ALL_UNION"},
    {"name": "APRA500 2000", "tokens": ("paddyrice", "2000"), "exclude": ("southandsoutheastasia",),
     "product_year": 2000, "our_years": (2000,), "season": "ALL_UNION"},
    {"name": "APRA500 2005", "tokens": ("paddyrice", "2005"), "exclude": ("southandsoutheastasia",),
     "product_year": 2005, "our_years": (2005,), "season": "ALL_UNION"},
    {"name": "APRA500 2010", "tokens": ("paddyrice", "2010"), "exclude": ("southandsoutheastasia",),
     "product_year": 2010, "our_years": (2010,), "season": "ALL_UNION"},
    {"name": "APRA500 2015", "tokens": ("paddyrice", "2015"), "exclude": ("southandsoutheastasia",),
     "product_year": 2015, "our_years": (2015,), "season": "ALL_UNION"},
    {"name": "APRA500 2020", "tokens": ("paddyrice", "2020"), "exclude": ("southandsoutheastasia",),
     "product_year": 2020, "our_years": (2020,), "season": "ALL_UNION"},
    {"name": "Singha 2017 Boro", "tokens": ("boro", "bgd", "2017"), "exclude": (),
     "product_year": 2017, "our_years": (2015, 2020), "season": "BORO"},
    {"name": "Singha 2017 Aus", "tokens": ("aus", "bgd", "2017"), "exclude": (),
     "product_year": 2017, "our_years": (2015, 2020), "season": "AUS"},
    {"name": "Singha 2017 Aman", "tokens": ("aman", "bgd", "2017"), "exclude": (),
     "product_year": 2017, "our_years": (2015, 2020), "season": "AMAN"},
]

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".cache", "chips"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def iter_tifs(root: Path, max_depth: int = 6):
    root = root.resolve()
    base = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).parts) - base
        if depth > max_depth:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name.lower().endswith((".tif", ".tiff")):
                yield Path(dirpath) / name


def discover(roots: list[Path]) -> dict[str, Path]:
    candidates: dict[str, Path] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in iter_tifs(root):
            key = normalise(path.name)
            if key not in candidates:
                candidates[key] = path
    found: dict[str, Path] = {}
    for spec in PRODUCTS:
        matches = [
            (key, path)
            for key, path in candidates.items()
            if all(token in key for token in spec["tokens"])
            and not any(token in key for token in spec.get("exclude", ()))
        ]
        if matches:
            matches.sort(key=lambda item: len(item[0]))
            found[spec["name"]] = matches[0][1]
    return found


def load_on_grid(path: Path, transform, shape) -> np.ndarray:
    from pyproj import Transformer

    destination = np.zeros(shape, dtype=np.float32)
    with rasterio.open(path) as source:
        if source.crs is not None and source.crs.to_string() != "EPSG:4326":
            transformer = Transformer.from_crs("EPSG:4326", source.crs, always_xy=True)
            xs, ys = transformer.transform(
                [AOI_BBOX[0], AOI_BBOX[2]], [AOI_BBOX[1], AOI_BBOX[3]]
            )
            bounds = (min(xs), min(ys), max(xs), max(ys))
        else:
            bounds = AOI_BBOX
        window = rasterio.windows.from_bounds(*bounds, source.transform)
        try:
            data = source.read(1, window=window, boundless=True, fill_value=0)
            src_transform = source.window_transform(window)
        except Exception:
            data = source.read(1)
            src_transform = source.transform
        reproject(
            source=data.astype(np.float32), destination=destination,
            src_transform=src_transform, src_crs=source.crs,
            dst_transform=transform, dst_crs=CRS,
            resampling=Resampling.nearest,
        )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    parser.add_argument("--external-dir", default="")
    parser.add_argument("--products-dir", default="")
    parser.add_argument("--out-dir", default=str(TABLE_DIR))
    args = parser.parse_args()

    data_root = Path(args.data_root).expanduser().resolve()
    products_dir = (
        Path(args.products_dir).expanduser().resolve()
        if args.products_dir
        else data_root / "rasters" / "products"
    )
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not products_dir.exists():
        print(f"Products directory not found: {products_dir}", file=sys.stderr)
        print("Download the products release, or pass --products-dir.", file=sys.stderr)
        return 2

    search_roots = []
    if args.external_dir:
        search_roots.append(Path(args.external_dir).expanduser())
    search_roots += [
        data_root / "external",
        data_root,
        Path.cwd(),
        REPO_ROOT,
        Path.home() / "Downloads",
        Path.home(),
    ]
    seen, unique_roots = set(), []
    for root in search_roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key not in seen:
            seen.add(key)
            unique_roots.append(root)

    print("Searching for benchmark files in:")
    for root in unique_roots:
        print(f"  {root}")

    found = discover(unique_roots)
    print("\nMatched files:")
    for spec in PRODUCTS:
        path = found.get(spec["name"])
        print(f"  {spec['name']:18} {'OK  ' + str(path) if path else 'MISSING'}")

    if not found:
        print("\nNo benchmark files found. Download links are in reports/BENCHMARKS.md.", file=sys.stderr)
        return 3

    zones = gpd.read_file(BOUNDARY_GPKG, layer="zones").to_crs(CRS)
    reference = None
    for candidate in sorted(products_dir.glob("rice_union_*_30m.tif")):
        reference = candidate
        break
    if reference is None:
        print(f"No rice_union rasters in {products_dir}", file=sys.stderr)
        return 4
    with rasterio.open(reference) as source:
        transform, shape = source.transform, (source.height, source.width)

    masks = {
        row["zone_id"]: geometry_mask(
            [row.geometry], out_shape=shape, transform=transform, invert=True, all_touched=False
        )
        for _, row in zones.iterrows()
    }

    rows = []
    for spec in PRODUCTS:
        path = found.get(spec["name"])
        if path is None:
            continue
        product = load_on_grid(path, transform, shape)
        product_rice = product == 1
        for our_year in spec["our_years"]:
            if spec["season"] == "ALL_UNION":
                our_path = products_dir / f"rice_union_{our_year}_30m.tif"
            else:
                our_path = products_dir / f"rice_class_{spec['season']}_{our_year}_30m.tif"
            if not our_path.exists():
                print(f"  skip {spec['name']} vs {our_year}: missing {our_path.name}")
                continue
            with rasterio.open(our_path) as source:
                ours = source.read(1) == 1
            for zone_id, mask in masks.items():
                if not mask.any():
                    continue
                a, b = ours & mask, product_rice & mask
                inter = int((a & b).sum())
                union = int((a | b).sum())
                rows.append(
                    {
                        "product": spec["name"],
                        "product_year": spec["product_year"],
                        "our_year": our_year,
                        "season": spec["season"],
                        "zone_id": zone_id,
                        "our_rice_fraction": round(float(a.sum() / mask.sum()), 4),
                        "product_rice_fraction": round(float(b.sum() / mask.sum()), 4),
                        "agreement": round(float(((a == b) & mask).sum() / mask.sum()), 4),
                        "iou": round(inter / union, 4) if union else None,
                    }
                )
        print(f"  compared {spec['name']}")

    if not rows:
        print("No comparison could be produced.", file=sys.stderr)
        return 5

    frame = pd.DataFrame(rows)
    csv_path = out_dir / "benchmark_products.csv"
    frame.to_csv(csv_path, index=False)

    summary = (
        frame.groupby(["product", "season"])[["agreement", "iou"]]
        .mean()
        .round(4)
        .reset_index()
    )
    summary.to_csv(out_dir / "benchmark_summary.csv", index=False)

    (data_root / "manifests").mkdir(parents=True, exist_ok=True)
    (data_root / "manifests" / "benchmark.json").write_text(
        json.dumps(
            {
                "generated_utc": utc_now(),
                "products_found": {name: str(path) for name, path in found.items()},
                "rows": len(rows),
                "note": "Agreement is not accuracy.",
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"\nrows: {len(rows)}")
    print(summary.to_string(index=False))
    print(f"\ntable:   {csv_path}")
    print(f"summary: {out_dir / 'benchmark_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
