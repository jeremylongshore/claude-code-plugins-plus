---
name: snowflake-cost-leak-hunter
description: >-
  Audit Snowflake warehouse, serverless, Adaptive, storage, transfer, and AI cost
  evidence with a typed ledger that prevents double counting and exposes freshness,
  attribution, control, and invoice boundaries. Use when a Snowflake bill increased,
  a team needs chargeback/showback evidence, credits appear unexplained, or an
  operator asks which usage merits investigation. Trigger with "Snowflake bill
  increased", "find idle Snowflake credits", "Snowflake cost attribution", or
  "untagged Snowflake spend". Do not use to mutate cost controls or claim savings.
allowed-tools: Read, Write, Bash(python3:*)
argument-hint: "[evidence-json-or-output-directory]"
model: inherit
effort: high
version: 2.2.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
  - saas
  - data-warehouse
  - analytics
  - snowflake
  - finops
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
---

# Snowflake Cost Leak Hunter

## Overview

Produce a read-only, evidence-first Snowflake cost investigation. The deterministic
analyzer emits a typed ledger whose `total`, `attribution`, `context`, `estimate`, and
`invoice-only` roles cannot silently collapse into one savings claim.

**Problem:** Cost views answer different questions, arrive at different times, and do
not equal invoice truth. Generic advice easily turns observed credits into unsupported
prices or promised savings.

**Outcome:** A reproducible review packet that identifies what the supplied evidence
confirms, what was estimated from an approved rate, what remains at risk, and what is
unknown.

## Prerequisites

- An exact account and UTC analysis window.
- Sanitized output collected by an operator through an approved read-only Snowflake
  session, or an equivalent exported evidence bundle.
- A role already authorized to read the required `SNOWFLAKE.ACCOUNT_USAGE` surfaces.
- A writable local working directory for report artifacts. Use `Write` only to create
  new local evidence/report files; never use it to alter Snowflake configuration.
- A customer-supplied rate-card record if currency estimates are requested.

## Safety and evidence contract

- **Read-only Snowflake work only.** Do not execute DDL/DML, change warehouse state or
  size, alter auto-suspend, assign monitors, create budgets, change tags, or cancel
  queries. Emit proposed changes for a named owner to review.
- **Do not invoke Snowflake authentication from this skill.** The operator runs the
  bounded collection queries through an approved read-only session and supplies only
  sanitized results. Never request connection files, private keys, tokens, passwords,
  or environment values.
- **Do not require `ACCOUNTADMIN`.** Use a role already authorized to read the needed
  `SNOWFLAKE.ACCOUNT_USAGE` views. Visibility differs by database role and account
  configuration; report missing access rather than escalating privileges.
- **Bound every history query by an explicit start and end time.** Record session
  timezone, account, role, query IDs used for collection, and the maximum source
  timestamp returned.
- **Treat source latency as evidence.** `QUERY_ATTRIBUTION_HISTORY` can lag by up to
  eight hours; `WAREHOUSE_METERING_HISTORY` can lag by up to three hours, with its
  cloud-services column lagging longer. Report observed source age. Do not call a
  partial recent window complete.
- **Credits are not invoice truth.** Warehouse metering can differ from billed credits,
  query attribution excludes idle time and several non-query categories, and resource
  monitors do not cover serverless features or AI services. Use invoice/usage-statement
  reconciliation for billing truth.
- **No public price assumptions.** Convert credits to currency only when the user
  supplies an applicable contract/rate-card record. Such conversion remains
  `estimated` until reconciled to the billing statement.

Read [references/attribution-and-staleness.md](references/attribution-and-staleness.md)
before collecting evidence. Read
[references/warehouse-and-idle-evidence.md](references/warehouse-and-idle-evidence.md)
for the bounded SQL surfaces. If controls are requested, read
[references/controls-boundaries.md](references/controls-boundaries.md), but return a
review packet only.
For Adaptive, storage, transfer, AI, surface-denominator, and typed-ledger rules, read
[references/cost-ledger-and-surfaces.md](references/cost-ledger-and-surfaces.md).

For a live, model-neutral collection, use the shared read-only collector with an
existing Snowflake CLI profile:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface cost --connection <approved-readonly-profile> \
  --output ./snowflake-cost-collector.json
