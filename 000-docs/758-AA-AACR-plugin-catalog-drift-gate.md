# Plugin Catalog Drift Gate — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.8, third bounded projection slice
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hz8f.11`
- **Implementation PR:** [#1237](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1237)
- **Base:** `98f652ff5ba00181b76d1aae9e6698741b69c132`
- **Reviewed head:** `26c1f10c9b0bc457264ba320e8acfaa6aaecb006`
- **Merge commit:** `960d9b2642cb90fee12dff814c173e45aed4ee8c`
- **Merge method:** merge commit with disclosed, owner-authorized administrator bypass
- **Status:** implementation merged and post-merge verified; E1.8 remains open at 3/4

## Outcome

`marketplace/src/data/catalog.json` is now a deterministic projection of the 467-row canonical
extended catalog and the 3,068-row full skill projection. The renderer no longer reads its own
previous output, carries runtime timestamps, preserves stale flags, or silently accepts malformed
skill relationships. The stale projection moved from 450 plugins, 3,022 skills, and 81 commands to
467 plugins, 3,068 distinct skill paths, and 80 commands.

Skill counts join by normalized canonical source path. The two intentional source-alias pairs
receive equal per-plugin counts, producing an alias-summed 3,074, while the global total counts each
`SKILL.md` path once at 3,068. Those cohorts are not interchangeable. Canonical plugin order is
preserved. The two rows without an explicit author retain the compatibility default
`Claude Code Plugins`, and the governed retired-domain normalizer applies to the complete rendered
object.

The renderer writes atomically and exposes a non-mutating `--check` that renders from canonical
inputs and compares exact bytes with the stage-0 Git index. The existing credential-free
`generated-content-drift` job now checks three of four deterministic tracked marketplace
projections without adding a required context or path filter. `unified-search-index.json` remains
the final E1.8 slice.

No plugin, skill, `SKILL.md`, `.source.json`, mirrored content, license, registry, credential,
contributor, Plane authority, branch rule, release, or production state changed.

## Evidence bundle

| Evidence item         | Result | Reproducing evidence                                                                                                                                                                                  |
| --------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution             | PASS   | `node marketplace/scripts/sync-catalog.mjs` reports 467 plugins, 3,068 distinct skills, and 80 commands.                                                                                              |
| Before/after          | PASS   | Base projection: 450 / 3,022 / 81. Merged projection: 467 / 3,068 / 80. Canonical and projected name arrays are identical and ordered.                                                                |
| Cohort reconciliation | PASS   | Independent review computed 3,068 distinct `filePath` values and 3,074 alias-summed per-plugin counts; the global projection uses the distinct cohort.                                                |
| Happy path            | PASS   | Two successive writes were byte-identical and matched the tracked output. Poisoning the previous output did not influence the next render.                                                            |
| Failure path          | PASS   | Renderer fixtures refuse duplicate identities and paths, traversal, contradictory ancestry, orphan parents, count mismatch, malformed components, and staged drift.                                   |
| Red proof             | PASS   | The independent reviewer planted staged catalog drift; `--check` exited 1 and the planted worktree hash remained unchanged.                                                                           |
| Compatibility         | PASS   | Fixtures preserve the default author on `formatter` and `security-agent` and normalize retired-domain values across description, keyword, and author fields.                                          |
| Generated gates       | PASS   | Post-merge generated-artifact validation passed 14/14; generated-content validation passed 8/8, 3,068/3,068 skills, and catalog 467/3,068/80.                                                         |
| Measurement           | PASS   | Post-merge `TMPDIR=/dev/shm pnpm run measure:e1:check` passed 37/37 and reported scorecard 742 byte-current with three of four projections gated.                                                     |
| Provenance boundary   | PASS   | The exact 12-file diff contains zero plugin, skill, `SKILL.md`, `.source.json`, mirror, license, or credential paths.                                                                                 |
| Docs versus reality   | PASS   | Blueprint 727, CHANGELOG, CLAUDE.md, registry, workflow, package script, scorecard, renderer, tests, and output agree on the 3/4 result.                                                              |
| Rollback              | PASS   | Reverse-applying the exact diff produced tree `be6a5fa9e24bb855988ae23c0dec265d5a7be14e`, exactly matching the base tree. Revert merge `960d9b264`, then rerun the three generated/measurement gates. |

## Validation and review

Exact head `26c1f10c9b0bc457264ba320e8acfaa6aaecb006` passed the required `ci-required`,
`gitleaks`, and `skill-conform` contexts and every substantive hosted job. This included the full
Validate Plugins matrix, marketplace build and validation, test shards, CLI smoke tests, CodeQL,
link checking, PR Pre-screen, Actionlint, formatting, Ruff, both kernel advisories, Secret Scan,
and all three MiniMax lanes.

[Greptile reviewed the exact head](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1237#issuecomment-5321106103)
at confidence 5/5 and reported no blocking failure. MiniMax initially identified the lost default
author and incomplete projection normalization. Both were corrected at the final head; its fresh
Review, Adversarial review, and A-grade coach lanes passed. There were zero review threads.

An independent non-implementing reviewer worked from a clean detached checkout. Its first bounded
verdict was **BLOCK** because five proofs were incomplete, not because it found a defect. The same
reviewer then ran only the missing proofs and returned **PASS**: independent population
reconciliation, planted drift with unchanged worktree bytes, output-poisoning immunity and
byte-identical renders, scorecard visibility semantics, and exact rollback-tree equality. The
interim BLOCK was not treated as approval.

GitHub still reported `REVIEW_REQUIRED` because the documented second-human approval topology is
unavailable. The owner-authorized
[administrator-bypass disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1237#issuecomment-5321329531)
was posted before merge. No branch rule or required context changed.

## Operational notes and follow-up

Root filesystem pressure from disposable test scratch directories constrained an additional local
Astro build. The ignored scratch population was removed by exact test-prefix, without touching
repository content. Hosted exact-head marketplace build and all test shards passed. Local
`pnpm run verify`, formatting, lint, typecheck, dead-domain policy, changelog coverage, Actionlint,
Gitleaks, generated gates, and Epic 1 measurement passed. The verifier's out-of-scope JSON
formatting rewrite was removed before commit and did not enter the PR.

Scorecard `invisible_files` counts tracked paths matched by the Gitleaks allowlist; it does not
count ignored or untracked working-tree files. Filing this ledgered AAR therefore increases both
`tracked_files` and `invisible_files` by one. The clean staged-index measurement reproduces that
change independently of ignored build or scratch output.

Keep `claude-hz8f.11` open at 3/4. The next and only E1.8 implementation slice is the deterministic
`unified-search-index.json` renderer and staged-index drift gate. Do not close the Bead or activate a
different Epic 1–3 child until that final projection is merged, independently reviewed, filed, and
verified.
