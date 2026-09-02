---
name: snowflake-query-forensics
description: >-
  Audit, analyze, and diagnose completed or failed Snowflake queries from query history, Query Insights,
  and GET_QUERY_OPERATOR_STATS evidence. Use when investigating slow queries, queueing, lock waits,
  local or remote spill, poor pruning, exploding joins, repeated query-hash regressions,
  or requests for a defensible query root-cause packet. Trigger with "Snowflake query
  spilled", "why is this Snowflake query queued", "Snowflake query ID", "exploding
  join", or "Snowflake pruning regression". Do not use for generic SQL tutoring,
  automatic query rewrites, warehouse resizing, cancellation, or clustering changes.
allowed-tools: Read, Write, Bash(python3:*)
argument-hint: "[query-id-or-evidence-json]"
model: inherit
effort: high
version: 3.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
  - saas
  - data-warehouse
  - analytics
  - snowflake
  - performance
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
---

# Snowflake Query Forensics

## Overview

Build a read-only query root-cause packet from platform evidence. Distinguish observed
facts, derived metrics, and hypotheses; isolate one variable for any later experiment.

**Problem:** A slow elapsed time does not identify whether compilation, execution,
queueing, blocking, spill, pruning, or query shape is responsible, and some diagnostic
surfaces are delayed or unavailable for particular query classes.

**Outcome:** A query-scoped packet that ranks observed operator evidence, preserves
competing explanations, and defines the next read-only check without changing SQL or
compute.

## Prerequisites

- An exact query ID, bounded candidate set, or sanitized exported evidence file.
- Sanitized output collected by an operator through an approved read-only Snowflake
  session, or an equivalent exported evidence bundle.
- A role with visibility to the selected history surface; `OPERATE` or `MONITOR` on the
  warehouse when operator statistics are required.
- A completed query within the documented operator-stat retrieval window for operator
  analysis.
- One Snowflake UUID query ID repeated on the anchor history, operator-statistics, and
  Query Insights rows, plus a positive source-freshness bound in seconds.
- A writable local working directory. Use `Write` only for new local evidence and
  report artifacts; never use it to alter SQL or Snowflake state.

## Safety and evidence contract

- **Read-only only.** Do not cancel queries, resize/resume/suspend warehouses, alter
  clustering, enable acceleration/search optimization, modify SQL, or change session or
  account policy on the user's behalf.
- **Do not invoke Snowflake authentication from this skill.** The operator runs the
  bounded collection queries through an approved read-only session and supplies only
  sanitized results. Never request environment variables, connection files, tokens,
  passwords, or keys.
- **Do not require `ACCOUNTADMIN`.** Query-history visibility and operator-stat access
  depend on the approved role. `GET_QUERY_OPERATOR_STATS` requires `OPERATE` or
  `MONITOR` on the warehouse. Report missing access; do not grant it.
- **Operator evidence exists only for completed queries and only within the platform's
  documented retrieval window.** Do not invent operator findings for running, too-old,
  or inaccessible queries. Every nonterminal query is a partial packet even when no
  operator or insight rows were supplied. A terminal full-evidence packet requires at
  least one bound operator row; otherwise binding is incomplete, completeness is blocked,
  and confirmed/derived/hypothesis sections stay empty.
- **History surfaces have different windows and latency.** Account Usage query history
  can lag; Information Schema history is more immediate but narrower. Record which
  surface produced every field. The normalized `metadata.history_source` and `role` must
  exactly match the receipted anchor row and source; a digest cannot repair a semantic
  mismatch.
- **Do not mix anchor evidence across query IDs.** Snowflake documents query IDs as UUID
  text strings; require that form and reject a history, operator, or insight row that
  names another query. Exclude an operator or insight row with no query ID and block
  completeness until the evidence is recollected with its anchor. Aligned comparison
  runs legitimately use other Snowflake UUID query IDs; keep them in `query_runs`, never
  attribute them to the anchor, and require the explicit comparison-alignment fields.
- **Query text is sensitive.** Do not export it by default. Use query ID, hashes,
  sanitized operator attributes, and an operator-approved redacted SQL fragment only
  when needed. The analyzer rejects unsafe identifier fields and recursively redacts
  credential-bearing or raw-SQL-like scalar text before either JSON or Markdown output,
  using a syntax-aware boundary: any explicit Authorization/Proxy-Authorization value,
  plus headerless standardized schemes (including the registered SCRAM-SHA-1/SHA-256 family) only when the token shape or a recognized sensitive
  parameter supplies credential evidence (ordinary capability/status words stay visible), password/token
  tails, and tokenized Snowflake statement families (including chained diagnostic/statement labels,
  empty prefixes, positional or named binds, quoted file URIs, object modifiers, and DML
  scripting across the full recognized statement-verb family). Ordinary authentication/OAuth status
  evidence, request counters, and prose beginning with “Select” must remain visible.
  Credential-adjacent `has_*` metadata is safe only when its value is an actual boolean.
