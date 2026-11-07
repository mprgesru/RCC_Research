# Manuscript Draft

**Working title:** Seasonal rice persistence and rice-to-urban conversion across
Rajshahi City Corporation and its peri-urban rings, Bangladesh, 1990–2025

**Status:** draft. Sections marked `[PENDING]` require interpreted reference
samples or manually downloaded benchmark products. Do not submit with placeholders.

**Target journals:** *Remote Sensing* / *GIScience & Remote Sensing* / *Scientific
Data* (if released as a dataset descriptor).

**Keywords:** paddy rice; Landsat; Sentinel-1; peri-urban; accuracy assessment;
Bangladesh; land-use change

---

## Abstract

Rice cultivation around rapidly expanding South Asian cities is being converted to
built-up land, but the conversion is hard to quantify because monsoon cloud cover,
small field sizes and overlapping cropping seasons defeat single-date optical
mapping. We assemble a 30 m, eight-epoch (1990–2025) record of seasonal rice
(Boro, Aus, Aman) for Rajshahi City Corporation and two non-overlapping peri-urban
rings, and combine it with a Sentinel-1 feature stack for the recent era. We use a
fixed, documented geography in EPSG:32645, multi-date phenology composites, and a
stratified probability sample designed to estimate accuracy and area with
confidence intervals. `[PENDING]` We report that rice extent changed from X to Y km²
in RCC and from A to B km² in the outer ring, with Z% of mapped rice loss
attributable to built-up conversion. `[PENDING]` Independent validation yields an
overall accuracy of X% (95% CI) and area estimates that differ from raw pixel
counts by Y%. We also quantify disagreement between our maps and two published
rice products in the fragmented urban fringe, where mixed pixels are most severe.
**Plain-language summary.** `[PENDING]`

---

## 1. Introduction

Rice is the staple crop of Bangladesh and the dominant land use of its floodplains.
Around divisional cities, urban expansion converts irrigated paddy to housing,
roads and brickfields, often in small parcels that are invisible to coarse
satellite products. Rajshahi is a useful case: a mid-sized city corporation
surrounded by intensive agriculture and mango orchard, with a well-documented
urban footprint and three overlapping rice seasons.

Mapping rice here is difficult for three reasons established in the literature.
First, monsoon cloud cover leaves few clear optical observations during Aus and
Aman (Singha et al., 2019). Second, fields approach the 30 m pixel size, so mixed
pixels dominate (protocol §9). Third, seasons overlap in calendar time and share
spectral signatures with other crops and wetland, so a single threshold does not
transfer between seasons (Dong and Xiao, 2016; Gumma et al., 2014).

Existing work takes two routes. Phenology-based optical composites exploit the
flood-to-green-up sequence (Xiao et al., 2006; Gumma et al., 2014; Zhao et al.,
2026), and synthetic-aperture radar exploits the low backscatter of flooded fields
(Singha et al., 2019; Rahman et al., 2026). Continental products now cover much of
the period: GCD-Rice maps three seasons at 30 m from 1990 to 2023 (Li et al.,
2025), and Zhao et al. (2026) map rice and cropping intensity from 1995 to 2024.
Both report high aggregate accuracy, but aggregate accuracy does not guarantee
performance in fragmented peri-urban fields, which is precisely where land-use
change concentrates.

We therefore do not claim to produce the first historical rice map. Our
contribution is a locally grounded, uncertainty-aware assessment of seasonal rice
and rice-to-urban conversion in a city-edge landscape, with three specific aims:

1. Produce a consistent 30 m seasonal rice record for a fixed geography of RCC and
   two non-overlapping rings from 1990 to 2025.
2. Separate seasonal area, all-rice physical footprint and cropping intensity.
3. Quantify accuracy and area with a probability sample, and benchmark published
   products in the urban fringe.

---

## 2. Study area and data

### 2.1 Study area and zones

