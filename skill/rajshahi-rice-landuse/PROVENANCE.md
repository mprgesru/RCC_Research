# Provenance

Record of where this skill came from, what it references, and how it is updated.

## Study definition

| Field | Value |
| --- | --- |
| Protocol | `Rajshahi_Rice_LandUse_Research_Protocol.md` |
| Protocol commit at skill creation | `bbc4a58` |
| Protocol status | Planning draft, prepared 7 November 2026 |
| Study area | Rajshahi City Corporation plus 0–5 km and 5–10 km rings |
| Target years | 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025 |
| Primary resolution | 30 m |
| Analysis CRS | EPSG:32645 (WGS 84 / UTM zone 45N) |

## Authoring reference

This skill was authored with `mprgesru/my-farm-advisor-skills` at commit
`38ea247` as a **read-only documentation and layout reference**.

- No files, code or assets were copied from that repository.
- That repository was not modified in any way.
- Its catalog structure informed the choice of `SKILL.md`, `INDEX.md`,
  `README.md`, `PROVENANCE.md` and `AGENTS.md`, and the role-based routing.

## Boundary source

| Field | Value |
| --- | --- |
| Service | `https://services.arcgis.com/5T5nSi527N4F7luB/arcgis/rest/services/Rajshahi_Wards_data/FeatureServer/0` |
| Portal item | `bfdf7c83715a4b0781e113fb16fd2ab7` |
| Portal item title | Rajshahi City Corporation EPI Digital Microplanning |
| Owner | `digital_micplan` (WHO ArcGIS Online) |
| Item last modified | 2024-10-15 |
| Features | 30 wards, 6 zones |
| Dissolved RCC area | 46.227 km² |
| Geometry check | 1 invalid ring repaired with `make_valid`; 0.002 km² overlap/gap |
| Licence | Unstated on the service; recorded as `licence: unstated` |
| Boundary status | `official_operational` (not cadastral or survey) |

The RCC area of 46.23 km² was confirmed by the project owner as the correct study
definition.

## Satellite sources

| Source | Endpoint | Authentication |
| --- | --- | --- |
| Landsat C2 L2 | AWS Earth Search STAC `https://earth-search.aws.element84.com/v1` | None |
| Landsat C2 L2 (fallback) | Microsoft Planetary Computer STAC | None |
| Sentinel-2 L2A | Planetary Computer `sentinel-2-l2a` | None |
| Sentinel-1 | Earth Search `sentinel-1-grd` | None |

Google Earth Engine is deliberately not used. It requires account credentials and
moves processing off this host; public STAC catalogs cover the protocol's needs.

## Product sources

| Product | Reference | Status |
| --- | --- | --- |
| GCD-Rice 1990–2023 | Science Data Bank, DOI 10.57760/sciencedb.21665 | Landing page reachable; bulk host returned 403 from build host; manual download required |
| Zhao et al. 2026 (1995–2024) | Zenodo, DOI 10.5281/zenodo.21349862 | Available; four ~500 MB GeoTIFFs (1995, 2005, 2015, 2024) |
| BBS yearbooks | `bbs.gov.bd` | Unreachable from build host; manual download required |

## Update procedure

1. Update the protocol file and note the new commit SHA here.
2. Do not change zone IDs, season codes or class codes without updating
   `references/data-dictionary.md` in the same change.
3. Rebuild boundaries only with `--force`, and record the new area in this file
   and in `manifests/boundary_manifest.json`.
4. Rerun `scripts/build_zones.py` and confirm the dissolved area is still
   46.23 km² (tolerance 1%).
5. Commit manifests and checksums with any regenerated output.
