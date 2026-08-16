# Epic 1 README Metrics Writer — After-Action Review

- **Date:** 2026-08-16
- **Authority:** Blueprint 727, Epic 1 bead 1.9
- **Bead:** `claude-hz8f.6`
- **Implementation PR:** [#1212](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1212)
- **Reviewed head:** `c9d952184322b1e77c185cd6fe9996d4e182dda5`
- **Merge commit:** `78143f4d27dd4dac0aa8330ba69a27f4beea6772`
- **Status:** Implementation merged and post-merge verification passed; Bead closure follows this filing transaction

## Outcome

`scripts/generate-readme-toc.mjs` is the sole governed writer for root README catalog, skill, and
agent counts. The orphaned `scripts/update-metrics.mjs` file and its package command are gone.
Scorecard row 25 changed from two writers to one writer against a target of one, while the tracked
tree decreased from 23,014 to 23,013 files.

The binding Epic 1 measurement gate now refuses any other production executable that writes
`README.md` and references count-bearing marketplace facts. Discovery covers the complete tracked
executable tree rather than a fixed list of script directories. Explicit exclusions preserve test
and spec sources, measurement instrumentation, and content beneath a tracked `.source.json`
ancestor. Regenerating scorecard 742 cannot convert a duplicate writer into an accepted state.
Under the repository's v4.4 filing mechanics, `000-docs/.gitignore` is the public filing ledger; the
filing PR appends document 745 there before generating the index and scorecard.

## Decision and before/after evidence

Rewriting `update-metrics.mjs` onto the corpus resolver was considered. Deletion won because the
script had no live caller beyond its own package command, claimed a workflow that does not exist,
read stale generated indexes, duplicated governed README output, and retained a GitHub repository
description mutation path. Deletion was the smallest reversible change and removed conflicting
authority rather than modernizing an unused surface.

The pre-edit command `pnpm --silent run measure:e1 --row=25 --stdout` reported two writers:
`scripts/generate-readme-toc.mjs` and `scripts/update-metrics.mjs`. The merged command reports one of
one and names only `scripts/generate-readme-toc.mjs`. Post-merge targeted tests passed 23/23, and the
deleted script and package command remained absent. README, workflow, plugin-skill, provenance, and
mirror-content diffs were zero.

## Verification and independent review

- Exact-head `pnpm run measure:e1:check` passed 36/36 deterministic tests and reported scorecard 742
  in sync. ESLint, typecheck, formatting, repository verification, CLI smoke, Python, MCP,
  validation-script, documentation-governance, link, security, and kernel-advisory checks passed.
- Required contexts completed successfully at the reviewed head in the
  [Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31951432381),
  [gitleaks](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31951432348),
  and [skill-conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31951432357)
  runs. MiniMax normal review said
  [“Ship it”](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1212#issuecomment-5307733820),
  and its adversarial lane returned
  [`lgtm`](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1212#issuecomment-5307734608).
- The first independent review returned the initial head for correction after a package-level writer
  escaped a detector limited to three script roots. The
  [correction record](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1212#issuecomment-5307804891)
  identifies the returned and corrected heads. The implementation then widened discovery to the
  tracked executable tree and moved the committed red fixture under `packages/`.
- A later review attempt was interrupted before its decisive command completed and correctly
  returned `BLOCK` on incomplete evidence. It was not used as approval.
- The final fresh reviewer planted writers under `packages/`, a first-party plugin, and
  `marketplace/src/lib/`. `pnpm --silent run measure:e1` refused all three plus the canonical writer
  and left scorecard 742 unchanged. A separate probe proved `.test.mjs`, `.spec.ts`, and
  `.source.json`-owned mirror writers remain excluded and row 25 stays one of one. The verdict was
  `PASS`; its exact-head evidence is in the
  [review and merge disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1212#issuecomment-5307886819).
- Greptile was triggered at the initial implementation head `d8918dce`, but its free-review trial
  had expired. No Greptile review exists for the corrected reviewed head `c9d95218`. The
  [response](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1212#pullrequestreview-4946327658)
  was inspected and was not counted as evidence.

Scorecard row 46's `allowlist_patterns` remains 25 because it counts path regexes in
`.gitleaks.toml`, not public-filing negations in `000-docs/.gitignore`. Its `invisible_files` value
rises by one because the existing `^000-docs/.*\.md$` gitleaks pattern matches the newly tracked
AAR. The scorecard values were mechanically regenerated; these two populations are intentionally
different.

The broad local `pnpm test` command exposed an unchanged dependency-baseline defect: Vitest 2.1.9
resolves Vite 7.3.3 through the root `vite >=6.4.2` override and the CLI suite fails before test
collection. GitHub's authoritative CLI smoke and widened MCP/Python/validation suites passed. The
command output and unchanged-lockfile comparison are retained in Bead `claude-hz8f.6`; the
dependency mismatch requires a separate isolated correction and was not mixed into E1.9.

## Merge topology, scope, and rollback

GitHub required one human approval after every executable, bot, and independent gate passed. The
platform owner authorized a one-time administrator bypass for the known second-identity topology;
the [disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1212#issuecomment-5307886819)
was recorded before merge. No branch-protection rule, required status, or approval policy changed.

This slice changed the measurement implementation and fixtures, generated scorecard 742,
`CHANGELOG.md`, and the package script inventory. It performed no registry, credential,
contributor, Plane, branch-protection, billing, package-release, marketplace-data, or production
mutation. A local disk-pressure incident damaged hard-linked dependency-store bytes before source
editing; `pnpm install --force --frozen-lockfile` restored the frozen install, `pnpm store status`
passed, and no lockfile or repository history changed.

Rollback must reverse this AAR filing first, then revert merge commit
`78143f4d27dd4dac0aa8330ba69a27f4beea6772`. Regenerate scorecard 742 and rerun the 36-test Epic 1
gate. No external rollback is required.

## Lesson and next gate

A single-writer assertion is only as strong as its discovery denominator. Security and authority
gates must search the complete governed population, then name narrow exclusions explicitly. Epic 1
remains open; this AAR activates no later bead. The next Epic 1–3 slice must be re-ranked from the
current merged `main` after `claude-hz8f.6` closes.
