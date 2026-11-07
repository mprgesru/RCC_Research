# Research Protocol: Rajshahi Rice Cultivation and Agricultural Land-Use Change, 1990–2025

**Working title:** *Seasonal rice persistence and rice-to-urban conversion across Rajshahi City Corporation and its 5- and 10-km peri-urban zones, Bangladesh, 1990–2025*

**Protocol status:** Planning draft  
**Prepared:** 7 November 2026  
**Study area:** Rajshahi City Corporation (RCC), plus the surrounding 0–5 km and 5–10 km rings  
**Target reference years:** 1990, 1995, 2000, 2005, 2010, 2015, 2020 and 2025  
**Primary map scale:** 30 m, for consistent comparison across the Landsat record

## 1. Project summary

The project will build a geospatial database of rice cultivation in Rajshahi from 1990 to 2025. It will map Boro, Aus and Aman separately, derive an all-rice footprint for each reference year, and estimate rice cropping intensity. It will then identify where rice cultivation persisted, appeared, disappeared or transitioned to built-up land, water, orchard or other land cover.

The study will compare three non-overlapping spatial zones: the RCC boundary, a 0–5 km ring outside it, and a 5–10 km ring outside that. Results will also be aggregated for the cumulative extents RCC + 5 km and RCC + 10 km. This prevents overlapping areas from being counted twice while showing how the patterns change as the study extent expands.

The research contribution is planned as a locally validated, uncertainty-aware analysis of seasonal rice and peri-urban land conversion. Bangladesh and Asian rice products already cover much of the intended historical period, so the project should not claim to be the first historical rice mapping. Its potential contribution is to assess how well those products represent fragmented city-edge fields in Rajshahi and to explain local land-use transitions.

## 2. Scope and operational definitions

### 2.1 Spatial zones

Use the latest suitable official RCC boundary as a fixed geography for the primary historical comparison.

| Zone ID | Zone name | Definition |
|---|---|---|
| RCC | City Corporation | Official RCC polygon |
| R0_5 | Inner peri-urban ring | 5 km outward buffer around RCC, minus RCC |
| R5_10 | Outer peri-urban ring | 10 km outward buffer, minus the 5 km buffer |
| RCC_5 | Cumulative city + 5 km | RCC plus R0_5 |
| RCC_10 | Cumulative city + 10 km | RCC plus R0_5 plus R5_10 |

Construct distances in a projected coordinate system using metres, such as WGS 84 / UTM zone 45N (EPSG:32645), and record the selected CRS. Keep rivers and other water bodies in the land-cover maps as explicit classes. Exclude permanent water from agricultural-area denominators, but report its area separately.

The fixed current boundary answers: “How did land use change in the geography that is now the city and its surrounding rings?” If historical legal boundaries are available, add a separate sensitivity analysis using the boundary in force for each date. Do not mix changing administrative boundaries into the main time series without clearly labelling the change in geography.

### 2.2 Time periods

The target years are 1990, 1995, 2000, 2005, 2010, 2015, 2020 and 2025. The primary map should represent the named crop year using all usable observations within that season. Store the actual observation window and scene count for every map.

If cloud or observation gaps make an exact target-year map unreliable, retain the target-year result with a low-support flag and run a consistent three-year composite sensitivity analysis. Label that result as a composite centred on the target year, not as an exact single-year observation. This matters especially for the monsoon Aman season and early Landsat years.

Label Boro by harvest year because its growing cycle crosses calendar years. Confirm local planting and harvest windows with Bangladesh rice-calendar sources and Rajshahi agricultural experts before fixing the date windows. Store crop year, season, start date and end date separately.

### 2.3 Rice measures

The database will distinguish three related measures:

1. **Seasonal rice area:** area classified as Boro, Aus or Aman for a given crop year.
2. **All-rice physical footprint:** the spatial union of land classified as rice in at least one of the three seasons. A location counts once in this measure.
3. **Rice cropping intensity:** the number of mapped rice seasons at a location in that crop year: 0, 1, 2 or 3.

The seasonal areas may sum to more than the all-rice physical footprint because the same land can support multiple rice crops in one year. Keep these measures separate in tables and explanations.

### 2.4 Land-cover classes

For transition analysis, use a consistent land-cover legend that can distinguish rice from other forms of agriculture and urban cover:

