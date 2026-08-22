<!-- doc-class: record -->

# Epic 2 Cross-System Authority Boundary — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Blueprint 727, Epic 2 bead 2.11
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hedb.6`
- **Implementation PR:** [#1222](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1222)
- **Base:** `4066493809657eb6f3d08b10e9b3bd37d2253696`
- **Reviewed head:** `d8c50cfc4e2d1b9fa0a6082b14ec5ec02fcd6861`
- **Merge commit:** `ebe6b2b12b12df50fb10a446530554a1dd714003`
- **Merge method:** merge commit with disclosed, owner-authorized administrator bypass
- **Status:** E2.11 implementation verified; Bead closure follows this filing transaction

## Outcome

Blueprint 727 section 4 remains the sole governing cross-system authority record. This slice did
not create a competing architecture document. It corrected four live first-party claims that
violated the existing boundary: three in the `validate-skillmd` skill and one in the Plane proof
guide instructed JRig to write directly into `freshie/inventory.sqlite`.

JRig now receives only an ephemeral `/dev/shm` scratch database through
`scripts/run-jrig-eval.sh`. The first-party recorder remains the writer for Freshie/Dolt
`forge_proofs`. A deterministic repository gate rejects active instructions that route JRig into
the Freshie inventory while classifying mirrors exclusively through applicable `.source.json`
ancestry. The merged scan checks 10,729 active first-party surfaces and skips 1,167
provenance-marked mirror surfaces. The base produced four findings; merged `main` produces zero.

The gate is part of the existing `doc-governance` job and therefore reports through
`ci-required`; no fourth required status context was added. `CHANGELOG.md` records the behavioral
boundary. The generated Epic 1 scorecard was regenerated and remains 36/36 byte-current.

No mirrored content, `.source.json`, package version, catalog release, kernel authority, pin,
database data, registry artifact, credential, contributor record, Plane record, branch rule, or
production setting changed. The ready-for-review auto-bumper briefly added an out-of-scope commit;
a normal additive revert removed its complete net effect without rewriting history.

## Implemented controls

- `scripts/check-jrig-db-boundary.mjs` inventories tracked active surfaces, resolves real
  provenance ancestry, and fails closed on malformed or unreadable evidence.
- Shell, parsed YAML, and operator-prose analysis normalize static aliases, assignment state,
  parameter expansion, control flow, command substitution, equivalent paths, and nested package
  ancestry without maintaining a name-based mirror list.
- The checker preserves reverse-safe shell semantics, including quoted or escaped literal dollars,
  literal glob characters, nonexecuting branches, and scratch-database commands.
- `scripts/check-jrig-db-boundary.test.mjs` provides durable red and reverse-safe fixtures;
  independent reviewers repeatedly planted additional cases until the final matrix passed.
- The target skill and Plane proof guide use the governed wrapper/recorder boundary rather than a
  direct JRig write.

## Evidence bundle

| Evidence item           | Result | Reproducing evidence                                                                                                                                                                                            |
| ----------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution               | PASS   | Post-merge `pnpm run validate:jrig-db-boundary` passed 8/8 and reported 10,729 first-party surfaces plus 1,167 provenance mirrors skipped. Recorder tests passed 6/6.                                           |
| Happy path              | PASS   | Governed wrapper guidance uses an ephemeral JRig database and the recorder-owned inventory write. Scratch paths and nonpersisting eval remain accepted.                                                         |
| Failure path            | PASS   | Fixtures refuse direct, aliased, multiline, shell/YAML-variable, command-substitution, glob-equivalent, prose, malformed-provenance, and unreadable-surface forms.                                              |
| Rollback                | PASS   | In a disposable worktree, reverse-reverting merge `ebe6b2b12b12df50fb10a446530554a1dd714003` produced tree `2ac48f5051acf6dc8e391ba6231ad1a175177941`, exactly its first-parent tree. The worktree was removed. |
| Durable receipt         | PASS   | PR #1222, exact-head Actions runs, independent-review evidence, Greptile receipt, merge commit, scorecard 742, Bead notes, this AAR, and the filing ledger form the evidence set.                               |
| Docs versus reality     | PASS   | Live authority validation reports two linked effective claimant documents and ten canonical-table links. The corrected operator surfaces match blueprint 727 section 4.                                         |
| Blueprint versus actual | PASS   | E2.11 preserves the pin/authority distinction and the rule that JRig owns evaluation execution but never Freshie runtime tables.                                                                                |
| Reproduction first      | PASS   | Applying the checker to exact base bytes produced four findings before the four live claims were corrected.                                                                                                     |
| Vertical slice          | PASS   | Operator guidance, fail-closed gate, hostile/reverse tests, CI wiring, measurement, CHANGELOG, review, rollback, and filing land as one bounded control.                                                        |
| Observed versus claimed | PASS   | The final reviewer ignored the author's proof table, inspected all 18 commits/eight changed files, planted eight dangerous and seven safe cases, and returned PASS from a clean detached checkout.              |

## Validation and review

The exact reviewed head passed
[Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32021028869),
including `ci-required`;
[Secret Scan](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32021028859),
including `gitleaks`;
[Skill Conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32021028861);
[Actionlint](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32021028860);
[link checking](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32021029099);
[PR Pre-screen](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32021028864);
all three [MiniMax review lanes](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32021072055);
and the kernel advisory checks. MiniMax's only annotation was the existing Node 20 action-runtime
deprecation, deferred outside this bead.

Local and post-merge checks passed: boundary 8/8, recorder 6/6, Dolt sync 42/42, document authority
8/8 plus two effective claimants/ten canonical links, Epic 1 measurement 36/36 byte-current,
Prettier, ESLint, typecheck, actionlint, verification, and gitleaks across all 18 PR commits. The
broad `pnpm test` command retained the pre-existing unrelated CLI/Vite transform failure in two
unchanged CLI suites; the exact-head CI test matrix and CLI smoke tests passed.

The final independent clean-checkout reviewer returned PASS at the exact head. Its own matrix
passed eight dangerous and seven safe cases, including both known-variable literal-dollar reverse
controls, shell/YAML/prose forms, provenance ancestry, and fail-closed malformed/unreadable input.
It also passed generated-artifact validation, scorecard measurement, formatting, lint, actionlint,
and 38 CI routing/injection tests, and ended with a clean detached worktree.

[Greptile review `4950721529`](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1222#pullrequestreview-4950721529)
was requested at the exact head. The free trial had ended, so Greptile is recorded as unavailable
rather than PASS.

## Merge topology and external effects

GitHub still required one human approval after every executable gate and the independent review
passed. The owner authorized administrator bypass, and the
[disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1222#issuecomment-5315079445)
was posted before merge. This temporary review-topology compromise is not Epic 10 independent
certification; no protection rule or required context changed.

No npm command, registry mutation, credential access, contributor contact, Plane mutation, or
production-setting change occurred. Ordinary repository automation triggered after the merge;
that existing automation does not broaden this bead's authority.

## Follow-up

This filing closes only E2.11. The complete Epic 2 parent remains open. The Node action-runtime
deprecation and the pre-existing CLI/Vite test transform failure remain deferred maintenance.
No later bead is activated by this AAR; the next slice requires a separate Beads/Dolt activation
after this filing is reviewed, merged, and closed.