Rajshahi City Corporation (RCC) sits on the north bank of the Padma in
north-western Bangladesh. We use the 30-ward RCC boundary published in the
WHO/UNICEF EPI digital microplanning dashboard (portal item
`bfdf7c83715a4b0781e113fb16fd2ab7`, modified 2024-10-15). The dissolved boundary
measures **46.23 km²**, confirmed by the project owner as the study definition.

Five zones are defined in EPSG:32645 (WGS 84 / UTM zone 45N):

| Zone | Definition | Area (km²) |
| --- | --- | --- |
| `RCC` | City corporation | 46.23 |
| `R0_5` | 5 km buffer minus RCC | 252.24 |
| `R5_10` | 10 km buffer minus 5 km buffer | 394.23 |
| `RCC_5` | RCC plus 0–5 km (cumulative) | 298.46 |
| `RCC_10` | RCC plus both rings (cumulative) | 692.69 |

Rings are non-overlapping; measured overlap with RCC and between rings is
0.000 km². The layer is an **operational** health-microplanning boundary, not a
cadastral or survey boundary; every output records `boundary_status =
official_operational`, and its licence is unstated.

### 2.2 Satellite data

| Source | Use | Access |
| --- | --- | --- |
| Landsat 4–9 Collection 2 Level-2 | Seasonal optical composites, all years | Public STAC |
| Sentinel-1 RTC (VV/VH) | Cloud-independent features, 2015–2025 | Planetary Computer |
| Sentinel-2 L2A | Recent optical comparison, 2016 onward | Planetary Computer |

The AOI is Landsat path/row 138/043. Scene inventory identified 17 Landsat scenes
for 1990 rising to about 60 per year from 2015; Sentinel-2 has **no coverage over
the AOI in 2015**, and Earth Search lacks Sentinel-2 over Bangladesh before 2017,
so Planetary Computer is the catalog of record for Sentinel-2.

Season windows are **confirmed** (project owner, 2026-11-07): Boro
November–April labelled by harvest year, Aus May–August, Aman June–November.

### 2.3 Benchmark products

| Product | Period | Resolution | Role |
| --- | --- | --- | --- |
| Zhao et al. (2026) | 1995–2024 | 30 m | Benchmark |
| APRA500 | 2000–2021 | 500 m | Benchmark |
| Singha et al. (2019) | 2017 | Sentinel-1 maps | Not used: host blocked |
| GCD-Rice (Li et al., 2025) | 1990–2023 | 30 m, three seasons | Not used: files not retrievable |
| BBS agricultural yearbooks | annual | district | Not used: site unreachable |

Benchmarks are comparisons, not truth. Zhao et al. (2026) and APRA500 form the
final comparison set. APRA500 is coarse (500 m), so its comparison is interpreted
at area and zonal level rather than at pixel boundaries. The three unavailable
products are documented as limitations.

---

## 3. Methods

### 3.1 Study geography and boundary provenance

Wards were retrieved from the ArcGIS FeatureServer as GeoJSON, repaired with
`make_valid` (one invalid ring), reprojected to EPSG:32645, and dissolved. Buffers
of 5 and 10 km were cut inward to form non-overlapping rings. Geometry validity,
part/union area difference (0.002 km²), ring overlap (0.000 km²) and the
dissolved area (46.227 km², 0.007% from 46.23) were asserted before writing. The
current boundary is held fixed for the historical comparison; a historical-boundary
sensitivity analysis is not attempted because comparable dated ward boundaries were
not available.

### 3.2 Observation inventory and composites

For each target year and season we queried a public STAC catalog, masked cloud,
shadow, cirrus, snow, fill and saturated pixels using `QA_PIXEL` and `QA_RADSAT`,
and counted valid observations per pixel. Composites were built on a fixed
1098 × 911 grid at 30 m (EPSG:32645).

From each seasonal stack we derived: median reflectance in six bands; NDVI and
LSWI medians; NDVI maximum, minimum and amplitude; maximum LSWI; and two
flooding indicators — the count of scenes where `LSWI ≥ NDVI` and `LSWI > 0.05`,
and its fraction of valid observations.

