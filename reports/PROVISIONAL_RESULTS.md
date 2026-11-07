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
| Land-cover rasters | 8 | `rasters/products/` (runtime) |
| `map_runs` rows | 64 | database |
| `area_estimates` (mapped only) rows | 320 | database and `tables/area_estimates_mapped.csv` |
| `transition_estimates` rows | 1,129 | database and `tables/transition_estimates_mapped.csv` |

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

## Step 5 — general land cover

Nine-class land cover derived per year from annual spectral state, with rice classes
taken from the seasonal products. 2020 fractions over RCC + 10 km:

| Class | Share |
| --- | --- |
| Boro | 6.3% |
| Aus | 1.0% |
| Aman | 3.8% |
| Other annual crop / fallow | 11.6% |
| Orchard / perennial | 46.8% |
| Other vegetation | 18.9% |
| Built-up | 3.4% |
| Water | 4.5% |
| Bare | 3.6% |

The orchard class is **perennial vegetation with the orchard signal unconfirmed**.
It very likely absorbs homestead trees, and mango orchard cannot be separated
without reference evidence. Built-up is probably underestimated in village areas
because tree cover dilutes the built-up index.

## Step 7 — transitions

1,129 transition rows were computed for seven five-year periods across five zones
and stored in `transition_estimates`.

The matrix works mechanically but is **not measuring land-use change**. The
diagnostic is rice persistence:

| Period | Rice at start (ha) | Still rice at end (ha) | Persistence |
| --- | --- | --- | --- |
| 1995→2000 | 4,443 | 1,795 | 40% |
| 2000→2005 | 10,862 | 4,145 | 38% |
| 2005→2010 | 9,410 | 2,399 | 25% |
| 2010→2015 | 5,053 | 3,010 | 60% |
| 2015→2020 | 13,855 | 3,765 | 27% |
| 2020→2025 | 6,790 | 2,691 | 40% |

Real paddy landscapes persist far more strongly between five-year reference
years. A persistence of 25–40% means the matrix is dominated by year-to-year
classifier disagreement, not conversion. The largest single transition,
4,711 ha of rice to "orchard" between 2015 and 2020, is not a credible
land-management process at that scale; it is classification noise.

**Do not report any transition result.** The machinery is correct; the inputs to
it are not yet calibrated.

## Step 3 — reference sample frame

The stratified design was sized with the Cochran/Olofsson formula using
conjectured user's accuracies and 2020 land-cover strata (9 classes × 3 zone
groups = 27 strata).

| Target SE (overall accuracy) | Required n |
| --- | --- |
| 0.010 | 2,017 |
| 0.020 | 506 |
| 0.030 | 225 |
| 0.040 | 127 |

Adopted: **SE 0.02, n = 506**, minimum 20 per non-empty stratum, one point per
1 km block. The frame is written to `reference_samples` (527 points after
allocation), `tables/sample_design.csv` and a blinded
`tables/interpretation_sheet.csv`.

Chips are exported from Sentinel-2 L2A as three-panel images (true colour, false
colour, NDVI). Chip titles and the interpretation sheet deliberately omit the
mapped class so that labelling is independent.

A first visual check already confirms the over-detection problem: sample
`S2020-0001` is mapped as Boro rice inside RCC but the imagery shows dense
homestead vegetation and trees.

**No accuracy has been computed.** The estimator is implemented and tested on a
synthetic copy; it will not produce numbers until real labels exist.

## Benchmark products

Final benchmark set: Zhao et al. (2026) for 1995, 2005, 2015 and 2024, and
APRA500 for 2000, 2005, 2010, 2015 and 2020.

| Product | Access | Status |
| --- | --- | --- |
| Zhao et al. 2026 | Zenodo, `10.5281/zenodo.21349862` | Used |
| APRA500 | Zenodo, `10.5281/zenodo.5557022` | Used |
| Singha et al. 2017 | figshare, `10.6084/m9.figshare.7873157` | Not used — host blocked, no mirror |
| GCD-Rice | Science Data Bank, `10.57760/sciencedb.21665` | Not used — not retrievable |
| BBS yearbooks | bbs.gov.bd | Not used — unreachable |

