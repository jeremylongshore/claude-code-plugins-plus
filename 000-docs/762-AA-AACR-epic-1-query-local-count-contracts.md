# Query-Local Count Contracts — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Scope:** query-result and entity-local counts in the search UI
- **Status:** implementation slice; merge fields are recorded in Beads/Dolt after review

## Outcome

The search UI now distinguishes counts attached to one result entity from the
current filtered query result. These values retain their existing numbers and
are labeled `entity-local` or `query-result-local`; they are not represented as
the marketplace-wide cohort. Each deferred expression carries the executable
checker command and one exact contract binding expression, label, provenance,
runtime sink, rendering function, and observed call site in the machine-
readable count registry. The checker does not claim to recompute arbitrary
browser-query values; it refuses deferred entries with missing, contradictory,
unbound, or unreachable local contracts.

## Evidence

| Gate                          | Result                                                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------------------------------ |
| Published-count fixture suite | PASS — 32/32, including missing local contract red proofs                                              |
| Live registry                 | PASS — `ALLOW cohorts=5 enforced=6 deferred=49 discovered=51`                                          |
| Mirrored content              | No `.source.json` or mirrored skill content changed                                                    |
| Numeric values                | Unchanged; only labels and contract metadata changed                                                   |
| Runtime bindings              | `renderCard`/`metaParts.push` and `updateResultsCount`/`el.innerHTML`, each with an observed call site |

## Rollback and boundaries

Revert the focused page, registry, checker, test, documentation, and changelog
changes, then rerun the fixture suite and live registry check. Global
marketplace totals, README work, vendor packs, research snapshots, package
contents, and external systems are outside this slice.
