# Epic 1 Build-Derived Data Disposition — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Blueprint 727, Epic 1 bead 1.7
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hz8f.9`
- **Implementation PR:** [#1220](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1220)
- **Base:** `dc9e54d1822a433b53271ef63c19a3811621025c`
- **Reviewed head:** `0a4ac96f26ab3d109359be667ac22d9f01c2455f`
- **Merge commit:** `ebda824926c5304be38f7a4a657899035351de28`
- **Merge method:** merge commit with disclosed, owner-authorized administrator bypass
- **Status:** E1.7 controls verified; Bead closure follows this filing transaction

## Outcome

Epic 1's six build-derived marketplace JSON files now have an evidence-backed disposition. Two
build-only projections are no longer tracked: `jrig-data.json`, whose live page importer was
removed by PR #1046, and `readme-sections.json`, which is regenerated before both marketplace build
and supported local development. The other four remain tracked because supported consumers or
prior-state semantics still require their committed bytes. Epic 1.8 owns their content-drift gates.

Scorecard row 22 moved from 10 to 8 tracked generated outputs without a content-drift gate. Row 56
moved from one public verified claim to zero because the unconsumed JRig projection had remained as
stale measurement input after its UI was removed. The temporary untracked JRig generator is not a
final endorsement: blueprint bead E9.2 still owns deleting that projection and build step.

No plugin, skill, `.source.json`, provenance-owned mirror, package version, registry artifact,
credential, contributor record, Plane record, branch rule, or release was changed. Open automation
PR #1149 touches README and three external-stat files, none of this bead's six paths; it remained
open and unmodified.

## Six-file disposition

| File                        | Producer                      | Checkout-level consumer or semantic contract                                                           | Decision                    |
| --------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------------- |
| `catalog.json`              | `sync-catalog.mjs`            | The producer consumes prior catalog metadata and ordering; clean-clone output is not yet deterministic | Keep tracked for E1.8       |
| `jrig-data.json`            | `enrich-jrig-data.mjs`        | No live page, component, layout, or library consumer after PR #1046                                    | Untrack; E9.2 deletes later |
| `readme-sections.json`      | `extract-readme-sections.mjs` | Astro plugin pages only; build and `npm run dev` regenerate first                                      | Untrack                     |
| `skills-catalog.json`       | `discover-skills.mjs`         | Freshie dataset builder and supported public/development flows                                         | Keep tracked for E1.8       |
| `skills-index.json`         | `discover-skills.mjs`         | Freshie dataset builder                                                                                | Keep tracked for E1.8       |
| `unified-search-index.json` | `generate-unified-search.mjs` | OG-image generator and supported public/development flows                                              | Keep tracked for E1.8       |

## Implemented controls

- Exact `.gitignore` entries and generated-artifact registry rows classify the two projections as
  untracked; the broad tracked-data class excludes only those exact names.
- `pnpm run validate:generated-artifacts` owns lifecycle, registry, reintroduction, and missing-Git
  tests plus the tracking checker. It runs in the existing `doc-governance` job; no required status
  context was added.
- Git enumeration now fails closed instead of converting an error into an empty tracked set.
- `marketplace` `predev` regenerates README sections before Astro starts.
- A missing Freshie database deterministically replaces stale JRig bytes with `{}` and emits a loud
  warning. No live page consumes that temporary inspection projection.
- `CLAUDE.md`, the generated Epic 1 scorecard, and `CHANGELOG.md` describe the same merged contract.

## Evidence bundle

| Evidence item           | Result | Reproducing evidence                                                                                                                                                                                                                              |
| ----------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution               | PASS   | Post-merge `pnpm run validate:generated-artifacts` passed 9/9 and reported four projection globs, zero tracked. `TMPDIR=/dev/shm pnpm run measure:e1:check` passed 36/36 and reproduced scorecard 742 byte-for-byte.                              |
| Happy path              | PASS   | A clean exact-head archive began without either projection, regenerated JRig `{}` and 449 README plugin keys, and built 3,869 pages from 3,068 skills.                                                                                            |
| Failure path            | PASS   | Fixtures refuse tracked JRig data, tracked README sections, and missing Git evidence. The independent reviewer planted another tracked projection and observed exit 1.                                                                            |
| Rollback                | PASS   | In a disposable worktree, `git revert -m 1 --no-commit ebda824926c5304be38f7a4a657899035351de28` produced tree `8a3e38475a8bf4da37128ec2a9942366fbaead8f`, exactly matching the merge's first-parent tree. The rehearsal was aborted and removed. |
| Durable receipt         | PASS   | PR #1220, merge commit, scorecard 742, this AAR, Bead notes, exact-head Actions runs, independent-review evidence, MiniMax disposition, and Greptile-unavailable receipt form the evidence set.                                                   |
| Docs versus reality     | PASS   | The base `build.mjs` already had nine stages; live-source search found no JRig importer; tracked-tree inspection confirms both files are absent. Documentation records those facts without claiming E9.2 complete.                                |
| Blueprint versus actual | PASS   | E1.7 classified exactly six files, untracked only the two with no supported checkout-level contract, deferred four retained files to E1.8, and preserved E9.2 authority.                                                                          |
| Reproduction first      | PASS   | Baseline build passed before edits. Red fixtures failed while either projection was tracked; green fixtures and a clean build passed after the disposition.                                                                                       |
| Vertical slice          | PASS   | Classification, lifecycle correction, registry, fail-closed gate, tests, CI wiring, measurement, documentation, and changelog landed together.                                                                                                    |
| Observed versus claimed | PASS   | The reviewer ignored the author's proof table, re-derived consumers from a detached clean checkout, planted a failure, reran measurements and build, and returned PASS.                                                                           |

## Validation and review

The exact head passed [Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31994247580), including `ci-required`; [Secret Scan](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31994247554), including `gitleaks`; [Skill Conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31994247572); [CodeQL](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31994247625); [Actionlint](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31994247560); [link checking](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31994247600); [PR Pre-screen](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31994247547); both rounds of [MiniMax review](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31994562661); and the kernel advisory checks. MiniMax's evidence questions were resolved with exact-base and exact-head commands; its current verdict is LGTM.

Local focused checks passed: generated-artifact tests 9/9, Epic 1 measurement tests 36/36,
dead-domain tests 19/19, actionlint, formatting, lint, typecheck, verification pipeline, catalog sync,
gitleaks, and clean marketplace build. The broad `pnpm test` command reproduced the pre-existing
CLI/Vite transform failure in `program.test.ts` and `constants.test.ts`; this PR changed no CLI file,
and the exact-head CI test matrix and CLI smoke tests passed. `quick-test.sh` also reported the known
413 standard-tier corpus errors while its build and lint phases and wrapper completed successfully;
this bead did not lower or relabel that baseline.

The independent reviewer returned PASS at the exact head from a detached clean worktree. It
re-derived all six decisions, checked registry overlap across 23,043 paths, planted a tracked
projection, passed the focused suite, scorecard check, full actionlint, clean build, predev,
gitleaks, mirror-path check, and reverse rollback, and ended with a clean tree. Greptile review
`4948421619` was requested at the exact head; the free trial had ended, so it is recorded as
unavailable rather than PASS.

## Merge topology and external effects

GitHub still required one human approval after executable gates and independent review passed. The
owner authorized administrator bypass, and the [disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1220#issuecomment-5311877586) was posted before merge. This is a temporary review-topology compromise, not Epic 10 independent certification; no rule changed.

The merge triggered the repository's existing main-branch validation and deployment automation.
Post-merge [Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31995125775), Secret Scan, Skill Conform, Actionlint, CodeQL, signed-evidence, and the ordinary
[Tons of Skills deployment](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31995126240)
completed successfully. The subsequent [production E2E run](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31995367828)
reported 123 passes and the same seven failures disclosed by AAR 749: six assertions still expect
the absent legacy `#hero-search-input`, and one badge-image assertion observed zero natural width.
PR #1220 changed none of the homepage, image, or production-test files. This existing site/test
contract mismatch is not represented as a green E1.7 check and was not scope-crept into this filing.

No workflow, Environment, credential, registry, or deployment setting was changed by this bead, and
no npm publication command was run during implementation or review. The automatic changed-package
publisher run remained queued without jobs at filing time; no environment approval, credential
exposure, registry contact, or package mutation was observed.

## Follow-up

This filing closes only E1.7 and leaves the Epic 1 parent open. E1.8 may consume the four retained
files only after this Bead closes and the next owner-authorized work slice is recorded. E9.2 remains
the sole owner of deleting the unconsumed JRig projection and its build step. No later bead is
activated by this AAR.
