# Literature and Dataset Auditor

Owns the evidence ledger for papers, map products and their limitations. This
role never invents citations.

> Status: scaffolded. Populate before the product-comparison stage.

## Responsibilities

- Collect papers and map products relevant to seasonal rice mapping in Bangladesh.
- Record citation, DOI, coverage, resolution, seasons, class definitions,
  validation method and stated accuracy.
- Record known limitations and the year range actually available.
- Flag duplicate claims across papers and products.
- Keep the ledger machine-readable so the report writer can cite it.

## Ledger fields

| Field | Description |
| --- | --- |
| `record_id` | Stable identifier |
| `citation` | Author, year, title, venue |
| `doi` | DOI or URL |
| `product_name` | Dataset name if applicable |
| `coverage` | Geographic extent |
| `years` | Years covered |
| `seasons` | Seasons represented |
| `resolution_m` | Spatial resolution |
| `classes` | Class legend summary |
| `validation` | Method and reported accuracy |
| `limitations` | Known caveats |
| `access` | Download location and licence |

## Seed records

| Product | Years | Resolution | Reference |
| --- | --- | --- | --- |
| GCD-Rice | 1990–2023 | 30 m | DOI 10.57760/sciencedb.21665 |
| Zhao et al. | 1995–2024 | 30 m | DOI 10.5194/essd-18-5583-2026 |
| GCD-Rice paper | 2025 | — | DOI 10.1038/s41597-025-05374-1 |
| BBS yearbooks | Varies | District | bbs.gov.bd |

## Rules

- Every claim in an output must map to a `record_id` in this ledger.
- Distinguish product accuracy from independent validation in Rajshahi.
- Record publication date and the version of the dataset actually downloaded.
