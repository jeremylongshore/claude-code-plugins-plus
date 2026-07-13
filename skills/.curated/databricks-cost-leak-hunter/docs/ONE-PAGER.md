# Databricks Cost Leak Hunter

**Finds the real-dollar cost leaks in a Databricks workspace and reports them as a dollar-ranked, CFO-grokkable fix list — computed from the customer's own billing tables.**

## Problem

Databricks spend leaks through four recurring configurations — clusters that never
auto-terminate, scheduled jobs on All-Purpose Compute (~$0.55/DBU) instead of Jobs
Compute (~$0.15/DBU), clusters sized for peak that idle below 25% CPU, and a ~2× Photon
premium on jobs it doesn't accelerate. The bill says how much but not where or why, and
DBU-denominated analysis needs an engineer to translate before a CFO can act.

## Solution

A detect → compute → rank → report pipeline. SQL over the workspace's own
`system.billing.usage` joined to `system.billing.list_prices` (via the Databricks CLI
Statement Execution API) produces the dollars; the `databricks-workspace-mcp`
control-plane tools corroborate the live config that explains each leak; a deterministic
Python ranker does all the arithmetic; and the output is a CFO-grokkable report — a split
confirmed-vs-pending-review headline, a ranked leak table with a Confidence column, and a
single-config-change fix per line. A Step-1 grant-chain probe fails fast if billing
access is missing.

## W5

|           |                                                                                                                                         |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Who**   | CFO / FinOps owners and the data-platform engineers who answer to them                                                                  |
| **What**  | Audits a workspace for four named leak categories and emits a dollar-ranked FinOps report with Confirmed / Estimated / At-risk labels   |
| **When**  | The bill spikes, the monthly FinOps review, or any "why is my Databricks bill so high?" moment                                          |
| **Where** | Claude Code (also Codex-compatible), against a Databricks Premium/Enterprise + Unity Catalog workspace                                  |
| **Why**   | Dollars come from the workspace's own billing rows and a deterministic ranker — never LLM guesswork — and each fix is one config change |

## Stack

| Layer             | Choice                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| Skill runtime     | Claude Code `SKILL.md` (compatibility: Codex)                                                     |
| Dollar data plane | Databricks CLI Statement Execution API over `system.billing.usage` × `system.billing.list_prices` |
| Config data plane | `databricks-workspace-mcp` — five read-only cluster/pool/pipeline tools                           |
| Arithmetic        | Deterministic Python ranker (`scripts/rank-and-report.py`) + `jq`                                 |
| Knowledge         | `references/*.md` loaded on demand (leak-category SQL, CFO format, grant-chain setup, DLT tiers)  |

## Differentiators

1. **Confirmed dollars, never estimates** — every confirmed figure is computed from the
   customer's own `system.billing.usage` joined to `list_prices`; the two modeled
   categories are explicitly labeled Estimated and At-risk and never blended in.
2. **The LLM never does the arithmetic** — a deterministic ranker sums, ranks, and
   annualizes, and the headline never sums confirmed and unconfirmed dollars under one
   verb (a regression-critical eval criterion).
3. **Every leak is one config change** — the second data plane corroborates live config
   (`auto_termination_minutes`, `cluster_source`, autoscale floor, `runtime_engine`), so
   each report line names the exact setting to flip.
