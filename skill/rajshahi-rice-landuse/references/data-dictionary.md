# Data Dictionary

Single source of truth for the Rajshahi rice land-use study. Every role and
script must use these definitions verbatim. Changing a value here requires a
coordinator decision and a note in the decision log at the end of this file.

## 1. Study definition

| Field | Value |
| --- | --- |
| Study area | Rajshahi City Corporation and surrounding peri-urban rings |
| Analysis CRS | EPSG:32645 — WGS 84 / UTM zone 45N |
| Interchange CRS | EPSG:4326 — WGS 84 |
| Spatial resolution | 30 m |
| Target years | 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025 |
| Seasons | Boro, Aus, Aman |
| Measures | Seasonal area, all-rice footprint, cropping intensity |

## 2. Zones

Zones are non-overlapping for rings and overlapping only where explicitly marked
as cumulative. Areas are computed in EPSG:32645.

| zone_id | zone_name | zone_type | distance_min_km | distance_max_km | Definition |
| --- | --- | --- | --- | --- | --- |
| `RCC` | City Corporation | core | 0 | 0 | Official RCC polygon, dissolved from 30 wards |
| `R0_5` | Inner peri-urban ring | ring | 0 | 5 | 5 km buffer around RCC minus RCC |
| `R5_10` | Outer peri-urban ring | ring | 5 | 10 | 10 km buffer minus 5 km buffer |
| `RCC_5` | City plus 5 km | cumulative | 0 | 5 | RCC plus `R0_5` |
| `RCC_10` | City plus 10 km | cumulative | 0 | 10 | RCC plus `R0_5` plus `R5_10` |

Rules:

- Rings must not overlap each other or `RCC`. Verify with an area-difference check.
- Cumulative zones intentionally overlap their components; never sum them together.
- Distance is measured outward from the RCC boundary in metres, then reported in km.
- Agricultural denominators exclude permanent water; water area is reported separately.

Boundary status values:

| Value | Meaning |
| --- | --- |
| `official_operational` | Official operational dataset (e.g. health microplanning), not survey-grade |
| `official_legal` | Legally gazetted boundary |
| `provisional` | Derived or crowdsourced, clearly non-official |
| `historical` | Boundary in force for a past date, used only in sensitivity analysis |

## 3. Seasons

Season windows are **confirmed** (project owner, 2026-11-07) and are used for all
maps. Season codes are frozen; any future change requires a coordinator decision
and a new dictionary version.

| season | Code | Confirmed window | Labelling rule |
| --- | --- | --- | --- |
| Boro | `BORO` | November – April | Labelled by harvest year (cycle crosses calendar years) |
| Aus | `AUS` | May – August | Calendar year of the growing window |
| Aman | `AMAN` | June – November | Calendar year of the growing window |

Derived products:

| product | Code | Definition |
| --- | --- | --- |
| All-rice union | `ALL_UNION` | Spatial union of rice in at least one season; each pixel counts once |
| Cropping intensity | `INTENSITY` | Number of mapped rice seasons at a pixel: 0, 1, 2 or 3 |
| Land cover | `LULC` | General land-cover classification for transition attribution |

Every map records its actual observation window (`window_start`, `window_end`) and
scene count. If support is inadequate, keep the target-year result with
`low_support = true` and additionally produce a three-year composite centred on the
target year, labelled as a composite.

### Sensor availability (from the 2026-11-07 inventory)

| Sensor | Availability at this AOI |
| --- | --- |
| Landsat 4/5/7/8/9 | All eight target years |
| Sentinel-1 GRD | 2014 onward |
| Sentinel-2 L2A | 2016 onward via Planetary Computer; **no scenes in 2015** |

Consequently the Sentinel-enhanced comparison covers 2020 and 2025 with S1 + S2.
If 2015 is retained, it must be S1-only and labelled as such; it is not comparable
to the S1 + S2 years.

## 4. Land-cover classes

| Code | Class | Notes |
| --- | --- | --- |
| 1 | Boro | Rice, dry-season |
| 2 | Aus | Rice, summer |
| 3 | Aman | Rice, monsoon |
| 4 | Other annual crop / fallow | Non-rice annual agriculture |
| 5 | Orchard / perennial agriculture | Keep mango orchard distinct where evidence allows |
| 6 | Other vegetation | Not a substitute for rice |
| 7 | Built-up / impervious | Urban and infrastructure |
| 8 | Water / wetland | Permanent and seasonal water |
| 9 | Bare soil / exposed land | |
| 255 | No data / insufficient observation | Never treated as a class in area sums |

Rice-season classification and general land cover are separate products. A
season-specific rice layer uses `0 = non-rice`, `1 = rice`, `255 = no data`.

## 5. Raster products

All rasters are 30 m, EPSG:32645, on a single fixed grid aligned to the study
extent.

