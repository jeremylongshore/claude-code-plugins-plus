# Epic 1 Asset Integrity — After-Action Review

- **Date:** 2026-08-16
- **Authority:** Blueprint 727, Epic 1 beads 1.3 and 1.4
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Beads:** `claude-hz8f.2`, `claude-hz8f.7`
- **Implementation PR:** [#1216](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1216)
- **Base:** `90c7034293de859832ceca9514ccb5d61ee32b55`
- **Reviewed head:** `9120a8aa69539be052a118d7d239f82afd2e0d5f`
- **Merge commit:** `5910711bf64eb50a8c1bbe62996d850c1752cf43`
- **Merge method:** merge commit, with the disclosed owner-authorized administrator bypass
- **Status:** Implementation merged and post-merge verification passed; Bead closure follows this filing transaction

## Outcome

Curated promotion now uses one fail-closed content classifier in build and drift-check modes. It
recognizes governed binary formats by magic bytes, requires exact extension agreement, permits
extensionless ELF and Mach-O only, and validates all other files as complete UTF-8 streams without
NUL bytes. Symlinks, unreadable files, malformed content, contradictory extensions, and failed
`git ls-files` enumeration abort rather than silently entering or emptying the mirror.

The coupled corpus correction removed or truthfully renamed seven first-party placeholder assets
that carried `.png`, `.pdf`, or `.zip` names without matching bytes, updated their references, and
rebuilt the generated text-only mirror. No changed path had a `.source.json` ancestor. No mirrored
skill content, package manifest, version, workflow, registry, credential, contributor, Plane,
branch-protection, billing, or production state changed.

## Before and after

| Measurement                          |         Base |        Merged |
| ------------------------------------ | -----------: | ------------: |
| Governed binary-extension candidates |           48 |            36 |
| Extension/content mismatches         |           11 |             0 |
| Detector strategy                    | `nul_prefix` | `magic_bytes` |
| Detector fixed probes passing        |        false |          true |
| Detector misses                      |           11 |             0 |
| Curated skills                       |        1,915 |         1,915 |

Generated scorecard row 11 is `measured` with 36 candidates and zero mismatches. Row 12 is
`measured` with strategy `magic_bytes`, every fixed probe passing, and zero misses.

The candidate decrease is exact: eleven mismatched source/generated paths were removed or renamed,
and the genuine generated
`skills/.curated/optimizing-cloud-costs/assets/cost_report_template.pdf` was omitted because the
projection is text-only. Thus 48 minus 12 equals 36; the genuine source PDF remains untouched.

The seven corrected first-party source artifacts were:

- `versioning_diagram.png` → `versioning-diagram-brief.md`
- `model_architecture.png` → `model-architecture-brief.md`
- `owasp_logo.png` → removed in favor of the existing OWASP source link
- `api_template.zip` → `api-template-outline.md`
- `example_code_with_vulnerabilities.zip` → `vulnerable-code-examples.md`
- `requirements.pdf` → `ecommerce-api-requirements-example.md`
- `test_environment_diagram.png` → `test-environment-diagram-brief.md`

Four applicable generated curated copies accounted for the other four mismatches.

The final font correction follows the primary format distinction: `.ttf` accepts the TrueType
sfnt values `0x00010000` and `true`, while `typ1` is rejected because it identifies legacy
PostScript in an sfnt wrapper. The scorecard probe directly requires the production inspection
window constant, so a renamed or removed contract fails loudly instead of falling back to the old
8 KiB value.

## Evidence bundle

| Evidence item           | Result | Reproducing evidence                                                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution               | PASS   | Post-merge `pnpm run measure:e1:check` ran 36 tests and reported document 742 byte-exact; `python3 freshie/scripts/promote-to-curated.py --check` reported 1,915 skills in sync.                                                                                                                                                                                                                                             |
| Happy path              | PASS   | Genuine PNG, ZIP, TrueType, executable, UTF-8, and empty-file fixtures pass through the production predicate with the expected include/exclude result.                                                                                                                                                                                                                                                                       |
| Failure path            | PASS   | The committed legacy-detector fixture stays red; wrong extensions, `typ1` under `.ttf`, invalid UTF-8, a NUL after 64 KiB, symlinks, unreadable files, and failed Git enumeration are refused. The independent reviewer ran 35/35 hostile probes.                                                                                                                                                                            |
| Rollback                | PASS   | In a disposable worktree at the merge, `git revert -m 1 --no-commit 5910711bf64eb50a8c1bbe62996d850c1752cf43` produced staged tree `bc32b4308efe4fe367fb297451ec6ef545f76baa`, exactly the tree of base `90c7034293de859832ceca9514ccb5d61ee32b55`; the rehearsal was aborted and removed. In a governed rollback, revert this filing first so it does not claim behavior that the subsequent implementation revert removes. |
| Durable receipt         | PASS   | PR #1216, merge commit, scorecard 742, this AAR, Bead notes, and the independent-review digest form the governed receipt set.                                                                                                                                                                                                                                                                                                |
| Docs versus reality     | PASS   | `CHANGELOG.md` records full-stream validation, fail-closed Git enumeration, the seven first-party corrections, and the measured 11-to-zero result. The PR diff and post-merge commands agree.                                                                                                                                                                                                                                |
| Blueprint versus actual | PASS   | E1.3 and E1.4 landed as one explicitly coupled slice because the new gate correctly rejected the old corpus. Scope and acceptance behavior match blueprint 727; no later bead was activated.                                                                                                                                                                                                                                 |
| Reproduction first      | PASS   | Before correction, the strict gate exited nonzero on `model_architecture.png`; the legacy 8 KiB detector fixture remains an executable red proof.                                                                                                                                                                                                                                                                            |
| Vertical slice          | PASS   | Production classifier, build/check callers, corpus correction, generated mirror, measurement harness, scorecard, tests, and changelog landed together.                                                                                                                                                                                                                                                                       |
| Observed versus claimed | PASS   | Every numeric claim above was rerun after merge; no PR table or bot prose was accepted as evidence.                                                                                                                                                                                                                                                                                                                          |

## Validation and independent review

The exact reviewed head passed
[Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31972765948)
including `ci-required`,
[Secret Scan](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31972765944)
including `gitleaks`,
[Skill Conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31972765821),
[Check Markdown Links](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31972765808),
PR Pre-screen, and all
[MiniMax Code Review](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31972784269)
jobs. Local exact-head verification passed `pnpm run verify`, lint, typecheck, formatting, Ruff,
Actionlint, the audit-harness integrity check, 31/31 focused Python tests, and 36/36 Epic 1
measurement tests.

The independent reviewer used a clean detached checkout and returned PASS for head
`9120a8aa69539be052a118d7d239f82afd2e0d5f`, diff SHA-256
`5ecb7f121c9709b77a0182c83dca24057645d8347bc8651f01e752df8c993b02`. It independently obtained
31/31 focused tests, 35/35 hostile probes, 36/36 measurement tests, 6,014/6,014 manifest files
byte-identical to source, zero row-11 mismatches, zero row-12 misses, and zero changed paths beneath
provenance. Greptile was checked, but its free trial had expired; its notice contained no review and
was not counted as evidence.

This v4.4 filing appended document 748 to the public ledger, then ran
`node scripts/generate-docs-index.mjs`, staged that output, and ran `pnpm run measure:e1` against the
staged Git bytes. The index now covers 188 tracked documents. Scorecard rows 1 and 46 increase by one
tracked file, and row 44 increases by one indexed document. Row 46's `invisible_files` value also
increases by one because filed `000-docs/*.md` paths match an existing path expression in
`.gitleaks.toml`; it is a measured subset, not the complement of tracked files. Its
`allowlist_patterns` count measures the 25 `.gitleaks.toml` path expressions, not public-ledger
negations in `000-docs/.gitignore`, so that value correctly remains 25. Neither generated projection
was hand-edited; both check-mode commands reproduced the committed bytes exactly.

## Merge topology and lesson

GitHub still required one human approval after the executable and independent gates passed. The
owner authorized an administrator bypass for this merge, and the
[disclosure](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1216#issuecomment-5309741910)
was posted before merge. This is a temporary review-topology compromise, not independent GitHub
certification; no branch rule or approval policy changed.

A binary exclusion rule is trustworthy only when it proves both byte identity and extension
agreement and reads the entire prospective text stream. Generated projections also need to be
measured as their own cohort: omitting one genuine binary from a text-only projection is correct and
must not be confused with correcting a counterfeit source artifact. Epic 1 remains open, and this
AAR activates no later bead.
