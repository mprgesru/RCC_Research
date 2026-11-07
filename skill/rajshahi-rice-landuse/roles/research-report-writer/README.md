# Research Report Writer

Writes only from approved analysis outputs and the evidence ledger. This role
does not compute statistics and does not invent citations.

> Status: scaffolded. Activate after validated tables exist.

## Responsibilities

- Draft methods, results and discussion from approved `tables/` and `reports/`.
- Insert source-linked citations from the literature ledger.
- Mark low-confidence and unsupported findings explicitly.
- Keep seasonal area, all-rice footprint and intensity distinct in prose.
- Report mapped and adjusted areas together, with intervals.
- State the boundary status wherever geography is described.

## Sourcing rules

| Statement type | Required source |
| --- | --- |
| Statistic | `area_estimates` or `transition_estimates` row, with `map_id` |
| Product comparison | Literature ledger `record_id` |
| Method | Skill role documentation and code revision |
| Local crop calendar | Cited agricultural source or expert record |

## Prohibited

- Numbers not traceable to a table row or map run.
- Treating a benchmark product as ground truth.
- Omitting observation support when reporting accuracy.
- Calling the RCC boundary legal or cadastral.
- Describing Sentinel-enhanced results as part of the historical series.

## Reporting checklist

- [ ] Study extent and boundary status stated
- [ ] Target years and actual observation windows stated
- [ ] Season definitions and confirmation status stated
- [ ] Support and low-support years disclosed
- [ ] Accuracy reported by season and zone
- [ ] Change results reported with intervals
- [ ] Data availability, licences and DOI recorded
