# Epic 1 Count-Cohort Closure — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Status:** closure candidate; actual merge and Beads/Dolt closure evidence are recorded after review

## Outcome

E1.6 now governs every discovered public numeric skill-count surface through
`scripts/published-count-cohorts.json` and the fail-closed checker. The five
canonical cohorts remain distinct: `marketplace-visible`, `graded`,
`first-party`, `curated-mirror`, and `curriculum`. Local or historical values
are explicitly classified rather than promoted into those corpus totals.

The completed slices covered query-local and entity-local values, Cowork
package-local values, vendor-pack and learning-hub values, the dated research
snapshot, and the docs historical-copy/quality-rule pages. The retained
numeric values were not rewritten to manufacture current-looking totals.

## Final inventory and evidence

| Gate                 | Result                                                                                                                                          |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Registry checker     | `ALLOW`; 5 cohorts, 6 enforced surfaces, 91 deferred claims, 20 discovered sources, no findings                                                 |
| Canonical resolver   | Five named cohorts resolve from `scripts/corpus-resolver.mjs`                                                                                   |
| Deferred populations | Six explicit classes: packaged/bundle-local, entity-local, vendor-pack-local, learning-hub-aggregate, live-copy/quality-rule, research-snapshot |
| Fixture coverage     | Published-count suite 35/35; Epic 1 measurement suite 37/37                                                                                     |
| Scorecard            | `TMPDIR=/dev/shm pnpm run measure:e1:check` → `epic-1-measurement: OK`                                                                          |
| Rendered site        | `pnpm --dir marketplace run build` → 3,871 pages built                                                                                          |
| Generated docs       | `node scripts/generate-docs-index.mjs --check` passed                                                                                           |
| Numeric values       | No cohort baseline was changed by the count-contract slices                                                                                     |
| Mirrored content     | No `.source.json` ancestor or mirrored skill content changed                                                                                    |
| External systems     | No registry, credential, contributor, Plane, branch-rule, or production mutation                                                                |

## Merge record

The final implementation slice, PR #1251, merged as squash commit
`7f8831daf9af58307bfb69f3f1174c18ecb14770` from independently reviewed head
`f4212539d4e2d8744ef0722950b3fe8381d20c54`. The independent clean-checkout
review returned PASS. Required checks and the link-check and Playwright gates
passed. GitHub still reported `REVIEW_REQUIRED`; an administrator bypass was
used and disclosed, with no self-approval.

## Closure boundary and rollback

This record closes the count-cohort classification work only. It does not
close the Epic 1 parent or activate Epic 2/3. README landing-contract work,
future canonical-cohort changes, and unrelated external or mirrored-content
work remain governed by their own beads. Roll back by reverting the focused
count-contract merges and rerunning the checker, measurement check, docs-index
check, and marketplace build.
