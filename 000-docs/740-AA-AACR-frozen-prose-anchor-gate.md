# Frozen Prose-Anchor Gate — After-Action Review

- **Date:** 2026-08-15
- **Authority:** Blueprint 727, Epic 2 bead 2.9
- **Bead:** `claude-hedb.4`
- **Implementation PR:** [#1204](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1204)
- **Reviewed head:** `fcdf54ef7a1e7ad6fb935efd1c0438e5f2841ee7`
- **Merge commit:** `40cefff5c114e36bcc685b625b5c469705c9f861`
- **Status:** Implementation complete; Bead closure follows successful filing of this AAR

## Outcome

The existing `doc-governance` job now runs a deterministic regression suite for the frozen 6767-h
section namespace. The suite pins the ordered 21-anchor identity contract—section ID, title, and
heading level—without treating diagnostic line numbers, parser timestamps, or the whole document
hash as anchor identity. It exercises valid and intentionally invalid citations and refuses missing
or malformed document, schema, and index inputs.

## Before and after

| Measure                                   | Before | After |
| ----------------------------------------- | -----: | ----: |
| Prose-anchor unittest cases               |      0 |     5 |
| Frozen anchors asserted                   |      0 |    21 |
| CI jobs invoking the prose-anchor checker |      0 |     1 |
| Required GitHub status contexts           |      3 |     3 |
| Changed `6767-*` files                    |      0 |     0 |

The implementation added one step to the existing `doc-governance` job. It added no workflow job,
required context, path filter, permissive fallback, `continue-on-error`, or timestamped output.

## Verification evidence

- `python3 -m unittest tests.test_prose_anchors -v` passed 5/5 before commit, at the reviewed head,
  in an independent detached checkout, and after merge.
- Red proofs renamed cited anchors `3.1` and `4.3`; the checker refused them with two and one broken
  citations respectively. The intentionally invalid `99.99.99` fixture also exited non-zero.
- Missing documents and indexes plus malformed schema and index JSON all failed closed.
- The independent reviewer matched all 21 ordered, unique anchors; verified every `6767-*` file was
  unchanged; reran the complete documentation-governance sequence; and returned PASS.
- Exact-head GitHub checks passed: `ci-required`, `gitleaks`, `skill-conform`, Validate Plugins,
  Actionlint, PR Pre-screen, both MiniMax reviews, and link-check.
- The first PR-title run correctly rejected the unregistered `docs` scope. The title changed to the
  registered `docs-governance` scope, and a fresh pull-request event passed the title gate without a
  code change or weakened rule.
- Local `pnpm run verify`, formatting, lint, typecheck, Actionlint, documentation governance, and a
  1,670-commit Gitleaks scan passed. Broad local `pnpm test` retained an unrelated CLI/Vitest loader
  failure on the unchanged base; the repository CI suites and CLI smoke tests passed at exact head.

## Review and merge topology

The platform owner authorized an administrator bypass only after exact-head CI, bot review, link
checking, and independent clean-checkout review passed. GitHub still required one human approval.
The bypass was disclosed on PR #1204 and addressed only that review-topology gap; no branch rule,
required context, workflow gate, or reviewer policy changed.

## Scope and rollback

The implementation changed one workflow step, one unittest module, one fixture manifest, and
`CHANGELOG.md`. It did not alter frozen prose, canonical authority, mirrored content, provenance,
catalogs, packages, credentials, registries, contributors, Plane, branch protection, or production.

Rollback must remove this filing transaction before the implementation because filing regenerates
`000-INDEX.md`. First revert the eventual AAR merge commit, then run
`git revert -m 1 40cefff5c114e36bcc685b625b5c469705c9f861`. Confirm document 740 and its
ledger/index entries are absent, then verify the workflow step, tests, fixture manifest, and
changelog entry are removed while every `6767-*` file remains unchanged.

## Lessons and next gate

Frozen prose can remain byte-stable while its externally consumed anchor namespace is executable.
The stable contract is the ordered ID/title/level map, not line position or a timestamped parser
artifact. E2.6 remains unactivated: its external-source figure depends on E1.12, and its agent count
must distinguish the 353-file validator cohort from the 347-file plugin-agent surface.
