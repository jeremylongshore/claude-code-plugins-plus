# ADR: databricks-cost-leak-hunter — billing-table dollars, deterministic ranking, two data planes

> Filed at `docs/ADR.md` beside the rest of the submission set, per
> `000-docs/700-DR-GUID-skill-submission-standard.md` §2 ("the same matrix applies to
> Intent Solutions' own skills") — keeping the four docs atomic and inside the
> markdownlint-gated `plugins/**` tree. The ADR template's `000-docs/` filing note is the
> known alternative reading; the divergence is called out in the backfill PR.

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-07
**Status:** Accepted

## Context

A cost report is only worth shipping if a finance owner can trust every number in it and
act on every line. Three forces shaped the design. (1) Generic waste estimates get
discounted on sight — a credible figure must be computed from the customer's own billing
rows, and Databricks exposes exactly that in `system.billing.usage` joined to
`system.billing.list_prices`, but behind a metastore-admin grant chain that is the single
most common failure. (2) An LLM eyeballing arithmetic is a nonstarter when the output is a
money claim — the math must be reproducible and auditable. (3) A billing row says how much
but not _why_: turning a leak into a fix requires live control-plane evidence (the
auto-termination setting, the cluster source, the autoscale floor, the runtime engine)
that the billing tables do not carry.

## Decision

We compute every confirmed dollar figure from the customer's own `system.billing.usage`
joined to `system.billing.list_prices` through the **Databricks CLI Statement Execution
API** — never an estimate — and we corroborate each leak's root cause on a second data
plane, the **`databricks-workspace-mcp`** control-plane tools, so each report line lands
as a single verified config change. All arithmetic runs in the **deterministic ranker**
(`scripts/rank-and-report.py`): it sums per-category figures by `kind`
(`confirmed` / `estimated` / `at-risk`), ranks by monthly dollar impact, annualizes the
headline and #1 line, and keeps confirmed and unconfirmed dollars split — the LLM does
not do the arithmetic. Step 1 probes the billing grant chain and fails fast with the
exact missing `GRANT` statements; if the MCP server is absent, the dollar half still runs
and corroboration degrades to pasted config rather than failing silently.

## Alternatives considered

| Alternative                                                    | Why rejected                                                                                                                                                                                                             |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Model waste from published industry rates (e.g. cloud-waste %) | An estimate a skeptical CFO can dismiss. The skill's contract is confirmed dollars from the workspace's own billing rows; published rates survive only as labeled framing in the illustrative sample output.             |
| Let the LLM compute and rank the dollar figures inline         | Money arithmetic must be reproducible. The deterministic ranker produces the same report from the same inputs and is auditable line-by-line; "the LLM does NOT do the arithmetic" is a stated invariant of the pipeline. |
| A single data plane — SQL only, or the workspace REST/MCP only | The REST control plane cannot produce billed dollars; the billing tables cannot confirm today's live config. Either half alone loses the dollar figure or loses the verified single-config-change fix.                   |

A fourth rejection is baked into the output contract: a single blended headline number.
Summing confirmed spend with modeled (estimated/at-risk) amounts under one verb is
forbidden by the skill's Output rules and enforced as the regression-critical eval
criterion `splits-confirmed-vs-estimated`.

## Consequences

**Positive:**

- Confirmed figures are billed dollars attributed to `system.billing.usage` — the
  strongest evidence class available, and the `dollars-from-billing-not-estimates` eval
  criterion holds the skill to it.
- Same inputs, same report: the ranker's sums, ranking, and annualization are
  deterministic and reviewable in `scripts/rank-and-report.py`.
- Every leak ships with corroborated live config, so each fix is one named setting
  (auto-termination, Jobs Compute, autoscale floor, `runtime_engine`).
- The grant-chain probe converts the most common failure into an upfront, verbatim
  `GRANT`-chain report instead of a mid-flow crash.

**Negative / accepted tradeoffs:**

- Hard prerequisites: Premium/Enterprise with Unity Catalog, a metastore-admin grant
  chain, and a running SQL warehouse (`DATABRICKS_WAREHOUSE_ID`). No grants, no report —
  accepted, because an unverifiable number is worse than no number.
- Two authentication surfaces (CLI host+token; the MCP's own PAT/U2M/M2M) mean more
  setup. Accepted as the price of two-plane evidence.
- Two of the four categories (overprovisioning `est_*`, Photon at-risk) are modeled and
  never join the confirmed headline, so the report undersells the total against a blended
  number. Accepted by design — that is the point.
- Without the MCP server, corroboration relies on pasted config: weaker evidence, clearly
  labeled, still dollar-accurate.

## Tool-permission scope

No bare `Bash`: shell access is scoped to exactly two binaries. The five MCP tools are
all read-only `get`/`list` calls; nothing in the tool set can mutate workspace config.

| Tool                                                 | Why it's needed                                                                                                                                      |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Read`                                               | Load the on-demand `references/*.md` knowledge (leak-category SQL, CFO format, grant-chain setup, DLT tiers) and per-category `leak-*.json` results. |
| `Write`                                              | Write the rendered report and per-leak detail artifacts to the runtime working dir (`$OUT`) — never into the skill package.                          |
| `Edit`                                               | Rescale the headline spend in the rendered report when the user asks.                                                                                |
| `Bash(databricks:*)`                                 | The CLI Statement Execution API calls (`databricks api post /api/2.0/sql/statements`) that run the Step-1 grant probe and every dollar query.        |
| `Bash(jq:*)`                                         | Parse statement-execution JSON, inject `warehouse_id` into the SQL template, and assemble the per-category results fed to the ranker.                |
| `Glob`                                               | Collect the per-category `leak-*.json` outputs for the ranking step.                                                                                 |
| `mcp__databricks-workspace-mcp__clusters_get`        | Confirm live `autotermination_minutes`, `autoscale.min_workers`/`max_workers`, `cluster_source`, and `runtime_engine` for a flagged cluster.         |
| `mcp__databricks-workspace-mcp__clusters_events`     | Measure the actual idle gap between `RUNNING` and `TERMINATING` events on never-terminating clusters.                                                |
| `mcp__databricks-workspace-mcp__clusters_list`       | Enumerate clusters and confirm compute type when validating the jobs-on-All-Purpose leak.                                                            |
| `mcp__databricks-workspace-mcp__instance_pools_list` | Detect the idle-pool overprovisioning variant (`min_idle_instances` + `stats.idle_count`) — pool waste is not a billing row.                         |
| `mcp__databricks-workspace-mcp__pipelines_get`       | Check DLT pipeline Photon/serverless/edition settings (`spec.photon`) when the Photon leak touches DLT.                                              |
