# Methods Review and Chosen Approach

Purpose: ground the pipeline in published practice, state what has been adopted,
and record what remains before results are publishable. This is the draft basis
for the article's methods section.

Protocol reference: `Rajshahi_Rice_LandUse_Research_Protocol.md`, commit `bbc4a58`.

## 1. The problem, stated the way the literature states it

Three difficulties recur in Bangladesh rice mapping:

1. **Cloud cover.** Monsoon (Aman) and early Aus seasons are persistently cloudy.
   Optical time series have few valid observations; Landsat alone is weakest in
   exactly the seasons that matter (Singha et al., 2019).
2. **Small, fragmented fields.** Field sizes approach or fall below one 30 m pixel,
   so mixed pixels dominate and parcel-level claims are unsupported (protocol §9).
3. **Seasonal overlap.** Boro, Aus and Aman overlap in calendar time and share
   spectral signatures with other crops, wetland and orchard. One season's
   thresholds do not transfer to another (protocol §2.2, §6 Step 4).

## 2. What comparable studies did

| Study | Data | Method | Validation | Reported accuracy |
| --- | --- | --- | --- | --- |
| Gumma et al. 2014 | MODIS 500 m | Phenology thresholds, three seasons | District statistics, visual | Seasonal area agreement |
| Singha et al. 2019 | Sentinel-1 | SAR backscatter trajectories | Independent samples | OA > 90%; Boro UA 82.4 / PA 95.0; Aus UA 99.4 / PA 90.6; Aman UA 92.8 / PA 86.0 |
| Peña-Arancibia et al. 2020 | Landsat + MODIS | Historic rice-type mapping | Reference samples | Historical rice types |
| Tiwari et al. 2024 | Sentinel-1/2, GEE | Automated in-season mapping, no training samples | Independent samples | Boro mean OA 87.9% |
| Li et al. 2025 (GCD-Rice) | Landsat + Sentinel-1 | TWDTW pre-classification 2016–2023, then random forest back to 1990 | 258,547 visually interpreted samples | OA 88.85%; UA 89.88%; PA 88.52% |
| Zhao et al. 2026 | Landsat + Sentinel-2 | Phenology-based composites, four periods 1995–2024 | Product and sample comparison | 30 m maps, rice and cropping intensity |
| Rahman et al. 2026 | Sentinel-1 | Monthly VV/VH medians, CART/RF/k-NN/SVM, GEE | Field polygons, 5-fold CV | Aman RF 92.7%; Aus CART 99.6%; Aman area within 0.01% of BBS |

Two patterns are consistent across all of them:

- **Temporal features, not single dates.** Every study builds a seasonal time
  series or composite and classifies on its shape.
- **SAR where cloud is the constraint.** The Bangladesh studies converge on
  Sentinel-1 for Aus and Aman, with optical as a complement.

Two cautions are equally consistent:

- **Pixel-level train/test splits leak.** Rahman et al. (2026) explicitly note
  that splitting pixels rather than polygons inflates accuracy through spatial
  autocorrelation. Our design must split by spatial block.
- **Benchmark products are not truth.** GCD-Rice and Zhao et al. are comparisons,
  not validation (protocol §6 Step 6).

## 3. Accuracy and area estimation: the adopted standard

We adopt Olofsson et al. (2014), the standard for land-change accuracy and area
estimation. Three components:

### 3.1 Sampling design

Stratified random sampling with strata defined by mapped class. We extend strata
to mapped class × zone group (`RCC`, `R0_5`, `R5_10`) so that the protocol's zone
comparison is supported by design rather than post-hoc subsetting.

Sample size (Cochran 1977, Eq. 5.25, in Olofsson et al. 2014 Eq. 13):

```text
n = (Σ W_h S_h)^2 / ( SE^2 + (1/N) Σ W_h S_h^2 )
```

where `W_h` is the mapped proportion of stratum `h`, `S_h = sqrt(U_h (1 - U_h))`,
`U_h` is the conjectured user's accuracy, `N` is the pixel count, and `SE` is the
target standard error of overall accuracy.

Allocation follows Olofsson's compromise: a minimum in rare strata, remainder
proportional to area, so that both user's accuracy and area estimates are usable.

Selection is random with at most one point per 1 km block per stratum, which
limits spatial autocorrelation between sample units.

### 3.2 Response design

Reference labels come from dated high-resolution or multi-date imagery and, where
possible, field evidence. Historical labels are recorded as *reference
interpretation*, not field truth (protocol §6 Step 3). Two independent
interpreters review a subset; disagreements are resolved by a documented rule.

### 3.3 Analysis

Let `p_ij` be the estimated proportion of area with map class `i` and reference
class `j`:

```text
p_ij = Σ_h W_h (n_hij / n_h)
```

- overall accuracy `O = Σ_i p_ii`
- user's accuracy `UA_i = p_ii / Σ_j p_ij`
- producer's accuracy `PA_j = p_jj / Σ_i p_ij`
- class area `A_j = p_.j × total_area`
- standard error of an area proportion:
  `SE(p_.j) = sqrt( Σ_h W_h^2 (n_hj/n_h)(1 - n_hj/n_h)/(n_h - 1) )`
