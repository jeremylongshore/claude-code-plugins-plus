# Epic 1 Domain Retirement — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Blueprint 727, Epic 1 bead 1.13
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hz8f.8`
- **Implementation PR:** [#1218](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1218)
- **Base:** `3543d5d167bd4e8d27666c8893080bca3bd72950`
- **Reviewed head:** `5b3ceda9647ee50ec473e8b26c31f4cbc6e59836`
- **Merge commit:** `e3a9d72037232cdec665a1d7480251b2b68ad1e7`
- **Merge method:** merge commit with disclosed, owner-authorized administrator bypass
- **Status:** E1.13 controls verified; an unrelated post-deploy site-test mismatch is disclosed below; Bead closure follows this filing transaction

## Outcome

The retired public domain is absent from every actionable first-party source and registered
generated projection. A case-insensitive, tracked-byte policy now partitions occurrences into
first-party, generated, frozen, provenance-mirror, and historical cohorts. It blocks actionable or
unclassifiable occurrences inside the existing `doc-governance` dependency of `ci-required`.

The immutable baseline at the exact base SHA was 356 occurrences across 125 files: 292 actionable
occurrences across 114 files and 64 retained occurrences across 11 files. The merged result is zero
actionable, 64 retained, and zero refused. The retained population is exactly four byte-pinned
frozen document/fixture occurrences and 60 Freshie run-1 historical occurrences. The superseded
293/63 partition had incorrectly classified the frozen prose-anchor fixture as editable.

Current navigation points to `https://tonsofskills.com/`. Historical prose uses a neutral retired
label, while executable and URL-shaped examples use the reserved, non-resolving
`retired-domain.invalid` host with explicit historical wording. Unsupported author contacts were
removed without removing contributor names. No preserved historical bytes, provenance-owned
content, plugin versions, registry state, credentials, contributors, Plane records, branch rules,
or production settings changed.

## Implemented controls

- `scripts/dead-domain-policy.mjs` scans all tracked bytes case-insensitively and refuses malformed,
  unreadable, contradictory, symlinked, unregistered, or hash-drift evidence.
- `scripts/generated-artifact-registry.mjs` identifies generated classes and their owning
  postprocessor rather than using filename guesses.
- `scripts/normalize-retired-domain-projections.mjs` corrects registered generated projections and
  excludes provenance mirrors.
- `scripts/plugin-provenance.mjs` uses descriptor-bound, no-follow reads. Only an initial failed
  open may establish absence; a dangling marker, identity change, or open-then-unlink race refuses.
- `pnpm run validate:dead-domain` runs locally and in `doc-governance`; no required status context
  was added or weakened.
- `CHANGELOG.md` records the cohort correction, identity policy, command-safe replacement, and
  fail-closed provenance behavior.

## Evidence bundle

| Evidence item           | Result | Reproducing evidence                                                                                                                                                                                                                                                       |
| ----------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution               | PASS   | Post-merge `pnpm run validate:dead-domain` passed 23/23 tests and reported 0 actionable, 4 frozen, 60 historical, 0 mirrored, and 0 refused. `pnpm run measure:e1:check` passed 36/36 and reproduced scorecard 742 byte-for-byte.                                          |
| Happy path              | PASS   | First-party and generated fixtures classify deterministically; all 64 governed retained occurrences remain readable and byte-pinned.                                                                                                                                       |
| Failure path            | PASS   | Mixed case, unregistered snapshots, malformed/non-regular provenance, tracked symlinks, path traversal, generated-projection symlinks, dangling provenance, descriptor/path identity changes, and open-then-unlink all refuse. The combined post-merge suite passed 43/43. |
| Rollback                | PASS   | In a disposable worktree, `git revert -m 1 --no-commit e3a9d72037232cdec665a1d7480251b2b68ad1e7` produced tree `702831717e07dec1760a04ceee7df49ac794391e`, exactly matching base tree `702831717e07dec1760a04ceee7df49ac794391e`; the rehearsal was aborted and removed.   |
| Durable receipt         | PASS   | PR #1218, merge commit, scorecard 742, this AAR, Bead notes, required-check runs, independent-review digest, and Greptile-unavailable receipt form the evidence set.                                                                                                       |
| Docs versus reality     | PASS   | Blueprint 727 and scorecard 742 name the corrected 356/292/64 baseline and exact command. `CHANGELOG.md` matches the merged controls and does not claim the dead domain redirects.                                                                                         |
| Blueprint versus actual | PASS   | E1.13 retired only classified actionable references, preserved governed evidence, installed a blocking reintroduction gate, and activated no later bead.                                                                                                                   |
| Reproduction first      | PASS   | The red fixture proves one actionable first-party occurrence fails the policy before replacement; legacy private-only publication and provenance-race fixtures remain red proofs.                                                                                          |
| Vertical slice          | PASS   | Classification, registered generation, normalization, CI wiring, scorecard measurement, regression fixtures, documentation, and changelog landed together.                                                                                                                 |
| Observed versus claimed | PASS   | Counts, ancestry, versions, frozen bytes, command syntax, and tests were independently rerun from a clean exact-head checkout rather than accepted from the PR table.                                                                                                      |

