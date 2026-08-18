# Unified Search Drift Gate — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.8, fourth and final bounded projection slice
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hz8f.11`
- **Implementation PR:** [#1239](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1239)
- **Base:** `8558c10dd5c29f62d74b4463a69fa922dd56cfc0`
- **Reviewed head:** `8daafb8fa7e911bfc3020d270183a24cdd7dd62e`
- **Merge commit:** `c05b27489cfd6257c59988358224aab7e09ef978`
- **Merge method:** merge commit with disclosed, owner-authorized administrator bypass
- **Status:** implementation merged and post-merge verified; E1.8 is 4/4 complete pending this AAR merge

## Outcome

`marketplace/src/data/unified-search-index.json` is now a deterministic projection of governed
repository inputs. The previous committed projection contained 448 plugins, 3,008 skills, no
documentation rows, 3,456 total items, 311 agents, and 19 hooks. The corrected projection contains
467 plugins, 3,068 skills, 24 documentation rows, 3,559 total items, 347 agents, and 28 hooks.

The renderer no longer emits a wall-clock `meta.generated` value. Two independent renders and the
committed artifact share SHA-256
`84c3785e990f184b40cbebd6518f9f06e371dc2eeb0d2b0f763cc139cfe367f7`. The public item sequence,
field order, cross-type identifiers, and consumer shape remain compatible. The corrected search
text includes array descriptions and 13 inline-frontmatter documents that the former producer did
not index correctly.

The renderer writes atomically and exposes a non-mutating `--check` that compares source-derived
bytes with the stage-0 Git index. It fails closed on missing or malformed sources, contradictory
counts or identities, unsafe slugs, case-fold duplicate names, path traversal, symlinked path
components, and unreadable counted files. The existing credential-free `generated-content-drift`
job now checks all four deterministic tracked marketplace projections without adding a required
context or path filter.

No plugin, skill, `SKILL.md`, `.source.json`, mirrored content, license, registry, credential,
contributor, Plane authority, branch rule, release, or production state changed.

## Evidence bundle

| Evidence item       | Result | Reproducing evidence                                                                                                                                                                                           |
| ------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution           | PASS   | `node marketplace/scripts/generate-unified-search.mjs --check` reports 467 plugins, 3,068 skills, 24 docs, and 3,559 total items.                                                                              |
| Before/after        | PASS   | Projection population changed from 448/3,008/0/3,456 to 467/3,068/24/3,559; agent and hook totals changed from 311/19 to 347/28.                                                                               |
| Determinism         | PASS   | Two independent renders and the committed artifact have SHA-256 `84c3785e990f184b40cbebd6518f9f06e371dc2eeb0d2b0f763cc139cfe367f7`.                                                                            |
| Happy path          | PASS   | Independent review reproduced the exact counts and bytes, and the marketplace build generated 3,870 pages.                                                                                                     |
| Failure path        | PASS   | Independent fixtures refused source and ancestor symlinks, missing docs, production chmod-000 and injected `EACCES`, unsafe slugs, duplicate normalized names, malformed identities, and contradictory counts. |
| Red proof           | PASS   | The reviewer planted staged index drift; `--check` exited 1 while both index and worktree hashes remained unchanged. An unstaged poison file was ignored and left untouched.                                   |
| Compatibility       | PASS   | Independent base comparison preserved sequence, field order, load-bearing shape, and all 38 cross-type duplicate identifiers. Only the two documented search corrections changed rendered meaning.             |
| Generated gates     | PASS   | Post-merge focused generated tests passed 19/19; the shared registry reports four deterministic projections and zero ungated projections.                                                                      |
| Measurement         | PASS   | Post-merge `TMPDIR=/dev/shm pnpm run measure:e1:check` passed 37/37 and reported `epic-1-measurement: OK`.                                                                                                     |
| Provenance boundary | PASS   | The exact 13-file implementation diff contains zero plugin, skill, `SKILL.md`, `.source.json`, mirror, license, or credential paths.                                                                           |
| Docs versus reality | PASS   | Blueprint 727, CHANGELOG, workflow, artifact registry, scorecard, renderer, tests, and committed output agree on 4/4 coverage.                                                                                 |
| Rollback            | PASS   | Independent review verified reverse application of the exact implementation diff. Revert merge `c05b27489`, then rerun the generated-content and Epic 1 measurement gates.                                     |

## Validation and review

Exact head `8daafb8fa7e911bfc3020d270183a24cdd7dd62e` passed required contexts
`ci-required`, `gitleaks`, and `skill-conform` and every substantive hosted job. This included the
full Validate Plugins matrix, marketplace validation and build, test shards, CLI smoke tests,
CodeQL, link checking, PR Pre-screen, Actionlint, formatting, Ruff, Secret Scan, and the final
MiniMax Review, Adversarial review, and A-grade coach lanes. MiniMax's final Review reported
**LGTM** and “Ship it.” An earlier generated-file-absence finding was disproved by the GitHub PR
files API and the exact-head drift gate; the generated artifact was modified with 10,116 additions
and 8,361 deletions. There were zero unresolved review threads.

Greptile reported confidence 5/5 and no blocking failure on the initial implementation head. It was
requested again on final head `8daafb8`, but produced no newer response before merge; this absence
is recorded rather than represented as an exact-head approval.

An independent non-implementing reviewer worked from a clean detached checkout. Its earlier
**RETURN FOR CORRECTION** identified five fail-closed gaps: required-input and root symlinks,
unreadable counted files, unsafe slugs, and case-fold duplicate names. All five were corrected. The
reviewer then reran the original probes plus ancestor symlinks, deterministic `EACCES`, planted
drift, consumer compatibility, rollback, Actionlint, 23 focused tests, 37 scorecard tests, and the
marketplace build at the final exact head. Its final verdict was **PASS**. The earlier verdict was
not treated as approval.

GitHub still reported `REVIEW_REQUIRED` because the documented second-human approval topology is
unavailable. The owner-authorized
[administrator-bypass disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1239#issuecomment-5322264794)
was posted before merge. No branch rule or required context changed.

## Operational notes and follow-up

The Epic 1 row-22 population is now fully measured: `skills-index.json`, `skills-catalog.json`,
`catalog.json`, and `unified-search-index.json` each have an executable deterministic content gate.
The external network snapshots remain owned by E1.10 and were not relabeled or modified. Editorial
and canonical hand-authored data remain outside the deterministic projection cohort.

The scorecard's `invisible_files` value counts tracked Git-index paths matched by the Gitleaks
allowlist; it does not count ignored or untracked files. Filing this ledgered AAR therefore raises
both `tracked_files` and `invisible_files` by one. Regenerate the document index and Epic 1
scorecard from staged bytes before merging this filing.

After this AAR merges and post-merge checks pass, close `claude-hz8f.11` with both merge SHAs and
store durable memory for the four-projection authority boundary. The Epic 1 parent remains open;
E1.6 is the next highest-priority unblocked candidate and must receive a fresh overlap audit before
activation.
