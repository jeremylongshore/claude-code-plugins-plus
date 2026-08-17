# Blog Markdown and Scorecard Correction — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Operational blockers discovered during blueprint 727 Epic 1 bead 1.8
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-igjk`
- **Implementation PR:** [#1232](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1232)
- **Base:** `2979bd5b5b8700ddf7f60b355902575548ba43f5`
- **Reviewed head:** `6d24466997d2ce03fe08bf55377407ca8cc46e16`
- **Merge commit:** `c0f87ad5a65a96118cb1e75d03746d089bd19231`
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** implementation merged; Bead closure follows this filing transaction and durable-memory
  capture

## Outcome

Current main introduced a new marketplace blog post whose numbered list lacked the blank line required
by MD032. The repository-wide blocking Markdownlint job therefore failed every pull request, even
when the pull request did not modify the article. PR #1232 added the single missing blank line without
changing article wording or lint policy and recorded the correction in `CHANGELOG.md`.

The same originating main merge had added one tracked file without regenerating the governed Epic 1
scorecard. Hosted `doc-governance` correctly rejected the stale `tracked_files` value. The canonical
generator changed only that value, from 23,050 to 23,051 in rows 1 and 46. The final implementation
range therefore contains exactly three modified files: the article, `CHANGELOG.md`, and the generated
scorecard. The implementation diff contains no lint exclusion, baseline lowering, mirror content,
credential, registry, contributor, Plane-authority, branch-policy, package, or production file.

## Evidence bundle

| Evidence item | Result   | Reproducing evidence                                                                                                                                                                                                                                                 |
| ------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Failure path  | PASS     | [Validate Plugins run 32045714543](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32045714543), a PR #1231 synthetic merge incorporating exact base `2979bd5b`, reported MD032 at article line 36 and rejected the stale scorecard. |
| Happy path    | PASS     | Exact-head [Validate Plugins run 32047053268](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32047053268) passed Markdownlint, document governance, and the aggregate `ci-required` context.                                        |
| Semantic fix  | PASS     | `git diff 2979bd5b...6d24466 -- marketplace/src/content/blog-posts/the-failure-that-knew-its-own-name.md` shows one blank-line insertion before the list and no wording change.                                                                                      |
| Scorecard     | PASS     | `pnpm run measure:e1:check` passed 37/37 tests and reported byte-current generated output; rows 1 and 46 contain `tracked_files: 23051`.                                                                                                                             |
| Scope         | PASS     | `git diff --name-status 2979bd5b...6d24466` lists only the article, `CHANGELOG.md`, and scorecard 742.                                                                                                                                                               |
| Rollback      | PASS     | Revert squash merge `c0f87ad5a`; the original MD032 and scorecard failures are the expected rollback signals.                                                                                                                                                        |
| Bypass record | RECORDED | The owner-authorized [administrator-bypass disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1232#issuecomment-5317958235) is an exception receipt, not a passing review.                                                          |

## Validation and review

The red run used markdownlint-cli2 0.22.1 over 10,616 files and emitted exactly the load-bearing
diagnostic: `MD032/blanks-around-lists` at article line 36. On reviewed head `6d244669`, the full
Validate Plugins workflow passed Markdownlint, document governance, and `ci-required`. The required
`gitleaks` and `skill-conform` contexts also passed. The exact-head checks API records 36 successful
pre-merge checks plus the designed `trufflehog (verified)` skip. One CodeQL SARIF upload logged
GitHub server unavailability and was retried successfully; it was an infrastructure retry, not a
code or policy exception. Post-merge Plane projection jobs are excluded from the pre-merge count.

MiniMax's exact-head standard review found no defect. Its adversarial review returned `Not lgtm` and
identified four evidence gaps: the PR body omitted the scorecard from its stated scope, did not
explain the 23,050→23,051 delta, did not link its red/green claims, and did not display the post-list
boundary. The generator and file evidence resolve the numeric and list-boundary questions. The
incomplete PR-body scope and traceability remain historical record defects; this AAR supplies the
missing exact range, generator, rows, and hosted links rather than rewriting the old review. The
committed scorecard bytes match the canonical generator; that proves byte currency, not the author's
editing method.

An independent clean-checkout reviewer returned **PASS** for exact range
`2979bd5b5b8700ddf7f60b355902575548ba43f5...6d24466997d2ce03fe08bf55377407ca8cc46e16`.
The reviewer inspected the three-file diff, reproduced the Markdownlint result and one-blank-line
semantics, verified the generated scorecard and 37/37 measurement tests, and found no unrelated or
external mutation. This receipt is recorded in the administrator-bypass disclosure; it was not a
GitHub approval.

[Greptile was requested on the exact head](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1232#issuecomment-5317841597)
and returned only a trial-ended notice. That historical receipt is recorded as unavailable, never as
PASS. GitHub still required a human approval because the independent second-identity topology was
unavailable. The owner-authorized administrator bypass disclosure states that no branch rule or
required context changed; the implementation patch itself contains no workflow or policy file.

## Filing verification

Document 755 was staged before running `node scripts/generate-docs-index.mjs` and
`TMPDIR=/dev/shm node scripts/measure-epic-1.mjs`. Those generators produced the committed index and
scorecard bytes. Their check modes then reported 195 tracked documents and a byte-current scorecard,
and `pnpm run measure:e1:check` passed all 37 tests. The committed generated bytes match both
generators. Because document 755 matches the explicit `^000-docs/.*\.md$` Gitleaks path allowlist, this filing increases
both the tracked-file and Gitleaks-invisible-file measurements by one; it does not change the
implementation PR's historical 23,051-file receipt.

## Lessons and follow-up

Repository-wide content gates make newly added prose part of every subsequent pull request's health.
New content must pass the same blocking Markdownlint command before merge, and every tracked-file
addition must regenerate scorecard 742 in the same transaction. The Slack journal boundary-test
timeout observed later is tracked separately as `claude-2uge`; it is not attributed to this fix.
PR #1229 must rebase onto the current main and rerun every exact-head gate. This operational repair
does not satisfy or close E1.8.