```

Map its `datasets.warehouse_metering`, `query_attribution`, `warehouse_load`, and
`serverless_usage` rows into the analyzer schema. Preserve `collected_at`, source
views, row count, and sanitized errors. The collector's current-week query is a
discovery aid; the report must still state the requested half-open window and call
out any rows outside or missing from it.
If `truncation_possible` is true, do not issue a completeness or savings verdict;
narrow or partition the window and recollect until every receipt is below its cap.
Every usage row must carry `start_time` and `end_time` wholly inside the requested
window. Query attribution uses `query_tag_present` and optional
`query_tag_sha256`; never supply raw user names or query tags.
The analyzer treats a missing collector receipt as unverified and blocks completeness
and savings claims. When supplied, it verifies the receipt's surface, source views,
reviewed SQL hash, receipt hash, dataset rows, status, and cap. An error, mismatch,
missing integrity field, or possible truncation is surfaced in the report and blocks
completeness/savings claims.
The bundled collector currently supplies the baseline warehouse, query, load, and
generic metering receipt. Supplemental canonical templates live under
`../../shared/evidence/sql/cost-*.sql`; run only the needed templates through the same
approved read-only profile and preserve a separate availability/freshness receipt for
each. An unavailable region, edition, view, or privilege is a bounded finding, never a
reason to broaden privileges or treat the surface as zero.

## Instructions

### 1. Fix scope before querying

Capture:

- account and role;
- half-open UTC window `[window_start, window_end)`;
- requested attribution dimension, such as warehouse, user, query tag, or service;
- whether an approved contract rate card is available;
- whether Adaptive Warehouses or serverless features are in scope.
- the complete expected-surface denominator, including storage, transfer, AI,
  resource-monitor, and budget evidence when those domains are in scope.

If the user supplies only an invoice total, state that the audit can explain usage but
cannot reconcile the invoice without the corresponding usage statement and contract
rates.

### 2. Verify access without changing grants

Have the operator run the smallest read probes with the approved connection and
provide the sanitized results. This skill does not expose the Snowflake CLI namespace.
A representative probe is:

```sql
SELECT MAX(end_time) AS max_end_time
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= :window_start
  AND start_time < :window_end;
```

Probe `QUERY_ATTRIBUTION_HISTORY` separately because its availability, latency, and
coverage differ. If either probe fails, preserve the exact sanitized error, name the
missing surface, and stop that branch. Do not propose granting broad imported
privileges automatically.

### 3. Collect normalized evidence

Use the queries and field definitions in
[references/warehouse-and-idle-evidence.md](references/warehouse-and-idle-evidence.md).
Export only the normalized fields accepted by
`scripts/analyze_cost_evidence.py`; exclude raw SQL text and credentials.

The input JSON has these optional evidence arrays:

- `warehouse_metering`: hourly or pre-aggregated warehouse credit observations;
- `query_attribution`: per-query attributed compute and query-acceleration credits;
- `serverless_usage`: observed serverless credit rows from an approved usage surface;
- `adaptive_usage`: per-query Adaptive credits from `QUERY_METERING_HISTORY`;
- `storage_usage`: storage bytes used as operational context, never invoice truth;
- `data_transfer_usage` and `internal_transfer_usage`: transfer bytes retained in
  their native unit;
- `ai_usage`: detailed Cortex AI function credits, treated as attribution beneath the
  generic `AI_SERVICES` total;
- `surface_inventory`: availability, privilege, latency, freshness, and truncation
  receipts for every expected surface;
- `controls_inventory`: visibility-scoped resource-monitor and budget inventory;
- `invoice_usage`: optional customer-supplied billing-statement rows, kept as
  `invoice-only` entries and never inferred from usage views;
- `credit_rates`: user-supplied rate-card entries used only for estimates.

Every supplied source must include its maximum returned timestamp in `source_max_times`.
An absent source is not zero usage.

### 4. Run deterministic analysis

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_cost_evidence.py" \
  --input cost-evidence.json \
  --json-out cost-analysis.json \
  --markdown-out cost-analysis.md
```

The script validates non-negative numeric evidence, sums with decimal arithmetic, and
keeps five ledger roles separate:

- **Total** — additive usage totals such as warehouse metering or generic service
  metering.
- **Attribution** — a child breakdown of a total, such as query or AI-function usage;
  never additive with its parent.
- **Context** — non-price operational measures such as storage or transfer bytes.
- **Estimate** — a non-additive currency conversion from an applicable customer rate.
- **Invoice-only** — billing truth that cannot be inferred from operational views.

It does not apply magnitude thresholds, infer a price, or recommend a warehouse size.
When query fingerprints have both attributed credits and elapsed time, it also emits
a non-dominance cost/latency Pareto view. A Pareto point is a comparison aid, not a
proof that a workload should move warehouses. Right-sizing is only a bounded review
proposal when the operator supplies the current size, explicit candidate sizes,
maximum size steps, measurement window, success criteria, and approver; never infer a
target size from credits or queue time.

### 5. Corroborate before recommending

For each ranked opportunity, record:

1. the exact source rows and time window;
2. the observed source age;
3. coverage exclusions or NULL fields;
4. a competing explanation;
5. a read-only next measurement;
6. the owner who would approve any later change.

