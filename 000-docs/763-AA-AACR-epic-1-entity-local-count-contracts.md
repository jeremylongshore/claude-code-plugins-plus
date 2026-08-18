<!-- doc-class: record -->

# Entity-Local Count Contracts — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Scope:** spotlight cards, plugin cards, community cards, and plugin-detail pages
- **Status:** implementation slice; merge fields are recorded in Beads/Dolt after review

## Outcome

The entity-local surfaces in this slice now identify the population attached to
the rendered entity instead of presenting its count as a marketplace total.
The four Astro surfaces use `entity-local`, `contributor-local`, or
`plugin-local` provenance labels. Their exact rendered expressions, labels,
contracts, and checker command are registered in
`scripts/published-count-cohorts.json`; no numeric values were changed.

The checker now supports multiple distinct claims for one source path while
rejecting duplicate expressions, missing contracts, unsafe paths, malformed
claims, and expressions that are not bound to either an enforced or owned
deferred contract. This slice does not govern Cowork bundles, vendor packs,
learning-hub aggregates, historical copy, research snapshots, README counts,
or mirrored skill content.

## Evidence

| Gate                          | Result                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------ |
| Published-count fixture suite | PASS — 33/33, including duplicate-expression and unregistered-claim red proofs |
| Live registry                 | PASS — `ALLOW cohorts=5 enforced=6 deferred=51 discovered=50`                  |
| Changed surfaces              | Four Astro pages/components plus the registry/checker fixtures                 |
| Numeric values                | Unchanged; only local labels and deterministic contracts changed               |
| Mirrored content              | No `.source.json` or mirrored skill content changed                            |
| External systems              | No registry, credential, contributor, Plane, or production mutation            |

## Reproduction

```bash
node --test scripts/check-published-count-cohorts.test.mjs
node scripts/check-published-count-cohorts.mjs --json
```

## Rollback and boundaries

Revert the focused Astro, registry, checker, test, changelog, index, and AAR
changes, then rerun both commands above. The next E1.6 slices must separately
classify the remaining deferred populations; this record does not close the
Bead or authorize Epic 2 work.