- Rice, with season-specific layers for Boro, Aus and Aman
- Other annual cropland / fallow
- Orchard and other perennial agriculture, with mango orchard separated where evidence allows
- Other vegetation
- Built-up / impervious
- Water and wetland
- Bare soil / exposed land
- No data / insufficient observation

Keep rice-season classification separate from general land-cover classification. A broad “vegetation” label is not a substitute for rice. Mango orchards are especially important to keep distinct in Rajshahi.

## 3. Research objectives and questions

### Objectives

1. Produce comparable 30 m rice maps for the eight reference years.
2. Map seasonal rice distribution and all-rice physical footprint across the RCC and peri-urban zones.
3. Estimate cropping intensity and persistence by location.
4. Quantify transitions from rice to built-up land and other classes between successive five-year reference years.
5. Test the local accuracy and uncertainty of existing rice products in Rajshahi.
6. Publish a traceable geospatial database, area tables, metadata and reproducible processing record.

### Research questions

- How did Boro, Aus, Aman and all-rice physical extent change in the RCC, 0–5 km ring and 5–10 km ring from 1990 to 2025?
- Where did rice persist, appear, disappear or change cropping intensity?
- What share of mapped rice loss transitioned to built-up land, orchard, other cropland, water or other cover?
- How do rice-change patterns vary with distance from the current city edge?
- How accurately do existing 30 m Asian rice products represent seasonal rice in Rajshahi’s urban-fringe landscape?
- How does adding Sentinel-1/2 data change recent estimates relative to a Landsat-only series?

### Working hypotheses

- Rice loss and rice-to-built-up transitions will be more concentrated near the urban edge than in the outer ring.
- Some locations will show seasonal switching or declining cropping intensity before they leave the all-rice footprint.
- Published national or regional products will have higher disagreement in mixed urban–agricultural pixels than in larger contiguous fields.
- The apparent magnitude of recent change will depend partly on whether Sentinel data are used; that sensor effect must be quantified before interpreting the time trend.

These are hypotheses to evaluate, not assumed findings. Spatial association with urban proximity does not by itself demonstrate that urban growth caused a specific field’s conversion.

## 4. Candidate methodological contribution

Recent research already provides multi-year and multi-season rice maps for Bangladesh and Asia. The study should therefore position its contribution around a focused combination of:

1. **Local product evaluation:** compare published rice products with independent Rajshahi reference samples and report agreement by season, zone and reference year.
2. **Rice-specific land transitions:** distinguish seasonal rice loss from broad vegetation decline, and identify where rice is replaced by built-up, orchard, other cropland, water or bare land.
3. **Explicit observation and classification uncertainty:** retain rice probabilities, valid-observation counts and confidence flags; report area-adjusted estimates with uncertainty intervals.
4. **Sensor-era comparison:** create a Landsat-only baseline spanning all target years, then compare it with a Sentinel-enhanced map for 2015, 2020 and 2025. Do not splice the enhanced values into the historical series without quantifying the difference.
5. **Nested peri-urban analysis:** report the RCC, non-overlapping buffer rings and cumulative extents. This can show where change is concentrated without double-counting the same land.

Treat this as a candidate novelty statement until a formal literature and dataset search has checked current papers, products, theses and local planning reports.

## 5. Data plan

| Data | Role | Notes |
|---|---|---|
| Landsat Collection 2 Level-2 surface reflectance, Landsat 4–9 | Historical and recent optical time series | Main consistent source for all epochs; use common bands and sensor-aware normalization. USGS describes global Level-2 surface reflectance availability from the Landsat TM era onward. |
| Sentinel-1 SAR | Recent rice phenology and cloud-independent observations | Available from 2014 onward; use VH and VV time series, with preprocessing and orbit/polarization recorded. |
| Sentinel-2 optical imagery | Recent higher-resolution optical phenology | Available from 2015 onward; use harmonized surface reflectance where available and document cloud masking. |
| GCD-Rice (1990–2023) | Baseline product and comparison | 30 m, three seasons, includes Bangladesh. Use as a comparison/reference layer, not as independent ground truth. |
| Zhao et al. South/Southeast Asia product (1995, 2005, 2015, 2024) | Additional product comparison | 30 m composite maps; useful at overlapping reference years. Product composition may smooth annual variation. |
| Bangladesh Bureau of Statistics agricultural yearbooks | External area-level consistency check | Harmonize definitions and geographic coverage by year. District statistics cannot validate individual RCC pixels. |
| Bangladesh Rice Research Institute, Department of Agricultural Extension, local agronomists and farmer knowledge | Crop calendars and recent field reference | Verify local crop timing, crop labels and unusual years. Record source, date and confidence. |
| Official RCC / ward boundaries and dated planning maps | Zone creation and contextual analysis | Record version, source and any known boundary changes. Historical ward-level boundaries may not be comparable. |
| Historical high-resolution imagery or archived maps | Historical visual interpretation | Availability varies by year and location; record the image date and interpretation confidence for each reference sample. |

