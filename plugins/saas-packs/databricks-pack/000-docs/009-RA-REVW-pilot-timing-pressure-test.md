# Pressure-Test: `databricks-cost-leak-hunter` as Pilot, 3-5 Day Window

**Reviewer:** Plan agent (adversarial review, 2026-05-27)
**Original decision:** Build cost-leak-hunter first, 3-5 days, covers 7 pains
**Verdict:** **MODIFY**

---

## Summary

Keep cost-leak-hunter as pilot. **Ship MCP server separately first** (1-2 days). **Cut pilot scope from 7 pains to 3-4** (D07 + D09 + D11 + optionally D02). **Drop `--models opus` from pilot JRig eval.** **Hold `databricks-pool-idle-auditor` as named 2-day fallback.** Lock build to 5 days with defined fallback at day 3.

## 1. Is 3-5 days realistic? No — not at stated scope.

The synthesis itself says: MCP server 1d + skill 1d + references 1d + scripts 0.5d × 4 = **2 days of scripts alone**. That's 5 days before validation. Gate chain (`/validate-mcp`, `/validate-skillmd --thorough`, `/validate-plugin`, `j-rig check`, `j-rig eval --models haiku,sonnet,opus`) adds 0.5-1d iteration because Tier 3 JRig routinely surfaces SKILL.md ambiguities forcing rewrites. **Realistic at original scope: 6-8 days.**

**Longest pole:** NOT the MCP server — the execution-plan JSON parser for `photon-fallback-audit.py`. Plan shape varies by DBR version (D02 explicitly notes this in domain 1 research). Robustness across DBR 13/14/15 is the slip risk, not OAuth wrapping.

## 2. Right pilot vs alternatives? Mostly yes, with caveats.

Cost-leak-hunter beats streaming-guardian on **live-demo safety** (reads-only, no PreToolUse blocking that can misfire on stage) and beats cluster-forensics on **universality**. Agreed.

**But** — for a 15-year Databricks practitioner audience, "another cost dashboard" is the lowest-status output in the entire Databricks tooling ecosystem. Overwatch, Unravel, Sync Computing, and Databricks' own System Tables dashboards already do this. The architectural-shift narrative does NOT automatically land. The demo must visibly demonstrate **MCP + script-vs-LLM separation (AP04) + progressive disclosure (AP01)** — not just print a dollar number. Without explicit on-screen reveal of the architecture, this looks like a wrapped SQL query.

## 3. Fallback if it slips

**`databricks-pool-idle-auditor`**: D09 only, one script (`pool-idle-cost-projection.py`), one slash command, one MCP endpoint (`instance_pools.list`). Shippable in 2 days. Same demo narrative ("here's $X in idle VMs") with 1/3 the surface. Keep in back pocket explicitly.

## 4. What a 15-year practitioner expects that's missing

Cost-leak-hunter as scoped omits: **serverless SQL warehouse autoscaling waste**, **DBU vs cloud-cost reconciliation** (the FinOps gap), **per-team chargeback attribution via tags**, **Photon × spot-instance interaction**. Synthesis covers D08 "silent serverless features" but the reference file alone won't land — practitioners want the audit script to *attribute* costs, not just *find* them. Without tag-based attribution, expect "cute, but Overwatch already does this" in comments.

## 5. Build sequencing — MCP first, separately versioned

Bundling MCP inside the pilot skill = wrong shape. Synthesis §2 Finding 1 is explicit: MCP is **package-level infrastructure** consumed by all future skills. Ship as `databricks-workspace-mcp@0.1.0` with the 4 endpoints cost-leak-hunter needs, validated independently. Buys: (a) reusability when streaming-guardian arrives, (b) clean SemVer for endpoint expansion, (c) demo credibility ("one server, N skills" > "skill includes a server").

## 6. JRig eval cost

`j-rig eval --models haiku,sonnet,opus` at $2-5 is trivial money. The question is **iteration time**. For a pilot whose job is template-setting, run `haiku,sonnet` only — opus rarely surfaces issues the other two miss on first pilots, rerun cost of find-and-fix is the actual budget killer. Save opus eval for skill #3-4 when template is stable.

---

**Net:** Stand on pilot choice. Modify scope to 3-4 pains. Ship MCP separately. Drop opus from pilot eval. Hold pool-idle-auditor as named 2-day fallback. Demo must explicitly show architecture, not just $ number.
