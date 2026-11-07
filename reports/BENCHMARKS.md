# Benchmark Data Sources — Final Set

The study uses **two benchmark products**: Zhao et al. (2026) and Singha et al.
(2019). GCD-Rice and the BBS yearbooks were assessed and are **out of scope**
because their files could not be retrieved from the available environment; this is
recorded as a documented deviation in the manuscript.

You do not need to place the files in one exact folder. The comparison script
searches by file name across `--external-dir`, the data root, the current
directory, the repository root, `~/Downloads` and the home directory, then reports
what it found.

## 1. Zhao et al. 2026 — South and Southeast Asia, 30 m, 1995–2024

- Landing page: <https://zenodo.org/records/21349862>
- DOI: <https://doi.org/10.5281/zenodo.21349862>
- Files needed: four Asia-wide GeoTIFFs. Do **not** download `India North 2024.tif`.

| File | Size (bytes) | MD5 | Direct link |
| --- | --- | --- | --- |
| `South and Southeast Asia Paddy Rice 1995.tif` | 511,818,929 | `09fd6521f579fb3c328805c596ec5078` | <https://zenodo.org/records/21349862/files/South%20and%20Southeast%20Asia%20Paddy%20Rice%201995.tif?download=1> |
| `South and Southeast Asia Paddy Rice 2005.tif` | 504,894,527 | `37a46aa4a9f5d782f611ba43b52d7ce7` | <https://zenodo.org/records/21349862/files/South%20and%20Southeast%20Asia%20Paddy%20Rice%202005.tif?download=1> |
| `South and Southeast Asia Paddy Rice 2015.tif` | 521,319,463 | `a235ba14bf991a4aa46fe65ea6387063` | <https://zenodo.org/records/21349862/files/South%20and%20Southeast%20Asia%20Paddy%20Rice%202015.tif?download=1> |
| `South and Southeast Asia Paddy Rice 2024.tif` | 470,463,280 | `0b18f8feadc2babfdfff5b95c2e02517` | <https://zenodo.org/records/21349862/files/South%20and%20Southeast%20Asia%20Paddy%20Rice%202024.tif?download=1> |

## 2. Singha et al. 2019 — Bangladesh 2017, three seasons

- Landing page: <https://figshare.com/articles/dataset/7873157>
- DOI: <https://doi.org/10.6084/m9.figshare.7873157.v1>

| File | Size (bytes) | MD5 | Direct link |
| --- | --- | --- | --- |
| `Boro_BGD_2017_V1.tif` | 168,363,958 | `ca943fb47a3e8e16ceeaa7a2531df634` | <https://ndownloader.figshare.com/files/14658833> |
| `Aus_BGD_2017_V1.tif` | 110,186,630 | `57e22f70a0db73638cd4c7a636c7a9e4` | <https://ndownloader.figshare.com/files/14658821> |
| `Aman_BGD_2017_V1.tif` | 143,942,908 | `95d28bb40f4b92128b32a33a9a00cc45` | <https://ndownloader.figshare.com/files/14658812> |

## 3. Not used

| Source | Reason |
| --- | --- |
| GCD-Rice 1990–2023 (DOI 10.57760/sciencedb.21665) | Science Data Bank bulk download not retrievable from the working environment |
| BBS agricultural yearbooks (bbs.gov.bd) | Site unreachable from the working environment |

Both are cited in the literature review and recorded as limitations. They can be
added later without changing the estimator, because benchmarking is a comparison,
not an input to the maps.

## Comparison years

| Product | Product year | Compared with our map |
| --- | --- | --- |
| Zhao 2026 | 1995 | 1995 union |
| Zhao 2026 | 2005 | 2005 union |
| Zhao 2026 | 2015 | 2015 union |
| Zhao 2026 | 2024 | 2025 union (nearest target year) |
| Singha 2017 | 2017 | 2015 and 2020, for Boro, Aus and Aman separately |

Singha 2017 is compared with both adjacent target years because 2017 sits between
2015 and 2020. Reporting both avoids implying a single nearest-year match.

## Run

Point the script at the study root. It will find the files wherever they are:

```bash
python skill/rajshahi-rice-landuse/scripts/benchmark_products.py \
  --data-root "$RAJSHAHI_RICE_DATA_ROOT"
```

If auto-discovery misses them, point directly at the folder:

```bash
python skill/rajshahi-rice-landuse/scripts/benchmark_products.py \
  --data-root "$RAJSHAHI_RICE_DATA_ROOT" \
  --external-dir "$HOME/Downloads"
```

If our own products are elsewhere:

```bash
--products-dir /path/to/rajshahi-rice/rasters/products
```

Outputs:

- `tables/benchmark_products.csv` — every product × year × zone row
- `tables/benchmark_summary.csv` — mean agreement and IoU per product and season
- `manifests/benchmark.json` — which files were found and where

## Verify downloads

```bash
md5sum "South and Southeast Asia Paddy Rice 2015.tif" Boro_BGD_2017_V1.tif
```

A truncated file will open with a wrong extent or fail to open. Checksums above
are authoritative.

## Current run

Zhao et al. (2026) downloaded and verified (MD5 matched). Compared 2026-11-07:

| Zhao year | Our rice share | Zhao rice share | Agreement | IoU |
| --- | --- | --- | --- | --- |
| 1995 | 4.8% | 19.6% | 0.796 | 0.077 |
| 2005 | 11.8% | 12.3% | 0.794 | 0.077 |
| 2015 | 17.0% | 12.7% | 0.791 | 0.151 |
| 2024 → 2025 | 7.1% | 10.6% | 0.844 | 0.053 |

Singha et al. (2019) is still to be added. The figshare host returns an AWS WAF
challenge to automated clients; run the script where the three files are present
and it will include them automatically.

## Interpretation

Agreement and IoU measure how closely a published product matches our map. They
are **not** accuracy. This step answers the study's stated contribution — how well
published products represent the fragmented Rajshahi fringe — while accuracy still
depends on the 527 interpreted reference points.

## Attribution

- Li, S. et al. (2025). *Scientific Data*. <https://doi.org/10.1038/s41597-025-05374-1>
- Singha, M. et al. (2019). *Scientific Data* 6, 26. <https://doi.org/10.1038/s41597-019-0036-3>
- Zhao, Z. et al. (2026). *Earth Syst. Sci. Data* 18, 5583–5599. <https://doi.org/10.5194/essd-18-5583-2026>
