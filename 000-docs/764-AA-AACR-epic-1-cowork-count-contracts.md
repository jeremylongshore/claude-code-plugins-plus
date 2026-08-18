# Cowork Package Count Contracts — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Scope:** Cowork category bundles, individual package cards, landing-page totals, and download summary
- **Status:** implementation slice; merge fields are recorded in Beads/Dolt after review

## Outcome

The Cowork surfaces now identify counts as `Cowork-package-local`, separating
downloadable package and bundle populations from the marketplace-visible
corpus. Nine exact rendered claims are registered for the two deferred Astro
surfaces and reproduced by `node scripts/check-published-count-cohorts.mjs --json`.
The stale numeric counts remain generated from `cowork-manifest.json`; the
landing-page metadata description no longer repeats an unlabeled count.

## Evidence

| Gate                          | Result                                                              |
| ----------------------------- | ------------------------------------------------------------------- |
| Published-count fixture suite | PASS — 33/33, including duplicate-expression red proof              |
| Live registry                 | PASS — `ALLOW cohorts=5 enforced=6 deferred=57 discovered=50`       |
| Claims                        | Nine exact contracts across `CoworkGrid.astro` and `cowork.astro`   |
| Numeric corpus values         | Unchanged; only local population labels/contracts changed           |
| Mirrored content              | No `.source.json` or mirrored skill content changed                 |
| External systems              | No registry, credential, contributor, Plane, or production mutation |

## Reproduction

```bash
node --test scripts/check-published-count-cohorts.test.mjs
node scripts/check-published-count-cohorts.mjs --json
```

## Rollback and boundaries

Revert the focused Cowork, registry, changelog, index, scorecard, and AAR
changes, then rerun both commands above. Vendor-pack, learning-hub,
historical-copy, research, README, and mirrored-content populations remain
separate E1.6 follow-up work; this slice does not close the Bead or authorize
Epic 2.
