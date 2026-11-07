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
| Singha et al. paddy maps | 2017 | 10 m | figshare DOI 10.6084/m9.figshare.7873157 — not retrievable (WAF) |
| APRA500 | 2000–2021 | 500 m | DOI 10.5281/zenodo.5557022 — substituted benchmark |
| Rahman et al. reference samples | 2021–2022 | 100 m² polygons | doi 10.1371/journal.pone.0355502; GitHub HamidurRahman |
| Olofsson et al. good practice | 2014 | — | DOI 10.1016/j.rse.2014.02.015 |
| BBS yearbooks | Varies | District | bbs.gov.bd |

Notes on usability for this study:

- Singha et al. 2017 provides independent maps, not samples, and only for 2017.
  Use for product comparison, not validation.
- Rahman et al. national samples contain 100 polygons for Aus and 100 for Aman.
  Only one polygon falls inside the Rajshahi AOI (aquaculture), so they cannot
  validate this study. They remain useful for method comparison.
- Olofsson et al. defines the sampling and estimation protocol we adopt.

## Rules

- Every claim in an output must map to a `record_id` in this ledger.
- Distinguish product accuracy from independent validation in Rajshahi.
- Record publication date and the version of the dataset actually downloaded.
