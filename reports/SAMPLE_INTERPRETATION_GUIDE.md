# Reference Sample Interpretation Guide

How to label the 506-point reference sample so that accuracy and area estimates are
defensible. Follow this exactly; deviations must be recorded in the manifest.

## 1. Blinding

Interpreters must not see the map class or the stratum.

- Use `tables/interpretation_sheet.csv`, which contains only `sample_id`, zone,
  year, chip path and blank label fields.
- The chip images show a sample ID, zone, date and cloud cover. They do **not**
  show the mapped class.
- `tables/reference_sample_sheet.csv` contains the map key and is for analysis
  only. Do not give it to interpreters.

This matters: if interpreters can see what the map predicted, agreement is
inflated and the validation is circular.

## 2. Evidence hierarchy

Prefer evidence in this order, and record which one you used.

| Rank | Evidence | `reference_source` value |
| --- | --- | --- |
| 1 | Field visit or geotagged photo | `field` |
| 2 | Dated high-resolution imagery (sub-metre) | `vhr:<provider>:<date>` |
| 3 | Multi-date Sentinel-2 or Landsat time series | `s2_timeseries` / `landsat_timeseries` |
| 4 | Dated archived map or planning document | `map:<source>:<date>` |
| 5 | Published product | `product:<name>` — comparison only, never a label |

Historical labels are **reference interpretation**, not field truth. Say so in the
methods section.

## 3. Label vocabulary

Use exactly one code per sample:

| Code | Meaning |
| --- | --- |
| `BORO` | Rice, dry season |
| `AUS` | Rice, summer season |
| `AMAN` | Rice, monsoon season |
| `OTHER_CROPLAND` | Non-rice annual crop or fallow |
| `ORCHARD` | Perennial agriculture, mango where identifiable |
| `OTHER_VEG` | Trees, homestead vegetation, non-agricultural vegetation |
| `BUILT` | Buildings, roads, impervious surfaces |
| `WATER` | River, pond, canal, wetland |
| `BARE` | Exposed soil, sand, construction site |

If a pixel is genuinely mixed, choose the dominant cover and set confidence `low`.

## 4. Confidence scale

| Value | Meaning |
| --- | --- |
| `high` | Unambiguous on the available evidence |
| `medium` | Probable, minor ambiguity |
| `low` | Mixed pixel, poor imagery, or conflicting evidence |

Report the share of low-confidence samples. Do not silently drop them.

## 5. Decision rules for hard cases

- **Rice vs other crop.** Rice needs evidence of paddy: standing water, bunded
  fields, or a clear flood-to-green-up sequence. A single green field is not rice.
- **Orchard vs other vegetation.** Only label `ORCHARD` when rows, planting
  pattern, or known mango blocks are visible. Otherwise use `OTHER_VEG`. Do not
  infer orchard from location alone.
- **Fallow vs other cropland.** Bare, recently harvested, or prepared fields are
  `OTHER_CROPLAND`.
- **Built-up in villages.** If buildings and trees are mixed, label the dominant
  surface. Note the ambiguity.
- **Water seasonality.** Use `WATER` for permanent water. Temporary flood on a
  field is not a water class; label the field.
- **Season.** If rice is present, assign the season whose window the evidence
  falls in. If timing is unclear, set `low` confidence.

## 6. Procedure

1. Open `tables/interpretation_sheet.csv`.
2. For each row, open the chip, and add extra evidence if needed.
3. Enter `reference_class`, `confidence`, `interpreter_id` and short `notes`.
4. Save as UTF-8 CSV. Do not rename or reorder rows.
5. A second interpreter independently labels at least 20% of the sample.
6. Compare the two sets. Where they disagree, resolve with a documented rule and
   record the resolution in `notes`.

## 7. What not to do

- Do not look at the map class before labelling.
- Do not label from the map itself, or from a product that the map was trained on.
- Do not invent dates or sources.
- Do not drop difficult samples; mark them `low` confidence instead.
- Do not label a point you cannot see clearly. Flag it for field checking.

## 8. After labelling

Run:

```bash
export RAJSHAHI_RICE_DATA_ROOT=/home/coder/research-runtime/rajshahi-rice
python skill/rajshahi-rice-landuse/scripts/validate.py --year 2020
```

This produces the area-proportion error matrix, user's and producer's accuracy,
overall accuracy with standard error, and class areas with 95% intervals.

## 9. Minimum acceptable evidence for a journal submission

- At least 506 points for 2020 (SE 0.02), or ~900 for SE 0.015.
- At least 20% double-interpreted, with a reported disagreement rate.
- Low-confidence share reported.
- Field or dated VHR evidence for a subsample, so the reference data are not
  purely satellite-derived.
