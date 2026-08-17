# Skills Index Drift Gate — Interim After-Action Review

- **Date:** 2026-08-17
- **Authority:** Blueprint 727 §15.1, Epic 1 bead 1.8
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hz8f.11` (open)
- **Implementation PR:** [#1227](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1227)
- **Base:** `66603ebe4704884f8cf886328b4fbe6c0b2fb99c`
- **Reviewed head:** `668478741418c830090a03b3e78e10c6c2e603da`
- **Merge commit:** `3c4cda75da92c087259a9b0db3a67988ca2db718`
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** first E1.8 projection gate live; three deterministic projections remain

## Outcome

The repository now classifies all 15 tracked JSON files in `marketplace/src/data/` by authority and
reproducibility. Four are deterministic tracked projections: `catalog.json`,
`skills-catalog.json`, `skills-index.json`, and `unified-search-index.json`. Three are external
snapshots assigned to E1.10, one is editorial canonical data, and seven are canonical hand-authored
files. This slice adds a non-mutating regenerate-and-diff gate for `skills-index.json`, moving
deterministic content-drift coverage from 0/4 to 1/4.

The checker renders the candidate in memory and compares it with stage-0 Git-index bytes. It fails
closed on missing, untracked, symlink, unmerged, malformed, duplicate, unsafe-path, and content-drift
conditions. `Validate Plugins` runs the install-free, credential-free check unconditionally and
aggregates it once into `ci-required`; the required contexts remain exactly `ci-required`,
`gitleaks`, and `skill-conform`. `CHANGELOG.md`, `CLAUDE.md`, blueprint 727, and scorecard 742 were
updated with the executable contract and current 1/4 state.

No plugin, skill, mirrored content, provenance record, registry, credential, contributor, Plane,
branch-protection, package-release, or production setting changed. E1.8 remains open for the other
three deterministic projections.

## Evidence bundle

| Evidence item           | Result  | Reproducing evidence                                                                                                                                                                                                                |
| ----------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution               | PASS    | Post-merge `TMPDIR=/dev/shm pnpm run validate:generated-content` passed 4/4 architecture tests and processed 3,068/3,068 skills with zero failures.                                                                                 |
| Full build              | PASS    | Exact reviewed head completed `cd marketplace && TMPDIR=/dev/shm npm run build`: 3,869 pages, exit 0.                                                                                                                               |
| Happy path              | PASS    | An unchanged stage-0 `skills-index.json` matches the in-memory metadata projection without modifying the worktree.                                                                                                                  |
| Failure path            | PASS    | Focused hostile fixtures refuse missing, untracked, symlink, unmerged, malformed, duplicate, path-traversal, and unreadable-source conditions.                                                                                      |
| Red proof               | PASS    | A disposable worktree staged a 3,068-to-3,067 index mutation; `validate:generated-content` exited nonzero for drift and left the worktree unchanged.                                                                                |
| Isolation proof         | PASS    | Removing `skills-catalog.json` from the disposable Git index did not affect the metadata-only check, which still passed 3,068/3,068.                                                                                                |
| Rollback                | PASS    | The independent reviewer applied the complete reverse patch cleanly; operational rollback is reverting merge `3c4cda75` and rerunning both generated-content and Epic 1 measurement gates.                                          |
| Durable receipt         | PASS    | PR #1227, its [pre-merge disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1227#issuecomment-5317148754), merge SHA, Bead notes, scorecard 742, this AAR, and the filing ledger form the receipt. |
| Docs versus reality     | PASS    | Post-merge scorecard row 22 is byte-current and reports four deterministic artifacts: one gated and three ungated.                                                                                                                  |
| Blueprint versus actual | PARTIAL | Blueprint E1.8 requires every deterministic tracked projection. This slice deliberately gates only `skills-index.json`; catalog, skills catalog, and unified search remain.                                                         |
| Vertical slice          | PASS    | The implementation net diff contains the registry, checker, generator, tests, one existing workflow, package script, governing docs, scorecard, and changelog; it changes no marketplace artifact bytes.                            |

## Validation and review

The exact reviewed head passed
[Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32039224868),
including `ci-required` and the new generated-content job;
[Secret Scan](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32039224786),
including `gitleaks`;
[Skill Conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32039224828);
[Actionlint](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32039224753);
[link checking](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32039224801);
[PR Pre-screen](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32039224789);
and all three [MiniMax review lanes](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/32039256750).

The independent clean-checkout reviewer returned **PASS** on exact range
`66603ebe4704884f8cf886328b4fbe6c0b2fb99c...668478741418c830090a03b3e78e10c6c2e603da`.
It inspected all five commits and the complete 14-file diff; passed generated-artifact tests 13/13,
generated-content tests 4/4, the hostile focused suite 29/29, actionlint, document checks, and
Gitleaks; reproduced 3,068/3,068 metadata processing; independently measured 4 artifacts, 1 gated,
and 3 ungated; and confirmed zero plugin, skill, provenance, or mirrored-content changes.

[Greptile was requested on the exact head](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1227#issuecomment-5317066786),
but returned no exact-head review; its prior response said the free trial ended. Greptile is recorded
as unavailable/no response, never as PASS. GitHub still required a human approval because the
documented independent second-identity topology is unavailable. The owner-authorized administrator
bypass was disclosed before merge; no branch rule or required context was changed.

## Operational notes and follow-up

One hosted attempt initially failed before executing the gate because the job used `npm ci` while
`marketplace/package-lock.json` is intentionally untracked. The final job has no install step, and
an architecture test prevents reintroduction. A local ENOSPC incident was traced to aged,
prefix-validated test scratch roots and recoverable caches; only those disposable paths were
removed. No repository or user source data was deleted.

Continue `claude-hz8f.11` through separately reviewable gates for `catalog.json`,
`skills-catalog.json`, and `unified-search-index.json`. Keep external snapshots in E1.10 and do not
relabel editorial or canonical data as generated merely to increase coverage.
