# Data Steward Instructions

## Read first

`references/data-dictionary.md` sections 1, 2 and 5, then `PROVENANCE.md`.

## Boundary edits

- Never hand-edit boundary files. Change `scripts/build_zones.py` and rerun.
- Reruns require `--force`; a plain run must refuse to overwrite an existing
  manifest.
- If the ward service changes, diff ward count and dissolved area before
  accepting. A change outside tolerance is a coordinator decision.

## Inventory edits

- Keep the Landsat path/row and AOI bbox in one constants block.
- Do not download full scenes for inventory. Read STAC metadata only.
- Record both the STAC item ID and the provider's original scene ID where they differ.
- Store asset URLs, not signed URLs, unless the signature is session-scoped.

## Checksum discipline

- Compute checksums after the file is closed and flushed.
- Sort file paths before hashing so manifests are deterministic.
- Manifests are append-only by run; do not rewrite prior run records.

## Prohibited

- Committing rasters or the populated database.
- Using credentials in scripts or manifests.
- Treating a provider's "latest" alias as a fixed version.
