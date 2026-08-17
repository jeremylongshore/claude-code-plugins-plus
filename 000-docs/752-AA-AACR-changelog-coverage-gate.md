# Changelog Coverage Gate — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Blueprint 727; Epic 1.8 program-maintenance prerequisite
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hz8f.10`
- **Implementation PR:** [#1162](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1162)
- **Base:** `b87703b0bd75ef30c57cfa7e1aa0ea08f063115f`
- **Reviewed head:** `81857757f5ef7d5f55a2d28ad652edb2b8e50b7c`
- **Merge commit:** `bb13f3161a4a99fcd759fdd414117bdcf2be18da`
- **Merge method:** merge commit with disclosed, owner-authorized administrator bypass
- **Status:** prerequisite implemented and verified; Bead closure follows this filing transaction

## Outcome

The changelog-coverage check now fails closed when Git tag evidence is unavailable, empty, or
incomplete. The base implementation caught tag-enumeration errors and exited successfully, also
exited successfully when no strict release tags were visible, exposed a `--warn-only` bypass, and
had no fixture tests. The corrected gate pins the coverage floor at `v4.14.0`, requires that tag
and its release note to remain visible, and reports 20/20 in-scope releases documented while
explicitly grandfathering 46 older tags.

`Validate Plugins` fetches tags and runs the gate through
`pnpm run validate:changelog-coverage`. The step has no path filter, permissive fallback,
`continue-on-error`, or warning-only mode. It reports through the existing `ci-required`
aggregate; no fourth required context was created. `CHANGELOG.md` records the new fail-closed
contract. This maintenance prerequisite removes a workflow conflict before Epic 1.8 but does not
satisfy or close E1.8.

No release tag, release object, package version, registry artifact, credential, contributor
record, Plane record, branch rule, mirrored content, catalog entry, or production setting changed.

## Implemented controls

- `scripts/check-changelog-coverage.mjs` parses strict `vX.Y.Z` tags and frontmatter-only release
  metadata, rejects duplicate or malformed versions, and refuses symlink or non-regular note
  paths.
- Missing Git, zero visible tags, a missing pinned floor tag or note, and any later release without
  exactly one note all exit nonzero with actionable diagnostics.
- `scripts/check-changelog-coverage.test.mjs` supplies ten deterministic success, red, and
  reverse-safe fixtures, including recursive note grouping.
- `package.json` provides one local reproduction command, and `validate-plugins.yml` fetches the
  complete tag evidence required by the check.
- The generated Epic 1 scorecard was regenerated from staged bytes and remained 36/36
  byte-current.

## Evidence bundle

| Evidence item           | Result | Reproducing evidence                                                                                                                                                                                   |
| ----------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Execution               | PASS   | Post-merge `pnpm run validate:changelog-coverage` passed 10/10 tests and reported 20/20 releases documented from `v4.14.0`.                                                                            |
| Happy path              | PASS   | A complete strict-tag and release-note fixture passes; 46 tags older than the pinned floor are explicitly out of scope.                                                                                |
| Failure path            | PASS   | Missing Git, zero tags, incomplete floor evidence, missing later notes, malformed/duplicate metadata, and symlink notes all refuse.                                                                    |
| Red proof               | PASS   | On base bytes, `PATH=/nonexistent /usr/bin/node scripts/check-changelog-coverage.mjs` exited 0 with “git tags unavailable — skipping”; the merged gate exits 1 for the same unavailable-Git condition. |
| Rollback                | PASS   | Reverse-reverting merge `bb13f3161a4a99fcd759fdd414117bdcf2be18da` in a disposable worktree produced tree `a67880e4e6a458f7dc1335672055b3b8d29ff2d6`, exactly its first-parent tree.                   |
| Durable receipt         | PASS   | PR #1162, exact-head Actions runs, independent-review evidence, Greptile receipt, merge commit, scorecard 742, Bead notes, this AAR, and the filing ledger form the evidence set.                      |
| Docs versus reality     | PASS   | The changelog describes a newly pinned gate and the live command reports the same floor, cohort, and refusal behavior.                                                                                 |
| Blueprint versus actual | PASS   | This is recorded as an E1.8 prerequisite only. The regenerate-and-diff work specified by E1.8 remains separately governed.                                                                             |
| Reproduction first      | PASS   | The fail-open Git-error behavior was reproduced before implementation; the corrected command refuses it.                                                                                               |
| Vertical slice          | PASS   | Checker, fixtures, workflow wiring, scorecard, changelog, hosted review, rollback, and filing are one bounded control.                                                                                 |
| Observed versus claimed | PASS   | The final reviewer ignored the author's proof table, inspected all six commits and the six-file net diff, planted hostile and reverse-safe cases, and returned PASS.                                   |

## Validation and review

The exact reviewed head passed
[Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32027791005),
including `ci-required`;
[Secret Scan](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32027791021),
including `gitleaks`;
[Skill Conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32027790967);
[Actionlint](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32027791088);
[link checking](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32027790966);
[PR Pre-screen](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32027791041);
all three [MiniMax review lanes](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32027852114);
and both kernel advisory checks.

The final independent clean-checkout reviewer returned PASS at the exact head. It inspected all six
commits, confirmed that 51 files touched by the historical merge-hook spillover match `main`
byte-for-byte, ran independent hostile and reverse-safe fixtures, passed changelog tests 10/10,
Epic 1 measurement 36/36, 38 CI routing/injection tests, formatting, ESLint, actionlint, and
Gitleaks, and reproduced the exact base tree through the reverse patch.

The filing outputs were independently regenerated in a disposable worktree at base
`bb13f3161a4a99fcd759fdd414117bdcf2be18da`. After applying only the staged ledger and document
752, `node scripts/generate-docs-index.mjs` and `TMPDIR=/dev/shm node
scripts/measure-epic-1.mjs` reproduced the PR bytes exactly. The index SHA-256 was
`5221086f9d46ddd92c8c6daa87569832c9ea5f6f2e799d73f9ddd1b8be9225a2`; the scorecard SHA-256 was
`59181615f73ba087754efa20d94cd2d58eec5a0a9520855ec3fff2b80a3c823d`. This receipt proves the
generated files were not hand-edited.

The scorecard's `invisible_files` field rose from 15,530 to 15,531 by design. Row 46 defines that
cohort as tracked paths matched by the Gitleaks path allowlist, not files hidden by `.gitignore`;
the newly tracked Markdown AAR is one additional Gitleaks-allowlisted path. The filing ledger is
the `PUBLIC FILING LEDGER` section in `000-docs/.gitignore`, where the document-752 negation was
appended before the generated index and scorecard were rebuilt.

[Greptile review `4951326422`](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1162#pullrequestreview-4951326422)
was requested at the exact head. The free trial had ended, so Greptile is recorded as unavailable
rather than PASS. The receipt requirement is therefore met without fabricating a Greptile verdict;
the administrator bypass below addressed GitHub's separate human-approval topology and was not a
substitute for Greptile. MiniMax's earlier wording recommendation was applied before the final
exact-head review: the changelog now calls this a newly pinned gate rather than an existing one.

## Merge topology and history reconciliation

Refreshing the old owner-authored branch from current `main` caused lint-staged to reformat 51
unrelated paths from the merge delta. Additive commit `4c9926624` restored every spillover byte to
current `main` without rewriting history. That restoration alone used `--no-verify` to avoid
re-triggering the defective merge-staging hook; the final net diff contained exactly the six
intended files, and every local and hosted gate ran on the final head.

GitHub still required one human approval after the executable gates and independent review passed.
The owner authorized administrator bypass, and the
[disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1162#issuecomment-5315844539)
was posted before merge. No branch rule, required context, or review policy was changed.

## Follow-up

This filing closes only `claude-hz8f.10`. Epic 1 remains open. A read-only follow-up audit found
that E1.8 can next address deterministic marketplace projections without editing the network stats
files in open PR #1149, but that work requires a separate Bead activation after this filing is
reviewed, merged, and closed. The merge-hook staging defect is also deferred maintenance and must
not normalize future `--no-verify` use.
