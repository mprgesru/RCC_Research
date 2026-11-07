# Benchmark Data Sources

Downloads are manual because the file hosts returned HTTP 403 to the build host.
Download from a browser or from your own machine, then place the files in the
paths below.

Target root:

```text
${RAJSHAHI_RICE_DATA_ROOT}/rajshahi-rice/external/
├── zhao/
├── singha/
└── gcd_rice/
```

## 1. Zhao et al. 2026 — South and Southeast Asia, 30 m, 1995–2024

- Landing page: <https://zenodo.org/records/21349862>
- DOI: <https://doi.org/10.5281/zenodo.21349862>
- Licence: see the record
- Files: four ~0.5 GB GeoTIFFs. **You only need the Asia-wide ones**, not "India North".

| File (exact name required) | Size (bytes) | MD5 |
| --- | --- | --- |
| `South and Southeast Asia Paddy Rice 1995.tif` | 511,818,929 | `09fd6521f579fb3c328805c596ec5078` |
| `South and Southeast Asia Paddy Rice 2005.tif` | 504,894,527 | `37a46aa4a9f5d782f611ba43b52d7ce7` |
| `South and Southeast Asia Paddy Rice 2015.tif` | 521,319,463 | `a235ba14bf991a4aa46fe65ea6387063` |
| `South and Southeast Asia Paddy Rice 2024.tif` | 470,463,280 | `0b18f8feadc2babfdfff5b95c2e02517` |

Place them in `${RAJSHAHI_RICE_DATA_ROOT}/rajshahi-rice/external/zhao/`.

Command line (resumable):

```bash
mkdir -p "$RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/external/zhao"
cd "$RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/external/zhao"

for y in 1995 2005 2015 2024; do
  curl -L -C - \
    -o "South and Southeast Asia Paddy Rice ${y}.tif" \
    "https://zenodo.org/records/21349862/files/South%20and%20Southeast%20Asia%20Paddy%20Rice%20${y}.tif?download=1"
done
```

## 2. Singha et al. 2019 — Bangladesh 2017, Sentinel-1

- Landing page: <https://figshare.com/articles/dataset/7873157>
- DOI: <https://doi.org/10.6084/m9.figshare.7873157.v1>
- Licence: see the record (CC BY 4.0 on the article)
- Files: three Bangladesh GeoTIFFs, one per season.

| File (exact name required) | Size (bytes) | MD5 | Direct link |
| --- | --- | --- | --- |
| `Boro_BGD_2017_V1.tif` | 168,363,958 | `ca943fb47a3e8e16ceeaa7a2531df634` | <https://ndownloader.figshare.com/files/14658833> |
| `Aus_BGD_2017_V1.tif` | 110,186,630 | `57e22f70a0db73638cd4c7a636c7a9e4` | <https://ndownloader.figshare.com/files/14658821> |
| `Aman_BGD_2017_V1.tif` | 143,942,908 | `95d28bb40f4b92128b32a33a9a00cc45` | <https://ndownloader.figshare.com/files/14658812> |

Place them in `${RAJSHAHI_RICE_DATA_ROOT}/rajshahi-rice/external/singha/`.

```bash
mkdir -p "$RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/external/singha"
cd "$RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/external/singha"
curl -L -o Boro_BGD_2017_V1.tif https://ndownloader.figshare.com/files/14658833
curl -L -o Aus_BGD_2017_V1.tif  https://ndownloader.figshare.com/files/14658821
curl -L -o Aman_BGD_2017_V1.tif https://ndownloader.figshare.com/files/14658812
```

## 3. GCD-Rice 1990–2023 — 30 m, three seasons

- Landing page: <https://www.scidb.cn/en/detail?dataSetId=68ea15cf08d7469f8c1a653f5589701a>
- DOI: <https://doi.org/10.57760/sciencedb.21665>
- Paper: <https://doi.org/10.1038/s41597-025-05374-1>
- Structure: 16 country folders, each split by season; 918 GeoTIFFs in total.

**Only the Bangladesh folder is needed.** On the landing page, open the data file
list and download the files under the Bangladesh / `BGD` folder, for the seasons
and years you want. There is no documented bulk API; use the browser download.

Place them under `${RAJSHAHI_RICE_DATA_ROOT}/rajshahi-rice/external/gcd_rice/BGD/`.

The comparison script currently covers Zhao and Singha. Once the GCD-Rice files
are downloaded, share the file names and the years/seasons they represent and the
mapping can be added.

## 4. BBS agricultural yearbooks (external consistency check)

- <https://bbs.gov.bd/pages/static-pages/6922e0d6933eb65569e28cbf>

`bbs.gov.bd` is unreachable from the build host. District-level statistics cannot
validate pixels, but they are the standard external check for total area.

## Verify before running

```bash
cd "$RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/external"
md5sum zhao/*.tif singha/*.tif
```

Compare against the tables above. A truncated download is the most common failure
and will otherwise appear as a strange raster extent.

## Run the comparison

```bash
python skill/rajshahi-rice-landuse/scripts/benchmark_products.py
```

Outputs:

- `tables/benchmark_products.csv` — agreement, intersection-over-union and rice
  fraction by product, zone and season.
- `manifests/benchmark.json` — record of which products were present.

Agreement is not accuracy. This step answers "how well do published products
represent the Rajshahi urban fringe", which is the study's stated contribution;
it does not validate our map.

## Licensing and attribution

Each product keeps its own licence. Cite the original papers:

- Li, S. et al. (2025). *Scientific Data*. <https://doi.org/10.1038/s41597-025-05374-1>
- Singha, M. et al. (2019). *Scientific Data* 6, 26. <https://doi.org/10.1038/s41597-019-0036-3>
- Zhao, Z. et al. (2026). *Earth Syst. Sci. Data* 18, 5583–5599. <https://doi.org/10.5194/essd-18-5583-2026>
