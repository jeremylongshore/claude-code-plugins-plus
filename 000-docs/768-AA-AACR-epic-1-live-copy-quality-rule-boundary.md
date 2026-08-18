# Live Copy and Quality-Rule Boundary — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Scope:** `marketplace/src/pages/docs/index.astro` and `marketplace/src/pages/grading.astro`
- **Status:** implementation slice; merge fields are recorded in Beads/Dolt after review

## Outcome

The documentation CTA retains its existing `418 plugins` and `2,834 skills`
wording, but now marks both values as `historical-copy` and explicitly says
they are not live totals. The grading page marks its numeric bands and
thresholds as `quality-rule` policy, not a marketplace corpus count. No
numeric values were changed.

The registry keeps both paths in the `live-copy-or-quality-rule` path-level
deferred population. This is deliberate: the docs values need a separate
source/copy disposition, while grading thresholds are policy facts rather than
canonical corpus measurements. The checker therefore does not substitute
either surface into the five canonical cohorts.

## Evidence

| Gate                    | Result                                                                                                   |
| ----------------------- | -------------------------------------------------------------------------------------------------------- |
| Published-count checker | PASS — `ALLOW`; canonical cohorts remain unchanged and both paths remain explicitly deferred             |
| Docs CTA                | PASS — both retained values carry `data-count-provenance="historical-copy"` and a not-live-total warning |
| Grading page            | PASS — policy values carry `data-count-provenance="quality-rule"`                                        |
| Numeric values          | PASS — `418`, `2,834`, and grading thresholds unchanged                                                  |
| Mirrored content        | No `.source.json` or mirrored skill content changed                                                      |
| External systems        | No registry, credential, contributor, Plane, or production mutation                                      |

## Reproduction

```bash
node scripts/check-published-count-cohorts.mjs --json
pnpm --dir marketplace run build
```

The checker result before filing this record was `ALLOW` with
`cohorts=5`, `enforced=6`, `deferred=91`, `discovered=20`, and no findings.

## Rollback and boundaries

Revert the focused page, registry, blueprint, changelog, index, and AAR
changes, then rerun the commands above. Replacing the legacy docs numbers with
current canonical totals, changing grading policy, editing README, touching
mirrored content, or starting another epic remains out of scope.