| Product | Bands / values | File pattern |
| --- | --- | --- |
| Seasonal probability | Float 0–1 per season | `rice_prob_{SEASON}_{YEAR}_30m.tif` |
| Seasonal class | 0 non-rice, 1 rice, 255 no data | `rice_class_{SEASON}_{YEAR}_30m.tif` |
| All-rice union | 0 none, 1 rice in ≥1 season, 255 no data | `rice_union_{YEAR}_30m.tif` |
| Cropping intensity | 0–3 seasons, 255 no data | `rice_intensity_{YEAR}_30m.tif` |
| Land cover | Codes 1–9, 255 no data | `lulc_{YEAR}_30m.tif` |
| Observation support | Valid observation count | `obs_support_{SEASON}_{YEAR}_30m.tif` |
| Confidence | Calibrated probability or confidence code | `confidence_{SEASON}_{YEAR}_30m.tif` |

Rules:

- `SEASON` is one of `BORO`, `AUS`, `AMAN`.
- `YEAR` is one of the eight target years, four digits.
- Output format is Cloud-Optimized GeoTIFF, LZW or DEFLATE compressed, tiled.
- Nodata is `255` for class rasters and `-9999` for continuous rasters.
- Sidecar metadata uses the same stem with `.json`.

### Raster sidecar fields

| Field | Required | Description |
| --- | --- | --- |
| `map_id` | yes | Foreign key to `map_runs.map_id` |
| `reference_year` | yes | Target year |
| `season` | yes | `BORO`, `AUS`, `AMAN`, `ALL_UNION`, `INTENSITY` or `LULC` |
| `crop_year` | yes | Harvest or crop year |
| `window_start` | yes | First observation date included, ISO 8601 |
| `window_end` | yes | Last observation date included, ISO 8601 |
| `sensors` | yes | `landsat` or `landsat+sentinel1+sentinel2` |
| `class_definition` | yes | Legend version from this document |
| `threshold` | yes | Probability threshold used for the class map |
| `crs` | yes | `EPSG:32645` |
| `resolution_m` | yes | `30` |
| `nodata` | yes | Nodata value |
| `valid_obs_summary` | yes | Min, median, max and count of valid observations |
| `model_name` | yes | Classifier or rule-set name |
| `model_version` | yes | Version identifier |
| `code_revision` | yes | Commit SHA of the producing code |
| `source_manifest` | yes | Path to the scene manifest used |
| `low_support` | yes | Boolean flag for weak observation support |

## 6. Database tables

The populated SQLite database lives in the runtime root. Episode DDL is committed
in `schema/`. Field names and types below are authoritative.

### zones

| Field | Type | Description |
| --- | --- | --- |
| `zone_id` | TEXT PK | `RCC`, `R0_5`, `R5_10`, `RCC_5`, `RCC_10` |
| `zone_name` | TEXT | Readable label |
| `zone_type` | TEXT | `core`, `ring` or `cumulative` |
| `distance_min_km` | REAL | Inner edge distance |
| `distance_max_km` | REAL | Outer edge distance |
| `area_km2` | REAL | Area in EPSG:32645 |
| `boundary_version` | TEXT | Boundary version or date |
| `boundary_status` | TEXT | Status enum from section 2 |
| `source_url` | TEXT | Source service or file |
| `geometry` | BLOB | Polygon or multipolygon, EPSG:32645 |

### map_runs

| Field | Type | Description |
| --- | --- | --- |
| `map_id` | TEXT PK | Unique map-run identifier |
| `reference_year` | INTEGER | One of the eight target years |
| `season` | TEXT | `BORO`, `AUS`, `AMAN`, `ALL_UNION`, `INTENSITY`, `LULC` |
| `crop_year` | INTEGER | Harvest or crop year |
| `window_start` | TEXT | ISO date |
| `window_end` | TEXT | ISO date |
| `sensors` | TEXT | Sensor set |
| `valid_obs_summary` | TEXT | JSON summary |
| `model_name` | TEXT | Classifier or rule-set name |
| `model_version` | TEXT | Version identifier |
| `threshold` | REAL | Probability threshold |
| `code_revision` | TEXT | Commit SHA |
| `output_path` | TEXT | Raster path under the runtime root |
| `low_support` | INTEGER | 0 or 1 |
| `created_utc` | TEXT | ISO timestamp |

### reference_samples

| Field | Type | Description |
| --- | --- | --- |
| `sample_id` | TEXT PK | Unique sample |
| `reference_year` | INTEGER | Year interpreted |
| `season` | TEXT | `BORO`, `AUS`, `AMAN` or `LULC` |
| `reference_class` | TEXT | Assigned label |
| `reference_source` | TEXT | Field, dated image, map or other |
| `reference_date` | TEXT | ISO date of evidence |
| `interpreter_id` | TEXT | Reviewer |
| `confidence` | TEXT | Codebook confidence scale |
| `split` | TEXT | `train`, `calibration` or `validation` |
| `notes` | TEXT | Reason for ambiguous labels |
| `geometry` | BLOB | Point or polygon, EPSG:32645 |

