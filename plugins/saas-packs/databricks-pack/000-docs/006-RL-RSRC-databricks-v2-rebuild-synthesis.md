# Databricks Pack — Rebuild Synthesis

**Inputs:** 4 parallel research deliverables (`databricks-pain-domain{1,2,3}-*.md` + `skill-architecture-patterns-2026.md`)
**Synthesis date:** 2026-05-27
**Status:** Design memo for Phase 2 — pre-build, design-time judgment calls live here

---

## 1. What the research actually found

**34 citation-grounded pain entries** across three domains. Every entry includes verbatim error messages, version context, and a recommended Claude Code primitive shape.

| Domain | Entries | Pain center of mass |
|---|---|---|
| 1 — Compute / Photon / DBR / Cost | 12 | Cost surprises (4), DBR version upgrades (3), Photon misuse (1), cluster lifecycle (4) |
| 2 — Delta / Liquid Clustering / Streaming / DLT | 12 | Design-decision class (9 of 12), platform-bug-adjacent (2), platform bug (1) |
| 3 — UC / Asset Bundles / SCIM / Networking | 10 | UC migration (3), Asset Bundles immature tooling (3), identity (1), CMK/networking/billing access (3) |

**10 architectural patterns documented** (AP01-AP10) from Anthropic's own first-party plugins — primary reference is the `security-guidance` plugin (v2.0.0, David Dworken / Anthropic) which demonstrates 6 of the 10 in one shipped surface.

---

## 2. Cross-cutting findings that drive the rebuild

### Finding 1 — MCP server is foundational, not optional

Two independent research agents (Domains 1 and 3) converged on the same conclusion from different pain clusters: **15-20 of the 34 pains require live access to the Databricks Workspace API and `system.billing.usage`** for diagnostics that the agent cannot do from static knowledge.

Implication: **build ONE shared MCP server first — `databricks-workspace-mcp` — and have every skill consume it.** Don't bundle one MCP server per skill; that's the wrong granularity. The MCP server is package-level infrastructure.

Endpoints the MCP server must wrap (derived from pain entries that need them):

- `clusters.list`, `clusters.get`, `clusters.events` — cluster forensics (D01, D06, D10)
- `sql.queries.history` + execution-plan JSON — Photon audit (D02)
- `jobs.list`, `jobs.get`, `jobs.runs.list` — cost attribution + run forensics (D07, D11)
- `pipelines.get`, `pipelines.get_event_log` — DLT diagnostics (D08, D09, D11)
- `system.billing.usage` query proxy — cost audit (D02, D07, D08, D11, D12)
- `system.streaming.query_progress` query proxy — streaming diagnostics (D03, D04, D12)
- `instance_pools.list` — idle waste detection (D09)
- `external_locations.list`, `storage_credentials.list` — UC governance (D2 in domain 3)
- `account.metastores.systemschemas` write — billing access remediation (D10 in domain 3)

### Finding 2 — Pain TYPE determines skill MODE

Domain 3 surfaced the sharpest cross-cutting distinction:

- **Immature-tooling pain** (e.g. Asset Bundles) → response is detection + safe-fallback workflows + hooks that catch broken states
- **Design-constraint pain** (e.g. UC single-metastore-per-region) → response is decision-support **at design time**, before the constraint locks in
- **Design-decision-surprise pain** (e.g. Photon billing model, Liquid Clustering writer-conflict semantics) → response is friction-at-trigger-time (PreToolUse hooks) + education in `references/`
- **Platform bug class** (e.g. checkpoint corruption) → response is monitoring + guided recovery playbooks

A skill targeting the wrong pain mode produces fluff. The current `databricks-pack` mostly targets design-decision-surprise pain with documentation, when much of it actually wants friction-at-trigger-time hooks.

### Finding 3 — Hook usage should be selective, not default

The architecture teardown found Anthropic itself avoids `PreToolUse` blocking and prefers `PostToolUse` + asyncRewake (their security skill is "best-effort assistive, not a guarantee"). For Databricks, this means:

- **Use PreToolUse blocking ONLY** where the action is genuinely irreversible — drop of streamed-from table (D12), VACUUM that crosses retention for an active reader (D07 domain 2), CREATE OR REPLACE on a table with active streaming consumers, IAM role deletion under a UC storage credential (D2 domain 3). These are the cases where Anthropic would also block.
- **Use PostToolUse + retry** for known-transient deploy failures (D6 domain 3 — bundle deploy grant-ordering retry).
- **Use SessionStart** to surface latent issues without interrupting flow (D03+D04 — streaming checkpoint health, D5 domain 3 — bundle state-file canary).
- **Avoid hooks entirely** for diagnostics the user explicitly invokes (Photon audit, cost audit, cluster forensics) — those are slash-command territory.

### Finding 4 — Subagents only where parallelism shortens wall-clock time

Of the 34 pains, only ~5 genuinely benefit from subagent fanout (D01 / D06 cluster triage, D02 domain 2 MERGE rewriting, D1 / D10 domain 3 UC migration planning + permission tracing). Most diagnostics are sequential API calls that subagents don't speed up.

---

## 3. Skill clustering proposal — fewer, deeper skills

Current pack: **24 flat skills, all the same shape.** Proposed rebuild: **6-8 skills clustered by problem-mode + primitive-mix.**

| Proposed skill | Pains covered | Primary primitives | Demo angle |
|---|---|---|---|
| `databricks-cost-leak-hunter` | D02, D07, D08, D09, D11, D12 (domain 1) + D11 (domain 2) | MCP (system.billing.usage), scripts, slash command, scheduled subagent | "Here's $4,200/mo in idle pool VMs you didn't know about" |
| `databricks-cluster-forensics` | D01, D06, D10 (domain 1) | MCP, subagent fanout, scripts, PostToolUse hook (optional) | "Why this cluster took 28 min to start — broken down by event class" |
| `databricks-dbr-upgrade-advisor` | D03, D04, D05 (domain 1) | MCP, scripts, references (deep version matrix) | "Here's every break point between your current DBR and 15.4 LTS" |
| `databricks-streaming-guardian` | D03, D04, D05, D08, D09, D10, D12 (domain 2) | PreToolUse + SessionStart hooks, MCP, scripts | "Blocked a CREATE OR REPLACE that would have killed 3 active streams" |
| `databricks-delta-conflict-resolver` | D01, D02, D06, D07 (domain 2) | PreToolUse hook on OPTIMIZE/VACUUM, scripts, references | "MERGE rewriter that adds the clustering-key predicate so writers don't conflict" |
| `databricks-uc-migration-pilot` | D1, D2, D3, D10 (domain 3) | Subagent, scripts, references, slash command | "Here's why 47 of your 200 HMS tables were silently skipped, and the fix per class" |
| `databricks-bundle-medic` | D4, D5, D6 (domain 3) | PreToolUse + PostToolUse hooks, references | "Detected state-file corruption pre-deploy; preserved last known good" |
| `databricks-identity-secrets-ops` | D7, D8, D9 (domain 3) | MCP (SCIM bridge), scripts, slash command (CMK rotation runbook) | "Drained workspace for CMK rotation in 12 min with zero data loss" |

**Plus the shared foundation:** `databricks-workspace-mcp` (the MCP server, consumed by all eight skills).

That's **8 skills + 1 MCP server = 9 artifacts**, replacing 24 current skills. **Each one earns its existence** by mapping to a named cluster of pains with citations.

---

## 4. Delete list — what gets cut from the current pack

These current skills do not survive the rebuild bar (no real pain mapping, hello-world-tier content, or fully subsumed by a new skill):