- **No universal thresholds.** Record exact queue time, spill bytes, partitions, row
  counts, and operator-time percentages. Compare against the same workload's baseline
  or a user-supplied objective; do not invent “slow,” “high,” or “bad” cutoffs.

Before collection, read
[references/history-and-collection.md](references/history-and-collection.md). For a
completed query, read [references/operator-statistics.md](references/operator-statistics.md).
When Query Insights is available, read
[references/query-insights-boundaries.md](references/query-insights-boundaries.md).

For bounded live history collection, use the shared read-only collector with an
approved Snowflake CLI profile:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface query --connection <approved-readonly-profile> \
  --source-max-age-seconds <positive-incident-bound> \
  --output snowflake-query-collector.json
```

Use normalized input schema `2.0` and collector receipt schema `2`. Before analysis,
apply the complete contract in
[History and collection](references/history-and-collection.md), including exact anchor
UUID, source, role, source-specific terminal status, anchor-only maximum time, reviewed
SQL cap, and an independently preserved input digest. Treat an embedded checksum as
consistency evidence, never authenticity. A missing or mismatched receipt field, stale
anchor, cap hit, truncation, or absent external digest blocks confirmed, completeness,
comparison, regression, and ROI claims. Keep aligned comparison runs in `query_runs`;
do not attribute them to the anchor. Narrow or partition any truncated collection before
making workload or absence claims.

## Instructions

Follow this sequence:

1. Anchor the investigation to a query ID or bounded candidate set.
2. Select the history surface and record its freshness boundary.
3. Have the operator collect the minimal redacted history, operator, and insight
   fields through the approved read-only session.
4. Assemble the normalized bundle and record its digest at the trusted local boundary.
5. Run the deterministic analyzer with the separately preserved digest.
6. Corroborate every causal hypothesis against a competing explanation.
7. Deliver the read-only root-cause packet and stop before mutation.

### 1. Anchor the investigation

Require at least one of:

- exact query ID;
- bounded UTC window plus user, warehouse, tag, or query hash;
- a sanitized exported evidence JSON file.

Capture the symptom, expected behavior, comparison query/run if available, account,
role, warehouse, execution state, and source timestamps. If the user only says “queries
are slow,” first identify a bounded candidate set; do not scan unbounded history.

### 2. Select the evidence surface

- Use the Information Schema query-history function for recent client-generated query
  discovery when its narrower retention and row behavior fit the task.
- Use `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` for longer historical comparisons, while
  disclosing its documented latency.
- Use `QUERY_INSIGHTS` only as an additional platform-detected signal; absence of an
  insight does not prove absence of a problem.
- Use `GET_QUERY_OPERATOR_STATS(QUERY_ID)` only after confirming the query completed,
  is within the supported retrieval window, and the role has warehouse visibility.

Use only the source-specific terminal statuses listed in
[History and collection](references/history-and-collection.md). Unknown, running,
queued, blocked, and warehouse-resume states remain nonterminal and fail closed. The
bundled collector receipts Account Usage; Information Schema discovery remains partial
without its own reviewed matching receipt.

The detailed choice table and bounded SQL are in
[references/history-and-collection.md](references/history-and-collection.md).

### 3. Collect a minimal redacted bundle

Collect only fields needed to distinguish:

- compilation, execution, queue-overload, provisioning, repair, and transaction-blocked
  time;
- bytes scanned/written and partitions scanned/total;
- local and remote spill;
- operator input/output rows and time breakdown;
- warehouse name/size as observed at execution time;
- query hash/parameterized hash for comparison;
- platform Query Insight type IDs and messages.

Exclude raw query text by default. If literals or object names are relevant, have the
operator provide a redacted fragment separately.

### 4. Run the deterministic classifier

Normalize the bundle to the schema in
[references/operator-statistics.md](references/operator-statistics.md), then run:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_query_evidence.py" \
  --input query-evidence.json \
  --json-out query-forensics.json \
  --markdown-out query-forensics.md
```

The analyzer emits:

- **Confirmed observations** — raw, positive delay/spill/insight/operator-time evidence
  supplied by Snowflake.
- **Estimated or derived metrics** — deterministic ratios such as join output/input and
  partitions scanned/total; these remain contextual, not severity judgments.
- **At-risk hypotheses** — possible causes that require corroboration, such as query
  shape versus warehouse capacity for spill or expected full scans versus missed
  pruning.

It never rewrites SQL, chooses a warehouse size, or assigns a root cause from a single
metric.

### 5. Build competing explanations

For every hypothesis, include at least one competing explanation and the next read-only
test. Examples:

- Remote spill: query shape or capacity pressure; compare the same query hash and data
  volume before proposing resize.
- Join expansion: valid many-to-many semantics or missing/incorrect join condition;
  inspect approved redacted predicates and baseline row counts.