$$\mathrm{NDVI}=\frac{\rho_{NIR}-\rho_{R}}{\rho_{NIR}+\rho_{R}},\qquad
\mathrm{LSWI}=\frac{\rho_{NIR}-\rho_{SWIR1}}{\rho_{NIR}+\rho_{SWIR1}}.$$

Flood fraction is preferred to raw flood counts because counts scale with scene
availability and bias detection upward in scene-rich years.

### 3.3 Seasonal rice mapping

A phenology rule set provides the baseline. A pixel is rice in a season when

```text
flood_frac ≥ f,  LSWI_max ≥ l,  NDVI_amplitude ≥ a,  NDVI_max ≥ m
```

with per-season thresholds stored in
`references/classification-thresholds.json` (`rules-0.3.0-provisional`). The
all-rice union is the spatial union of the three seasonal layers; intensity is the
number of mapped seasons (0–3). Seasonal area, union and intensity are reported
separately.

For the recent era we built a Sentinel-1 RTC feature stack (VV, VH, VH−VV, VH
minimum, VH standard deviation, low-VH fraction, observation count) for 2015,
2020 and 2025. A random forest was implemented over six optical and six SAR
features with spatially blocked `GroupKFold` cross-validation by 1 km block. The
classifier accepts interpreted reference labels; with pseudo-labels derived from
the rule baseline it is circular (cross-validation accuracy 1.00) and inflates
area, so its outputs are not used for any reported result. This is stated rather
than hidden because it is a common failure mode when no independent labels exist.

### 3.4 Land cover for transition attribution

A nine-class land-cover layer was derived per year from annual spectral state
(median of seasonal medians) and the rice products: water (NDWI > 0.10 and
NDVI < 0.30), built-up (NDBI > 0.05 and NDVI < 0.35), bare, orchard/perennial
(high, stable NDVI), other annual crop (seasonal amplitude ≥ 0.25), and other
vegetation. Rice classes are assigned from the seasonal products by highest
probability. Orchard is reported as perennial vegetation with the orchard signal
unconfirmed; mango orchard cannot be separated without reference evidence, as the
protocol anticipates.

### 3.5 Reference data design

We follow Olofsson et al. (2014). Strata are mapped class × zone group
(9 classes × 3 groups = 27). Sample size follows Cochran (1977, Eq. 5.25):

$$n=\frac{\left(\sum_h W_h S_h\right)^2}{SE^2+\frac{1}{N}\sum_h W_h S_h^2},$$

with $S_h=\sqrt{U_h(1-U_h)}$ from conjectured user's accuracies. Allocation gives a
minimum of 20 to each non-empty stratum and distributes the remainder in
proportion to area. Selection is random with at most one point per 1 km block, to
limit spatial autocorrelation.

At $SE = 0.02$ this yields **n = 506** (527 realised); at 0.015 it yields about
900. Points are stored in the GeoPackage `reference_samples` layer. Interpretation
chips are exported from Sentinel-2 as three panels (true colour, false colour,
NDVI) and are **blinded** to the map class so that labels are independent. The
interpretation sheet records one land-cover class and three seasonal rice calls
per point (`Y`/`N`/`NA`), each with its own confidence, so a single pass supports
both land-cover and seasonal validation.

Reference labels are not yet available. Consequently no accuracy figure is
reported in this draft. The estimator is implemented and was verified on a
synthetic copy, which was then deleted.

### 3.6 Accuracy and area estimation

With $p_{ij}=\sum_h W_h n_{hij}/n_h$ as the area proportion in map class $i$ and
reference class $j$:

$$O=\sum_i p_{ii},\qquad UA_i=\frac{p_{ii}}{\sum_j p_{ij}},\qquad
PA_j=\frac{p_{jj}}{\sum_i p_{ij}},$$

class area $A_j=p_{\cdot j}A_{total}$, and

