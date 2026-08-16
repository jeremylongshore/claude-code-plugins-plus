# Epic 1 Corpus Resolver — After-Action Review

- **Date:** 2026-08-16
- **Authority:** Blueprint 727, Epic 1 bead 1.5
- **Bead:** `claude-hz8f.5`
- **Implementation PR:** [#1210](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1210)
- **Reviewed head:** `239214b12d3a203e000f168852d64106e0b50623`
- **Merge commit:** `1fbd29381db4dd4be2f25a281766fd21b42bfbf5`
- **Status:** Implementation merged and post-merge verification passed; Bead closure follows this filing transaction

## Outcome

One fail-closed `resolveCorpus(cohort)` authority now defines five tracked skill populations. At the
merged tree, the exact resolver reports:

| Cohort              | Files |
| ------------------- | ----: |
| Marketplace-visible | 3,068 |
| Graded              | 3,679 |
| First-party         | 2,802 |
| Curated mirror      | 1,915 |
| Curriculum          |   500 |

The separate raw tracked plugin inventory remains 3,179 and is explicitly named
`raw_tracked_plugin_skill_files` in scorecard row 1. Scorecard row 24 owns the five governed cohort
answers; unlike populations are not interchangeable.

Four binding consumers use the resolver: README metrics, marketplace discovery, canonical schema
validation, and curated promotion. README and the generated marketplace skills index now project
3,068 marketplace-visible skills. Curated promotion remains the graded/first-party intersection and
reports 1,915 files in sync.

## Before and after

Before this slice, row 24 exposed five artifact-specific answers: 3,179, 3,678, 3,051, 3,008, and
1,915. The 3,051 and 3,008 values were stale generated projections, while 3,678 was a historical
Freshie export. The resolver now derives named membership from the tracked tree, catalog source
roots and names, `.source.json` ancestry, and the curated manifest. It preserves explicit orphan
compatibility instead of silently reclassifying a plugin with neither provenance nor a manifest.

The red fixture demonstrates the former raw plugin walker admitting five skills while the governed
marketplace-visible cohort admits three, excluding hidden and orphaned entries. Direct Git scans and
caller-supplied inventories reject path traversal, Windows-absolute paths, unknown cohorts,
malformed or contradictory provenance, unreadable records, curated-manifest drift, duplicate
manifest rows, missing manifests, tracked `SKILL.md` symlinks, final-file symlinks, and symlinked
ancestor directories.

## Verification and review

- Exact-head and post-merge `pnpm run measure:e1:check` passed 35/35 deterministic tests and
  reported `epic-1-measurement: OK` for document 742.
- Focused Python discovery and promotion tests passed 22/22.
- `node scripts/generate-readme-toc.mjs --check` passed; the independently regenerated marketplace
  index contained 3,068 skills across 19 categories.
- `python3 freshie/scripts/promote-to-curated.py --check` reported 1,915 promoted skills in sync.
- Formatting, ESLint, typecheck, validation, repository verify, CLI smoke, Python, MCP, security,
  link, documentation-governance, CodeQL, `ci-required`, `gitleaks`, and `skill-conform` checks
  passed at the reviewed head.
- No workflow, mirrored `SKILL.md`, `.source.json`, curated mirror, or provenance implementation
  bytes changed.

The filing transaction followed the v4.4 mechanics rather than hand-editing derived values. After
document 744 and its curated public-ledger entry were staged,
`node scripts/generate-docs-index.mjs` generated the 184-document index and `pnpm run measure:e1`
generated scorecard 742. The scorecard's `invisible_files` value is a subset of tracked paths that
match existing gitleaks allowlist patterns, not the complement of `tracked_files`; the new
`000-docs/*.md` record therefore increases both values by one while `allowlist_patterns` correctly
remains 25. `000-docs/.gitignore` is the curated filing ledger checked by
`check-docs-ignore-policy.mjs`, not an output of the index generator.

The first independent review found that callers supplying a precomputed path inventory bypassed the
Git-index mode check. That head was returned for correction. The resolver now validates every
filesystem ancestor for supplied skill paths, README metrics use direct Git inventory, and the
scorecard has an end-to-end injected-symlink fixture. The
[fresh exact-head review](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1210#issuecomment-5307511152)
replanted direct, final-file, ancestor-directory, and scorecard symlinks and returned PASS.

MiniMax's exact-head normal lane returned LGTM / Ship it and its adversarial lane passed. Evidence
questions were closed with exact commands, the unchanged base provenance-helper blob, per-file test
totals, and the raw-to-marketplace reconciliation. Greptile was triggered at the reviewed head, but
its free-review trial had expired; its response was inspected and was not treated as review evidence.

## Merge topology, scope, and rollback

GitHub still required one human approval after every executable and independent gate passed. The
platform owner authorized a one-time administrator bypass for the known second-identity topology.
The [bypass disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1210#issuecomment-5307513029)
was recorded before merge. No standing branch rule, status context, or approval policy changed.

This slice changed the resolver and fixtures, four binding consumers, generated README/index data,
the measurement harness and scorecard, and `CHANGELOG.md`. It performed no registry, credential,
contributor, Plane, branch-protection, billing, package-release, or production mutation.

Rollback must reverse this AAR filing first, then revert merge commit
`1fbd29381db4dd4be2f25a281766fd21b42bfbf5`. Regenerate the README/index and scorecard, then rerun
the 35-test measurement gate and focused Python suite. No external rollback is required.

## Lesson and next gate

A count is governed only when its membership, not merely its integer, has one executable authority.
Injected inventories require the same fail-closed boundary as direct Git scans. Epic 1 remains open;
this AAR activates no later bead. E1.1 is already closed, E1.2 overlaps open PR #1171, E1.6 still
needs fact-class and cohort adjudication, and E1.7 overlaps PR #1149. The next slice must be
re-ranked from current `main` after this Bead closes.
