#!/usr/bin/env bash
# Reproduce the Rajshahi rice pipeline from committed inputs.
# Requires RAJSHAHI_RICE_DATA_ROOT to point outside the repository.
set -euo pipefail

: "${RAJSHAHI_RICE_DATA_ROOT:?set RAJSHAHI_RICE_DATA_ROOT to an absolute writable path}"
PY="${PYTHON:-python}"
SKILL="skill/rajshahi-rice-landuse/scripts"

echo "== Step 1: boundaries"
"$PY" "$SKILL/build_zones.py" --force

echo "== Step 1-2: database"
"$PY" "$SKILL/make_db.py" --force

echo "== Step 2: scene inventory"
"$PY" "$SKILL/stac_inventory.py"

echo "== Step 4: optical composites"
for year in 1990 1995 2000 2005 2010 2015 2020 2025; do
  for season in BORO AUS AMAN; do
    "$PY" "$SKILL/build_composites.py" --year "$year" --season "$season" --force
  done
done

echo "== Step 4: rule-based rice maps"
for year in 1990 1995 2000 2005 2010 2015 2020 2025; do
  "$PY" "$SKILL/classify.py" --year "$year" --force
done

echo "== Step 5: land cover"
for year in 1990 1995 2000 2005 2010 2015 2020 2025; do
  "$PY" "$SKILL/classify_lulc.py" --year "$year" --force
done

echo "== Step 4 upgrade: Sentinel-1 features (2015, 2020, 2025)"
for year in 2015 2020 2025; do
  for season in BORO AUS AMAN; do
    "$PY" "$SKILL/build_sar_composites.py" --year "$year" --season "$season" --force
  done
done

echo "== Load tables and transitions"
"$PY" "$SKILL/load_tables.py"
"$PY" "$SKILL/transitions.py"

echo "== Step 3: reference design and chips"
"$PY" "$SKILL/sample_design.py" --year 2020 --se 0.02 --force
for season in BORO AMAN AUS; do
  "$PY" "$SKILL/export_chips.py" --year 2020 --season "$season" --limit 600
done

echo "== Step 2 and 8: summaries"
"$PY" "$SKILL/support_summary.py"
"$PY" "$SKILL/study_manifest.py"

echo "== Step 6: validation (requires interpreted samples)"
"$PY" "$SKILL/import_labels.py" --year 2020 || true
for measure in LULC BORO AUS AMAN; do
  "$PY" "$SKILL/validate.py" --year 2020 --measure "$measure" || true
done

echo "== Step 6: benchmark (requires manually downloaded products)"
"$PY" "$SKILL/benchmark_products.py" || true

echo "Done. Random forest is intentionally excluded: it requires reference labels."
