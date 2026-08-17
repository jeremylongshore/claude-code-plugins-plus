# 726-AA-AACR — Mission 01 After-Action Review: Repository Cleanup Baseline

**Mission window:** 2026-08-11 → 2026-08-12 · **Baseline HEAD:** `4358a65a3` · **PR:** #1174

## What shipped

- **Category-1 cleanup:** untracked `freshie/archives/*.sqlite` (48.8 MB raw; zero consumers,
  files retained on disk) and closed the `.gitignore` gap that admitted them.
- **Preservation:** five cited canonical governance records (147, 685, 686, 687, 691) moved from
  dev-box-only into the tracked estate — sha256 triple-verified, secret/sensitivity rescan clean.
- **Baseline deliverables:** docs 716–725 (+ machine JSON) — repo state, estate inventory,
  source-of-truth tiers, cleanup register, doc crosswalk, CI baseline, duplicate/orphan,
  version drift, security findings, legacy-migration inventory.
- **Governance:** `000-docs/000-INDEX.md` created (mandatory per doc-filing v4.4; absent since
  the standard's adoption). Two governance records republished in sanitized form (681, 684)
  with citations resolving unchanged.

## Headline findings

1. **The documentation estate was majority-invisible.** 200 of 343 on-disk `000-docs` files were
   gitignored-untracked — including records cited by root `CLAUDE.md`. Mechanism: the
   `.gitignore` negation rules sit _above_ the blanket `000-docs/**` ignores, so last-match-wins
   renders the entire allowlist structurally dead. Every doc filed since the 2026-05 sweep landed
   local-only. (Register row 9 owns the redesign.)
2. **Credential incident (remediated).** The untracked-docs sweep found live credentials in
   local-only documents; pickaxe analysis confirmed one credential class had been present in
   public git history since 2025-10 (introduced in root-level migration notes, tree-removed
   2025-10-23 but never history-removed). Response: rotation confirmed 2026-08-12, local
   redaction completed (13 occurrences, 4 files, zero-hit verification), no history rewrite
   (values dead post-rotation). Detection-gap lesson: structured-secret scanners (gitleaks:
   0 findings across 1,595 commits) cannot see free-prose credentials — content-level sweeps of
   docs directories are now standing practice.
3. **Advisory-lane baseline established.** First recorded numbers for previously-unbaselined
   gates: agents-only validator 253 errors (contradicting the "all agents A-grade" claim in
   CLAUDE.md — doc-drift fix pending); marketplace validator 7,687 (known); scan-synced
   0 REFUSE / 63 CHALLENGE / 27 FLAG.
4. **Local-env divergence recorded, not concealed:** `packages/cli` vitest fails locally
   (`__vite_ssr_exportName__`, vitest 2.1.9 transform artifact) while CI is green on main.

## Corrections made mid-mission (honesty log)

- `git commit -- <pathspec>` silently reverted staged `rm --cached` deletions (pathspec commits
  working-tree state); caught on verification, amended from the index.
- A local repro of the markdownlint gate swept untracked files and briefly pulled an untracked
  local research doc into a fix-up commit; caught before the push stood, removed, disclosed in
  the commit body. Lesson: reproduce CI failures against _tracked_ state only.
- Tracked-bytes total was quoted on two measurement bases (du-block vs stat-sum); both recorded
  in doc 716 so future baselines diff cleanly.

## Exit-gate verdict

Independent review (separate agent, adversarial): **PASS — 8/8 checks, zero blocking findings (reviewer: separate agent, adversarial brief; manifest set-equality, hash triple-match, index 163/163 cross-check, baseline metrics reproduced exactly, secret-pattern scan of all 1,827 added lines = 0 hits)** — per-item results recorded in
the reviewer transcript and summarized on the mission epic bead. Deferred dispositions live in
register doc 719 (rows 3–15) as approval-gated follow-up beads.

## Numbers

22,963 tracked files → -2 sqlite +21 docs · index 163 entries at merge (166 after this filing) ·
16-bead mission DAG, acyclic, every bead closed with evidence · 12 read-only diagnostics, all
exit codes recorded, tree verified unmutated.
