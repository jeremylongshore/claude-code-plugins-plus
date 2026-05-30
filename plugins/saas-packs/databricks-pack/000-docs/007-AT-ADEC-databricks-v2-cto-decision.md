# CTO Decision Record — Databricks Pack Rebuild (v2 — REVISED)

**Date:** 2026-05-27
**Decider:** Claude (delegated CTO authority per Jeremy 2026-05-27)
**Revisions in this version:**

- Pressure-test feedback (`008-RA-REVW-pack-handling-pressure-test.md` MODIFY, `009-RA-REVW-pilot-timing-pressure-test.md` MODIFY) incorporated
- Jeremy's 2026-05-27 directive incorporated: **3-5 badass skills total, no fluff** (cut from 8 → 5)
- Jeremy's 2026-05-27 v1/v2 framing confirmed: current `databricks-pack` is v1, rebuild is v2.0.0

---

## Decision 1 — Pack handling: deprecation lane + v2.0.0 + tombstones

**Call:**

1. **Ship `databricks-pack@1.1.0` immediately** — a deprecation release of the current pack. Adds banner warnings in the 15 doomed-skill SKILL.md files: "DEPRECATED: this skill will be removed in v2.0.0. See README for migration path." Updates CHANGELOG with the v2 plan. No content changes beyond banners.
2. **Wait 2-4 weeks** for users on auto-update to see the warnings.
3. **Ship `databricks-pack@2.0.0`** with the actual rebuild: 5 new operational skills + shared MCP server + tombstone `SKILL.md` stubs in the 15 deleted-skill directories pointing at their replacement (or "removed, no replacement; here's why" for the 8-9 that aren't being replaced).
4. **Ship `databricks-pack@2.1.0`** 1-2 release cycles later — removes the tombstones, cleans up.
5. **Rewrite the catalog description** in `marketplace.extended.json` before tagging 2.0.0 — current text advertises "MLflow, notebooks" that aren't in the new skill set. New description targets operational depth, not surface breadth.

**Why this is harder than just "version bump":**

The architect-reviewer pressure-test surfaced a real risk I missed: Claude Code marketplace auto-updates (v2.0.72+) actually delete files on uninstall (v2.0.30+). On upgrade from 1.x to 2.0.0, deleted skill directories vanish with no in-product warning to the user. A user who has `databricks-hello-world` in their CLAUDE.md will see references suddenly break. Tombstone stubs prevent the 404 cliff; deprecation lane gives users a window to see what's coming.

**Slug decision confirmed:** `databricks-pack` stays. Per Jeremy 2026-05-27 ("v1 was the SaaS pack, v2 is the rebuild"). Per CLAUDE.md "Key Identifiers — Do Not Normalize."

---

## Decision 2 — 5 skills, not 8. Jeremy's call, accepted.

**Call:** Cut to **5 skills + 1 MCP server**. No fluff.

| # | Skill | Pains covered | Why it earns a slot |
|---|---|---|---|
| 1 | `databricks-cost-leak-hunter` | D02, D07, D08, D09, D11, D12 (domain 1) + D11 (domain 2) | Pilot. Universal demand. FinOps angle that lands with practitioners. |
| 2 | `databricks-cluster-forensics` | D01, D03, D04, D05, D06, D10 (domain 1) | Cluster lifecycle + DBR upgrade pain + spot-interruption — operational SRE spine. |
| 3 | `databricks-streaming-guardian` | D01, D02, D03, D04, D05, D06, D07, D08, D09, D10, D12 (domain 2) | Every Delta + Liquid + Streaming + DLT pain consolidated into one skill — the data-ops spine. |
| 4 | `databricks-uc-migration-pilot` | D1, D2, D3, D7, D10 (domain 3) | UC migration is the peak-pain forcing function (Sept 30 2026 deadline). |
| 5 | `databricks-bundle-medic` | D4, D5, D6, D8, D9 (domain 3) | Asset Bundles immature tooling + CMK + networking — deploy + infra spine. |

**Plus:** `databricks-workspace-mcp` (the shared MCP server — not a skill, but the package-level infrastructure all 5 skills consume).

**Coverage:** all 34 pain entries from the research land in one of the 5 skills. No pain dropped.

**What got merged out vs the 8-skill plan:**

- `databricks-dbr-upgrade-advisor` → folded into `databricks-cluster-forensics` (DBR upgrade IS a cluster-lifecycle concern)
- `databricks-delta-conflict-resolver` → folded into `databricks-streaming-guardian` (conflict resolution is part of the data-ops spine)
- `databricks-identity-secrets-ops` → folded into `databricks-bundle-medic` (CMK rotation + SCIM are deploy-time concerns; this skill becomes the "infra + identity + secrets" spine)

**Cut from current pack (15 of 24 skills):**

databricks-hello-world, databricks-install-auth, databricks-local-dev-loop, databricks-core-workflow-a, databricks-core-workflow-b, databricks-sdk-patterns, databricks-prod-checklist, databricks-security-basics, databricks-enterprise-rbac, databricks-rate-limits, databricks-webhooks-events, databricks-common-errors, databricks-debug-bundle, databricks-reference-architecture, databricks-multi-env-setup, databricks-ci-integration, databricks-deploy-integration, databricks-migration-deep-dive, databricks-data-handling.

(That's 19 names cut/absorbed. Net: 24 → 5 skills.)

---

## Decision 3 — Pilot: `databricks-cost-leak-hunter` at REDUCED scope

**Call:** Build the pilot, but at reduced scope per pilot-timing pressure-test.

**Scope cut from 7 pains to 3:**

- D07 (all-purpose vs job cluster cost)
- D09 (instance pool idle waste)
- D11 (DLT serverless cost spike)
- (Optional, time-permitting: D08 silent serverless features)

**Dropped from pilot, deferred to follow-up:**

- D02 (Photon silent fallback) — execution-plan JSON parsing across DBR versions is the longest-pole risk; defer to skill #2
- D12 (serverless notebook bill attribution) — narrow scope, doesn't move the needle on architectural proof

**Demo must explicitly show architecture, not just $ numbers.** Per pressure-test: "for a 15-year practitioner audience, 'another cost dashboard' is the lowest-status output." Overwatch / Unravel / Sync Computing already do dollar numbers. The differentiator is the MCP + scripts + references composition — show it on screen.

**Tag-based per-team chargeback attribution** — pressure-test flagged this as the "Overwatch-killer" missing capability. Adding to pilot scope as a stretch goal if days 4-5 are clean.

**Fallback if 5 days slips:** ship `databricks-pool-idle-auditor` instead — D09 only, ~2 days. Same "$X/mo in idle VMs" demo, 1/3 the surface. Named fallback, not vague.

---

## Decision 4 — Build sequencing: MCP server first, separately

**Call:** Ship MCP server as its own deliverable BEFORE the pilot skill.

```
Day 1-2:  databricks-workspace-mcp@0.1.0
          - 4 endpoints: clusters.list, instance_pools.list,
            sql.queries.history, system.billing.usage query proxy
          - OAuth flow tested against sandbox workspace
          - /validate-mcp passes
          - Standalone PR, mergeable independently

Day 3:    databricks-cost-leak-hunter SKILL.md scaffold via /skill-creator
          References: 3 of 5 written (the ones for D07, D09, D11)
          Scripts: 3 of 4 written (cost-leak-audit, pool-idle-cost-projection, dlt-cost-audit)

Day 4:    Integration: SKILL.md orchestrates scripts + MCP calls
          End-to-end run on sandbox workspace
          Optional: D08 + serverless-shadow-audit if time clean

Day 5:    Validation gates
          - /validate-skillmd --thorough (JRig tier 3, models=haiku,sonnet ONLY — drop opus per pressure-test)
          - /validate-plugin on whole databricks-pack
          - j-rig eval with same model set
          Iterate on what they surface
          Commit + open PR
```

**Slippage tripwire at day 3:** if MCP auth still painful or execution-plan parser stuck, switch to `databricks-pool-idle-auditor` fallback the same day. Don't burn day 4-5 trying to rescue.

---

## Decision 5 — Demo arc for Luciano: architectural shift, not just dollars

**Call:** 45-min demo, structured to land the architectural shift:

- **0-5 min** — What v1 looked like. Walk `databricks-hello-world` and `databricks-performance-tuning` SKILL.md. Acknowledge: "These describe Databricks ops. They don't do them."
- **5-15 min** — What changed. Show the research process (34 pain entries from real forums/GH issues, 10 Anthropic-derived patterns). Show the architecture: MCP server, references, scripts, hooks. Slides for this part.
- **15-30 min** — Live demo of `databricks-cost-leak-hunter` on sandbox. Run the slash commands. Surface real $ numbers. **Reveal the architecture on screen:** show the SKILL.md, show the MCP server tool calls, show the script outputs, show the references loaded on demand. Practitioner audience needs to see the composition or they'll think it's just SQL.
- **30-40 min** — Roadmap. The remaining 4 skills, when they ship, how Luciano's audience can contribute pain entries.
- **40-45 min** — Q&A.

---

## Audit trail commitments

- This file gets promoted to `000-docs/NNN-AT-DECR-databricks-rebuild-cto-call.md` per Doc Filing Standard v4.3.
- Bead `claude-setb` (rebuild umbrella) gets a `bd-sync note` linking here.
- GH issue #785 (Luciano outreach) gets cross-referenced — demo planning ties to the rebuild work.
- Pressure-test files `pressure-test-pack-handling.md` and `pressure-test-pilot-timing.md` are the supporting evidence for these modifications.

---

## Questions parked for Jeremy (only these)

1. **Sandbox workspace.** Which Databricks workspace gets used for build + demo? Free Tier won't cut it (needs UC + system tables). Existing customer workspace OK? If not, provision Premium trial?
2. **Luciano date.** Push for 14+ days out so 5-day build + 4-week deprecation lane fits, OR accept earlier date and demo from v1.1.0 with "v2 launches next month" framing?
3. **Tag-based chargeback in pilot.** Pressure-test flagged this as the Overwatch-killer feature. Include in pilot scope (adds ~1 day) or defer to follow-up release?

Everything else proceeds. Phase 3 (pilot build) starts on your go.
