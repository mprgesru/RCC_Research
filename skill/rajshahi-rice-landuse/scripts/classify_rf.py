#!/usr/bin/env python3
"""Random-forest rice classifier on optical + Sentinel-1 features.

Trains one model per season using spatially blocked cross-validation, then
predicts probability and class rasters and derives the all-rice union and
cropping intensity.

Label source
------------
`--labels reference` uses interpreted `reference_samples` (preferred, but only
available once points are labelled). `--labels pseudo` uses high-confidence
outputs of the rule baseline. Pseudo-labels make this a self-trained model:
useful for consistency and for testing SAR contribution, but circular for
accuracy claims. The manifest records which source was used.

Features
--------
Optical: NDVI median/max/min/amplitude, LSWI max, flood fraction
SAR: VV, VH, VH-VV ratio, VH minimum, VH standard deviation, low-VH fraction

Outputs (runtime root)
----------------------
rasters/products/rice_prob_rf_{SEASON}_{YEAR}_30m.tif
rasters/products/rice_class_rf_{SEASON}_{YEAR}_30m.tif
rasters/products/rice_union_rf_{YEAR}_30m.tif
rasters/products/rice_intensity_rf_{YEAR}_30m.tif
manifests/rf_{YEAR}.json

Repository output
-----------------
tables/rf_summary.csv

Usage
-----
    python classify_rf.py --year 2020 --labels pseudo
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

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GroupKFold

REPO_ROOT = Path(__file__).resolve().parents[3]
TABLE_DIR = REPO_ROOT / "tables"
CRS = "EPSG:32645"
SEASONS = ("BORO", "AUS", "AMAN")
OPTICAL_FEATURES = ("ndvi_median", "ndvi_max", "ndvi_min", "ndvi_amplitude", "lswi_max", "flood_frac")
SAR_FEATURES = ("vv_db", "vh_db", "ratio_db", "vh_min_db", "vh_std_db", "low_vh_frac")
MODEL_VERSION = "rf-0.1.0"
N_ESTIMATORS = 300


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_named(path: Path, names) -> dict[str, np.ndarray]:
    with rasterio.open(path) as source:
        data = {}
        for name in names:
            if name in source.descriptions:
                data[name] = source.read(source.descriptions.index(name) + 1).astype(np.float32)
        profile = source.profile.copy()
        shape = (source.height, source.width)
        transform = source.transform
    return data, profile, shape, transform


def build_features(data_root: Path, year: int, season: str):
    optical_path = data_root / "rasters" / "composites" / f"composite_{year}_{season}_30m.tif"
    support_path = data_root / "rasters" / "composites" / f"obs_support_{season}_{year}_30m.tif"
    sar_path = data_root / "rasters" / "sar" / f"sar_{year}_{season}_30m.tif"
    for path in (optical_path, support_path, sar_path):
        if not path.exists():
            raise FileNotFoundError(path)

    with rasterio.open(support_path) as source:
        support = source.read(1).astype(np.float32)

    optical, profile, shape, transform = read_named(
        optical_path, ("ndvi_median", "ndvi_max", "ndvi_min", "ndvi_amplitude", "lswi_max", "flood_obs")
    )
    optical["flood_frac"] = np.divide(optical.pop("flood_obs"), np.maximum(support, 1))
    sar, _, _, _ = read_named(sar_path, ("vv_db", "vh_db", "ratio_db", "vh_min_db", "vh_std_db", "low_vh_count", "n_obs"))
    sar["low_vh_frac"] = np.divide(sar.pop("low_vh_count"), np.maximum(sar.pop("n_obs"), 1))

    features = []
    for name in OPTICAL_FEATURES + SAR_FEATURES:
        features.append(optical.get(name, sar.get(name)))
    matrix = np.stack(features, axis=-1)
    valid = np.isfinite(matrix).all(axis=-1) & (support > 0)
    return matrix, valid, OPTICAL_FEATURES + SAR_FEATURES, profile, shape, transform


def reference_points(data_root: Path, year: int):
    db_path = data_root / "db" / "rajshahi_rice.gpkg"
    connection = sqlite3.connect(db_path)
    try:
        frame = pd.read_sql_query(
            "SELECT sample_id, reference_class FROM reference_samples "
            "WHERE reference_year = ? AND reference_class IS NOT NULL AND reference_class != ''",
            connection, params=(year,),
        )
    finally:
        connection.close()
    if frame.empty:
        return None
    samples = gpd.read_file(db_path, layer="reference_samples")
    samples = samples[samples["reference_year"] == year].to_crs(CRS)
    samples = samples[samples["sample_id"].isin(frame["sample_id"])]
    return samples


def pseudo_labels(prob_path: Path, class_path: Path, valid: np.ndarray, low: float = 0.20):
    with rasterio.open(prob_path) as source:
        score = source.read(1)
    with rasterio.open(class_path) as source:
        classes = source.read(1)
    labels = np.full(valid.shape, -1, dtype=np.int8)
    labels[valid & (classes == 1)] = 1
    labels[valid & (classes == 0) & (score <= low)] = 0
    return labels


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--labels", choices=("auto", "pseudo", "reference"), default="auto")
    parser.add_argument("--max-training", type=int, default=120000)
    parser.add_argument("--force", action="store_true")
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
    product_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    union_path = product_dir / f"rice_union_rf_{args.year}_30m.tif"
    if union_path.exists() and not args.force:
        print(f"Refusing to overwrite existing RF products: {union_path}", file=sys.stderr)
        return 2

    label_source = args.labels
    if label_source == "auto":
        label_source = "reference" if reference_points(data_root, args.year) is not None else "pseudo"
    print(f"label source: {label_source}")

    seasonal = {}
    seasonal_valid = {}
    metrics = []
    outputs = []
    importances = {}

    for season in SEASONS:
        matrix, valid, names, profile, shape, transform = build_features(data_root, args.year, season)
        height, width = shape
        y_index, x_index = np.mgrid[0:height, 0:width]
        xmin = transform.c
        ymax = transform.f
        block = ((xmin + x_index * 30) // 1000).astype(np.int32) * 100000 + (
            (ymax - y_index * 30) // 1000
        ).astype(np.int32)

        if label_source == "pseudo":
            prob_path = product_dir / f"rice_prob_{season}_{args.year}_30m.tif"
            class_path = product_dir / f"rice_class_{season}_{args.year}_30m.tif"
            if not prob_path.exists() or not class_path.exists():
                print(f"Missing rule products for pseudo-labels: {prob_path}", file=sys.stderr)
                return 3
            labels = pseudo_labels(prob_path, class_path, valid)
            X = matrix[labels >= 0]
            y = labels[labels >= 0]
            groups = block[labels >= 0]
        else:
            samples = reference_points(data_root, args.year)
            if samples is None:
                print("No reference labels available.", file=sys.stderr)
                return 4
            rows = samples.to_crs(CRS)
            values, targets, group_ids = [], [], []
            for _, sample in rows.iterrows():
                col_f, row_f = ~transform * (sample.geometry.x, sample.geometry.y)
                col, row = int(col_f), int(row_f)
                if 0 <= row < height and 0 <= col < width and valid[row, col]:
                    values.append(matrix[row, col])
                    targets.append(
                        1 if str(sample["reference_class"]).upper() in ("BORO", "AUS", "AMAN", "RICE") else 0
                    )
                    group_ids.append(int(block[row, col]))
            if len(values) < 40:
                print(f"Too few usable reference points for {season}: {len(values)}", file=sys.stderr)
                return 5
            X = np.stack(values)
            y = np.array(targets)
            groups = np.array(group_ids)

        if len(y) < 100 or len(np.unique(y)) < 2:
            print(f"Insufficient or single-class labels for {season}: {len(y)}", file=sys.stderr)
            return 6

        # Balanced subsample for training speed.
        rng = np.random.default_rng(42)
        take = min(args.max_training, len(y))
        chosen = rng.choice(len(y), size=take, replace=False)
        X_train, y_train, groups_train = X[chosen], y[chosen], groups[chosen]

        model = RandomForestClassifier(
            n_estimators=N_ESTIMATORS, class_weight="balanced", n_jobs=-1, random_state=42
        )
        cv_scores = []
        n_splits = min(5, len(np.unique(groups_train)))
        if n_splits >= 2:
            for train_idx, test_idx in GroupKFold(n_splits=n_splits).split(X_train, y_train, groups_train):
                fold = RandomForestClassifier(
                    n_estimators=120, class_weight="balanced", n_jobs=-1, random_state=42
                )
                fold.fit(X_train[train_idx], y_train[train_idx])
                cv_scores.append(accuracy_score(y_train[test_idx], fold.predict(X_train[test_idx])))
        model.fit(X_train, y_train)

        flat = matrix.reshape(-1, matrix.shape[-1])
        probability = np.full(flat.shape[0], np.nan, dtype=np.float32)
        valid_flat = valid.reshape(-1)
        probability[valid_flat] = model.predict_proba(flat[valid_flat])[:, 1]
        probability = probability.reshape(height, width)
        classes = np.full((height, width), 255, dtype=np.uint8)
        classes[valid] = 0
        classes[valid & (probability >= 0.5)] = 1

        prob_out = product_dir / f"rice_prob_rf_{season}_{args.year}_30m.tif"
        class_out = product_dir / f"rice_class_rf_{season}_{args.year}_30m.tif"
        for path, array, dtype, nodata, description in (
            (prob_out, probability, "float32", np.nan, f"rice_prob_rf_{season}"),
            (class_out, classes, "uint8", 255, f"rice_class_rf_{season}"),
        ):
            out_profile = dict(profile)
            out_profile.update(driver="GTiff", count=1, dtype=dtype, nodata=nodata,
                               compress="deflate", predictor=2 if dtype == "float32" else 1,
                               tiled=True, blockxsize=512, blockysize=512, BIGTIFF="IF_SAFER")
            with rasterio.open(path, "w", **out_profile) as destination:
                destination.write(array.astype(dtype), 1)
                destination.descriptions = (description,)
                destination.build_overviews([2, 4, 8], Resampling.average)
            outputs.append(path)

        seasonal[season] = valid & (probability >= 0.5)
        seasonal_valid[season] = valid
        importances[season] = dict(
            sorted(zip(names, [round(float(v), 4) for v in model.feature_importances_]),
                   key=lambda kv: -kv[1])
        )
        metrics.append(
            {
                "season": season,
                "training_pixels": int(len(y)),
                "rice_pixels": int(y.sum()),
                "cv_accuracy_mean": round(float(np.mean(cv_scores)), 4) if cv_scores else None,
                "cv_accuracy_sd": round(float(np.std(cv_scores)), 4) if cv_scores else None,
                "cv_folds": len(cv_scores),
                "predicted_rice_fraction": round(float(seasonal[season].sum() / max(valid.sum(), 1)), 4),
            }
        )
        print(f"{season}: train={len(y)} CV={metrics[-1]['cv_accuracy_mean']} "
              f"rice={100 * metrics[-1]['predicted_rice_fraction']:.1f}%")

    any_valid = np.logical_or.reduce([seasonal_valid[s] for s in SEASONS])
    union = np.logical_or.reduce([seasonal[s] for s in SEASONS]) & any_valid
    intensity = np.zeros(any_valid.shape, dtype=np.uint8)
    for season in SEASONS:
        intensity += seasonal[season].astype(np.uint8)
    intensity[~any_valid] = 255

    with rasterio.open(product_dir / f"rice_class_rf_{SEASONS[0]}_{args.year}_30m.tif") as source:
        profile = source.profile.copy()

    for path, array, description in (
        (product_dir / f"rice_union_rf_{args.year}_30m.tif",
         np.where(union, 1, np.where(any_valid, 0, 255)).astype("uint8"), "rice_union_rf"),
        (product_dir / f"rice_intensity_rf_{args.year}_30m.tif", intensity, "rice_intensity_rf"),
    ):
        out_profile = dict(profile)
        out_profile.update(count=1, dtype="uint8", nodata=255, compress="deflate",
                           predictor=1, tiled=True, blockxsize=512, blockysize=512)
        with rasterio.open(path, "w", **out_profile) as destination:
            destination.write(array, 1)
            destination.descriptions = (description,)
            destination.build_overviews([2, 4, 8], Resampling.nearest)
        outputs.append(path)

    manifest = {
        "artifact": "random_forest_classification",
        "reference_year": args.year,
        "generated_utc": utc_now(),
        "model_version": MODEL_VERSION,
        "label_source": label_source,
        "features": list(OPTICAL_FEATURES + SAR_FEATURES),
        "metrics": metrics,
        "feature_importances": importances,
        "union_rice_fraction": round(float(union.sum() / max(any_valid.sum(), 1)), 4),
        "outputs": [{"path": str(path), "sha256": sha256_file(path)} for path in outputs],
        "limitations": [
            "Pseudo-labels are circular for accuracy claims." if label_source == "pseudo"
            else "Reference sample size may limit precision.",
            "CV accuracy is a diagnostic on training labels, not independent validation.",
            "Independent accuracy requires the stratified reference sample.",
        ],
    }
    manifest_dir.joinpath(f"rf_{args.year}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    row = {
        "reference_year": args.year,
        "label_source": label_source,
        "union_rice_fraction": manifest["union_rice_fraction"],
        "cv_accuracy_mean": round(float(np.mean([m["cv_accuracy_mean"] for m in metrics if m["cv_accuracy_mean"]])), 4),
        "intensity_0": int((intensity == 0).sum()),
        "intensity_1": int((intensity == 1).sum()),
        "intensity_2": int((intensity == 2).sum()),
        "intensity_3": int((intensity == 3).sum()),
    }
    csv_path = TABLE_DIR / "rf_summary.csv"
    frame = pd.DataFrame([row])
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        existing = existing[existing.reference_year != args.year]
        frame = pd.concat([existing, frame], ignore_index=True)
    frame.sort_values("reference_year").to_csv(csv_path, index=False)

    print(f"union rice fraction: {manifest['union_rice_fraction']:.3f}")
    print(f"summary: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
