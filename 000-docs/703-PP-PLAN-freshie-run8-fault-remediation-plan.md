<!-- doc-class: record -->

# Freshie Run-8 Fault-Remediation Plan

**Doc:** 703-PP-PLAN · **Date:** 2026-07-10 · **Author:** Jeremy Longshore (Backlog Zero sweep)
**Ground truth:** Freshie inventory run 8 — commit `5bb105f72`, tree `129f92001` (post #1008/#1009/#1010 merges) · runs 6/7 preserved byte-identical
**Fulfills:** the deep-dive + remediation-plan child of the Freshie rerun epic (GH-adjacent record; beads tracker is source of truth)

---

## 1. Run-8 headline

| Metric                               | Run 7               | Run 8                 | Δ                                     |
| ------------------------------------ | ------------------- | --------------------- | ------------------------------------- |
| Skills graded                        | 3,713               | 3,681                 | −32                                   |
| A / B / C                            | 954 / 1,505 / 1,048 | 1,013 / 1,424 / 1,027 | A +59                                 |
| D / F                                | 195 / 11            | 197 / 20              | F +9                                  |
| Marketplace-tier errors (skill rows) | 9,076               | 9,001                 | −75                                   |
| `is_stub` flags                      | 99                  | 111                   | +12                                   |
| Agents graded                        | 322                 | 345                   | +23 (hyperflow mirror first-mirrored) |
| Plugins discovered                   | 398 rows            | 456                   | catalog grew                          |

Production-ready (A+B): **66.2%**, avg score 83.7.

## 2. The load-bearing split: internal vs external

**D+F = 217 skills → 204 external mirrors (94%) · 13 internal (6%).** All 20 F-grades are external; internal has **zero F**. External sources contribute 37.5% of all errors from 9.8% of the corpus.

- **External D+F mass:** tonone 128 (curated-frozen — lever is upstreaming, per 694-AT-DECR), portaljs 12, hyperflow 10, wondelai family 23 one-skill plugins, long tail of singletons.
- **New-F wave (11→20) is portaljs onboarding, NOT hyperflow.** 12 of 13 new Fs are portaljs skills that entered the corpus at run 8 (scores 53–56, 13–14 errors each; every one defers to a `.claude/commands/*.md` file absent from the mirror — dangling pointers). Hyperflow _improved_ (F 4→3) — the unfreeze did not regress grades.
- **Internal D list (complete, 13 skills):** ga4-pack ×3, algolia-pack ×4, miro-pack ×2, attio-pack ×2, apify-pack ×1, adobe-pack ×1 — all scores 67–69, 3–7 errors each.

**Hand-read verdict on the internal 13: every one is FIX, none is DROP.** Each is a substantial, technically accurate skill (244–333 lines, current SDKs) whose D grade comes from one shared v1-template gap — the same 3 missing marketplace-tier required body sections. No deletions needed on the internal side; npm one-way-door checks therefore moot for this wave.

## 3. Wave A — batch-remediate the internal auto-fixables (530 skills)

843 skills miss ≥1 required frontmatter field. The **strictly auto-fixable cohort is 530 — all internal, zero external**:

- 500 = `tags`+`compatibility` missing, spread exactly 25-per-dir across the 20 legacy `skills/01-*`…`20-*` directories.
- 30 = `compatibility`-only in `plugins/saas-packs/skill-databases/`.

Mechanics (run in this order):

1. `freshie/scripts/batch-remediate.py --dry-run` first, **path-scoped to the internal dirs** (the fixer must not touch sources.yaml target_paths).
2. `--execute` writes SKILL.md frontmatter only.
3. ⚠️ **Known-broken fixer:** `--fix-compatible-with` is stale — its DB-mode query matches zero run-8 rows (gaps are recorded as `compatibility` now) and its no-db mode writes the _deprecated_ `compatible-with` field. Use the tags/compatibility writers + chain `scripts/batch-remediate.py --migrate-compatible-with` afterward; fixing the fixer is beaded.
4. Re-validate + freshie run 9 to confirm the 530 clear.

The other 312 metadata-missing skills are external mirrors → Wave C, never batch-remediate.

## 4. Wave B — hand-fix the 13 internal D skills

One-pack-a-day cadence (the epic's step 3): ga4 → algolia → miro → attio → apify → adobe. Fix = add the 3 missing required body sections per skill (same template gap everywhere); effort S per skill. Read-first discipline held: verdicts came from reading every file, not the grade column.

## 5. Wave C — mirror posture for the 204 external D/F (never local `rm`)

Levers, per 694-AT-DECR (sync re-mirrors anything deleted locally):

- **portaljs (12 F):** raise the dangling-pointer defect upstream (their skills reference un-mirrored `.claude/commands/`); either upstream ships the commands, our include list adds them, or the entry gets `verified: false` pending fix. Friendly-issue-first protocol.
- **tonone (128 D+F):** stays `curated: true` frozen; the planned upstreaming is the only path that reduces this mass.
- **wondelai family (23):** already flipped `verified: false` (2026-07-08 census PR); no further action until upstream moves.
- **hyperflow upstream agents (22 of the 36 error-carrying agents at run 8):** first-mirrored at run 8 via the #1008 include-list extension — nothing regressed; upstream agents are simply 3-field frontmatter. Same playbook that worked for their skills (upstream merged our uplift in <1 day): friendly issue offering the agent-frontmatter uplift PR. Jeremy signs off on wording before posting.
- Remaining error-carrying agents: sugar ×3 (banned `type` field), singletons ×6 → note on the weekly sync review; **4 internal offenders are the x-bug-triage agents synced from Jeremy's own `x-bug-triage-plugin` repo** (missing color/version/author/tags) — fix at the source repo, beaded.

## 6. `is_stub` — still not a delete trigger (recorded)

Run-8 sample verification: **~60% false-positive** (8 FP / 7 genuine in a 15-sample read; extrapolated ≈67 FP / 44 genuine of 111). Better than run 2's 92% FP, still unusable for deletion. FP mechanisms are structural: `references/` content not counted, curated router/dispatcher skills flagged (tonone — the delete-class disaster), template payloads under `*/templates/**` flagged, and a bogus "no code blocks" signal; several flagged rows are simultaneously graded A in the same run.

**Genuine stub concentrations (hash-verified template stamping):** wispr-pack 16, stackblitz 8, veeva 6, together 2 — byte-identical Instructions blocks within each pack. These go through Wave-B-style read-and-fix-or-drop per pack (npm publish history checked before any drop; catalog-entry → `sync-marketplace` → cowork validate → files, in that order, or the drift gate fails the build).

**Proposed deterministic criterion** (not implemented; bead filed): flag only when (a) normalized body hash shared by ≥3 skills in one pack, or (b) body defers to an in-plugin path missing on disk; count `references/**` toward content; exempt `*/templates/**`; forbid `is_stub=1` on same-run A/B grades.

## 7. Catalog + pipeline hygiene (from the anomaly sweep)

- 4 duplicated catalog sources (claudebase ×3, geepers-agents ×2, dolt-mcp-vcs ×2, x-bug-triage ×2); 3 disk dirs missing catalog entries (general-legal-assistant, claude-memory-kit, saas-packs/claude-pack); `axiom` is a nested mini-marketplace discovery skips. The claudebase missing-entry loop is what the sync engine keeps auto-adding.
- **`forge_proofs` is EMPTY at run 8** — no JRig-Verified badge has data. The write path shipped in PR #1011 (#935 Unit 1); Unit 2's gated pilot populates the first ground-truth rows.
- `rebuild-inventory.py` hardcodes `REPO_ROOT` → unsafe from worktrees (bit us during run 8; retried with `--run-id 8`). Beaded.
- Duplicate-file clusters: 18, all benign intra-plugin layout mirrors. The run-1 mass-duplication era is gone.

## 8. Execution tracking

All waves live under the Freshie rerun epic in beads (plain-English titles; bd-sync mirrors). Scan rerun child: **closed with run-8 evidence.** Deep-dive/plan child: **closed by this doc.** Cadence child stays open and consumes Waves A→B→C in order; new children filed for: batch-remediate fixer repair, stub-criterion redesign, x-bug-triage upstream agent fix, portaljs upstream issue, hyperflow agent-uplift upstream issue, catalog dedupe/missing-entries, REPO_ROOT worktree safety.
