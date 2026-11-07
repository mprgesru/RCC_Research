# Geospatial Data Steward

Owns boundaries, satellite inventory, source manifests and checksums.

## Responsibilities

- Build and validate the five study zones.
- Inventory candidate scenes per year and season from public STAC catalogs.
- Record scene identifiers, acquisition dates, cloud cover and asset URLs.
- Maintain checksums for every committed and runtime artifact.
- Acquire benchmark products and record their coverage and licence.
- Never substitute a source silently.

## Boundary build

Script: `scripts/build_zones.py`

Input: `Rajshahi_Wards_data/FeatureServer/0` (GeoJSON, 30 wards).

Steps:

1. Fetch all 30 features with `f=geojson`, `outSR=4326`.
2. Repair invalid geometry with `make_valid`.
3. Reproject to EPSG:32645.
4. Verify sum-of-parts area against union area; tolerance 0.05 km².
5. Dissolve to the RCC outline; assert 46.23 km² within 1%.
6. Buffer 5 km and 10 km, subtract inward, derive `R0_5` and `R5_10`.
7. Build cumulative `RCC_5` and `RCC_10` by union.
8. Write shapefile, GeoJSON and GeoPackage; record checksums.

Outputs:

```text
RCC_Research/boundaries/rcc_boundary.shp   (+ .shx .dbf .prj .cpg)
RCC_Research/boundaries/rcc_boundary.geojson
RCC_Research/boundaries/rcc_zones.gpkg     (layers: rcc, zones, wards)
RCC_Research/manifests/boundary_manifest.json
```

## Satellite inventory

Catalogs:

| Endpoint | Collections |
| --- | --- |
| `https://earth-search.aws.element84.com/v1` | `landsat-c2-l2`, `sentinel-2-l2a`, `sentinel-1-grd` |
| `https://planetarycomputer.microsoft.com/api/stac/v1` | `landsat-c2-l2`, `sentinel-2-l2a`, `sentinel-1-rtc` |

For Rajshahi the Landsat path/row is **138/043**.

Inventory output fields: `scene_id`, `collection`, `datetime`, `cloud_cover`,
`platform`, `path`, `row`, `assets`, `aoi_coverage`, `scene_manifest_id`.

## Manifest and checksum rules

- One manifest per source and per stage.
- SHA-256 for every output file, including rasters.
- Record retrieval timestamp in UTC and the request URL.
- Record licence and attribution; use `unstated` when absent.

## Validation

- CRS is EPSG:32645 for analysis layers.
- Geometry validity is true for every zone and ward.
- Ring overlap area is under 0.01 km⁻².
- Ward count is 30; zone count is 5 in the `zones` layer, 6 in the source zone layer.
- Dissolved area is 46.23 km² ± 1%.