### area_estimates

| Field | Type | Description |
| --- | --- | --- |
| `reference_year` | INTEGER | Target year |
| `zone_id` | TEXT | Foreign key to `zones` |
| `season_or_measure` | TEXT | Season, `ALL_UNION` or intensity class |
| `mapped_area_ha` | REAL | Raw classified area |
| `adjusted_area_ha` | REAL | Accuracy-adjusted estimate |
| `ci95_lower_ha` | REAL | Lower 95% bound |
| `ci95_upper_ha` | REAL | Upper 95% bound |
| `valid_land_area_ha` | REAL | Eligible non-permanent-water area |
| `sample_n` | INTEGER | Validation sample count |
| `ua` | REAL | User's accuracy |
| `pa` | REAL | Producer's accuracy |
| `f1` | REAL | F1 score |
| `map_id` | TEXT | Foreign key to `map_runs` |

### transition_estimates

| Field | Type | Description |
| --- | --- | --- |
| `period_start` | INTEGER | Earlier reference year |
| `period_end` | INTEGER | Later reference year |
| `zone_id` | TEXT | Foreign key to `zones` |
| `season_or_measure` | TEXT | Season or `ALL_UNION` |
| `from_class` | TEXT | Earlier class code, or `ALL_RICE` for union transitions |
| `to_class` | TEXT | Later class code, or `ALL_RICE` for union transitions |
| `mapped_area_ha` | REAL | Raw transition area |
| `adjusted_area_ha` | REAL | Adjusted estimate |
| `ci95_lower_ha` | REAL | Lower bound |
| `ci95_upper_ha` | REAL | Upper bound |
| `validation_n` | INTEGER | Change-reference sample count |

### ward_summary

| Field | Type | Description |
| --- | --- | --- |
| `ward_id` | TEXT | Ward identifier |
| `boundary_version` | TEXT | Ward geography version |
| `reference_year` | INTEGER | Target year |
| `season_or_measure` | TEXT | Season, union or intensity |
| `mapped_area_ha` | REAL | Area within ward |
| `adjusted_area_ha` | REAL | Adjusted estimate if supported |
| `ci95_lower_ha` | REAL | Lower bound |
| `ci95_upper_ha` | REAL | Upper bound |

### Supporting tables

`reference_labels` stores interpreted labels, one row per sample and season:
`LULC` rows carry `reference_class`; `BORO`, `AUS` and `AMAN` rows carry
`is_rice` 1/0. It is populated by `scripts/import_labels.py` from the
interpretation sheet.

`data_sources` records each source with URL, version, licence, retrieval date and
checksum. `checksums` records SHA-256 for every committed and runtime artifact.

## 7. Naming and identifiers

| Object | Pattern | Example |
| --- | --- | --- |
| Raster | `{product}_{season}_{year}_30m.tif` | `rice_class_AMAN_2025_30m.tif` |
| Sidecar | same stem, `.json` | `rice_class_AMAN_2025_30m.json` |
| Map run | `{year}_{season}_{sensor}_{code_rev7}` | `2025_AMAN_landsat_38ea247` |
| Ward | `RCC-W{nn}` | `RCC-W16` |
| Zone | fixed table above | `R5_10` |

## 8. Units and rounding

- Areas stored in hectares to three decimals; zone areas may also be reported in km².
- Coordinates and distances in metres internally, km in reports.
- Accuracies and proportions stored 0–1, displayed as percentages.
- Dates ISO 8601; timestamps UTC.

## 9. Decision log

| Date | Decision | By |
| --- | --- | --- |
| 2026-11-07 | RCC boundary from WHO/UNICEF ward service; 46.23 km² confirmed correct | Project owner |
| 2026-11-07 | Analysis CRS EPSG:32645; rings at 5 km and 10 km | Protocol |
| 2026-11-07 | Landsat-only baseline; Sentinel comparison separate | Protocol |
| 2026-11-07 | Local STAC processing; no Google Earth Engine | Project owner |
| 2026-11-07 | SQLite + GeoPackage; rasters as COG outside Git | Project owner |
| 2026-11-07 | Season windows confirmed: Boro Nov–Apr, Aus May–Aug, Aman Jun–Nov | Project owner |
| 2026-11-07 | Final benchmark set: Zhao 2026 and Singha 2017; GCD-Rice and BBS out of scope | Project owner |
| 2026-11-07 | Singha unavailable (figshare WAF); APRA500 substituted as second benchmark | Project owner |
