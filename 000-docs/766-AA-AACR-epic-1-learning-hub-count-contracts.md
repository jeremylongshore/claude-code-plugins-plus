# Learning-Hub Count Contracts — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Scope:** `marketplace/src/pages/learn/index.astro`
- **Status:** implementation slice; merge fields are recorded in Beads/Dolt after review

## Outcome

The learning hub now distinguishes its aggregate vendor-pack totals from the
per-pack counts shown in its tier and vendor cards. Four exact claims are
registered on the page: two `learning-hub-aggregate` claims and two
`vendor-pack-local` claims. Unscoped metadata and range wording were removed;
numeric source values were not changed.

## Evidence

| Gate                          | Result                                                              |
| ----------------------------- | ------------------------------------------------------------------- |
| Published-count fixture suite | PASS — 35/35, including hub claim coverage                          |
| Live registry                 | PASS — `ALLOW cohorts=5 enforced=6 deferred=91 discovered=20`       |
| Claims                        | Four exact claims on the learning hub                               |
| Numeric values                | Unchanged; only population labels and copy wording changed          |
| Mirrored content              | No `.source.json` or mirrored skill content changed                 |
| External systems              | No registry, credential, contributor, Plane, or production mutation |

## Reproduction

```bash
node --test scripts/check-published-count-cohorts.test.mjs
node scripts/check-published-count-cohorts.mjs --json
```

## Rollback and boundaries

Revert the focused learning-hub, registry, test, changelog, index, scorecard,
and AAR changes, then rerun the commands above. Research, stale/live-copy,
README, mirrored-content, and external work remain separate E1.6 scope; this
record does not close the Bead or authorize Epic 2.