$$SE(p_{\cdot j})=\sqrt{\sum_h W_h^2\,\frac{\hat p_{hj}(1-\hat p_{hj})}{n_h-1}}.$$

Intervals are $p \pm 1.96\,SE$. The error matrix is reported in area proportions,
not raw counts. The estimator is implemented separately for the land-cover map
and for each seasonal rice map (`LULC`, `BORO`, `AUS`, `AMAN`), using the same
probability sample and design weights.

### 3.7 Change analysis

For each consecutive five-year pair we computed rice persistence, loss and gain
for the union and each season, cross-tabulated against land cover at the later
date, and aggregated by zone. Areas are mapped only; accuracy-adjusted transitions
require validated labels. Cumulative zones are never summed with their components.

### 3.8 Product benchmarking

The final benchmark set is Zhao et al. (2026) at 30 m for 1995, 2005, 2015 and
2024, and APRA500 at 500 m for 2000, 2005, 2010, 2015 and 2020. Benchmarks are
reprojected to the study grid and compared by zone using agreement and
intersection-over-union. Because product class codes differ, rice values are
declared explicitly per product. APRA500 is interpreted at area and zonal level
because its 500 m cells cannot resolve field boundaries. Agreement is not accuracy
and is not reported as such. Singha et al. (2019), GCD-Rice and BBS are excluded
because their files were not retrievable; all remain cited as limitations.

### 3.9 Reproducibility

Each stage writes a manifest with parameters, scene lists and SHA-256 checksums;
`manifests/study_manifest.json` consolidates them with the code revision and
environment. A single `scripts/run_all.sh` reproduces the pipeline. Thresholds are
versioned files, not constants buried in code.

### 3.10 Protocol compliance and deviations

Every protocol step was addressed. Where a step could not be completed, the
constraint and the adopted best practice are recorded here, as Olofsson et al.
(2014) recommend.

| Protocol step | Implementation | Status |
| --- | --- | --- |
| 1 Boundary and manifest | 30 wards → 5 zones, consolidated manifest | Complete |
| 2 Observation inventory | STAC inventory, valid-observation counts by zone | Complete |
| 3 Seasonal reference data | 506-point stratified frame, blinded chips | Frame complete; labels pending |
| 4 Seasonal rice mapping | Multi-date composites, phenology metrics, rule baseline | Complete, uncalibrated |
| 4 Sentinel-1 upgrade | Nine SAR seasonal products, 2015/2020/2025 | Complete |
| 4 Random forest | Implemented, accepts reference labels | Not reportable on pseudo-labels |
| 5 General land cover | Nine-class derived layer per year | Complete, unvalidated |
| 6 Validation | Olofsson estimator with intervals | Blocked on labels |
| 6 Benchmark | Script ready, products require manual download | Blocked on retrieval |
| 7 Change | Persistence, loss, gain by zone | Computed; not interpretable |
| 8 Reproducible outputs | Manifests, checksums, environment, run script | Complete |

Documented deviations and their justification:

1. **Reference labels are not yet interpreted.** We do not substitute product
   labels for reference data, which would be circular. Instead we report the
   sampling design and withhold accuracy and adjusted area. The best-practice
   alternative is the Olofsson design we implement; other Bangladesh studies
   (Singha et al., 2019; Rahman et al., 2026) obtained independent samples by
   field survey and visual interpretation, which is the remaining human task.
2. **No Sentinel-2 in 2015.** The sensor-era comparison uses Sentinel-1 only for
   2015; 2020 and 2025 use Sentinel-1 and Sentinel-2. Results are labelled by
   sensor set and not spliced.
3. **Thresholds are uncalibrated.** Rule thresholds are placeholders pending
   calibration on the calibration split of the reference sample.
4. **Random forest uses pseudo-labels.** It is excluded from results; the
   manuscript reports this as a design constraint rather than presenting inflated
   areas.
