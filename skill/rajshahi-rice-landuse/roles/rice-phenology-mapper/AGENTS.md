# Phenology Mapper Instructions

## Preconditions

- `scripts/build_zones.py` has produced validated zones.
- A scene inventory manifest exists for the target year and season.
- Training samples are approved and stored in `reference_samples` with
  `split = train`.
- Watch for leakage: validation samples must be spatially blocked from training.

## Processing order

```text
inventory -> windowed scene reads -> cloud mask -> seasonal composite
          -> features -> train/select -> predict probability -> threshold
          -> class -> support -> confidence -> sidecar
```

## Read discipline

- Never download a full Landsat scene for this AOI. Read the windowed COG.
- Keep a scene list per composite so it can be rebuilt.
- Store composite inputs in the manifest, not only outputs.

## Model discipline

- Fix random seeds.
- Record library versions for the classifier.
- Keep rule-based and random-forest candidates comparable on the same samples.
- Do not tune on the independent validation split.

## Prohibited

- Splicing Sentinel-enhanced values into the historical series.
- Reporting a class map without its probability and support layers.
- Applying one season's threshold to another season.
- Filling gaps silently.
