# Coordinator Instructions

## Authority

This role may freeze definitions and reject work that violates them. It may not
alter the scientific protocol's requirements.

## When reviewing a stage

1. Check that outputs reference a `map_id` or manifest entry.
2. Check that zone IDs, season codes and class codes match the data dictionary.
3. Check that observation support is reported, not just accuracy.
4. Check that low-support years are flagged rather than smoothed away.
5. Check that any source substitution is recorded explicitly.

## Status maintenance

Update the status table in `README.md` whenever a stage changes state. Keep one
source of truth; do not duplicate status into other role files.

## Escalation

Stop and ask the project owner when:

- a season window cannot be confirmed from an authoritative source;
- a third-party product's licence is unclear and redistribution is proposed;
- a gate's counts differ materially from prior estimates;
- a definition change would invalidate earlier outputs.