- 95% interval `p_.j ± 1.96 SE(p_.j)`

Report the error matrix in terms of area proportion, not raw sample counts, and
report confidence intervals for both accuracy and area. This is what makes the
area table defensible in a paper.

## 4. What our implementation adopts, and why

| Protocol step | Adopted method | Status |
| --- | --- | --- |
| 2 Inventory | Public STAC metadata; per-scene cloud and date records | Done |
| 4 Seasonal mapping | Multi-date composites; phenology metrics (NDVI, LSWI, amplitude, flood fraction); rule baseline | Done, provisional |
| 4 Seasonal mapping (upgrade) | Sentinel-1 VV/VH monthly features for 2015/2020/2025; random forest on SAR + optical features | SAR built; RF awaits reference labels |
| 5 Land cover | Annual spectral rules; nine classes; rice from seasonal products | Done, provisional |
| 3 Reference data | Olofsson stratified design; 27 strata; SE 0.02 → 506 points | Frame built, labels pending |
| 6 Validation | Olofsson estimators; blocked, independent labels; confusion matrix by season and zone | Estimator built, blocked on labels |
| 6 Benchmark | Compare against Zhao et al. 2026 and APRA500 | Complete; Singha, GCD-Rice and BBS unavailable |
| 7 Change | Five-year transition matrices; persistence and intensity transitions | Computed, not interpretable until validated |
| 8 Reproducibility | Manifests, checksums, pinned thresholds, code revisions | Done |

### Why Sentinel-1 is the right next upgrade

Our Landsat-only Aman and Aus composites have median 2–8 valid observations per
pixel, and the provisional classifier's persistence diagnostic (25–40% between
five-year pairs) shows it is unstable. Rahman et al. (2026) and Singha et al.
(2019) both obtain >90% overall accuracy in Bangladesh with Sentinel-1 time series
during exactly these cloudy seasons. Adding VV/VH monthly medians for 2015, 2020
and 2025 is therefore the highest-value methodological change available, and it
is already required by protocol §2.2 and §6 Step 4.

It does not solve the historical years. Landsat remains the only option before
2014, which is why the Landsat-only series must stay separate and flagged.

## 5. Validity threats we will report rather than hide

| Threat | Mitigation |
| --- | --- |
| Spatial autocorrelation inflating accuracy | Blocked sampling; split by block, not pixel |
| Mixed pixels near the urban edge | Report as a stated limitation; avoid parcel-level claims |
| Low observation support in 1990–1995 and Aus | `low_support` flags; wider intervals; no precise trend claims |
| Threshold sensitivity | Report sensitivity across thresholds, not a single number |
| Benchmark mistaken for truth | Products used only for comparison, never as labels |
| Sensor-era discontinuity | Landsat-only baseline; Sentinel comparison separate |
| Boundary status | RCC layer marked `official_operational`, never cadastral |

## 6. Sample size result for this study

Computed from the 2020 land-cover strata (9 classes × 3 zone groups = 27 strata):

| Target SE of overall accuracy | Required n |
| --- | --- |
| 0.010 | 2,017 |
| 0.020 | 506 |
| 0.030 | 225 |
| 0.040 | 127 |

Adopted: **SE 0.02, n = 506**, minimum 20 per non-empty stratum. This yields a
95% half-width of about ±3.9 percentage points on overall accuracy. If resources
allow, SE 0.015 (about 900 points) is a better target for a journal submission.

## 7. What remains before submission

1. Label the reference sample (field visit, dated high-resolution imagery, or
   trusted local agronomic evidence).
2. Confirm season windows with BRRI/DAE.
3. Add Sentinel-1 features and retrain; compare against the rule baseline on
   blocked validation.
4. Run the Olofsson estimator and report adjusted areas with intervals.
5. Compare against Zhao et al. (2026) and APRA500; document the unavailable products.
6. Map land cover with the same evidence standard, or state that transition
   attribution is limited to the classes that can be validated.

## References

- Cochran, W. G. (1977). *Sampling Techniques*, 3rd ed. Wiley.
- Gumma, M. K. et al. (2014). ISPRS J. Photogramm. Remote Sens. https://doi.org/10.1016/j.isprsjprs.2014.02.007
- Li, S. et al. (2025). Scientific Data. https://doi.org/10.1038/s41597-025-05374-1
- Olofsson, P. et al. (2014). Remote Sensing of Environment 148, 42–57. https://doi.org/10.1016/j.rse.2014.02.015
- Peña-Arancibia, J. et al. (2020). Remote Sensing Applications: Society and Environment. https://doi.org/10.1016/j.rsase.2020.100460
- Rahman, H. M. H. et al. (2026). PLoS ONE 21(9), e0355502. https://doi.org/10.1371/journal.pone.0355502
- Singha, M. et al. (2019). Scientific Data 6, 26. https://doi.org/10.1038/s41597-019-0036-3
- Tiwari, V. et al. (2024). J. Environmental Management. https://doi.org/10.1016/j.jenvman.2023.119615
- Zhao, Z. et al. (2026). Earth Syst. Sci. Data 18, 5583–5599. https://doi.org/10.5194/essd-18-5583-2026
