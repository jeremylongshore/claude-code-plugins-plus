# Epic 1 Measurement Harness — After-Action Review

- **Date:** 2026-08-16
- **Authority:** Blueprint 727, Epic 1 bead 1.0
- **Bead:** `claude-hz8f.4`
- **Implementation PR:** [#1208](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1208)
- **Reviewed head:** `e8894a4ef8054dc0807b6c9e2d240c827e45722d`
- **Merge commit:** `fae9b3e787f7735df38880b227da81af1b766872`
- **Status:** Implementation merged; [independent reviewer PASS recorded on PR #1208](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1208#issuecomment-5306812695); Bead closure follows this filing transaction

## Outcome

Epic 1 measurements now come from one deterministic command over an immutable Git-index snapshot.
`pnpm run measure:e1` emits a stable, committed
[62-row scorecard plus the graded-artifact cohort](742-RA-DATA-epic-1-scorecard.json);
`pnpm run measure:e1:check` fails when executable inputs or the artifact drift. Facts without
committed evidence remain null with explicit `not_reproducible` or `partial` reason codes.

The [reviewed-head scorecard](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/blob/e8894a4ef8054dc0807b6c9e2d240c827e45722d/000-docs/742-RA-DATA-epic-1-scorecard.json)
keeps unlike populations separate. At that head it measured 23,009 tracked paths, 3,179 plugin
skills, and 347 plugin-agent files (row 1). Row 4's `skill_rows` and the
`graded_artifact_cohort` report 3,679 graded rows, 962 failing A/B artifacts, 2,155 A/B errors, and
7,433 total row errors. Row 4's separate `marketplace_terminal` cohort reports 7,687 findings over
4,405 skill, command, and agent files.

## Before and after

| Contract                                        | Before |          After |
| ----------------------------------------------- | -----: | -------------: |
| Blueprint scorecard rows emitted by one command |      0 |             62 |
| Committed deterministic scorecards              |      0 |              1 |
| Focused regression cases                        |      0 |             29 |
| CI jobs enforcing scorecard drift               |      0 | 1 existing job |
| Required GitHub contexts                        |      3 |              3 |

The implementation also dynamically measures generated-data producers, README count writers,
publisher provenance boundaries, `ci-required.needs`, and the live STANDARDS authority graph. It
does not collapse the five historical skill counts into one headline number.

## Verification and red proofs

- Exact-head and post-merge `pnpm run measure:e1:check` exited zero and matched the
  [reviewed-head document 742](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/blob/e8894a4ef8054dc0807b6c9e2d240c827e45722d/000-docs/742-RA-DATA-epic-1-scorecard.json)
  byte-for-byte.
- This filing added one tracked document; current `origin/main` concurrently added one unrelated
  blog path. Harness regeneration changed only the expected live-tree values: tracked paths 23,009 →
  23,011 (one per change), indexed documents 182 → 183, and ignore-policy invisible files 15,499 →
  15,500. The remaining scorecard values stayed byte-identical.
- The focused measurement and authority suite passed 29/29 in the implementation checkout and an
  independent detached checkout.
- Hostile fixtures refuse ignored or unstaged contamination, changed imported measurement modules,
  malformed and contradictory validator output, path traversal, duplicate evidence, sparse,
  cyclic, non-finite, or runtime-stamped JSON, Type-1 bytes mislabeled as TTF, false README writers,
  read-only consumers presented as drift gates, malformed CI dependencies, and unlinked authority
  claims.
- Formatting, ESLint, typecheck, Actionlint, documentation index/authority gates, Validate Plugins,
  PR Pre-screen, link check, `ci-required`, `gitleaks`, and `skill-conform` passed at the reviewed
  head. Repository-wide `pnpm test` retains the unrelated pre-existing CLI/Vite loader failure;
  GitHub's CLI smoke and repository test matrix passed.

The first candidate head `5b90e37f55bc4cb3d9e98aa43e870ac2e47811a8` was returned for
correction. It mixed a working-tree mirror into clean counts, emitted only part of the scorecard,
used invalid per-row commands, and had fail-open registries and terminal parsing. Those defects were
corrected without rewriting history. The final independent reviewer inspected all ten changed
files, reran the evidence, planted its own input-drift cases, and returned
[PASS](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1208#issuecomment-5306812695).

## Bot review and merge topology

The [exact-head MiniMax review](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1208#issuecomment-5306380614)
and [adversarial lane](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1208#issuecomment-5306374033)
passed. A later manual rerun incorrectly reported the 130,996-byte
scorecard as absent. GitHub's PR-files response omitted the file's patch, and the action drops files
without patches before applying its 100,000-character cap. Git's blob, GitHub's file inventory, and
the [exact-head evidence record](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1208#issuecomment-5306753677)
disproved the finding. [Greptile was manually triggered at the reviewed SHA](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1208#pullrequestreview-4945869399),
but its only response was an expired-trial notice, so it supplied no findings and is not review
evidence.

GitHub still required a human approval after executable and independent review passed. The platform
owner authorized an administrator bypass for that review-topology gap. The
[one-time bypass was disclosed on PR #1208](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1208#issuecomment-5306812695);
it modified no standing branch rule, required context, workflow gate, or review rule.

## Scope and rollback

The implementation changed the measurement scripts and tests, one generated scorecard, package
commands, one step in the existing documentation-governance job, filing ledger/index entries, and
`CHANGELOG.md`. It changed no mirror-owned content, catalog, package release, credential, registry,
contributor record, Plane projection, branch protection, billing, or production state.

Rollback must reverse this AAR filing first, then revert merge commit
`fae9b3e787f7735df38880b227da81af1b766872`. Rerun the documentation index and confirm document
742, its ledger entry, package commands, workflow step, harness, tests, and changelog entry are gone.
No corpus or external-system rollback is required.

## Lesson and next gate

A number is meaningful only with its cohort, exact-tree source, and executable reproduction path.
Epic 1 remains open. No later bead is activated by this AAR; the next slice must be re-ranked against
live open-PR overlap before Beads/Dolt creates its single child record.