Primary technical source links:

- [USGS Landsat Collection 2](https://www.usgs.gov/landsat-missions/landsat-collection-2)
- [Google Earth Engine Sentinel data catalog](https://developers.google.com/earth-engine/datasets/catalog/sentinel)
- [BBS Agricultural Statistics Yearbooks](https://bbs.gov.bd/pages/static-pages/6922e0d6933eb65569e28cbf)

## 6. Processing and analysis workflow

### Step 1 — Finalize the study boundary and data manifest

- Obtain the official RCC polygon and source/version information.
- Create the two outer rings and cumulative extents.
- Check geometry validity, projection, area and overlap.
- Create a data manifest listing every source, acquisition date, collection/version, cloud or quality-filter settings, licence and processing date.
- Save boundary files and raster grids in one documented CRS and grid alignment.

### Step 2 — Inventory observations by crop season and target year

For each target year and season:

- List every candidate Landsat scene and, where applicable, Sentinel observation.
- Apply cloud, cloud-shadow, saturation and invalid-pixel masks.
- Count valid clear observations per pixel and summarize support by zone.
- Record gaps and low-support regions rather than silently filling them.
- Keep a Landsat-only data stack for all years. Prepare a separate Sentinel-enhanced stack for recent years.

### Step 3 — Create seasonal reference data

Create a stratified reference-sample set that includes:

- Each rice season
- Other annual crops and fallow
- Orchard/perennial agriculture
- Built-up land
- Water/wetland
- Other vegetation and bare land
- Stable areas, apparent transitions and product-disagreement locations

For recent years, prioritize field checks, geotagged observations or trusted local agricultural information. For historical years, use dated high-resolution imagery, archived maps and other dated sources where available. Record the evidence source and its confidence. Present historical visual interpretation as reference interpretation, not field ground truth.

Keep training samples separate from final validation samples. Use spatial blocks so neighbouring pixels from the same field or neighbourhood do not appear in both sets. If two interpreters are available, independently review a subset and resolve disagreements using a documented rule.

### Step 4 — Map rice by season

- Reconstruct seasonal phenology from multi-date observations, not from one selected image.
- Use optical indicators such as vegetation and water-sensitive indices (for example, NDVI/EVI and LSWI) to capture flooding/transplanting, green-up, peak growth and harvest signals.
- For post-2014 years, test whether Sentinel-1 VH/VV trajectories improve rice identification during cloudy periods. Use Sentinel-2 as complementary optical evidence.
- Train separate seasonal rice classifiers or decision rules for Boro, Aus and Aman. Do not assume one season’s threshold transfers unchanged to another.
- Compare a phenology-guided random forest baseline with a simpler phenology-rule baseline. Select the production method using spatially blocked validation and document the selection.
- Export probability and class maps for each season.
- Derive the all-rice union and cropping intensity from the three seasonal layers.

### Step 5 — Map general land cover for transition attribution

For each target year, map or derive the land-cover classes required to distinguish where lost rice went. Keep orchard separate from annual cropland where reference evidence supports it. Use the same class definitions and mapping rules across years; flag years where a class cannot be reliably separated.

### Step 6 — Validate and benchmark products

For each season and target year with enough reference evidence:

- Report user’s accuracy, producer’s accuracy, F1 and confusion matrices.
- Report valid-observation support and the number/source of reference samples.
- Estimate class area with accuracy adjustment and confidence intervals, rather than relying only on raw classified-pixel counts.
- Validate change classes separately, including stable rice, rice gain, rice loss and rice-to-built-up transition.
- Compare GCD-Rice and the 2026 regional product at overlapping years. Treat the products as benchmarks, not truth.
- For early periods with weak historical reference coverage, report reduced confidence and avoid presenting precise trend claims unsupported by the evidence.

### Step 7 — Calculate change and spatial patterns

For each consecutive five-year pair:

- Calculate gross gains, gross losses and net change for each season and all-rice union.
- Build transition matrices from rice to built-up, orchard, other cropland/fallow, water/wetland, other vegetation and bare land.
- Calculate persistence and cropping-intensity transitions, such as single-season to double-season or rice to no mapped rice.
- Summarize results for RCC, both rings, cumulative extents and wards where ward boundaries are comparable.
- Analyze distance to the current RCC edge as a spatial gradient. If historical road data are not reliable, do not infer road-access effects from a modern road layer.
- Report both mapped area and error-adjusted area, alongside confidence intervals and observation support.

### Step 8 — Prepare reproducible outputs

Use Google Earth Engine for image discovery and scalable satellite processing, with Python/QGIS for local review, statistics, data packaging and map production. Version scripts and record the code version used for each map run.

## 7. Data schema

Use a GeoPackage for vector boundaries and sample points, Cloud-Optimized GeoTIFFs for raster outputs, and CSV or Parquet for tabular summaries. Store rasters at 30 m on a fixed grid. Preserve source data separately from derived outputs.

### 7.1 Raster products

| Product | Bands / values | Purpose |
|---|---|---|
| Seasonal rice probability | Float 0–1 for Boro, Aus and Aman | Retains classification confidence |
| Seasonal rice class | 0 = non-rice, 1 = rice, 255 = no data | Binary seasonal map |
| All-rice union | 0 = no rice detected, 1 = rice in at least one season, 255 = no data | Physical footprint counted once |
| Rice intensity | 0, 1, 2 or 3 rice seasons; 255 = no data | Annual rice cropping intensity |
| Land cover | 1 = Boro, 2 = Aus, 3 = Aman, 4 = other annual crop/fallow, 5 = orchard, 6 = other vegetation, 7 = built-up, 8 = water/wetland, 9 = bare/exposed land, 255 = no data | Transition attribution; rice-season class may use dominant/season-specific representation, documented in metadata |
| Observation support | Number of valid observations by season | Shows where the map is supported by imagery |
| Confidence / uncertainty | Calibrated probability or documented confidence code | Supports masking and uncertainty analysis |

Suggested file names:

- rice_prob_BORO_1990_30m.tif
- rice_class_AMAN_2025_30m.tif
- rice_union_2020_30m.tif
- rice_intensity_2015_30m.tif
- lulc_2025_30m.tif
- obs_support_AUS_2005_30m.tif

Use a sidecar metadata record for each raster, including target year, season, observation window, sensor set, valid-observation summary, model version, class definitions, probability threshold, CRS, resolution, nodata value, source manifest and code revision.

### 7.2 Vector and tabular tables

#### zones

| Field | Type | Description |
|---|---|---|
| zone_id | text, primary key | RCC, R0_5, R5_10, RCC_5 or RCC_10 |
| zone_name | text | Readable zone label |
| zone_type | text | Core, ring or cumulative |
| distance_min_km | numeric | Inner edge distance for ring |
| distance_max_km | numeric | Outer edge distance for ring |
| area_km2 | numeric | Area in projected CRS |
| boundary_version | text | Official boundary file/version |
| source_url | text | Source link |
| geometry | multipolygon | Study-zone geometry |

#### map_runs

| Field | Type | Description |
|---|---|---|
| map_id | text, primary key | Unique map-run identifier |
| reference_year | integer | One of the eight target years |
| season | text | BORO, AUS, AMAN, ALL_UNION, INTENSITY or LULC |
| crop_year | integer | Harvest/crop year |
| window_start | date | First observation date included |
| window_end | date | Last observation date included |
| sensors | text | Landsat-only or Landsat + Sentinel-1/2 |
| valid_obs_summary | text or JSON | Observation-support summary |
| model_name | text | Classifier/rule-set name |
| model_version | text | Version identifier |
| threshold | numeric | Probability threshold used for class map |
| code_revision | text | Git commit or release identifier |
| output_path | text | Raster product path |

#### reference_samples

| Field | Type | Description |
|---|---|---|
| sample_id | text, primary key | Unique sample |
| reference_year | integer | Year being interpreted |
| season | text | Boro, Aus, Aman or general LULC |
| reference_class | text | Label assigned from reference evidence |
| reference_source | text | Field, dated high-resolution image, map, or other |
| reference_date | date | Date of reference imagery/observation |
| interpreter_id | text | Reviewer/interpreter |
| confidence | integer or text | Confidence scale defined in codebook |
| split | text | Train, calibration or independent validation |
| notes | text | Reason for ambiguous labels |
| geometry | point/polygon | Sample location or field boundary |

#### area_estimates

| Field | Type | Description |
|---|---|---|
| reference_year | integer | Target year |
| zone_id | text | Zone being summarized |
| season_or_measure | text | Season, all-rice union or intensity class |
| mapped_area_ha | numeric | Raw classified area |
| adjusted_area_ha | numeric | Accuracy-adjusted area estimate |
| ci95_lower_ha | numeric | Lower confidence bound |
| ci95_upper_ha | numeric | Upper confidence bound |
| valid_land_area_ha | numeric | Eligible non-permanent-water area |
| sample_n | integer | Validation sample count |
| ua | numeric | User’s accuracy |
| pa | numeric | Producer’s accuracy |
| f1 | numeric | F1 score |
| map_id | text | Map-run foreign key |

#### transition_estimates

| Field | Type | Description |
|---|---|---|
| period_start | integer | Earlier reference year |
| period_end | integer | Later reference year |
| zone_id | text | Study zone |
| season_or_measure | text | Boro, Aus, Aman or all-rice union |
| from_class | text | Earlier class |
| to_class | text | Later class |
| mapped_area_ha | numeric | Raw transition area |
| adjusted_area_ha | numeric | Accuracy-adjusted transition estimate |
| ci95_lower_ha | numeric | Lower confidence bound |
| ci95_upper_ha | numeric | Upper confidence bound |
| validation_n | integer | Change-reference sample count |

#### ward_summary (optional)

| Field | Type | Description |
|---|---|---|
| ward_id | text | Ward identifier |
| boundary_version | text | Ward geography version |
| reference_year | integer | Target year |
| season_or_measure | text | Season, union or intensity |
| mapped_area_ha | numeric | Area within ward |
| adjusted_area_ha | numeric | Error-adjusted area, if supported |
| ci95_lower_ha | numeric | Lower confidence bound |
| ci95_upper_ha | numeric | Upper confidence bound |

The raster layers are the spatial source of truth. Do not store millions of repeated pixel rows in CSV unless a downstream use requires them; use raster files and summarize into these tables.

## 8. Agent skill plan

Create the skills in this order:

1. **Research coordinator** — maintains agreed scope, year/season definitions, zone IDs, file naming, task status and deliverable checklist.
2. **Literature and dataset auditor** — collects papers and map products; records citations, coverage, resolution, class definitions, validation and limitations; flags duplicate claims and publication dates.
3. **Bangladesh geospatial data steward** — inventories satellite scenes, boundaries, BBS tables and crop calendars; records source, version, licence, date range and missingness.
4. **Rice phenology mapper** — implements crop-season preprocessing, feature generation, model runs, probability layers and export metadata.
5. **Accuracy and change analyst** — designs independent validation, area adjustment, confidence intervals, transition matrices and zone summaries.
6. **Research report writer** — writes only from approved analysis outputs and the evidence ledger; inserts source-linked citations and marks unsupported or low-confidence findings.

All skills should use shared data dictionaries and structured output templates. They should not independently rename zones, redefine seasons or change the class legend. The literature and report skills must not invent citations. Every reported statistic should point to a source table, map run or reproducible calculation.

## 9. Main risks and safeguards

| Risk | Safeguard |
|---|---|
| Sparse cloud-free Landsat imagery, especially in Aman and early years | Record observation counts, retain confidence layers and run a clearly labelled composite sensitivity analysis. |
| Mixing of rice with other crops, wetland or orchard | Use seasonal time series and keep mango orchard and other perennial vegetation distinct where possible. |
| Sensor change creates an artificial trend | Keep a Landsat-only baseline and publish a separate Sentinel-enhanced comparison for recent years. |
| Local field sizes are near or below one 30 m pixel | Report mixed-pixel uncertainty; avoid claiming parcel-boundary precision from Landsat. |
| Existing maps are mistaken for truth | Use products as benchmarks; validate independently in Rajshahi. |
| Historical reference evidence is uneven | Report confidence by year and season; do not imply uniform accuracy across the full 35 years. |
| Seasonal area is confused with physical land footprint | Publish seasonal harvested areas, all-rice union and cropping intensity as separate measures. |
| Boundary changes affect apparent area | Hold the current study geography fixed for the main comparison; add historical-boundary results only as a separate analysis. |

## 10. Core references

### Bangladesh and Rajshahi

- Gumma, M. K. et al. (2014). “Mapping seasonal rice cropland extent and area in the high cropping intensity environment of Bangladesh using MODIS 500m data for the year 2010.” [ISPRS Journal of Photogrammetry and Remote Sensing](https://doi.org/10.1016/j.isprsjprs.2014.02.007).
- Shapla, T. et al. (2015). “Change Detection of Rice Cultivation in Bangladesh Based on the Phenological Analysis of MODIS Data.” [Advances in Remote Sensing](https://doi.org/10.4236/ars.2015.44026).
- Shew, A. M. and Ghosh, A. (2017). “Using multi-temporal remote sensing data to analyze the spatio-temporal patterns of dry season rice production in Bangladesh.” [ISPRS Annals](https://doi.org/10.5194/isprs-annals-IV-4-W2-61-2017).
- Singha, M. et al. (2019). “High resolution paddy rice maps in cloud-prone Bangladesh and Northeast India using Sentinel-1 data.” [Scientific Data](https://doi.org/10.1038/s41597-019-0036-3).
- Peña-Arancibia, J. et al. (2020). “The Green Revolution from space: Mapping the historic dynamics of main rice types in one of the world’s food bowls.” [Remote Sensing Applications: Society and Environment](https://doi.org/10.1016/j.rsase.2020.100460).
- Tiwari, V. et al. (2024). “Automated in-season rice crop mapping using Sentinel time-series data and Google Earth Engine: A case study in climate-risk prone Bangladesh.” [Journal of Environmental Management](https://doi.org/10.1016/j.jenvman.2023.119615).
- Li, S. et al. (2025). “A long-term paddy rice distribution dataset in Asia at a 30 m spatial resolution.” [Scientific Data](https://doi.org/10.1038/s41597-025-05374-1).
- Firoz, M. I. et al. (2025). “Long-term geospatial assessment of land cover dynamics and surface-groundwater resources in Rajshahi City for sustainable urban management.” [Applied Water Science](https://doi.org/10.1007/s13201-025-02722-9).

### Multi-country and international methods

- Xiao, X. et al. (2006). “Mapping paddy rice agriculture in South and Southeast Asia using multi-temporal MODIS images.” [Remote Sensing of Environment](https://www.sciencedirect.com/science/article/pii/S0034425705003433).
- Dong, J. and Xiao, X. (2016). “Evolution of regional to global paddy rice mapping methods: A review.” [ISPRS Journal of Photogrammetry and Remote Sensing](https://doi.org/10.1016/j.isprsjprs.2016.05.010).
- Han, J. et al. (2021). “NESEA-Rice10: high-resolution annual paddy rice maps for Northeast and Southeast Asia from 2017 to 2019.” [Earth System Science Data](https://doi.org/10.5194/essd-13-5969-2021).
- Han, J. et al. (2022). “Annual paddy rice planting area and cropping intensity datasets and their dynamics in the Asian monsoon region from 2000 to 2020.” [Agricultural Systems](https://doi.org/10.1016/j.agsy.2022.103437).
- Sun, C. et al. (2023). “Twenty-meter annual paddy rice area map for mainland Southeast Asia using Sentinel-1 synthetic-aperture-radar data.” [Earth System Science Data](https://doi.org/10.5194/essd-15-1501-2023).
- Zhang, C. et al. (2023). “Phenology-assisted supervised paddy rice mapping with the Landsat imagery on Google Earth Engine: Experiments in Heilongjiang Province of China from 1990 to 2020.” [Computers and Electronics in Agriculture](https://doi.org/10.1016/j.compag.2023.108105).
- Zhao, Z. et al. (2026). “Mapping paddy rice distribution and cropping intensity in South and Southeast Asia (1995–2024) at 30 m resolution.” [Earth System Science Data](https://doi.org/10.5194/essd-18-5583-2026).
- Zhang, Z. et al. (2025). “Long history paddy rice mapping across Northeast China with deep learning and annual result enhancement method.” [Earth System Science Data](https://doi.org/10.5194/essd-17-6851-2025).
- “Widespread land surface cooling from paddy rice cultivation revealed by global satellite mapping.” (2025). [Nature Communications](https://doi.org/10.1038/s41467-025-67549-z).

---

**Decisions now fixed:** RCC core plus 0–5 km and 5–10 km non-overlapping rings; report cumulative extents too; map all-rice union and Boro/Aus/Aman separately; target years 1990–2025 at five-year intervals.
