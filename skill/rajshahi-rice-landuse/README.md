# Rajshahi Rice Land-Use Skill

Human overview of the processing skill for the Rajshahi rice and peri-urban
land-use study.

## What this skill does

It converts the research protocol into a deterministic pipeline with five
outcomes:

1. **Study geography** — RCC, two non-overlapping peri-urban rings and two
   cumulative extents, in EPSG:32645.
2. **Seasonal rice maps** — Boro, Aus and Aman at 30 m for eight target years,
   with probability, class, observation-support and confidence layers.
3. **Derived measures** — all-rice physical footprint and cropping intensity
   (0–3 seasons), kept separate from seasonal area.
4. **Change analysis** — five-year transition matrices, persistence and
   intensity transitions by zone.
5. **Validation and publication** — blocked reference samples, UA/PA/F1,
   accuracy-adjusted areas with confidence intervals, and a traceable database.

## Design principles

- **Rasters are the spatial source of truth.** Summary tables are derived and
  must point back to a `map_id`.
- **Landsat-only baseline.** Every year has a Landsat-only result. Sentinel
  enhancements are reported as a separate recent-era comparison.
- **Observation support is data.** Every map carries valid-observation counts and
  a low-support flag; gaps are never silently filled.
- **Benchmarks are not truth.** GCD-Rice and Zhao et al. are compared, not adopted.
- **Reproducibility over convenience.** Each run records code revision, thresholds,
  windows, scene lists and checksums.

## Directory guide

| Path | Contents |
| --- | --- |
| `SKILL.md` | Routing entrypoint and non-negotiable rules |
| `INDEX.md` | Map of roles and scripts |
| `AGENTS.md` | Operating instructions for agents working in this tree |
| `PROVENANCE.md` | Source, reference and update record |
| `references/data-dictionary.md` | Zones, seasons, classes, rasters, tables |
| `roles/` | Six role folders, one per protocol responsibility |
| `scripts/` | Runnable pipeline stages |

## Environments

The pipeline needs Python 3.12 with `geopandas`, `rasterio`, `shapely`,
`pyproj`, `numpy`, `pandas`, `scikit-learn`, `requests` and `pyarrow`.
A dedicated virtual environment is created under the runtime data root, not in
this repository.

## Output locations

```text
${RAJSHAHI_RICE_DATA_ROOT}/rajshahi-rice/
├── raw/          downloaded source windows
├── curated/      merged, validated intermediate layers
├── rasters/      30 m COG products
├── db/           populated SQLite and GeoPackage
├── manifests/    run manifests and checksums
└── logs/
```

Only small, reviewable derivatives are copied back into the repository
(`boundaries/`, `schema/`, `tables/`, `manifests/`, `reports/`).
