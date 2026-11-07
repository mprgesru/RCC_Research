# Accuracy and Change Analyst

Owns independent validation, area adjustment, confidence intervals, transition
matrices and zone summaries.

> Status: scaffolded. Methods specified here; scripts pending.

## Responsibilities

- Design stratified, spatially blocked reference sampling.
- Keep training, calibration and independent validation splits separate.
- Compute confusion matrices, user's accuracy, producer's accuracy and F1 by
  season, zone and year.
- Estimate class area with accuracy adjustment and 95% confidence intervals.
- Validate change classes separately: stable rice, gain, loss, rice-to-built-up.
- Build five-year transition matrices and persistence summaries.
- Summarise by zone and, where defensible, by ward.
- Report observation support alongside every accuracy figure.

## Sampling design

Stratify by:

1. Mapped class and season.
2. Zone (`RCC`, `R0_5`, `R5_10`).
3. Stability: stable rice, apparent transition, product disagreement.

Constraints:

- Spatial blocks keep neighbouring pixels from the same field out of both train
  and validation sets.
- Minimum sample sizes are recorded per stratum; small strata are reported as
  low-confidence rather than pooled silently.
- Historical evidence is labelled as reference interpretation, not field truth.

## Area adjustment

Use a stratified estimator consistent with the sampling design. Report:

- mapped area
- adjusted area
- 95% interval
- sample count
- UA, PA and F1

Never present raw pixel counts as the final area estimate when validation
evidence exists.

## Transition analysis

For each consecutive five-year pair:

- gross gain, gross loss and net change per season and for the all-rice union
- transitions from rice to built-up, orchard, other cropland, water, other
  vegetation and bare land
- persistence and intensity transitions (for example single- to double-season)

Aggregate for `RCC`, `R0_5`, `R5_10`, `RCC_5` and `RCC_10`, plus wards where
boundaries are comparable. Do not sum cumulative zones with their components.

## Guardrails

- Do not infer road-access effects from a modern road layer.
- Do not present precise trend claims for early years with weak support.
- Keep mapped and error-adjusted results side by side.
- Change validation is separate from stable-class validation.
