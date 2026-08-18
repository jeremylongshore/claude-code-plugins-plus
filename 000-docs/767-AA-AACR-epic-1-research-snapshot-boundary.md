# Research Snapshot Boundary — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Scope:** research landing page and six published research documents
- **Status:** implementation slice; merge fields are recorded in Beads/Dolt after review

## Outcome

The research index and all six research document pages now display a common
snapshot boundary: captured 2026-03-04 from repository commit
`256db0b3eabc0669ffe75bc16f19053820c3e91c`. The boundary explicitly states
that the figures are historical evidence, not live corpus totals. Existing
research values remain unchanged and stay in the `research-snapshot` deferred
population rather than being relabeled as current marketplace counts.
The index separately labels its original `1,500+` figure as a historical
analysis claim; it does not present that value as the `1,372`-skill evidence
corpus documented by the source commit.

## Evidence

| Gate                    | Result                                                                     |
| ----------------------- | -------------------------------------------------------------------------- |
| Published-count checker | PASS — existing research paths remain explicit deferrals                   |
| Snapshot boundary       | PASS — shared template plus research index                                 |
| Numeric values          | Unchanged; only boundary wording and presentation added                    |
| Corpus distinction      | PASS — original `1,500+` claim is not conflated with source `1,372` corpus |
| Mirrored content        | No `.source.json` or mirrored skill content changed                        |
| External systems        | No registry, credential, contributor, Plane, or production mutation        |

## Reproduction

```bash
node scripts/check-published-count-cohorts.mjs --json
# Observed: ALLOW; cohorts=5, enforced=6, deferred=91, discovered=20.
pnpm --dir marketplace run build
```

The checker output was `ALLOW` with no findings; the four population counts
above are the result observed on the reviewed source commit.

## Rollback and boundaries

Revert the focused research-template, research-index, changelog, index,
scorecard, and AAR changes, then rerun the commands above. The two live-copy /
quality-rule pages, README, mirrored content, and external work remain separate
E1.6 scope; this record does not close the Bead or authorize Epic 2.
