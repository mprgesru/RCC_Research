#!/usr/bin/env python3
"""Import interpreted labels from the sheet into the database.

Reads `tables/interpretation_sheet.csv`, validates the label vocabulary and writes
one row per point and season into the `reference_labels` table:

- season `LULC`:  reference_class (nine-class legend)
- season BORO/AUS/AMAN: is_rice = 1/0 from the per-season Y/N columns

Unlabelled cells are skipped, not imputed.

Output
------
reference_labels table in the study GeoPackage

Usage
-----
    python import_labels.py --year 2020
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
SHEET = REPO_ROOT / "tables" / "interpretation_sheet.csv"
CLASSES = {
    "BORO", "AUS", "AMAN", "OTHER_CROPLAND", "ORCHARD",
    "OTHER_VEG", "BUILT", "WATER", "BARE",
}
TRUTHY = {"Y", "YES", "1", "TRUE", "T", "RICE"}
FALSY = {"N", "NO", "0", "FALSE", "F", "NON_RICE", "NONRICE"}
CONFIDENCE = {"high", "medium", "low"}


def clean(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def parse_rice(value: str) -> int | None:
    key = value.upper().replace(" ", "_")
    if key in TRUTHY:
        return 1
    if key in FALSY:
        return 0
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--sheet", default=str(SHEET))
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    sheet = Path(args.sheet)
    if not sheet.exists():
        print(f"Sheet not found: {sheet}", file=sys.stderr)
        return 2
    db_path = Path(args.data_root).expanduser().resolve() / "db" / "rajshahi_rice.gpkg"
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 3

    frame = pd.read_csv(sheet, dtype=str).fillna("")
    frame = frame[frame["reference_year"].astype(str) == str(args.year)]
    if frame.empty:
        print("No rows for this year.", file=sys.stderr)
        return 4

    rows = []
    problems = []
    for _, row in frame.iterrows():
        sample_id = clean(row["sample_id"])
        source = clean(row.get("reference_source", ""))
        date = clean(row.get("reference_date", ""))
        interpreter = clean(row.get("interpreter_id", ""))
        overall_confidence = clean(row.get("confidence", "")).lower()
        notes = clean(row.get("notes", ""))

        lulc = clean(row.get("reference_class", "")).upper().replace(" ", "_")
        if lulc:
            if lulc not in CLASSES:
                problems.append(f"{sample_id}: invalid reference_class {lulc!r}")
            else:
                confidence = overall_confidence if overall_confidence in CONFIDENCE else None
                rows.append(
                    (sample_id, args.year, "LULC", lulc, None, source, date,
                     confidence, interpreter, notes)
                )

        for season in ("BORO", "AUS", "AMAN"):
            value = clean(row.get(f"{season.lower()}_rice", ""))
            is_rice = parse_rice(value)
            if value and is_rice is None and value.upper() not in ("NA", "N/A", "-"):
                problems.append(f"{sample_id} {season}: invalid rice value {value!r}")
                continue
            if is_rice is None:
                continue
            confidence = clean(row.get(f"{season.lower()}_confidence", "")).lower()
            rows.append(
                (sample_id, args.year, season, None, is_rice, source, date,
                 confidence if confidence in CONFIDENCE else None, interpreter,
                 clean(row.get("season_notes", "")) or notes)
            )

    if problems:
        print("Label problems found:", file=sys.stderr)
        for item in problems[:20]:
            print(f"  {item}", file=sys.stderr)
        print(f"  ... {len(problems)} total", file=sys.stderr)
        return 5

    if not rows:
        print("No valid labels found. Fill the sheet first.", file=sys.stderr)
        return 6

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("DELETE FROM reference_labels WHERE reference_year = ?", (args.year,))
        connection.executemany(
            """
            INSERT OR REPLACE INTO reference_labels
                (sample_id, reference_year, season, reference_class, is_rice,
                 reference_source, reference_date, confidence, interpreter_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
        counts = connection.execute(
            "SELECT season, COUNT(*) FROM reference_labels WHERE reference_year = ? GROUP BY season",
            (args.year,),
        ).fetchall()
    finally:
        connection.close()

    print(f"imported rows: {len(rows)}")
    for season, count in counts:
        print(f"  {season}: {count}")
    print(f"database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
