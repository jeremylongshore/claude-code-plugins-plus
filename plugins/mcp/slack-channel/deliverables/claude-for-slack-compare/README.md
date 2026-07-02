# "Claude for Slack" competitive content push — DRAFT deliverables

**Status: DRAFT-FIRST. Nothing here is published.** No `master` push, no Netlify deploy, no X/LinkedIn/Dev.to posting until Jeremy approves each artifact individually. Built 2026-06-30.

**Posture (Jeremy's steer):** *honest about what Claude Tag genuinely provides — as an offset — with vendor lock-in as the lens.* No FUD, no hit piece. Claude Tag's security model (isolated sandbox + Agent Proxy + deny-by-default egress) is genuinely strong; the wedge is **who owns the substrate (memory + audit)**, not "theirs is insecure." Every technical claim traces to CCSC/AGP code (Phase 0 dossier); external claims cite official Anthropic + Semantic Scholar sources.

**The thesis (one line):** *Claude Tag is the best agent you can rent. If the agent — and its memory and audit trail — must be yours and verifiable on your own infra, you host it (CCSC + AGP). Both legitimate; pick by who must own the substrate.*

---

## Deliverables (Jeremy's sequence)

### #3 — startaitools deep technical dive (the anchor)  ·  bead `ccsc-gmb`
Staged in the blog repo (NOT this dir), ready as a Hugo draft (`draft = true`):
- `~/000-projects/blog/startaitools/drafts/rent-the-agent-own-the-proof/index.md` — canonical Hugo post ("Rent the Agent, Own the Proof", ~2,000 words, S2 citations + references inline)
- `…/substack.md` — Substack variant  ·  `…/x-thread.md` — 10-post X thread  ·  `…/devto.md` — dev.to variant (`published: false`)

### #2 — compare/contrast report + HTML infographic  ·  bead `ccsc-3dp`
- `02-compare/comparison-report.md` — 4-way matrix (Anthropic-A / Anthropic-B / CCSC / AGP) + per-product pros/cons + "what only each side does"
- `02-compare/claude-for-slack-infographic.html` — **self-contained** dark-theme infographic (open directly in any browser; zero external resources)

### #1 — long-form X + LinkedIn (personal + company)  ·  bead `ccsc-wzt`
- `01-social/social-drafts.md` — long-form X post (+ optional thread), LinkedIn personal (operator voice), LinkedIn company (Intent Solutions)

### #4 — respectful AI Circle community response to Ben's video  ·  bead `ccsc-2r4`
- `04-ben/community-response.md` — credits Ben's framing (his 8 chapters, esp. "Second Brain in Slack"), adds the ownership/verifiability layer without knocking the video
- `04-ben/_ben-video-grounding.md` — what we recovered about the video (no verbatim transcript exists; metadata + chapter list + 2 verbatim lines only)

### Research (grounding — source of truth for claims)
- `_research/citations.md` — 18 Semantic Scholar / primary-source entries with arXiv IDs / DOIs (verified via S2 MCP)
- `_research/anthropic-facts.md` — verified Claude Tag facts + honest benefits (the "offset") + criticism, with sources

---

## Fact-check pass (done — PASS-WITH-FIXES, applied)
A fact-checker verified every load-bearing claim against the **live CCSC + AGP source** (30/30 confirmed with file:line) and spot-checked 7 arXiv citations (all resolved). Corrections applied across all artifacts:
- **CCSC fail-closed was an overclaim** → fixed. Only `upload_file` defaults fail-closed in CCSC (`policy.ts:360`); default-deny-by-construction is **AGP's** property. Every artifact now says so.
- **Nonce handshake was mis-attributed to CCSC's `require` HITL** → fixed. That nonce guards the admin `!restart` path (EchoLeak/T11); CCSC's `require` uses a reply-code + quorum + gate-drops-bot-messages. AGP's per-call approval keeps its (correct) `(messageId, sessionId)` nonce.
- **Agent-Proxy specifics hedged** to "per launch coverage" everywhere.
- **Person-quotes** (Gopinath, AlphaSignal) softened from unverified verbatim to attributed paraphrase; `agp verify` CLI string paraphrased (logic confirmed, exact output string unverified).
- Banned-term scan: **clean**.

## Before anything goes public (per-artifact gate)
1. **Jeremy reviews + approves each artifact.** These are drafts.
2. **Re-verify the one secondary-sourced claim:** the Agent-Proxy "credentials injected at network boundary / deny-by-default egress" detail is from launch coverage — now hedged as "per launch coverage" everywhere; re-confirm against `claude.com/docs/claude-tag` if you want it unhedged. (Flagged in `_research/anthropic-facts.md`.)
3. **AGP README reconcile (`ccsc-j39`)** — AGP's README says "composes the CCSC kernel" but its ADR ratified independent reimplementation (zero imports). Our copy correctly says "reimplements-and-hardens"; fix the AGP README (or accept the wording) before publish so a reader checking the repo doesn't see a conflict. **Positioning decision — your call.**
4. **Publish order:** #3 deep-dive first (so every social link resolves), then #2, #1, #4.
5. **Publish reality:** startaitools = Hugo → Netlify on push to `master` (flip `draft = false` first). Live cross-post = **Dev.to only**. Substack / X / LinkedIn / the AI Circle post = **manual** (copy from the draft files). Infographic = share the HTML / a screenshot.

## Honest-claims discipline (enforced)
- Never "tamper-proof / forensic-grade / compliance-grade" — only **"signed, offline-verifiable."** (Mirrors AGP's CI banned-terms scanner.)
- Own-stack limits are stated in every long-form piece (CCSC doesn't stop host-OS/same-UID compromise; bare chain doesn't stop truncation — that's AGP's job; AGP sandbox is namespace/cgroup not VM-grade; live Codex is provisional; B− test grade).
- AGP↔CCSC is **"reimplements-and-hardens"** — never "composes/depends on."
