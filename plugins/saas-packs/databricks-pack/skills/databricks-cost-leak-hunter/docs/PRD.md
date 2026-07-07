# PRD: databricks-cost-leak-hunter

**Author:** Jeremy Longshore (Intent Solutions)
**Date:** 2026-07-07
**Status:** Active

> Backfilled 2026-07-07 from the shipped skill (SKILL.md v0.1.0, `eval-spec.yaml`, and the
> pack's design-review record) to the `templates/skill-docs/` submission standard — the
> first first-party skill held to the pack/flagship tier of the doc matrix. Refs #984.

## Problem

Databricks bills climb without an explanation a finance owner can act on. The waste hides
in four recurring configurations: clusters that never auto-terminate and bill around the
clock for idle compute; scheduled jobs running on All-Purpose Compute (~$0.55/DBU) instead
of Jobs Compute (~$0.15/DBU) — 2–3× the cost for identical work; clusters sized for peak
that idle below 25% CPU; and the ~2× Photon DBU premium paid on jobs it doesn't
accelerate. The native billing data can prove all four, but it lives in `system.*` tables
behind a metastore-admin grant chain and speaks in DBUs — so cost reviews either stall on
access, or arrive as engineering jargon a CFO can't act on, or fall back to generic
industry waste estimates that a skeptical reader can dismiss.

## Target users

| User                       | Context                                                                                       | Primary need                                                                                          |
| -------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| CFO / FinOps owner         | Monthly spend review, or the Databricks bill just spiked                                      | A dollar-ranked report readable in ~90 seconds and actionable without an engineer to translate        |
| Data-platform engineer     | Asked "why is our Databricks bill so high?" and needs defensible numbers, not vibes           | Deterministic detection SQL over `system.billing.usage` plus a ranked list of one-config-change fixes |
| Databricks workspace admin | Recurring cost-hygiene sweeps (idle clusters, wrong-SKU jobs, oversized floors, Photon usage) | A repeatable detect → compute → rank → report pipeline with confirmed-vs-estimated labeling           |

## Success criteria

Criteria 1–3 are enforced verbatim by the skill's `eval-spec.yaml` judge criteria.

1. Triggers on Databricks cost questions ("why is my databricks bill", "find wasted
   spend", "cost leak") and does not trigger on unrelated prompts — eval criterion
   `triggers-on-cost-question` (blocker) plus the two should-not-trigger control cases.
2. A CFO with no Databricks engineering knowledge can read the output in ~90 seconds and
   say "we are wasting $X here, fix it" without an engineer — eval criterion
   `produces-cfo-grokkable-report` (blocker).
3. Confirmed and estimated/at-risk dollars are never summed under one figure, and every
   leak carries a Confidence label (Confirmed / Estimated / At-risk) — eval criterion
   `splits-confirmed-vs-estimated` (regression-critical), with confirmed figures
   attributed to `system.billing.usage` (`dollars-from-billing-not-estimates`).
4. A workspace missing the billing grant chain is reported upfront with the exact missing
   `GRANT` statements — Step 1 fails fast instead of dying mid-analysis (eval criterion
   `checks-grant-chain-upfront`).

## Functional requirements

- **FR-1:** Verify the metastore-admin grant chain on `system.billing` before any
  analysis; on failure, report the exact missing grants verbatim and stop.
- **FR-2:** Detect the four named leak categories with SQL over `system.billing.usage`
  joined to `system.billing.list_prices` via the CLI Statement Execution API: idle
  clusters (`auto_termination_minutes = 0`), scheduled jobs on `ALL_PURPOSE`,
  overprovisioned clusters (<25% CPU from `system.compute.node_timeline`), and the Photon
  premium (`sku_name ILIKE '%PHOTON%'`).
- **FR-3:** Corroborate each leak's live configuration through `databricks-workspace-mcp`
  (`clusters_get`, `clusters_events`, `clusters_list`, `instance_pools_list`,
  `pipelines_get`); if the MCP server is absent, still produce the dollar figures and
  accept pasted config instead of failing.
- **FR-4:** Do all dollar arithmetic in the deterministic ranker
  (`scripts/rank-and-report.py`) — the LLM never eyeballs a number; every leak carries a
  `kind` of `confirmed` / `estimated` / `at-risk`.
- **FR-5:** Render the CFO report per `references/cfo-output-format.md`: a split headline
  that never sums confirmed and unconfirmed dollars under one verb, a trailing-30-day
  window stamp, a ranked table with a Confidence column, and a #1-line annualized callout
  — each fix a single config change.

## Out of scope

- Authoring cost-control policy (cluster policies, spot configs) — that is the sibling
  `databricks-cost-tuning` skill; this skill detects and reports.
- Applying any fix — every remediation is a recommendation for a human-approved config
  change; the skill never mutates workspace configuration.
- Estimating spend when the billing tables are unreadable — no grant chain, no report
  (fail fast at Step 1 rather than substitute guesses).
- Standard-tier / non-Unity-Catalog workspaces — the `system.*` tables are UC-governed
  and unavailable there.
