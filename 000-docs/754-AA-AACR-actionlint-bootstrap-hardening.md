<!-- doc-class: record -->

# Actionlint Bootstrap Hardening — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Operational blocker discovered during blueprint 727 Epic 1 bead 1.8
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-8085`
- **Implementation PR:** [#1230](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1230)
- **Base:** `e39ed6dcae0e6eead8a018d5b796eae6caba324c`
- **Reviewed head:** `50302490f5b7993e75beea66dd97c421a5e04a8b`
- **Merge commit:** `c0824bbe1e18d23c7e308f13e4c2a2e3e41a0d44`
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** implementation merged; Bead closure follows this filing transaction and durable-memory
  capture

## Outcome

PR #1229 exposed an operational defect rather than a lint failure: three attempts of Actionlint run
`32043702358` received HTTP 429 while fetching the pinned installer from
`raw.githubusercontent.com`, so the job never executed Actionlint. PR #1230 replaced the remote
installer-script pipe with the official actionlint v1.7.4 Linux amd64 release archive. The workflow
now fails on HTTP errors, retries at most three times, verifies the hardcoded upstream SHA-256 before
extracting only the `actionlint` member with ownership preservation disabled, and then runs the
unchanged blocking lint command.

The checksum is sourced from the primary v1.7.4 release file
`actionlint_1.7.4_checksums.txt` and is recorded beside the pin. The final exact-head hosted job
downloaded, verified, extracted, and executed actionlint 1.7.4 successfully. No trigger, required
context, branch rule, credential, package, registry, contributor, Plane, or production setting
changed.

## Evidence bundle

| Evidence item | Result   | Reproducing evidence                                                                                                                                                                                       |
| ------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution     | PASS     | Exact-head [Actionlint run](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32044581315) completed successfully.                                                           |
| Happy path    | PASS     | The official archive digest matched `fc0a6886bbb9a23a39eeec4b176193cadb54ddbe77cdbb19b637933919545395`; extracted `actionlint -version` reported 1.7.4 for Linux/amd64; repository workflow lint exited 0. |
| Failure path  | PASS     | Curl uses `--fail` under `set -euo pipefail`; checksum and extraction failures abort before tool execution.                                                                                                |
| Red proof     | PASS     | Substituting an all-zero expected digest made `sha256sum --check --strict` exit 1 with a mismatch.                                                                                                         |
| Scope         | PASS     | The [implementation file diff](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1230/files) contains only `.github/workflows/actionlint.yml` and `CHANGELOG.md`.                    |
| Rollback      | PASS     | The independent reviewer applied the complete reverse patch with `git apply --reverse --check`; operational rollback is reverting merge `c0824bbe1`.                                                       |
| Bypass record | RECORDED | The owner-authorized [administrator-bypass disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1230#issuecomment-5317591712) is an exception receipt, not a passing check. |

## Independent reproduction receipt

At `2026-08-17T17:47:35Z`, an independent rerun against reviewed head `50302490f` produced these
terminal receipts:

- `sha256sum actionlint_1.7.4_linux_amd64.tar.gz` returned
  `fc0a6886bbb9a23a39eeec4b176193cadb54ddbe77cdbb19b637933919545395`.
- `actionlint -version` reported 1.7.4 for Linux/amd64, and linting every workflow exited 0.
- Replacing the expected digest with 64 zeroes printed `FAILED` and exited 1.
- `git diff --name-status e39ed6d...50302490f` listed only `.github/workflows/actionlint.yml`
  and `CHANGELOG.md`; `git apply --reverse --check` exited 0 on the complete binary patch.
- The checks API timestamps show 33 successful pre-merge checks plus the designed TruffleHog skip.
  The two Plane projection jobs started only after the `2026-08-17T16:20:00Z` merge.

## Validation and review

Before merge, 33 checks succeeded and the designed `trufflehog (verified)` lane skipped. A direct
checks-API enumeration by exact head confirms that the only two later jobs were post-merge Plane
projections; they are not counted as pre-merge evidence. The successful checks included
[Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32044581266),
[Secret Scan](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32044581270),
[Skill Conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32044581274),
[Actionlint](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32044581315),
[link checking](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32044581265),
[PR Pre-screen](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32044581259),
and all three [MiniMax lanes](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32044581291).

The independent clean-checkout reviewer returned **PASS** for exact range
`e39ed6dcae0e6eead8a018d5b796eae6caba324c...50302490f5b7993e75beea66dd97c421a5e04a8b`.
It independently matched the archive to the primary checksum file, ran the exact binary, reproduced
the wrong-digest refusal, inspected retry and extraction safety, confirmed unchanged gate topology,
and found no unrelated churn or fail-open path.

[Greptile was requested on the exact head](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1230#issuecomment-5317516012)
and replied that its trial had ended. That receipt is recorded as unavailable, never as PASS.
GitHub still required a human approval because the documented independent second-identity topology
is unavailable. The owner-authorized administrator bypass was disclosed before merge; no branch
rule or required context was changed.

## Filing verification

Document 754 was staged before running `node scripts/generate-docs-index.mjs` and
`TMPDIR=/dev/shm node scripts/measure-epic-1.mjs`; those generators produced the committed index and
scorecard bytes. Their check modes then reported 194 tracked documents and a byte-current scorecard,
and `pnpm run measure:e1:check` passed all 37 tests. Neither generated file was hand-edited. The
`invisible_files` metric counts tracked paths matching `.gitleaks.toml` `[allowlist].paths`; document
754 matches the explicit `^000-docs/.*\.md$` documentation pattern, so adding it increases both
`tracked_files` and `invisible_files` by one.

## Lessons and follow-up

An immutable tag does not make an executable installer transport reliable, and `curl | bash`
couples availability and execution before local verification. Prefer direct, version-pinned release
artifacts with reviewed digests and fail-closed extraction. The E1.8 full-catalog PR must rebase onto
this merge and rerun every exact-head gate; this operational fix does not satisfy or close E1.8.
