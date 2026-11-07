# Operating Instructions

Local rules for agents and contributors working in this skill tree.

## Read first

1. `SKILL.md` for routing and non-negotiable rules.
2. `references/data-dictionary.md` for zone, season, class and table definitions.
3. `PROVENANCE.md` before changing sources, boundaries or versions.
4. The matching role `README.md` before running or editing a stage.

## What may be edited

- Documentation and scripts inside `skill/rajshahi-rice-landuse/`.
- Boundary, schema, table and manifest outputs, but only through the scripts that
  produce them.

## What must not be edited

- Zone IDs, season codes and class codes. They are frozen in the data dictionary.
- The protocol document's substantive requirements.
- Third-party source records. Add corrections as new manifest entries instead of
  rewriting history.

## Data handling

- Never commit rasters, raw scenes, populated databases or virtual environments.
- Every generated artifact goes under `${RAJSHAHI_RICE_DATA_ROOT}`.
- Copy only small reviewable derivatives into the repository.
- Write a manifest with SHA-256 checksums for every stage that produces files.

## Reproducibility

- Record the code revision, parameters, input scene list and output checksums for
  every map run.
- A map run is identified by `map_id`; tables reference it.
- Reruns must be deterministic given the same scene list and parameters.

## Validation

- Geometry: validity, CRS, area, overlap and gap checks before writing.
- Schema: foreign keys resolve; enum values match the data dictionary.
- Analysis: confusion matrices and adjusted areas recompute from stored samples.

## Communication

- Report counts before long runs: scenes per year and season, valid-observation
  estimates, expected runtime and size.
- Stop at agreed gates rather than continuing through them.
- Flag substitutions explicitly; never silently swap a source.