5. **Benchmark scope limited to two products.** Singha et al. (2019) could not be
   retrieved because its only host (figshare) returns an AWS WAF challenge, and no
   mirror exists. GCD-Rice and the BBS yearbooks were likewise not retrievable. We
   substitute APRA500, a published multi-year monsoon-Asia product, as the second
   benchmark and report the substitution. Its 500 m resolution limits comparison
   to area and zonal patterns, not pixel boundaries. The estimator and comparison
   script accept the missing products without modification.
6. **Boundary status.** The RCC layer is operational, not cadastral, and its
   licence is unstated. Historical boundary sensitivity is not attempted.

---

## 4. Results

### 4.1 Data availability and observation support

Landsat scene counts rise from 17 (1990) to about 60 per year from 2015. Median
valid observations per pixel after masking are shown below; 1990 and 1995 Aus and
Aman are the weakest.

| Year | Boro | Aus | Aman |
| --- | --- | --- | --- |
| 1990 | 6.0 | 2.0 | 2.0 |
| 1995 | 5.2 | 2.0 | 3.0 |
| 2000 | 12.0 | 4.0 | 7.0 |
| 2005 | 15.4 | 3.0 | 5.0 |
| 2010 | 9.0 | 3.0 | 7.0 |
| 2015 | 11.0 | 5.6 | 8.0 |
| 2020 | 13.8 | 3.0 | 5.0 |
| 2025 | 15.0 | 4.6 | 7.8 |

Sentinel-1 supplies a median of 32 valid observations per pixel for 2020 Aman,
against 5 optical observations.

### 4.2 Provisional maps

`[PENDING VALIDATION]` Provisional all-rice union area for RCC + 10 km ranges from
0.6% (1990) to 20.0% (2015) of valid area under the current thresholds. These
values are threshold-sensitive and are not reported as findings. Threshold
sensitivity across flood-fraction cuts is tabulated in
`reports/PROVISIONAL_RESULTS.md`.

### 4.3 Product comparison

| Product | Year | Our rice | Product rice | Agreement | IoU |
| --- | --- | --- | --- | --- | --- |
| Zhao 2026 | 1995 | 4.8% | 19.6% | 0.796 | 0.077 |
| Zhao 2026 | 2005 | 11.8% | 12.3% | 0.794 | 0.077 |
| Zhao 2026 | 2015 | 17.0% | 12.7% | 0.791 | 0.151 |
| Zhao 2026 | 2024 → 2025 | 7.1% | 10.6% | 0.844 | 0.053 |
| APRA500 | 2000 | 12.0% | 10.8% | 0.842 | 0.134 |
| APRA500 | 2005 | 11.8% | 11.0% | 0.841 | 0.148 |
| APRA500 | 2010 | 5.2% | 13.4% | 0.862 | 0.124 |
| APRA500 | 2015 | 17.0% | 23.2% | 0.756 | 0.209 |
| APRA500 | 2020 | 7.1% | 16.6% | 0.827 | 0.123 |

IoU is lowest inside RCC (0.02–0.07 for both products) and highest in the outer
ring (APRA500 0.20–0.34), consistent with greater divergence in mixed
urban–agricultural pixels. Agreement is inflated by matching non-rice area and
should not be read as accuracy. APRA500's 500 m cells make pixel-level IoU
structurally lower; its area shares and zonal pattern are the meaningful
comparison. Our own under-detection in 2010 and 2020 (5–7% against 13–17%)
contributes to the disagreement.

### 4.4 Accuracy and area

`[PENDING LABELS]` Table 4 will report the area-proportion error matrix, overall
accuracy with 95% interval, user's and producer's accuracy by class, and
accuracy-adjusted class areas with intervals.

### 4.5 Change and transitions

`[PENDING VALIDATION]` Table 5 will report persistence, loss and gain by zone and
period, and transitions from rice to built-up, orchard, other cropland, water and
bare land.

---

## 5. Discussion

### 5.1 Contribution

