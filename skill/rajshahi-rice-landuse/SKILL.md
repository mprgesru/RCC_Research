---
name: rajshahi-rice-landuse
description: >
  Reproducible geospatial workflow for mapping seasonal rice (Boro, Aus, Aman),
  all-rice footprint, cropping intensity and rice-to-urban land-use transitions in
  Rajshahi City Corporation and its 0-5 km and 5-10 km peri-urban rings,
  Bangladesh, 1990-2025. Use for source acquisition, seasonal classification,
  accuracy assessment, transition analysis and publication of the study database.
license: MIT
metadata:
  author: mprgesru
  version: "0.1.0"
  skill-author: mprgesru
  skill-version: "0.1.0"
  protocol: Rajshahi_Rice_LandUse_Research_Protocol.md
  protocol-commit: bbc4a58
---

# Rajshahi Rice Land-Use

Reproducible workflow for the Rajshahi rice and peri-urban land-use study. This
skill turns the research protocol into runnable steps: acquire sources, build
seasonal 30 m rice maps, validate them, quantify transitions and publish a
traceable database.

## Start Here

Read [references/data-dictionary.md](references/data-dictionary.md) first. It is the
single source of truth for zone IDs, season definitions, class codes, raster
naming and database fields.

Then open the role that matches the task:

- [Research Coordinator](roles/research-coordinator/README.md) — scope, definitions, status, deliverable checklist
- [Literature and Dataset Auditor](roles/literature-dataset-auditor/README.md) — papers, products, coverage and limitations
- [Geospatial Data Steward](roles/geospatial-data-steward/README.md) — boundaries, STAC inventory, manifests, checksums
- [Rice Phenology Mapper](roles/rice-phenology-mapper/README.md) — composites, features, classifiers, probability layers
- [Accuracy and Change Analyst](roles/accuracy-change-analyst/README.md) — validation, area adjustment, transitions, zone summaries
- [Research Report Writer](roles/research-report-writer/README.md) — reports from approved outputs only

## Non-negotiable rules

1. Do not rename zone IDs, seasons or class codes. Use the data dictionary verbatim.
2. Keep seasonal area, all-rice physical footprint and cropping intensity separate.
3. Keep a Landsat-only series for every target year. Sentinel-enhanced results are a
   separate comparison, never spliced into the historical series.
4. Record observation windows, scene counts and valid-observation support for every
   map. Flag low-support years instead of silently filling gaps.
5. Treat published rice products as benchmarks, not ground truth.
6. Every reported statistic must point to a `map_id` or table row that can be rebuilt.

## Runtime

All generated data lives outside the repository:

```bash
export RAJSHAHI_RICE_DATA_ROOT=/home/coder/research-runtime/rajshahi-rice
```

Committed here: boundaries, schema, summary tables, manifests and reports.
Not committed here: COG rasters, raw scenes, populated databases, virtual
environments.

## Data sources

| Source | Use | Access |
| --- | --- | --- |
| Landsat C2 L2 (L4–L9) | Historical optical series, all years | Public STAC (Earth Search / Planetary Computer) |
| Sentinel-2 L2A | Recent optical comparison, 2015+ | Public STAC |
| Sentinel-1 GRD/RTC | Cloud-independent recent comparison, 2014+ | Public STAC |
| GCD-Rice 1990–2023 | Benchmark product | Science Data Bank, DOI 10.57760/sciencedb.21665 |
| Zhao et al. 2026 | Benchmark product | ESSD, DOI 10.5194/essd-18-5583-2026 |
| BBS yearbooks | External consistency check | Manual download (site unreachable from build host) |
| RCC wards and zones | Study geography | ArcGIS FeatureServer, portal item bfdf7c83715a4b0781e113fb16fd2ab7 |

## Status

Phase 0 (skill scaffold) and Phase 1 (study boundaries) are in progress. The
database schema, source inventory and processing run are pending. See the
[coordinator role](roles/research-coordinator/README.md) for the live checklist.
