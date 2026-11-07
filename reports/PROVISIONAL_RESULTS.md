# Provisional Results — Unvalidated

**Status:** generated 2026-11-07. **Provisional. Do not cite as findings.**
**Model:** `rules-0.3.0-provisional`, thresholds uncalibrated.
**Data:** Landsat C2 L2, eight target years, 30 m, EPSG:32645.

This note records what the pipeline produced and why the numbers are not yet
interpretable. It is a build record, not a results section.

## What was produced

| Artifact | Count | Location |
| --- | --- | --- |
| Seasonal composites (12 bands + flood count) | 24 | `rasters/composites/` (runtime) |
| Observation-support rasters | 24 | `rasters/composites/` (runtime) |
| Seasonal probability and class rasters | 48 | `rasters/products/` (runtime) |
| All-rice union rasters | 8 | `rasters/products/` (runtime) |
| Cropping-intensity rasters | 8 | `rasters/products/` (runtime) |
| `map_runs` rows | 64 | database |
| `area_estimates` (mapped only) rows | 320 | database and `tables/area_estimates_mapped.csv` |

The grid is 1098 × 911 pixels at 30 m. All 24 composites completed; two 2025 Boro
scenes (`LC09_..._20241221`, `LC08_..._20241229`) were not yet ingested in the
Planetary Computer catalog, so 21 of 23 scenes were used for that season.

## Observation support

Median valid observations per pixel after cloud, shadow, cirrus, saturation and
fill masking.

| Year | Boro | Aus | Aman |
| --- | --- | --- | --- |
| 1990 | 6 | 2 | 2 |
| 1995 | 5 | 2 | 3 |
| 2000 | 12 | 4 | 7 |
| 2005 | 15 | 3 | 5 |
| 2010 | 9 | 3 | 7 |
| 2015 | 11 | 5 | 8 |
| 2020 | 14 | 3 | 5 |
| 2025 | 15 | 4 | 8 |

Low-support flags were raised for 1990 Boro and Aman, 1990 Aus and 1995 Aus.
Every other season cleared the three-observation median threshold.

## Provisional mapped areas — RCC + 10 km

All-rice union, unadjusted pixel counts converted to hectares.

| Year | Mapped ha | Share of valid area |
| --- | --- | --- |
| 1990 | 392 | 0.6% |
| 1995 | 4,443 | 6.4% |
| 2000 | 10,862 | 15.7% |
| 2005 | 9,410 | 13.6% |
| 2010 | 5,053 | 7.3% |
| 2015 | 13,855 | 20.0% |
| 2020 | 6,790 | 9.8% |
| 2025 | 6,584 | 9.5% |

## Why these numbers are not findings

1. **The thresholds are uncalibrated.** No reference samples exist yet, so the
   values in `references/classification-thresholds.json` are placeholders.
2. **The result is highly threshold-sensitive.** Varying only the flood-fraction
   threshold changes the RCC + 10 km union share substantially:

   | Year | frac ≥ 0.1 | frac ≥ 0.2 | frac ≥ 0.3 | frac ≥ 0.4 |
   | --- | --- | --- | --- | --- |
   | 1990 | 0.9% | 0.7% | 0.6% | 0.5% |
   | 1995 | 7.1% | 6.7% | 4.7% | 1.7% |
   | 2000 | 26.7% | 17.1% | 10.7% | 7.1% |
   | 2005 | 22.0% | 14.3% | 5.3% | 3.4% |
   | 2010 | 14.3% | 8.2% | 3.8% | 1.9% |
   | 2015 | 43.7% | 21.6% | 9.0% | 4.9% |
   | 2020 | 18.8% | 11.1% | 6.2% | 3.6% |
   | 2025 | 17.9% | 10.1% | 6.4% | 5.3% |

3. **Detection probability still varies with scene count.** 1990 has 4–8 scenes
   per season; later years have 15–23. Even with observation normalisation, a
   season with two usable dates cannot catch a short flooding window.
4. **No land-cover product exists yet**, so rice loss cannot be attributed to
   built-up, orchard, water or other classes.
5. **No independent validation has been done.** No UA, PA, F1, confidence
   interval or accuracy-adjusted area can be reported.

The year-to-year pattern above should not be read as land-use change. It mixes
signal with observation opportunity.

## What must happen before results are reported

| Step | Dependency |
| --- | --- |
| Stratified, spatially blocked reference samples | Manual interpretation of high-resolution imagery |
| Calibrate per-season thresholds on the calibration split | Reference samples |
| Train and compare random forest against the rule baseline | Calibration samples |
| Independent validation on the held-out split | Validation samples |
| Accuracy-adjusted areas with 95% intervals | Validation results |
| General land-cover classes for transition attribution | Separate classification |
| Sentinel-1/2 comparison for 2020 and 2025 | Composites and samples |
| Transition matrices | Land-cover product across years |

## Reproduce

```bash
export RAJSHAHI_RICE_DATA_ROOT=/home/coder/research-runtime/rajshahi-rice
cd RCC_Research

python skill/rajshahi-rice-landuse/scripts/build_composites.py --year 2020 --season BORO --force
python skill/rajshahi-rice-landuse/scripts/classify.py --year 2020 --force
python skill/rajshahi-rice-landuse/scripts/load_tables.py --year 2020

# all years
for y in 1990 1995 2000 2005 2010 2015 2020 2025; do
  for s in BORO AUS AMAN; do
    python skill/rajshahi-rice-landuse/scripts/build_composites.py --year "$y" --season "$s" --force
  done
  python skill/rajshahi-rice-landuse/scripts/classify.py --year "$y" --force
done
python skill/rajshahi-rice-landuse/scripts/load_tables.py
```

Run manifests with per-scene lists, failed scenes and SHA-256 checksums are under
`${RAJSHAHI_RICE_DATA_ROOT}/rajshahi-rice/manifests/`.
