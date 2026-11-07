# Research Coordinator

Owns agreed scope, definitions, task status and the deliverable checklist. This
role does not process data; it prevents drift.

## Responsibilities

- Keep the eight target years, three seasons, five zones and three measures fixed.
- Maintain the decision log in `references/data-dictionary.md`.
- Track stage status and record blockers.
- Approve any change to definitions before other roles act on it.
- Confirm gates before expensive steps.

## Current status

| Stage | State | Gate |
| --- | --- | --- |
| Skill scaffold | Complete | Files present, internal checks pass |
| Study boundaries | Complete | Zone table reviewed by owner |
| Database schema | Complete | Schema review |
| Source inventory | Complete | Scene counts per year and season reported |
| Product ingest (GCD-Rice) | Pending | Checksums and coverage confirmed |
| Pilot years 2020 and 2025 | Complete | Accuracy and support review |
| Full 1990–2025 run | Complete (provisional) | Per-year manifests complete |
| Land cover (Step 5) | Complete (provisional) | Nine-class derived layer |
| Transitions (Step 7) | Complete (mapped only) | Not interpretable until calibrated |
| Validation (Step 6) | Frame complete | 506-point stratified design, labels pending |
| Release | Pending | Zenodo DOI and checksums |

## Deliverables

- [ ] `boundaries/` — RCC shapefile, GeoJSON and zone GeoPackage
- [ ] `schema/` — SQLite DDL and dictionary alignment
- [ ] `tables/` — area and transition summaries
- [ ] `manifests/` — boundary, scene and run manifests
- [ ] `reports/` — methods, results and validation write-up
- [ ] Skill documentation complete and internally consistent

## Open decisions

| Topic | Needed from |
| --- | --- |
| Season windows confirmed against BRRI/DAE calendars | Local expert or agricultural source |
| Ward boundary version for sensitivity analysis | Owner, if historical wards are available |
| BBS yearbook years and definitions | Owner, manual download |
| Zenodo account and token | Owner, at release |

## Gate protocol

At each gate, report: what was produced, counts and areas, checks performed,
known limitations, and what happens next. Do not proceed through a gate without
an explicit go-ahead.