Examples of competing explanations include intentionally warm warehouses, SLA-driven
capacity, untagged shared-service queries, or usage outside the attribution view's
coverage. Do not label those cases waste without workload-owner confirmation.

### 6. Deliver the review packet

Follow [references/output-contract.md](references/output-contract.md). Lead with the
window and coverage, not a sensational savings number. A valid packet contains:

- confirmed credits by evidence surface;
- the typed ledger with parent IDs, overlap keys, aggregation eligibility, freshness,
  availability, and invoice-reconciliation status;
- attribution completeness by warehouse, including unknown boundaries for NULL
  attribution and query coverage gaps;
- cost/latency Pareto points by query fingerprint and warehouse-load correlation;
- estimated currency in a separate table, if and only if a rate card was supplied;
- at-risk opportunities ranked by observed credits, each labeled `review required`;
- missing/late-source warnings;
- read-only verification queries;
- proposed changes in an approval queue, with no execution performed.

## Output

Return `cost-analysis.json` and `cost-analysis.md` in the user's chosen working
directory, plus the exact analyzer command used. The JSON is the machine-readable
receipt; Markdown is the human review packet. Both must contain the analysis window,
source freshness, confirmed observations, estimated amounts, at-risk opportunities,
warnings, and non-claims. Do not write runtime output into the skill directory.

## Stop conditions

Stop and return a bounded partial result when:

- authentication or the approved role fails;
- the requested window is newer than the available source timestamps;
- account and organization usage are mixed without aligned account identifiers and UTC
  boundaries;
- Adaptive Warehouse rows make warehouse attribution columns NULL;
- a required cost surface is unavailable, stale beyond its supplied documented
  boundary, truncated, region-limited, or hidden by the approved role;
- a currency request has no applicable contract rate;
- evidence contains negative credits, malformed timestamps, or incompatible currencies;
- the only proposed next step would mutate production.

## Error Handling

| Condition | Meaning | Required response |
|---|---|---|
| Approved role cannot read a required view | Coverage unavailable | Preserve the sanitized error, name the missing surface, and stop that branch without changing grants. |
| Source maximum time trails the requested window | Recent evidence may be incomplete | Report observed age and return a partial result; do not convert missing rows to zero. |
| Attributed-query credits are NULL | Idle/unattributed calculation is unsupported for that row | Emit `COST_ADAPTIVE_ATTRIBUTION_GAP`; exclude the row from that calculation and do not substitute zero. |
| Generic AI or warehouse total and detailed attribution both exist | The evidence overlaps by design | Retain one additive total and attach detailed evidence as a non-additive ledger child. |
| Storage or transfer evidence has bytes but no contract billing model | Operational context is present without price evidence | Keep bytes as `context`; do not infer currency or invoice amounts. |
| No applicable contract rate | Currency cannot be defended | Report credits only; do not substitute a public price. |
| Analyzer rejects evidence | Malformed timestamp, negative/non-finite number, or incompatible shape | Correct the input from source evidence; never coerce it into a plausible value. |
| User requests mutation | New authority and impact review are required | Return a proposed change packet and stop before execution. |

## Examples

### “Why did warehouse credits jump last week?”

Collect the two warehouse surfaces over the same UTC window. The analyzer may report
`42.5 confirmed warehouse compute credits` and `11.2 credits at risk for idle-time
review`. It must not call all 11.2 credits waste or convert them to dollars without a
supplied rate.

### “Show costs by team from QUERY_TAG”

Aggregate `QUERY_ATTRIBUTION_HISTORY` by the existing tag. Report tagged and untagged
credits, the view's maximum timestamp, and exclusions such as idle, serverless, storage,
and cloud-services cost. Missing tags are an at-risk attribution gap, not proof of
unowned spend.

### “Create a monitor to shut down expensive warehouses”

Do not create or alter a monitor. Audit current warehouse evidence, explain the
warehouse-only coverage and suspension caveats from
[references/controls-boundaries.md](references/controls-boundaries.md), and return a
reviewable control proposal requiring explicit authorization.

## Resources

- [Attribution and staleness](references/attribution-and-staleness.md) — view coverage,
  latency, privilege, and invoice-reconciliation boundaries.
- [Warehouse and idle evidence](references/warehouse-and-idle-evidence.md) — bounded
  collection queries and normalization schema.
- [Controls boundaries](references/controls-boundaries.md) — resource-monitor and budget
  semantics, including uncovered serverless usage.
- [Pareto and right-sizing](references/pareto-and-right-sizing.md) — cost/latency
  frontier and bounded, one-variable resize review.
- [Output contract](references/output-contract.md) — evidence labels and review-packet
  format.
- [`scripts/analyze_cost_evidence.py`](scripts/analyze_cost_evidence.py) — deterministic
  validator, classifier, and renderer.
