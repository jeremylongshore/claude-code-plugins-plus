# Databricks Cost Leak Hunter — CFO One-Pager

> This document is required for this skill: `databricks-pack` is the 2026-W27 featured
> pick and money is the pitch (per the `templates/skill-docs/README.md` tier matrix).
> Numbers discipline, inherited from the skill itself: confirmed (billed) dollars and
> modeled (estimated/at-risk) dollars are presented separately and never summed under one
> figure.

## The cost of the problem

On the skill's worked example — a **$100K/month** Databricks workspace — the four leak
categories account for **~$19,000/month of confirmed billed waste (~$228K/year)**, plus
**up to ~$8,000/month flagged for review (~$96K/year)**. The $100K/month workspace spend
is the only assumed input; on a live run, every confirmed figure is computed from your
own `system.billing.usage` joined to `system.billing.list_prices`. The mechanics behind
the leaks are published rates, not house numbers — e.g. All-Purpose Compute bills
~$0.55/DBU against ~$0.15/DBU on Jobs Compute, so a scheduled job on the wrong tier pays
roughly 2–3× for identical work, and Photon carries a ~2× DBU premium that only pays off
when the job actually runs faster.

## What the skill changes

One invocation replaces a manual FinOps audit. It verifies billing-table access upfront
(and, if access is missing, reports the exact grants to request instead of failing
halfway), runs four detection scans over the workspace's own billing rows, corroborates
each finding against the live cluster/pool/pipeline configuration, and hands the results
to a deterministic ranker — the LLM never does the arithmetic. The output is a
dollar-ranked report designed to be read by a non-engineer in ~90 seconds, where every
line is a single config change an engineer can be assigned: idle clusters that never shut
off, scheduled jobs on the premium tier, oversized clusters, and Photon premium paid
without the speedup.

## Impact per run

| Dimension     | Per run                                                                                                                                                                                                                                                                     |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Time saved    | Replaces manual billing-table SQL plus per-cluster config archaeology; the report itself is built to a ~90-second CFO read — a blocking criterion in the skill's eval spec.                                                                                                 |
| Risk reduced  | Confirmed vs Estimated vs At-risk labeling prevents booking modeled savings as recoverable dollars; the upfront grant check prevents half-run analyses.                                                                                                                     |
| Dollars saved | Worked example ($100K/month workspace): ~$19K/month confirmed (~$228K/yr) + up to ~$8K/month pending review (~$96K/yr); the #1 line alone (idle clusters, confirmed) is ~$144K/yr, fixed in one setting. Live runs compute your actual figures from `system.billing.usage`. |

## Adoption cost

| Item          | Cost                                                                                                                                                                                                                                                                                                                                                                  |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Setup time    | Minutes if billing grants already exist; otherwise gated on a metastore admin running a four-statement `GRANT` chain — the skill checks upfront and prints exactly what is missing.                                                                                                                                                                                   |
| Prerequisites | Databricks Premium or Enterprise with Unity Catalog; metastore-admin grant chain on `system.billing` (and `system.compute` for corroboration); Databricks CLI authenticated; `jq`; `DATABRICKS_WAREHOUSE_ID` pointing at a running SQL warehouse; `databricks-workspace-mcp` registered (own PAT/U2M/M2M auth) — optional, the dollar analysis still runs without it. |
| Ongoing       | None required; re-run per billing review — every report stamps its trailing-30-day window.                                                                                                                                                                                                                                                                            |

## Risk notes

- **Read-only against Databricks.** The workspace access is billing `SELECT`s plus
  read-only `get`/`list` config calls; the skill changes no workspace configuration —
  every fix is a recommendation applied by your engineer.
- **Permissions bound the blast radius.** Billing access requires an explicit Unity
  Catalog grant chain; the MCP server authenticates separately; no secrets are hardcoded
  — all auth comes from the environment or the registered MCP server.
- **Modeled numbers are fenced.** Overprovisioning figures are estimates (labeled
  `est_*`); the Photon premium is at-risk pending a runtime-gain review; neither is ever
  counted in the confirmed headline.
- **Negotiated pricing can diverge from list prices.** The price join matches
  `sku_name` and `usage_unit` within the price-effective window; if it returns NULL, the
  skill falls back to your contracted rate card rather than guessing.
- **Degraded mode is explicit.** If the workspace MCP is absent, dollar figures still
  compute and config corroboration relies on pasted config — weaker evidence, clearly
  labeled, never a silent failure.