| Current skill | Reason to cut |
|---|---|
| `databricks-hello-world` | Confirmed by user — documentation cosplay |
| `databricks-install-auth` | Just wraps `databricks configure --token`; one-line setup, not a skill |
| `databricks-local-dev-loop` | Subsumed by `databricks-bundle-medic` once Asset Bundles is the canonical local dev surface |
| `databricks-core-workflow-a` and `-b` | Generic — no specific pain cluster |
| `databricks-sdk-patterns` | SDK ergonomics is library documentation, not a skill |
| `databricks-prod-checklist` | Checklists belong in `references/`, not as a top-level skill |
| `databricks-security-basics`, `databricks-enterprise-rbac` | Subsumed by `databricks-uc-migration-pilot` + `databricks-identity-secrets-ops` |
| `databricks-rate-limits`, `databricks-webhooks-events` | No corresponding pain in the catalog. Either find evidence they hurt or cut. |
| `databricks-common-errors` | Subsumed — every new skill carries its own error catalog in references/ |
| `databricks-debug-bundle` | Subsumed by `databricks-bundle-medic` |
| `databricks-reference-architecture` | Architecture doc, not a skill — moves to `references/` shared pack-level |
| `databricks-multi-env-setup` | Subsumed by `databricks-uc-migration-pilot` (env isolation patterns from D3 domain 3) |
| `databricks-ci-integration` | Generic. Cut unless a real CI-Databricks pain surfaces. |
| `databricks-deploy-integration`, `databricks-migration-deep-dive` | Replaced by `databricks-bundle-medic` and `databricks-uc-migration-pilot` respectively |
| `databricks-data-handling` | Too vague. Cut. |

**Surviving from current pack (rebuilt, not just renamed):** `databricks-performance-tuning` (becomes part of `databricks-cost-leak-hunter` + `databricks-cluster-forensics`), `databricks-incident-runbook` (becomes the operational spine of `databricks-cluster-forensics` + `databricks-streaming-guardian`), `databricks-observability` (becomes the SessionStart-hook surface inside `databricks-streaming-guardian`), `databricks-upgrade-migration` (becomes `databricks-dbr-upgrade-advisor`), `databricks-cost-tuning` (becomes `databricks-cost-leak-hunter`).

**Net deletion: ~15 of 24 skills cut, ~5 absorbed/rebuilt, ~4 spirit-of survives in new clusters.**

---

## 5. Pilot recommendation — start with `databricks-cost-leak-hunter`

Of the eight proposed skills, the highest-leverage pilot is **`databricks-cost-leak-hunter`**. Reasoning:

1. **Demo visceral.** Output is a dollar figure: "Your workspace is leaking $X,XXX/month — here's where." Audience response is immediate.
2. **Single MCP integration** (`system.billing.usage` + `clusters.list` + `instance_pools.list`) — proves the MCP-server-as-foundation pattern without sprawling across 5 API surfaces.
3. **No production-risk operations** — all reads, no writes. Safe to demo live on Luciano's stream.
4. **Universal.** Every Databricks workspace has cost leaks. Every viewer will check theirs after the demo.
5. **Covers 7 of 34 pain entries** in one skill — high ROI per skill built.
6. **Pattern coverage:** AP01 (progressive disclosure), AP04 (script-vs-LLM separation — billing math is deterministic, "where to focus" is LLM), AP08 (domain-sliced reference loading — per-leak-class deep dives), AP09 (MCP server). Four of the six recommended patterns exercised in one skill.
7. **Architectural proof.** If this skill works end-to-end at the new bar, every other skill in the pack has a template — not a content template (that was the wrong move), but a primitive-shape template.

**What the pilot delivers:**

- The `databricks-workspace-mcp` server stub (only the endpoints this skill needs — `clusters.list`, `instance_pools.list`, `sql.queries.history`, `system.billing.usage` query proxy)
- `SKILL.md` with the orchestration logic
- `references/`:
  - `photon-eligibility-and-fallback.md` (D02)
  - `compute-pricing-cheat-sheet.md` (D07, all-purpose vs job)
  - `silent-serverless-features.md` (D08 — Predictive Optimization, Lakehouse Monitoring, materialized views, vector search)
  - `instance-pool-cost-model.md` (D09)
  - `dlt-tier-cost-tradeoffs.md` (D11)