## Validation and review

The reviewed head passed [Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988418020), including `ci-required` and its `verify` job; [Secret Scan](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988418086), including `gitleaks`; [Skill Conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988418118); [CLI Cross-Platform Testing](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988418177); [CodeQL](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988418126); [Actionlint](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988418182); [link checking](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988418158); [Playwright E2E](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988418037); PR Pre-screen; kernel advisory checks; and all [MiniMax review](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31988448450) jobs. The separate `prescreen-grade` status was advisory; the authoritative PR Pre-screen workflow succeeded.

The merge also triggered the repository's existing deployment automation. The
[site deployment](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31989033215)
completed successfully without changing deployment settings. Its subsequent
[production E2E run](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31989329105)
reported 123 passes and seven failures: six assertions expected the absent legacy
`#hero-search-input`, and one badge-image assertion raced the deployment. A later direct request to
the badge returned HTTP 200, while the live homepage and unchanged source still contain no
`#hero-search-input`. Neither the homepage, badge, nor affected production tests changed in PR
#1218. This is an existing site/test contract mismatch, is not represented as a green E1.13 check,
and was not scope-crept into this filing.

The automatic [changed-package publisher run](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31989312597)
for the merge completed as cancelled without creating any jobs or pending deployments. No
environment approval was granted, no credential was exposed, and no registry contact or package
mutation occurred.

The independent reviewer returned PASS at exact head
`5b3ceda9647ee50ec473e8b26c31f4cbc6e59836` with non-binary diff SHA-256
`dc328bd62d756e402bd73e161bb68dea0543585fb65e5b2298cdea9214081032`. It
independently reproduced 356/292/64 at the base and 0/64/0 at the head, 135/135 changed paths as
first-party, zero changed paths beneath `.source.json`, 63/63 repository mirrors and 58/58 live
scoped mirrors excluded, zero version deltas, 20 shell blocks syntax-valid, and the provenance
open-then-unlink refusal. Greptile review `4948039277` was checked at the exact head; the free trial
had ended, so it was recorded as unavailable rather than PASS.

A local `pnpm run verify` retry was interrupted by host `ENOSPC` while writing a generated catalog;
the interrupted worktree change was restored exactly and stale detached review worktrees were
removed. This was an infrastructure interruption, not represented as a pass. The exact-head CI
`verify` job succeeded, and all focused local and post-merge commands above passed.

## Merge topology and follow-up

GitHub still required one human approval after executable gates and independent review passed. The
owner authorized administrator bypass, and the [disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1218#issuecomment-5311182556) was posted before merge. This is a temporary review-topology compromise, not Epic 10 independent certification; no rule changed.

The next-candidate audit found no Epic 1–3 bead that is both unblocked and non-overlapping. E1.7 is
the highest-priority candidate after PR #1149 is dispositioned and its six-versus-ten generated
artifact population is remeasured; E1.8 depends on that work. This AAR closes only E1.13, leaves the
Epic 1 parent open, and activates no later bead.
