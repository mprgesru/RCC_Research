# How to View the Interpretation Chips

The chips are generated data and are **not committed to this repository**, so they
do not appear in the normal Codespace file tree. There are three ways to get them.

## Option 1 — Download from the GitHub release (works anywhere)

Release: <https://github.com/mprgesru/RCC_Research/releases/tag/chips-2020-v1>

Download one season:

```bash
gh release download chips-2020-v1 -R mprgesru/RCC_Research -p "chips_2020_BORO.zip"
```

If `gh` is unavailable, open the release page in a browser and click the asset.

Unzip with Python (no `unzip` needed):

```bash
python - <<'PY'
import zipfile
with zipfile.ZipFile("chips_2020_BORO.zip") as z:
    z.extractall(".")
PY
```

Files land under `chips/2020/BORO/`. Open any PNG directly in the Codespace
explorer, or in GitHub Desktop, or download it.

## Option 2 — If you share this machine's filesystem

The chips are at:

```text
/home/coder/research-runtime/rajshahi-rice/chips/2020/{BORO,AMAN,AUS}/
```

Add that folder to your VS Code workspace:

1. Command Palette (`Ctrl/Cmd+Shift+P`)
2. **Workspace: Add Folder to Workspace**
3. Enter `/home/coder/research-runtime/rajshahi-rice/chips`

You can then click any PNG.

## Option 3 — Browse in a browser with a local server

From a terminal on the machine that holds the chips:

```bash
cd /home/coder/research-runtime/rajshahi-rice/chips/2020
python3 -m http.server 8000
```

Then forward port 8000 (Codespaces **Ports** tab) and open it. The generated
`index.html` shows all chips grouped by season with a sample-ID filter.

Regenerate the viewer at any time:

```bash
python skill/rajshahi-rice-landuse/scripts/make_chip_viewer.py --year 2020
```

## What a chip contains

Each PNG is a three-panel image for one sample point:

| Panel | What to look for |
| --- | --- |
| True colour | Field structure, roofs, roads, water, tree cover |
| False colour (NIR-R-G) | Vegetation in red; water dark; built-up cyan/white |
| NDVI | Green = vegetation, red = water/bare, yellow = sparse cover |

The title shows the sample ID, zone, image date and scene cloud cover. It does
**not** show the mapped class, by design.

## Examples committed to the repository

Six example chips are in [`figures/chip_examples/`](figures/chip_examples/):

| File | What it shows |
| --- | --- |
| `BORO_S2020-0428.png` | Clear water (Padma), mapped as water |
| `BORO_S2020-0001.png` | Dense homestead vegetation mapped as Boro rice — a visible false positive |
| `BORO_S2020-0041.png` | Mixed peri-urban fields and trees |
| `AMAN_S2020-0001.png` | Same point as above, monsoon date |
| `AMAN_S2020-0041.png` | Same point, monsoon date |
| `AUS_S2020-0428.png` | Same water point, Aus date |

These examples are deliberately small enough to commit (under 1 MB total).

## Which file to label

Use `tables/interpretation_sheet.csv`. Each row has three chip paths
(`chip_2020_BORO`, `chip_2020_AMAN`, `chip_2020_AUS`) and fields for one
land-cover class plus a rice call per season (`boro_rice`, `aus_rice`,
`aman_rice`, each `Y`/`N`/`NA`).

After filling it:

```bash
python skill/rajshahi-rice-landuse/scripts/import_labels.py --year 2020
python skill/rajshahi-rice-landuse/scripts/validate.py --year 2020 --measure AMAN
```

See [SAMPLE_INTERPRETATION_GUIDE.md](SAMPLE_INTERPRETATION_GUIDE.md) for the
decision rules.
