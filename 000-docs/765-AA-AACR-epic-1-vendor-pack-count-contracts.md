<!-- doc-class: record -->

# Vendor-Pack Count Contracts — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Scope:** 30 generated `/learn/<vendor>/` pages
- **Status:** implementation slice; merge fields are recorded in Beads/Dolt after review

## Outcome

Each vendor learning page now labels its pack and category counts as
`vendor-pack-local`. Metadata titles and descriptions no longer repeat an
unscoped skill total. Sixty exact claims (two per page) are registered against
the generated vendor-pack population; numeric values are unchanged.

## Evidence

| Gate                          | Result                                                              |
| ----------------------------- | ------------------------------------------------------------------- |
| Published-count fixture suite | PASS — 34/34, including live vendor-pack claim coverage             |
| Live registry                 | PASS — `ALLOW cohorts=5 enforced=6 deferred=88 discovered=20`       |
| Claims                        | 60 exact claims across 30 vendor pages                              |
| Numeric values                | Unchanged; labels and metadata wording only                         |
| Mirrored content              | No `.source.json` or mirrored skill content changed                 |
| External systems              | No registry, credential, contributor, Plane, or production mutation |

## Reproduction

```bash
node --test scripts/check-published-count-cohorts.test.mjs
node scripts/check-published-count-cohorts.mjs --json
```

## Rollback and boundaries

Revert the focused vendor-page, registry, test, changelog, index, scorecard,
and AAR changes, then rerun the commands above. Learning-hub aggregate,
historical/live-copy, research, README, and mirrored-content populations remain
separate E1.6 work; this record does not close the Bead or authorize Epic 2.
