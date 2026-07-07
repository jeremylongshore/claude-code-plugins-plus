# Marketplace legitimacy report — open PRs + Killer-Skill nominations

**Date:** 2026-07-07 · **Evidence basis:** required gates (`ci-required` + `gitleaks` + pinned validator + `scan-synced-content`) actually executed on every open PR (stalled `action_required` runs approved at latest heads; #960 given a fresh post-rebuild event via update-branch; #965 superseding sync dispatched). Nomination evidence gathered read-only from upstream HEADs via GitHub API. Nothing merged, no contributor-surface comments posted.

---

## Part 1 — Open PRs (5)

### Gate execution proof

| PR | head | ci-required | gitleaks | scan-synced-content | validator (`validate`) |
|---|---|---|---|---|---|
| #981 portaljs | `f4c54cab` | **FAIL** (scan only) | **PASS** | CHALLENGE ×1 | PASS |
| #983 llm-box | `bfaa6e71` | **FAIL** (format + scan) | **PASS** | CHALLENGE ×1 | PASS |
| #964 agent-safety-preflight | `d77a5d67` | **FAIL** (4 real findings) | **PASS** | CHALLENGE ×1 | **FAIL** (catalog churn) |
| #960 walkie-talkie | `79678fe2` (fresh event) | pending→fail | **PASS** | CHALLENGE ×1 | PASS |
| #965 bot sync | `2622c2da` (stale) | n/a | — | superseding run **REFUSE-blocked** | — |

The common `scan-synced-content` CHALLENGE on the three `feat(sources)` PRs is the **designed human-sign-off gate** (`sources-change-unscanned`): a source-list change requires a reviewed waiver line in `scripts/scan-allowlist.txt` after the 699 vetting checklist. That's the system working, not a defect.

### Verdicts

**#981 portaljs (datopian, 2,304★, MIT, pushed today) — LEGIT, one-line fix.**
The contributor's original entry had `include: 'license'` (lowercase — **correct**: upstream file is lowercase, no uppercase variant exists). Greptile's P1 suggestion claimed the opposite and the contributor applied it via web UI at `f4c54cab` → current head has `'LICENSE'`, which silently fails to match on the case-sensitive sync runner. **Greptile's applied "fix" introduced the exact bug it warned about**, and the thread is misleadingly marked resolved. Everything else verified: `.claude-plugin/` + `skills/**` resolve upstream, `verified: false` honest, all other gates green.
→ **Action: revert to `- 'license'` + add the vetted waiver line → merge.** Strongest source in the batch.

**#983 llm-box (alib8b8, 4★, MIT, active today) — LEGIT, two mechanical fixes.**
All 9 include globs verified to exist upstream; narrow include list (deliberately excludes `.grok-plugin/`, `contrib/` etc. — good sign); contributor made two corrective pushes same-day (moved the entry out of the `config:` block; dropped a wrong `marketplace.json` include). Remaining: `format-check` (prettier on sources.yaml) + the waiver line. `verified: false` correctly reflects thin adoption. Note: ships an `.mcp.json` → payload scanner gets its say at sync time.
→ **Action: prettier-format + waiver → merge.**

**#964 agent-safety-preflight (el-zachariah) — LEGIT code, needs 4 mechanical fixes + one maintainer call.**
Confirmed at head: **no SKILL.md anywhere** — plugin.json + one command + Python scanner + tests. All 7 substantive Greptile/Gemini security findings resolved with matching fix commits. CI found (all real, all small):
1. `ruff` E401 — `import argparse, json, os, re, subprocess` on one line (`agent_preflight_lite.py:4`)
2. `markdownlint` ×3 — MD031/MD032 blank-line issues in `commands/agent-preflight.md`
3. `validate` — catalog churn **+1,592 lines** for 1 added entry (a formatter pass rewrote `marketplace.json`'s load-bearing layout; must be reverted)
4. `scan-synced-content` CHALLENGE — **meta false-positive**: it flagged the plugin's own `curl|wget` *detection regex* as an outbound network call. The plugin makes no network calls. Narrow waiver.
→ **Action: request-changes with the concrete list** + Jeremy's call: accept commands-only (below the 8-field SKILL.md marketplace tier by design) or require a SKILL.md.

**#960 walkie-talkie (MulhamAnalytics → walkie-talkie-skill/walkie-talkie, 0★, 5 days old) — HOLD (upstream-blocked).**
Upstream SKILL.md frontmatter **provably unparseable** at HEAD `0b74f4d3` (`ScannerError` at the unquoted `Triggers:` in `description`). Jeremy's fix issue walkie-talkie#1: open, 0 comments, no push since repo-creation day. PR author ≠ upstream org (relationship unverified). Entry also missing `verified:` flag. Fresh-event CI: gitleaks/validate/format all PASS; scan = the standard sources CHALLENGE.
→ **Action: hold; one status comment (nudge #1, note the two gaps). Not merge-eligible until upstream YAML parses.**

**#965 bot sync PR — superseded-in-principle, blocked by a real catch.**
The superseding sync run (28886237377) was **hard-blocked by the supply-chain gate**: `plugins/community/mytradeledger-skills/…/mtl.py:52 [REFUSE] secret-exfil-cooccur` + 8 urllib CHALLENGEs, same file. Code review of upstream (`trpsbill/skills`, 0★, MIT): it's a **standard API client** — reads its own skill-local `.env` (`MTL_URL`/`MTL_TOKEN`) and sends the token as a Bearer header to its own configured service (default `https://mytradeledger.com`). Not exfiltration — dual-use pattern the scanner is rightly paranoid about.
→ **Action needed (Jeremy):** narrow waiver for mtl.py (recommended — reviewed, own-service client) **or** drop the source. Then re-dispatch sync → fresh PR auto-closes #965.

---

## Part 2 — Killer-Skill nominations (6)

| # | Repo | ★ | pushed | YAML | 8-field | Call |
|---|---|---|---|---|---|---|
| **833** | polyxmedia/mnemos | 20 | 07-02 | ✓ | **8/8** | **FEATURE-READY — W28** |
| 828 | nostrband/ServiceGraph | **68** | 06-02 | ✓ | 3/8 | Mirror + `curated:true` (fix staged: fork `skill-frontmatter-spec` @ `df4648a4`, 1 ahead, covers all 18 SKILL.md) |
| 834 | tonone-ai/tonone | 56 | 06-17 | ✓ | 6/8 | **Already curated on main** (`curated: true`, ~100 agents A-graded locally) — feature-viable now; upstream offer #107 still open, 0 response |
| 830 | lemondepat/schedule-after-usage-reset | 1 | 05-23 | ✓ | 2/8 | Fix staged (fork @ `a83ea165`) — but 1★, upstream dead since day one. Editorial: weak feature candidate |
| 829 | ggrigo/align | 0 | 07-02 | ✓ | 2/8 | Park/decline — author iterates (0.5.3→0.8.2) but zero adoption, stub frontmatter |
| 832 | rhinehart514/founder-os | 3 | 05-25 | **✗ root parse FAIL** | 4/8 | **Decline-with-invite** (broken as shipped, idle upstream) — same treatment as #831 |

**Hygiene (confirmed):**
1. Three outreach artifacts silently self-closed 2026-07-07 ~02:16 UTC with **zero maintainer engagement ever**: `ServiceGraph#2` (not_planned), `schedule-after-usage-reset#2` (not_planned), `tonone#108` (PR, closed unmerged). Nominations #828/#830/#834 still link them as live → each needs a one-line status note.
2. The #830 triage claim "YAML parse break" **does not reproduce** at upstream HEAD (parses clean; upstream unchanged since 05-23) — triage record needs correcting.
3. tonone now has **616** SKILL.md files upstream (triage said 402).

**Recurring gaps across the pool** (feeds the submission standard): missing `compatibility`+`tags` (5/6), missing `author`/`license`/`version` (4/6), YAML breaks from unquoted colon-bearing descriptions (founder-os live; walkie-talkie in the PR queue; #831 rejected for same).

---

## Part 3 — Decisions needed

1. **#981 + #983:** push the tiny fixes to contributor branches ourselves (`maintainerCanModify: true` on both) + vetted waiver lines, then merge — or comment and wait. (Recommend: push + merge; credit the contributor in the merge message.)
2. **#964:** accept commands-only plugin (no SKILL.md, below marketplace tier by design) or require a SKILL.md in the request-changes ask?
3. **mytradeledger REFUSE:** narrow reviewed waiver (recommend) or drop the source? Unblocks all future syncs either way.
4. Contributor-surface comment drafts (#964 request-changes, #960 status note, 3 nomination status notes) follow for wording sign-off per AGENTS.md.

---

## Part 4 — Outcomes (same day, 2026-07-07)

Applied after Jeremy's checkpoint approval (push-fixes-and-merge / require-SKILL.md / resolve-the-REFUSE):

| Item | Outcome |
|---|---|
| #981 portaljs | **MERGED** `c70f4388` — casing reverted to upstream's lowercase `license`, vetting waiver, full gate green |
| #983 llm-box | **MERGED** `87d006ea` — prettier fix + main merged in (conflict resolved), full gate green |
| #987 sources hygiene | **MERGED** `d6d307ee` — REFUSEd mytradeledger removed (rule-fidelity gap, not malware; #985 defect 1), mnemos W28 pinned mirror added (#833), waiver line swapped |
| #964 preflight | Request-changes drafted (4 mechanical fixes + require SKILL.md per maintainer call) — awaiting wording sign-off |
| #960 walkie-talkie | Hold note drafted — upstream YAML still unparseable; awaiting wording sign-off |
| #965 bot sync | Still open — superseding sync (run 28889050755) cleared the REFUSE but hit the **first lock-baseline reconcile**: 39 pure-mirror sources drift-quarantined by sources.lock.json (#968 working as designed; sync stalled for weeks so upstreams legitimately moved). Relock decision pending |
| Gate defects | Filed as #985 / four beads: own-service REFUSE fidelity, REFUSE-walls-sync, waiver persistence, prescreen path filter |
| Submission standard | PR #986: templates/skill-docs/ ×4 + tier→docs matrix + issue-before-PR intake + 000-docs/700 + CONTRIBUTING sections |
| Backlog | #789–794 collapsed under #795 (decision 2026-08-04); dispositions on #935/#859/#796/#938; #941's 15 policy calls surfaced |
