<!-- doc-class: record -->

# Generated Documentation Estate Index — After-Action Review

- **Date:** 2026-08-15
- **Authority:** Blueprint 727, Epic 2 bead 2.4
- **Bead:** `claude-hedb.3`
- **Implementation PR:** [#1202](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1202)
- **Reviewed head:** `b42244846202c73eb6a9f3b122d423e7182aa683`
- **Merge commit:** `88fcf6a8f2bd9f1ef7de1b8e06b34c877e724dac`
- **Status:** Implementation complete; Bead closure follows successful filing of this AAR

## Outcome

`000-docs/000-INDEX.md` is now generated deterministically from the Git-tracked documentation estate.
The existing `doc-governance` job runs a non-writing byte comparison and rejects count, membership,
ordering, link-target, or reference-tail drift. The generator excludes only its own index and
`000-docs/.gitignore`; newly filed documents enter the index only after they are staged.

## Before and after

| Measure                         | Before | After |
| ------------------------------- | -----: | ----: |
| Tracked paths under `000-docs/` |    180 |   180 |
| Indexable tracked documents     |    178 |   178 |
| Committed index links           |    178 |   178 |
| Missing or extra index targets  |      0 |     0 |
| Deterministic generator tests   |      0 |     7 |
| Required GitHub status contexts |      3 |     3 |

The blueprint's earlier 166/168 figures describe a historical population and were not substituted
for the current Git-derived cohort. Fifteen archived paths retain their relative targets while the
global list sorts by displayed basename. No duplicate basenames were present.

## Verification evidence

- `node --test scripts/generate-docs-index.test.mjs` passed 7/7 tests.
- `node scripts/generate-docs-index.mjs --check` reported 178 tracked documents before and after
  merge and matched the committed index byte for byte.
- Red fixtures proved that wrong counts, missing rows, reordered rows, mutated reference text,
  unsafe or duplicate paths, and Git inventory failure are refused without repairing a stale index.
- An independent clean-checkout reviewer planted separate staged-file and drift cases, rejected
  12 unsafe paths, verified C and C.UTF-8 output identity, and returned PASS at the reviewed head.
- Documentation governance passed with 21 ignore-policy assertions, 20 baselined citations and zero
  new citations, one unchanged internal-link baseline, two authority claimants, ten canonical links,
  and no tracked generated-artifact projections.
- Every applicable exact-head GitHub check passed, including `ci-required`, `gitleaks`,
  `skill-conform`, the Validate Plugins fan-out, Actionlint, prescreen, both MiniMax reviews, and
  link-check. Two unrelated jobs were intentionally skipped.

## Review and merge topology

The platform owner authorized an administrator bypass only after all exact-head executable, bot,
link, and independent-review gates passed. GitHub still required one human approval. The bypass
addressed only that temporary review-topology gap and was disclosed on PR #1202; no branch rule,
required context, path filter, workflow gate, or reviewer policy changed.

## Known filing-layout variance

`/doc-filing v4.4` requires folder-grouped index sections when lifecycle folders exist. The estate
contains 15 grandfathered paths under `_archive/ms-oldv/`, while the pre-existing index contract is a
single global chronological list with relative archive targets. E2.4 preserved that published layout
to avoid an unratified navigation rewrite; it did not establish the global list as compliant with the
folder-grouping rule. A future owner-authorized documentation-governance slice must either migrate the
index to folder-grouped output with compatibility evidence or ratify a canonical exception. Until
then, this is an explicit historical variance, not a claim of full filing-layout compliance.

## Scope and rollback

The implementation changed one generator, its fixture tests, the generated index header, one step
inside the existing `doc-governance` job, and `CHANGELOG.md`. It did not alter document bodies,
frozen history, canonical authority, mirrored content, catalogs, packages, credentials, registries,
contributors, Plane, branch protection, or production.

Rollback must remove the filing transaction before the implementation because both merge commits
modify the generated index. First revert the eventual PR #1203 merge commit. Then run
`git revert -m 1 88fcf6a8f2bd9f1ef7de1b8e06b34c877e724dac`. Confirm document 739 and its
ledger/index entries are absent, the generator, tests, workflow gate, marker, and changelog entry are
removed, and the prior 178-row manual index is restored. Reversing that order causes an expected
`000-INDEX.md` conflict and is not the supported rollback path.

## Lessons and next gate

The tracked Git index, not the ambient filesystem, is the stable documentation inventory boundary.
Generation must fail closed and share the same transaction as filing: ledger the document, stage it,
then regenerate. E2.5 is not yet activated; its class semantics, frontmatter interaction, frozen-file
bootstrap, and binary Markdown anomalies require reconciliation before a safe mass-labeling slice.