The comparison script finds the GeoTIFFs by file name, so they do not need a fixed
folder. Run it with `--data-root` and, if needed, `--external-dir`.

## Sentinel-1 feature stack

Nine seasonal SAR products were built (2015, 2020, 2025 × Boro, Aus, Aman) from
Sentinel-1 RTC gamma0, resampled from 10 m to the 30 m study grid.

| Check | Result |
| --- | --- |
| 2020 Aman scenes | 33 of 33 read |
| Median valid SAR observations | 32 per pixel |
| VV median | −7.8 dB |
| VH median | −14.3 dB |
| VH−VV ratio median | −6.4 dB |

This is the cloud-independent evidence the Landsat series lacks. Aman has 32 SAR
observations where the optical composite has 5.

## Random forest with pseudo-labels

An RF classifier was implemented over 12 features (6 optical, 6 SAR) with
spatially blocked cross-validation. It was trained on pseudo-labels derived from
the rule baseline.

**It is circular and must not be reported as a result.**

| Year | Union rice fraction | Rule union | Blocked CV |
| --- | --- | --- | --- |
| 2015 | 54.4% | 21.6% | 1.00 |
| 2020 | 31.6% | 11.1% | 1.00 |
| 2025 | 27.9% | 10.1% | 1.00 |

CV accuracy of exactly 1.00 is the tell: the labels are a threshold on the same
optical features fed to the model, so the model trivially reconstructs them.

One genuine improvement was measured: five-year persistence rose from 31% (rule)
to 48% (RF) for 2015→2020 and from 38% to 67% for 2020→2025. The RF is temporally
more consistent, but it inflates rice area to implausible levels. Consistency
without calibration is not accuracy.

Conclusion: the RF is complete and will accept `--labels reference`. It should
not be run with pseudo-labels for any reported figure.

## Reference chips

All 527 points have chips for all three seasons (1,581 images), exported from
Sentinel-2 as three panels (true colour, false colour, NDVI), blinded to the map
class. `tables/interpretation_sheet.csv` lists the three chip paths per point with
blank label fields.

## Benchmark comparison (Zhao 2026 and APRA500)

Two benchmarks were compared at overlapping years: Zhao et al. (2026) at 30 m and
APRA500 at 500 m.

| Product | Year | Our rice | Product rice | Agreement | IoU |
| --- | --- | --- | --- | --- | --- |
| Zhao 2026 | 1995 | 4.8% | 19.6% | 0.796 | 0.077 |
| Zhao 2026 | 2005 | 11.8% | 12.3% | 0.794 | 0.077 |
| Zhao 2026 | 2015 | 17.0% | 12.7% | 0.791 | 0.151 |
| Zhao 2026 | 2024→2025 | 7.1% | 10.6% | 0.844 | 0.053 |
| APRA500 | 2000 | 12.0% | 10.8% | 0.842 | 0.134 |
| APRA500 | 2005 | 11.8% | 11.0% | 0.841 | 0.148 |
| APRA500 | 2010 | 5.2% | 13.4% | 0.862 | 0.124 |
| APRA500 | 2015 | 17.0% | 23.2% | 0.756 | 0.209 |
| APRA500 | 2020 | 7.1% | 16.6% | 0.827 | 0.123 |

IoU is lowest inside RCC (0.02–0.07 for both products) and highest in the outer
ring (APRA500 0.20–0.34). That is consistent with the hypothesis that published
products diverge most in mixed urban–agricultural pixels.

Cautions: agreement is dominated by matching non-rice area and is not accuracy;
APRA500 at 500 m cannot resolve field boundaries, so its area shares and zonal
pattern are the meaningful comparison; and our under-detection in 2010 and 2020
(5–7% against 13–17%) contributes to the disagreement.

Singha et al. (2019) could not be retrieved: figshare returns an AWS WAF challenge
and no mirror exists. APRA500 was substituted and the substitution is recorded in
the manuscript.
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
