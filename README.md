# Rajshahi Rice Cultivation and Agricultural Land-Use Change, 1990–2025

Research data repository for the study *Seasonal rice persistence and rice-to-urban
conversion across Rajshahi City Corporation and its 5- and 10-km peri-urban zones,
Bangladesh, 1990–2025*.

The full study design is in
[Rajshahi_Rice_LandUse_Research_Protocol.md](Rajshahi_Rice_LandUse_Research_Protocol.md).
This repository holds the reproducible processing skill, the study boundaries, the
database schema and the published summary tables. Large raster products and the raw
scene cache live outside Git (see [Where the data lives](#where-the-data-lives)).

## Status

| Stage | State |
| --- | --- |
| Research protocol | ✅ Committed |
| Processing skill (`skill/rajshahi-rice-landuse`) | ✅ Scaffolded |
| Study boundaries | ✅ Committed |
| Database schema | ✅ Committed |
| Source inventory (STAC, GCD-Rice) | ✅ Committed |
| Full 1990–2025 processing run | 🚧 Provisional products generated |

## Repository layout

```text
RCC_Research/
├── Rajshahi_Rice_LandUse_Research_Protocol.md
├── README.md
├── LICENSE                 MIT — code
├── LICENSE-DATA            CC BY 4.0 — data, tables and documentation
├── .gitignore
├── skill/
│   └── rajshahi-rice-landuse/   Processing skill and role documentation
├── boundaries/                  Study zones, wards and the RCC outline
├── schema/                      Database DDL and data dictionary
├── tables/                      Published summary tables (CSV / Parquet)
├── manifests/                   Source inventory, checksums and run records
├── reports/                     Figures and written outputs
└── data/                        Git-ignored pointer to the runtime data root
```

## Study geography

Zones are built in **EPSG:32645 (WGS 84 / UTM zone 45N)** from the official-looking
RCC ward layer published in the WHO/UNICEF EPI digital microplanning dashboard.

| Zone | Definition |
| --- | --- |
| `RCC` | Rajshahi City Corporation, dissolved from 30 wards |
| `R0_5` | 0–5 km ring outside RCC (5 km buffer minus RCC) |
| `R5_10` | 5–10 km ring (10 km buffer minus 5 km buffer) |
| `RCC_5` | Cumulative RCC + 0–5 km |
| `RCC_10` | Cumulative RCC + 0–5 km + 5–10 km |

The RCC outline measures **46.23 km²**, confirmed against the study definition.
The layer is an operational boundary from a 2024 immunisation microplanning
dataset, not a cadastral or survey boundary. All outputs record
`boundary_status = official_operational` so that distinction is never lost.

## Where the data lives

| Artifact | Location | Committed |
| --- | --- | --- |
| Boundaries, schema, tables, manifests, reports | This repository | Yes |
| Populated SQLite database | Runtime data root | No — rebuilt from `schema/` and scripts |
| COG rasters, raw scenes, virtual environments | Runtime data root | No |
| Final raster release | Zenodo (DOI assigned at release) | No — checksums only |

The runtime data root is an absolute path outside this repository, set through the
`RAJSHAHI_RICE_DATA_ROOT` environment variable:

```bash
export RAJSHAHI_RICE_DATA_ROOT=/home/coder/research-runtime/rajshahi-rice
```

## Provenance

| Input | Reference |
| --- | --- |
| Research protocol | commit `bbc4a58` of this repository |
| Ward and zone boundaries | `Rajshahi_Wards_data/FeatureServer/0`, portal item `bfdf7c83715a4b0781e113fb16fd2ab7`, modified 2024-10-15 |
| Skill authoring reference | `mprgesru/my-farm-advisor-skills` @ `38ea247` (read-only reference; no files copied) |
| Satellite imagery | Landsat Collection 2 Level-2 and Sentinel-1/2 via public STAC catalogs |

The catalog repository above was used only as a documentation and layout reference.
No content was copied from it, and it was not modified.

## Licensing

- **Code** (scripts, skill instructions): MIT — see [LICENSE](LICENSE)
- **Data, tables and documentation**: CC BY 4.0 — see [LICENSE-DATA](LICENSE-DATA)
- **Third-party layers** keep their own status. The RCC ward service declares no
  licence, so boundaries derived from it are marked `licence: unstated` in
  `manifests/boundary_manifest.json`.

## Reproducing

```bash
export RAJSHAHI_RICE_DATA_ROOT=/home/coder/research-runtime/rajshahi-rice
python skill/rajshahi-rice-landuse/scripts/build_zones.py
```

Each script writes a manifest with SHA-256 checksums. Rerun order is recorded in
`manifests/`.
