<!-- doc-class: record -->

# Social Image Count Cohort — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Scope:** the deferred `scripts/generate-og-image.mjs` social-image surface only
- **Status:** implementation slice; merge fields are recorded in Beads/Dolt after review

## Outcome

The generated social card now labels its embedded totals as the
`marketplace-visible` cohort and visibly includes the canonical source plus the
reproduction command. Its metadata sidecar records the same contract. Generation
fails closed when the unified-search source is unreadable or its totals are not
non-negative integers; `--check` refuses a missing or contradictory cohort
contract. No plugin, skill, mirror, `.source.json`, registry, credential,
contributor, Plane, branch-rule, release, or production state changed.

## Evidence

| Gate                         | Result                                                              |
| ---------------------------- | ------------------------------------------------------------------- |
| Social-card contract tests   | PASS — 4/4, including two red proofs                                |
| Published-count registry     | PASS — `ALLOW cohorts=5 enforced=6 deferred=49 discovered=51`       |
| Social-card generation       | PASS — 1,200×630 PNG; 3,068 marketplace-visible skills; 467 plugins |
| Social-card structural check | PASS — valid PNG, dimensions, metadata cohort/source/command        |
| Visual inspection            | PASS — cohort, source, and resolver command are legible             |

## Rollback

Revert the focused generator, sidecar, registry, test, index, scorecard, and
changelog changes, then rerun the contract test, published-count checker, and
`node scripts/generate-og-image.mjs --check`. The generated PNG is reproducible
from the canonical index and is not hand-edited.

## Boundaries and follow-up

Entity-local cards, vendor-pack pages, learning aggregates, research snapshots,
active docs, and README counts remain separately deferred E1.6 surfaces. This
slice does not claim E1.6 completion.