The study contributes a fixed-geography, uncertainty-aware record of seasonal rice
in a South Asian urban fringe, with three methodological features that are often
missing: non-overlapping rings and cumulative extents reported separately;
explicit separation of seasonal area, physical footprint and cropping intensity;
and a probability sample designed for area estimation rather than pixel counts.

### 5.2 Limitations

Mixed pixels near the urban edge limit parcel-level inference. Historical reference
evidence is uneven, and early Aus and Aman seasons have very low observation
support. Rule thresholds are uncalibrated, and the random-forest experiment shows
that self-training without independent labels produces plausible-looking but
circular results. The boundary is operational, not legal. These limits are reported
rather than smoothed.

### 5.3 Relevance

`[PENDING]` If validated, the record supports monitoring of farmland conversion in
peri-urban Rajshahi and provides a template for other divisional cities where
cloud cover and small fields defeat coarse products.

---

## 6. Conclusions

`[PENDING]`

---

## Data and code availability

- Code and summary tables: `https://github.com/mprgesru/RCC_Research`
- Processing environment and checksums: `manifests/study_manifest.json`,
  `environment/pip-freeze.txt`
- Rasters: Zenodo DOI `[PENDING RELEASE]`
- Benchmark products retain their original licences.

## Ethics

No human subjects. Field interpretation, if undertaken, will follow informed
consent and data-minimisation practice.

## References

- Cochran, W. G. (1977). *Sampling Techniques*, 3rd ed. Wiley.
- Han, J., Zhang, Z., Luo, Y., Cao, J., Zhang, L., Cheng, F., Zhuang, H., & Zhang, J. (2021). APRA500: a 500 m annual paddy rice dataset for monsoon Asia using multisource remote sensing data [Data set]. Zenodo. https://doi.org/10.5281/zenodo.5557022
- Dong, J., & Xiao, X. (2016). Evolution of regional to global paddy rice mapping methods: A review. *ISPRS J. Photogramm. Remote Sens.* https://doi.org/10.1016/j.isprsjprs.2016.05.010
- Gumma, M. K., et al. (2014). Mapping seasonal rice cropland extent and area in the high cropping intensity environment of Bangladesh using MODIS 500 m data for the year 2010. *ISPRS J. Photogramm. Remote Sens.* https://doi.org/10.1016/j.isprsjprs.2014.02.007
- Li, S., et al. (2025). A long-term paddy rice distribution dataset in Asia at a 30 m spatial resolution. *Scientific Data*. https://doi.org/10.1038/s41597-025-05374-1
- Olofsson, P., et al. (2014). Good practices for estimating area and assessing accuracy of land change. *Remote Sens. Environ.* 148, 42–57. https://doi.org/10.1016/j.rse.2014.02.015
- Peña-Arancibia, J., et al. (2020). The Green Revolution from space. *Remote Sens. Appl.: Soc. Environ.* https://doi.org/10.1016/j.rsase.2020.100460
- Rahman, H. M. H., et al. (2026). Estimating aman and aus rice area in Bangladesh using Sentinel-1 imagery and machine learning algorithms. *PLoS ONE* 21(9), e0355502. https://doi.org/10.1371/journal.pone.0355502
- Singha, M., et al. (2019). High resolution paddy rice maps in cloud-prone Bangladesh and Northeast India using Sentinel-1 data. *Scientific Data* 6, 26. https://doi.org/10.1038/s41597-019-0036-3
- Tiwari, V., et al. (2024). Automated in-season rice crop mapping using Sentinel time-series data and Google Earth Engine. *J. Environ. Manage.* https://doi.org/10.1016/j.jenvman.2023.119615
- Xiao, X., et al. (2006). Mapping paddy rice agriculture in South and Southeast Asia using multi-temporal MODIS images. *Remote Sens. Environ.* 100, 95–113.
- Zhao, Z., et al. (2026). Mapping paddy rice distribution and cropping intensity in South and Southeast Asia (1995–2024) at 30 m resolution. *Earth Syst. Sci. Data* 18, 5583–5599. https://doi.org/10.5194/essd-18-5583-2026