- `scripts/`:
  - `photon-fallback-audit.py` (parses execution plans, computes Photon-effective %)
  - `cost-leak-audit.py` (cross-references billing × cluster type × workload)
  - `pool-idle-cost-projection.py` (cloud-provider rate × min_idle × hours)
  - `dlt-cost-audit.sql` (canonical system tables query)
- Slash commands: `/cost-audit-all-purpose-leaks`, `/photon-audit`, `/pool-idle-audit`, `/serverless-shadow-audit`
- Optional: scheduled subagent via the `loop` skill for weekly digest

**Effort estimate:** 3-5 days of focused build for the pilot. MCP server stub is the longest-pole item (~1 day). Skill content is ~1 day. References are ~1 day. Scripts are ~0.5 day each.

---

## 6. Decisions parked for the user

These are judgment calls the rebuild plan can't make without input:

1. **Pilot choice** — agree with `databricks-cost-leak-hunter`, or want a different starting skill (e.g. `databricks-streaming-guardian` for the operational SRE angle)?
2. **Skill clustering granularity** — is 8 skills the right number, or should some merge (e.g. cluster forensics + streaming guardian) for fewer, broader artifacts?
3. **MCP server scope** — minimal-first (only endpoints the pilot needs) and grow with each new skill, OR full surface-area scaffold upfront?
4. **Delete-list timing** — cut the current 15 skills *before* the rebuild (clean slate, marketplace shows the gap), *during* the rebuild (gradual replacement), or *after* (current pack stays until rebuild is fully shipped)?
5. **Pack naming** — keep `databricks-pack` (slug stability), rename to `databricks-pro` or similar to signal the rebuild?
6. **Luciano timing pressure** — is the pilot needed for the live stream (in which case build window is days, not weeks), or is the stream demo-able with the current pack as a "here's what we have today, here's the rebuild direction" framing?

---

## 7. Open research gaps to close before final design

All four research agents flagged the same gap: **Reddit and Twitter/Bluesky fetch is blocked from this environment.** Field-anecdote layer is thin. Manual or authenticated-MCP follow-up needed to ground the pain catalog in community sentiment, not just docs + GH issues + forum threads.

Other unfilled areas (per agent reports):

- DAIS / Data + AI Summit 2024-2025 video talks (transcript work, 4-6h)
- `databricks/databricks-sdk-py` GitHub issues (Python SDK ergonomics pain — possible new domain entry)
- GCP-specific pain (under-represented vs AWS/Azure across all three domains)
- Stack Overflow `[databricks-unity-catalog]` long-tail (~600 questions, only top 20 mined)
- `delta-rs` Rust client protocol-version skew pain
- Delta UniForm / Iceberg compat pain (emerging)
- Bundle "direct" engine known-bug inventory (moving target)

Not blockers for the pilot, but should be closed before the full pack ships.

---

## Files referenced

All research lives in `plugins/saas-packs/databricks-pack/000-docs/`:

- `002-RL-RSRC-databricks-compute-pain-research.md` — 12 entries, compute/Photon/DBR/cost
- `003-RL-RSRC-databricks-delta-streaming-research.md` — 12 entries, Delta/Liquid/Streaming/DLT
- `004-RL-RSRC-databricks-uc-bundles-ops-research.md` — 10 entries, UC/Bundles/SCIM/networking
- `005-RL-RSRC-anthropic-skill-architecture-patterns.md` — 10 patterns, Anthropic-grounded
- `006-RL-RSRC-databricks-v2-rebuild-synthesis.md` — this document
- `007-AT-ADEC-databricks-v2-cto-decision.md` — the locked-in decision record
- `008-RA-REVW-pack-handling-pressure-test.md`, `009-RA-REVW-pilot-timing-pressure-test.md` — adversarial reviews

Bead: `claude-setb` (Phase 1 — Research)
