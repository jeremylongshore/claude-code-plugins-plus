---
name: snowflake-cost-leak-hunter
description: >-
  Audit Snowflake warehouse and query-attribution evidence to locate idle compute,
  unallocated or untagged usage, query-acceleration spend, and serverless visibility
  gaps without guessing prices or savings. Use when a Snowflake bill increased, a
  team needs chargeback/showback evidence, warehouse credits appear unexplained, or
  an operator asks which usage merits investigation. Trigger with "Snowflake bill
  increased", "find idle Snowflake credits", "Snowflake cost attribution", or
  "untagged Snowflake spend". Do not use to change warehouse size, suspend compute,
  create resource monitors, or claim invoice reconciliation.
allowed-tools: Read, Write, Bash(python3:*)
argument-hint: "[evidence-json-or-output-directory]"
model: inherit
effort: high
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
  - saas
  - data-warehouse
  - analytics
  - snowflake
  - finops
compatibility: Designed for Claude Code
---

# Snowflake Cost Leak Hunter

## Overview

Produce a read-only, evidence-first Snowflake cost investigation. Report observed
credits, derived currency estimates, and remediation opportunities as different
classes; never collapse them into one savings claim.

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

## Instructions

### 1. Fix scope before querying

Capture:

- account and role;
- half-open UTC window `[window_start, window_end)`;
- requested attribution dimension, such as warehouse, user, query tag, or service;
- whether an approved contract rate card is available;
- whether Adaptive Warehouses or serverless features are in scope.

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
keeps three result classes separate:

- **Confirmed observations** — credits present in supplied Snowflake evidence.
- **Estimated amounts** — currency conversions using an explicitly supplied rate-card
  entry, always labeled with that entry's provenance.
- **At-risk opportunities** — observed idle/unattributed compute or untagged query
  usage that merits review; not promised savings.

It does not apply magnitude thresholds, infer a price, or recommend a warehouse size.

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
- a currency request has no applicable contract rate;
- evidence contains negative credits, malformed timestamps, or incompatible currencies;
- the only proposed next step would mutate production.

## Error Handling

| Condition | Meaning | Required response |
|---|---|---|
| Approved role cannot read a required view | Coverage unavailable | Preserve the sanitized error, name the missing surface, and stop that branch without changing grants. |
| Source maximum time trails the requested window | Recent evidence may be incomplete | Report observed age and return a partial result; do not convert missing rows to zero. |
| Attributed-query credits are NULL | Idle/unattributed calculation is unsupported for that row | Exclude the row from that calculation and explain the platform/account limitation. |
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
- [Output contract](references/output-contract.md) — evidence labels and review-packet
  format.
- [`scripts/analyze_cost_evidence.py`](scripts/analyze_cost_evidence.py) — deterministic
  validator, classifier, and renderer.
