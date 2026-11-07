# Benchmark Data Sources — Final Set

The study uses **two benchmark products**:

1. **Zhao et al. (2026)** — 30 m, South and Southeast Asia, 1995–2024
2. **APRA500** — 500 m, monsoon Asia, 2000–2021

Singha et al. (2019) could not be retrieved: its only host (figshare) returns an
AWS WAF challenge to automated clients, and no mirror exists. It is replaced by
APRA500, a published multi-year monsoon-Asia product that covers Bangladesh. The
substitution and its resolution consequence are recorded in the manuscript.

GCD-Rice and the BBS yearbooks are out of scope for the same reason (not
retrievable from the working environment) and remain cited as limitations.

The script finds files by name, so they do not need a fixed folder. It searches
`--external-dir`, the data root, the current directory, the repository root,
`~/Downloads` and the home directory.

## 1. Zhao et al. 2026 — 30 m, 1995–2024

- Landing page: <https://zenodo.org/records/21349862>
- DOI: <https://doi.org/10.5281/zenodo.21349862>
- Files needed: four Asia-wide GeoTIFFs. Do **not** download `India North 2024.tif`.

| File | Size (bytes) | MD5 |
| --- | --- | --- |
| `South and Southeast Asia Paddy Rice 1995.tif` | 511,818,929 | `09fd6521f579fb3c328805c596ec5078` |
| `South and Southeast Asia Paddy Rice 2005.tif` | 504,894,527 | `37a46aa4a9f5d782f611ba43b52d7ce7` |
| `South and Southeast Asia Paddy Rice 2015.tif` | 521,319,463 | `a235ba14bf991a4aa46fe65ea6387063` |
| `South and Southeast Asia Paddy Rice 2024.tif` | 470,463,280 | `0b18f8feadc2babfdfff5b95c2e02517` |

Place under `external/zhao/` (any folder is fine).

## 2. APRA500 — 500 m, monsoon Asia, 2000–2021

- Landing page: <https://zenodo.org/records/5557022>
- DOI: <https://doi.org/10.5281/zenodo.5557022>
- Format: one GeoTIFF per year, EPSG:4326, values `0` non-rice, `1` paddy rice, `3` nodata.
- Files used here: 2000, 2005, 2010, 2015, 2020 (the years overlapping the study).

| File | Size (bytes) | MD5 |
| --- | --- | --- |
| `paddyRice2000.tif` | 3,375,907 | `45132089613877c41799e711af086969` |
| `paddyRice2005.tif` | 3,504,263 | `6e5198b8f58f2beb80712844fe97930c` |
| `paddyRice2010.tif` | 3,488,203 | `29cfee8cdcde8dd5e5c718c7c1c027a4` |
| `paddyRice2015.tif` | 3,399,515 | `c5ad97502b38a0487f1e08c4fc5fb9c8` |
| `paddyRice2020.tif` | 3,421,065 | `72598d648f1f764d9cc9d4043e6f2e85` |

```bash
mkdir -p "$RAJSHAHI_RICE_DATA_ROOT/external/apra500"
cd "$RAJSHAHI_RICE_DATA_ROOT/external/apra500"
for y in 2000 2005 2010 2015 2020; do
  curl -L -o "paddyRice${y}.tif" \
  "https://zenodo.org/api/records/5557022/files/paddyRice${y}.tif/content"
done
```

## 3. Not used

| Source | Reason |
| --- | --- |
| Singha et al. 2019 (figshare `10.6084/m9.figshare.7873157`) | AWS WAF challenge on the only host; no mirror |
| GCD-Rice 1990–2023 (DOI `10.57760/sciencedb.21665`) | Bulk download not retrievable |
| BBS yearbooks (`bbs.gov.bd`) | Site unreachable |

All three are cited and recorded as limitations. Benchmarking is a comparison,
not an input to the maps, so they can be added later without changing results.

## Current results

Run 2026-11-07 with Zhao 2026 and APRA500 (Singha unavailable).

| Product | Year | Our rice | Product rice | Agreement | IoU |
| --- | --- | --- | --- | --- | --- |
| Zhao 2026 | 1995 | 4.8% | 19.6% | 0.796 | 0.077 |
| Zhao 2026 | 2005 | 11.8% | 12.3% | 0.794 | 0.077 |
| Zhao 2026 | 2015 | 17.0% | 12.7% | 0.791 | 0.151 |
| Zhao 2026 | 2024→2025 | 7.1% | 10.6% | 0.844 | 0.053 |
| APRA500 | 2000 | 12.0% | 10.8% | 0.842 | 0.134 |
| APRA500 | 2005 | 11.8% | 11.0% | 0.841 | 0.148 |
| APRA500 | 2010 | 5.2% | 13.4% | 0.862 | 0.124 |
| APRA500 | 2015 | 17.0% | 23.2% | 0.756 | 0.209 |
| APRA500 | 2020 | 7.1% | 16.6% | 0.827 | 0.123 |

By zone, IoU is lowest inside RCC (Zhao 0.02–0.07; APRA500 0.02–0.07) and highest
in the outer ring (APRA500 0.20–0.34). That is consistent with greater divergence
in mixed urban–agricultural pixels.

Two cautions. Agreement is inflated by matching non-rice area and is not accuracy.
APRA500 is 500 m, so pixel-level IoU is structurally lower than for a 30 m
product; compare its area shares and zonal pattern, not its boundaries. And our
map is uncalibrated: in 2010 and 2020 we detect much less rice than APRA500,
partly because of low optical observation counts.

## Run

```bash
python skill/rajshahi-rice-landuse/scripts/benchmark_products.py \
  --data-root "$RAJSHAHI_RICE_DATA_ROOT"
```

Outputs: `tables/benchmark_products.csv`, `tables/benchmark_summary.csv`,
`manifests/benchmark.json`.

## Attribution

- Zhao, Z. et al. (2026). *Earth Syst. Sci. Data* 18, 5583–5599. <https://doi.org/10.5194/essd-18-5583-2026>
- APRA500: <https://doi.org/10.5281/zenodo.5557022>
- Singha, M. et al. (2019). *Scientific Data* 6, 26. <https://doi.org/10.1038/s41597-019-0036-3>
- Li, S. et al. (2025). *Scientific Data*. <https://doi.org/10.1038/s41597-025-05374-1>
