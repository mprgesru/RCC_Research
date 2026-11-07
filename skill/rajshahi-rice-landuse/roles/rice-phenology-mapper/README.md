# Rice Phenology Mapper

Owns seasonal preprocessing, feature generation, model runs, probability layers
and product metadata.

## Responsibilities

- Build seasonal 30 m composites from multi-date observations, never from a
  single selected image.
- Generate phenology features (for example NDVI, EVI, LSWI and SWIR1 trajectories).
- Train separate classifiers or decision rules per season: Boro, Aus and Aman.
- Compare a phenology-guided random forest baseline with a simple phenology-rule
  baseline, and select using spatially blocked validation.
- Export probability and class maps, observation support and confidence layers.
- Derive all-rice union and cropping intensity from the three seasonal layers.
- Produce general land cover for transition attribution.

## Method constraints

| Constraint | Reason |
| --- | --- |
| Separate model per season | Thresholds do not transfer across seasons |
| Landsat-only stack for all years | Prevents sensor-driven artificial trends |
| Sentinel-enhanced stack for 2015+ only | Reported as a separate comparison |
| Multi-date phenology, not single dates | Rice is defined by flooding and green-up timing |
| Probabilities retained | Supports thresholds, confidence and uncertainty |
| Valid-observation counts exported | Support is part of the result |

## Features

| Feature | Definition | Use |
| --- | --- | --- |
| NDVI | `(NIR - Red) / (NIR + Red)` | Green-up and peak growth |
| EVI | `2.5(NIR - Red) / (NIR + 6Red - 7.5Blue + 1)` | Dense canopy |
| LSWI | `(NIR - SWIR1) / (NIR + SWIR1)` | Flooding and transplanting |
| SWIR1 trajectory | Surface reflectance time series | Moisture and paddy signal |
| SAR VH/VV (recent) | Sentinel-1 backscatter | Cloud-independent flooding signal |

## Outputs

For each year and season:

```text
rice_prob_{SEASON}_{YEAR}_30m.tif
rice_class_{SEASON}_{YEAR}_30m.tif
obs_support_{SEASON}_{YEAR}_30m.tif
confidence_{SEASON}_{YEAR}_30m.tif
```

Per year:

```text
rice_union_{YEAR}_30m.tif
rice_intensity_{YEAR}_30m.tif
lulc_{YEAR}_30m.tif
```

Each output has a JSON sidecar with the fields defined in the data dictionary.

## Support flagging

- Compute valid observations per pixel after cloud, shadow, saturation and
  invalid-value masking.
- Summarise support by zone and season.
- Set `low_support = true` when median valid observations fall below the agreed
  threshold, and produce a three-year composite centred on the target year.
- Never interpolate across a season to manufacture support in the production
  product; keep interpolation for pre-classification experiments only.

## Selection and reporting

- Report the candidate models compared, the validation design, the chosen method
  and the reason.
- Record threshold selection method.
- Report per-season and per-zone metrics, not only a global average.

## Status

Not implemented. Expected scripts: `scripts/build_composites.py`,
`scripts/classify.py`.
