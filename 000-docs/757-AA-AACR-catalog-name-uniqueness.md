# Catalog Name Uniqueness — After-Action Review

- **Date:** 2026-08-17
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.2
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hz8f.12`
- **Implementation PR:** [#1235](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1235)
- **Base:** `48894e82d31f8bc160d3157d299e675c538ca0a7`
- **Reviewed head:** `97f9bb05060b85400035186c6ac653b76d6daabd`
- **Merge commit:** `637bfbbcddb0e81db962b08798dca3dca2dc5f13`
- **Merge method:** merge commit with disclosed, owner-authorized administrator bypass
- **Status:** implementation merged and post-merge verified; Bead closes after this filing lands

## Outcome

The canonical marketplace catalog moved from 471 rows and 467 distinct names to 467 rows and 467
normalized identities. Three redundant `claudebase` rows and one duplicate `geepers-agents` row
were removed. The retained Geepers record preserves its richer contributor and component metadata
and incorporates the non-conflicting upstream homepage and repository fields from the removed row.
Both source-owned catalogs and the generated README navigation now agree on 467 plugins.

The existing catalog invariant validator now fails closed on duplicate names after trimming and
Unicode case folding. It also refuses empty, non-string, and non-object catalog rows. The rule is
source-side: `.claude-plugin/marketplace.extended.json` owns canonical catalog identity, while
`.claude-plugin/marketplace.json` and README are regenerated projections. E1.8 consumes this clean
source but remains a separate four-projection drift-gate bead, currently complete for 2/4 outputs.

No plugin, skill, `.source.json`, mirrored content, registry, credential, contributor, Plane,
branch-protection, release, or production state changed.

## Evidence bundle

| Evidence item           | Result | Reproducing evidence                                                                                                                                                      |
| ----------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution               | PASS   | `python3 scripts/validate-catalog-invariants.py` reports `Catalog invariant check passed (467 plugins).`                                                                  |
| Before/after            | PASS   | Base: 471 rows / 467 exact names (`claudebase` ×4, `geepers-agents` ×2). Merge: 467 rows / 467 trimmed, case-folded identities and zero duplicates in both catalog files. |
| Happy path              | PASS   | `pnpm run sync-marketplace` produced byte-current `.claude-plugin/marketplace.json` and README output on two consecutive runs.                                            |
| Failure path            | PASS   | `python3 -m unittest tests.test_validate_catalog_invariants` passed 8/8 fixtures for malformed rows and exact or normalization-equivalent duplicates.                     |
| Red proof               | PASS   | An independently planted whitespace/case-equivalent duplicate exited 1 and named the duplicate identity.                                                                  |
| Measurement             | PASS   | Post-merge `TMPDIR=/dev/shm pnpm run measure:e1:check` passed 37/37 and reported scorecard 742 byte-current.                                                              |
| Generated gates         | PASS   | Post-merge generated-artifact validation passed 14/14; generated-content validation passed 4/4 and 3,068/3,068 skills with both gated skill projections byte-current.     |
| Provenance boundary     | PASS   | The complete eight-file implementation diff contains zero `plugins/`, `skills/`, `SKILL.md`, or `.source.json` changes.                                                   |
| Durable receipt         | PASS   | PR #1235, exact-head reviews, bypass disclosure, merge SHA, Bead notes, scorecard 742, CHANGELOG entry, this AAR, and the public filing ledger form the receipt.          |
| Docs versus reality     | PASS   | Blueprint 727, CHANGELOG, both catalogs, README, validator, tests, and scorecard row 2 agree on the 467/467 result.                                                       |
| Blueprint versus actual | PASS   | E1.2 owns canonical deduplication and name uniqueness; E1.8 remains responsible for deterministic projection rendering and drift checks.                                  |
| Rollback                | PASS   | Revert merge `637bfbbcdd`, run `pnpm run sync-marketplace`, then rerun catalog invariants, generated gates, and `measure:e1:check`. No external rollback is required.     |

## Validation and review

Exact head `97f9bb05060b85400035186c6ac653b76d6daabd` passed all three required contexts:
`ci-required`, `gitleaks`, and `skill-conform`. The same SHA passed every Validate Plugins job,
link checking, PR Pre-screen, Actionlint, formatting, Ruff, security scanning, generated-content
validation, CLI smoke tests, the regular MiniMax review, and the MiniMax A-grade coach.

[Greptile reviewed the exact head](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1235#issuecomment-5320180196)
at confidence 5/5 and reported no blocking failure. Its earlier P2 finding—that exact string counting
allowed case- and whitespace-equivalent identities—was corrected before the final review. There
were zero unresolved review threads.

An independent non-implementing reviewer worked from a fresh detached checkout at the exact base
and head and returned **PASS**. It independently reproduced 471/467 to normalized 467/467, verified
the retained source paths and merged Geepers metadata, passed 8/8 fixtures, planted its own refused
duplicate, ran two byte-identical syncs, passed the 37/37 measurement and both generated gates,
confirmed zero content-scope edits, and proved rollback produced the exact base tree.

The MiniMax adversarial provider was cancelled at its ten-minute boundary on two attempts without
returning a finding or verdict. It is recorded as unavailable, not as PASS. The independent hostile
review and Greptile exact-head review provide separate adversarial evidence.

GitHub still reported `REVIEW_REQUIRED` because the documented independent-human approval topology
remains unavailable. The owner-authorized
[administrator-bypass disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1235#issuecomment-5320498647)
was posted before merge. No branch rule or required context changed.

## Operational notes and follow-up

The repository-wide `pnpm test` still reproduces the pre-existing unchanged CLI/Vite transform
failure, `__vite_ssr_exportName__ is not defined`, before collecting two CLI suites. No CLI file was
in the implementation diff; targeted tests and hosted test shards passed. A local `quick-test` run
completed build and lint before ignored build output exhausted the constrained host root. Those
generated outputs were removed, the tracked tree was restored exactly, and hosted exact-head CI
provided the complete repository gate.

Close `claude-hz8f.12` with `bd-sync close` after this filing is merged and independently verified.
Then resume `claude-hz8f.11` at 2/4 deterministic projections, implementing only `catalog.json`
before the final `unified-search-index.json` slice. Do not cherry-pick the preserved exploratory WIP
wholesale; it predates the E1.2 authority split and contains superseded renderer decisions.
