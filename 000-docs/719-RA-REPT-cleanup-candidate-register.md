# 719-RA-REPT — Cleanup Candidate Register (Mission 01)

**Captured:** 2026-08-11 @ `4358a65a3` · **Machine-readable:** `719-RA-REPT-cleanup-candidate-register.json`
Disposition vocabulary: KEEP · UNTRACK · DELETE · DEDUP · COMMIT · REDACT-THEN-COMMIT · LEAVE-LOCAL · UNRESOLVED.
Nothing below is executed without the listed approval; this PR contains only rows 1, 2, and 2b.

## Executed in this PR (approved 2026-08-11)

| #   | Candidate                                                      | Size                 | Disposition                  | Guard / evidence                                        | Rollback     |
| --- | -------------------------------------------------------------- | -------------------- | ---------------------------- | ------------------------------------------------------- | ------------ |
| 1   | `freshie/archives/*.sqlite` (2 files)                          | 48.8 M raw (42 M du) | UNTRACK (files stay on disk) | `git grep 'archives/.*\.sqlite'` → zero consumers       | `git revert` |
| 2   | `000-docs/000-INDEX.md`                                        | —                    | CREATE (tracked estate)      | v4.4 mandatory; was absent                              | delete file  |
| 2b  | Five cited canonical governance docs (147, 685, 686, 687, 691) | 45 K                 | COMMIT (preservation)        | sha256 triple-verified; secret/sensitivity rescan clean | `git revert` |

## Approval-gated (each becomes a bead only on approval)

| #   | Candidate                                                                                                               | Size    | Proposed                                                             | Blocker                                    |
| --- | ----------------------------------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------- | ------------------------------------------ |
| 3   | `kobiton` Mach-O binary ×3                                                                                              | 35.4 M  | DELETE from tracking                                                 | plugin-owner check + licensing             |
| 4   | `marketplace/{src,public}/data` byte-dupe pair                                                                          | 28.46 M | DEDUP                                                                | build.mjs path trace                       |
| 5   | 4 uncatalogued plugin dirs (`general-legal-assistant`, `mcp/a2a-client`, `claude-memory-kit`, `saas-packs/claude-pack`) | —       | UNRESOLVED                                                           | investigate: WIP vs orphan                 |
| 6   | Loose `plugins/` root files (×3)                                                                                        | small   | UNRESOLVED                                                           | file-or-remove decision                    |
| 7   | tonone auto-gen `CLAUDE.md` in `curated:true` frozen mirror                                                             | 319 B   | DELETE                                                               | curated-exception approval                 |
| 8   | Untracked local `000-docs` corpus                                                                                       | —       | per-file (doc 720)                                                   | recovery-plan approvals                    |
| 9   | `.gitignore` 000-docs blanket+allowlist design                                                                          | —       | UNRESOLVED                                                           | redesign only after recovery plan settles  |
| 10  | `workspace/` ignored-yet-18-tracked conflict                                                                            | —       | UNRESOLVED                                                           | reconcile decision                         |
| 11  | `tests/RTM.md` dead reference                                                                                           | —       | FIX by Jeremy only                                                   | hash-pinned POLICY zone (AI edits refused) |
| 12  | Version drift (`intent-labs-pack`) + unwired `reconstruct-versions --check`                                             | —       | FIX bead                                                             | doc 723                                    |
| 13  | Freshie run-stamp inconsistency                                                                                         | —       | FIX bead (next dolt-sync re-stamps)                                  | doc 723                                    |
| 14  | Kernel pin `core@0.9.0` behind `0.10.0`                                                                                 | —       | KEEP (documented advisory breach; lockstep bump is its own decision) | —                                          |
| 15  | Legacy surfaces (`docs.anthropic.com`, `claude-3`, `claude-2`)                                                          | —       | KEEP → migration epic later (doc 725, GH #1146)                      | functional, never mechanical               |

Waste accounting at baseline: rows 1+3+4 ≈ 104 M of the 267.9 MB tracked payload (~39% by
stat-sum; ~34% against the earlier du-based total — both bases in doc 716).
