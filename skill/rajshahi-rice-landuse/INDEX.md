# Skill Index

Route a task through the role that owns it. Roles may read each other's outputs
but must not redefine shared definitions.

## Roles

| Role | Owns | Start here |
| --- | --- | --- |
| Research Coordinator | Scope, definitions, task status, deliverable checklist | [roles/research-coordinator/README.md](roles/research-coordinator/README.md) |
| Literature and Dataset Auditor | Citations, product coverage, class definitions, limitations | [roles/literature-dataset-auditor/README.md](roles/literature-dataset-auditor/README.md) |
| Geospatial Data Steward | Boundaries, satellite inventory, manifests, checksums | [roles/geospatial-data-steward/README.md](roles/geospatial-data-steward/README.md) |
| Rice Phenology Mapper | Composites, features, classifiers, probability and class layers | [roles/rice-phenology-mapper/README.md](roles/rice-phenology-mapper/README.md) |
| Accuracy and Change Analyst | Reference samples, accuracy, area adjustment, transitions | [roles/accuracy-change-analyst/README.md](roles/accuracy-change-analyst/README.md) |
| Research Report Writer | Reports and figures from approved outputs | [roles/research-report-writer/README.md](roles/research-report-writer/README.md) |

## Shared references

- [Data dictionary](references/data-dictionary.md) — zones, seasons, classes, rasters, tables
- [Provenance](PROVENANCE.md) — sources, versions, reference repositories
- [Operating rules](AGENTS.md) — what agents may and may not change

## Scripts

| Script | Role | Status |
| --- | --- | --- |
| `scripts/build_zones.py` | Data Steward | Implemented |
| `scripts/make_db.py` | Data Steward | Implemented |
| `scripts/stac_inventory.py` | Data Steward | Implemented |
| `scripts/download_gcd_rice.py` | Data Steward | Pending |
| `scripts/build_composites.py` | Phenology Mapper | Pending |
| `scripts/classify.py` | Phenology Mapper | Pending |
| `scripts/validate.py` | Accuracy and Change Analyst | Pending |
| `scripts/load_tables.py` | Data Steward | Pending |

## Execution order

```text
build_zones -> make_db -> stac_inventory -> download_gcd_rice
            -> build_composites -> classify -> validate -> load_tables
```

Every stage writes a manifest and can be rerun independently. A stage never
overwrites a completed manifest without `--force`.
