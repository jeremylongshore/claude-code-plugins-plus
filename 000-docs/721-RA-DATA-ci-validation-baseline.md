# 721-RA-DATA — CI & Validation Baseline (Mission 01)

**Captured:** 2026-08-11 @ `4358a65a3` · **Machine-readable:** `721-RA-DATA-ci-validation-baseline.json`
12 read-only diagnostics run with exit codes recorded faithfully (no `|| true`); working tree
verified byte-identical before/after the run. Required merge contexts remain
`ci-required` + `gitleaks` + `skill-conform`.

| Check                                          | Exit | Runtime | Baseline recorded                                                                                                                                  |
| ---------------------------------------------- | ---- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `validate-skills-schema.py --marketplace`      | 1    | 79.3 s  | **7,687 errors** (known corpus baseline); A+B 2,582 (70.2 %), C 896, D 193, F 9                                                                    |
| `validate-skills-schema.py --agents-only`      | 1    | 2.1 s   | **253 errors** — first recorded baseline for the advisory agent lane; contradicts the "all agents A-grade" claim in CLAUDE.md (crosswalk fix bead) |
| `validate-unicode-hygiene.py`                  | 0    | 15.7 s  | PASS default mode; U+200B advisories (strict-only) in one plugin                                                                                   |
| `check-catalog-format.py origin/main`          | 0    | 0.1 s   | catalog unchanged                                                                                                                                  |
| `check-internal-doc-links.mjs`                 | 0    | 0.8 s   | 1 unresolved = the known baseline of exactly 1                                                                                                     |
| `scan-synced-content.mjs`                      | 1    | 1.0 s   | 0 REFUSE / 63 CHALLENGE / 27 FLAG / 34 waived — designed full-corpus posture                                                                       |
| `check-submission-docs.mjs`                    | 0    | 0.6 s   | designed skip (no new plugin dirs)                                                                                                                 |
| `run-verification-pipeline.mjs --dry-run`      | 0    | 40.0 s  | no files modified; scores not computed in dry-run                                                                                                  |
| `packages/cli` `pnpm test`                     | 1    | 2.5 s   | **LOCAL-ENV failure**: vitest 2.1.9 `__vite_ssr_exportName__` collection error; CI green on main — environment divergence, not a code defect       |
| root `pnpm test`                               | 1    | 2.6 s   | first-fails at packages/cli (same root cause); downstream suites unreached                                                                         |
| `unittest tests.test_dolt_sync`                | 0    | 0.2 s   | 42 tests OK                                                                                                                                        |
| `unittest tests.test_validate_unicode_hygiene` | 0    | 0.8 s   | 8 tests OK                                                                                                                                         |

## Gaps recorded, deliberately not built/run

| Gap                                              | Why                                                                     |
| ------------------------------------------------ | ----------------------------------------------------------------------- |
| Python suite (39 test files)                     | no runner config (mixed unittest/pytest); decision: record, don't build |
| `actionlint` · marketplace production playwright | network-bound (webkit also unavailable on this box)                     |
| `pnpm run verify`                                | MUTATES (regenerates catalog) — `--dry-run` form used instead           |
| `analytics-daemon` / `analytics-dashboard` tests | stub `exit 0` / no test script — would test nothing                     |

Reproduce: re-run each command at the same HEAD and diff exit/counts against the JSON.