- Full partition scan: required full-table workload or ineffective pruning; compare the
  filter and table layout without changing clustering.
- Queue time: concurrency pressure, warehouse provisioning, or workload placement;
  correlate the same interval before changing capacity.
- Transaction block: identify blocker/waiter evidence and ownership; do not terminate a
  session automatically.

### 6. Produce a query root-cause packet

Use [references/output-contract.md](references/output-contract.md). Required contents:

- query identity, execution state, collection role, and source freshness;
- timeline decomposition;
- top operators by observed time contribution;
- confirmed observations, derived metrics, and hypotheses in separate sections;
- Query Insights with their documented limitations;
- warehouse load and queue correlation for the same interval;
- query-hash/parameterized-hash comparisons across aligned runs;
- pruning fractions plus Search Optimization Service (SOS) ROI only when before/after
  latency or scan evidence and maintenance credits are supplied;
- comparison to a baseline only when inputs are aligned;
- one-variable experiment plan with owner approval;
- explicit statement that no mutation occurred.

## Validation

Before delivery, verify that the packet names the query ID and evidence surfaces, gives
actual source timestamps, reports `evidence_binding: BOUND` and `source_freshness:
FRESH` before making a completeness claim, contains no raw query text or credentials,
includes at least one operator row bound to a surface-compatible terminal query, and
keeps all three confidence classes separate. Re-run the analyzer on the saved
normalized JSON; the machine-readable result must be identical for identical input. If
a proposed experiment appears, confirm it changes one variable, uses a user-supplied
success objective, names an approver, and has not been executed.

## Output

Return `query-forensics.json` and `query-forensics.md` in the user's chosen working
directory, plus the exact analyzer command used. The packet includes identity and
freshness, confirmed observations, estimated/derived metrics, at-risk hypotheses, top
operators, warnings, non-claims, and a one-variable experiment proposal only when the
user supplies a success objective. Do not write runtime output into the skill directory.

## Stop conditions

Return a partial or inconclusive packet rather than guessing when:

- the query ID is missing and the history request is unbounded;
- the query is running, older than the operator-stat window, or operator access fails;
- Account Usage is too delayed for the incident window;
- secure objects, Native Apps, reused results, multi-step plans, or other documented
  Query Insights exclusions apply;
- operator JSON is absent or malformed;
- the comparison run differs in data window, query hash, parameters, warehouse behavior,
  or cache state in ways that prevent a defensible conclusion;
- the next action would mutate production without new authorization.

## Error Handling

| Condition | Meaning | Required response |
|---|---|---|
| Query ID cannot be found | Wrong surface/window/account, retention, latency, or visibility may apply | Check scope and freshness; return unknown rather than “query did not run.” |
| Query is running or too old | Operator statistics are not available | Produce a history-only partial packet and state the missing operator boundary. |
| `GET_QUERY_OPERATOR_STATS` privilege failure | Approved role lacks warehouse `OPERATE`/`MONITOR` | Preserve the sanitized error and request owner review; do not grant privileges. |
| No Query Insights row | Exclusion, availability, timing, or no supported signal are all possible | State which interpretation is supported; never certify health from absence. |
| Analyzer rejects evidence | Negative/non-finite counters, malformed timestamps, or invalid objects | Correct from source data; do not coerce or invent fields. |
| User demands resize, rewrite, cancellation, or clustering change | Mutation exceeds this skill's authority | Return evidence and an approval-bounded experiment proposal, then stop. |

## Examples

### “This query spilled remotely after yesterday’s release”

Confirm the query completed, collect operator statistics, and report the exact remote
spill bytes and affected operator. Compare the same parameterized hash and aligned data
volume. Return query-shape and capacity-pressure hypotheses separately; do not resize.

### “Why did this MERGE wait for ten minutes?”

Decompose queue and transaction-blocked time from query history. If blocked time is
present, identify the relevant transaction evidence through approved read-only surfaces.
Do not cancel the blocker. The packet names the blocker owner and escalation path.

### “Snowflake shows no Query Insights, so the query is healthy”

Reject that inference. Query Insights has documented exclusions. Use history and
operator evidence, and report whether insights were unavailable, inapplicable, absent,
or actually returned no rows.

## Resources

- [History and collection](references/history-and-collection.md) — source selection,
  latency, privileges, and redaction.
- [Operator statistics](references/operator-statistics.md) — normalized fields and
  defensible interpretations.
- [Query Insights boundaries](references/query-insights-boundaries.md) — official
  insight types and exclusions.
- [Load, hash, pruning, and SOS](references/load-hash-and-sos.md) — aligned load,
  fingerprint, operator, pruning, and Search Optimization evidence.
- [Output contract](references/output-contract.md) — root-cause packet structure and
  confidence labels.
- [`scripts/analyze_query_evidence.py`](scripts/analyze_query_evidence.py) — deterministic
  evidence validator and classifier.
