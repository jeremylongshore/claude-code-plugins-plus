---
name: snowflake-pipeline-guardian
description: |
  Diagnose production Snowflake pipelines spanning tasks, task graphs, streams,
  dynamic tables, and Snowpipe. Use when a pipeline is stale, skipped, suspended,
  lagging, duplicating rows, failing after a schema/object change, or missing file
  notifications. The skill builds a read-only evidence graph, walks every supplied
  dependency branch, and returns an ordered recovery plan with
  post-fix invariants. It never resumes, refreshes, recreates, replays, deploys,
  or mutates Snowflake automatically. Trigger with "stream is stale", "task graph
  suspended", "dynamic table lag", "dynamic refresh failed", "Snowpipe not
  loading", "SYSTEM$PIPE_STATUS", "duplicate loads", or "schema drift".
allowed-tools: Read, Bash(python3:*)
argument-hint: "[redacted-pipeline-evidence.json]"
version: 2.2.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
tags: [saas, snowflake, pipelines, tasks, streams, dynamic-tables, snowpipe]
---

# Snowflake Pipeline Guardian

## Overview

Snowflake pipeline incidents cross object boundaries. A failed dynamic-table
refresh may be a consequence of a stale stream; a child task may be skipped
because its predecessor failed; a Snowpipe “no data” symptom may be a cloud-event
path mismatch rather than a COPY error. This skill turns the evidence into a
dependency paths and bounded hypotheses instead of treating every downstream red
status as a new incident or claiming that graph order proves causality.

The deterministic core is
[`scripts/analyze_pipeline_state.py`](scripts/analyze_pipeline_state.py). It
accepts a small JSON snapshot and emits findings, dependency order, recovery actions,
and invariants. Use it with pasted/redacted evidence when a connector or
Snowflake session is unavailable. Read
[`references/observability-queries.md`](references/observability-queries.md) for
the current read-only collection queries, and
[`references/recovery-matrix.md`](references/recovery-matrix.md) for recovery
tradeoffs.

## Hard boundaries

- Read-only diagnosis only. Never automatically run `ALTER TASK`, `EXECUTE TASK`,
  `ALTER DYNAMIC TABLE ... REFRESH`, `CREATE OR REPLACE STREAM`, `CREATE OR
  REPLACE TABLE`, `INSERT`, `MERGE`, `COPY`, `TRUNCATE`, or `DROP`.
- Never call a stale stream “fixed” because a task retry succeeded. A stale
  stream has an unconsumed-change gap; replacement and backfill require explicit
  data-loss reasoning and operator approval.
- Never call a dynamic table healthy from `TARGET_LAG` alone. Target lag is a
  freshness goal; compare actual lag, refresh duration, warehouse queueing, and
  upstream state.
- Never turn a missing privilege or missing history row into a healthy verdict.
  Label it unknown and ask for the narrowest additional read-only evidence.
- Redact credentials, tokens, private keys, payloads, PII, and presigned URLs from
  receipts. Query IDs, object names, timestamps, statuses, and error codes are the
  useful correlation fields.

## Prerequisites

Prefer the least-privileged role that can inspect the named objects. Depending on
the account's grants, read-only evidence may require database/schema `USAGE`,
object visibility, task/dynamic-table `MONITOR`, and access to the relevant
`INFORMATION_SCHEMA` functions. Do not prescribe `ACCOUNTADMIN` as a default.

Collect a timestamped, redacted snapshot with:

1. Nodes: `id`, `kind` (`TABLE`, `STREAM`, `TASK`, `DYNAMIC_TABLE`, or `PIPE`),
   status/state, and the error/query identifier when present.
2. Edges: `from` and `to`, or `upstream`/`source` fields on each node.
3. Streams: `stale`, `stale_after`, source object, append-only mode, and last
   consumer boundary.
4. Tasks: graph root/children, predecessor state, scheduled/completed time,
   error code/message, and query ID from `TASK_HISTORY`.
5. Dynamic tables: target/current lag, scheduling state, refresh mode and reason,
   refresh error/message, data timestamp, and refresh query ID.
6. Snowpipe: raw `SYSTEM$PIPE_STATUS` fields, stage/prefix, notification times,
   load errors, and correlated `COPY_HISTORY` rows.
7. Duplicate evidence: business key, event/file identity, duplicate count/rate,
   target uniqueness/MERGE semantics, idempotency status, and retry/replay boundary.
   Include task run history or explicit counts for SKIPPED and overlapping runs,
   plus notification duplicate counts when available. Do not include raw customer
   records.

Read [`references/privilege-and-boundaries.md`](references/privilege-and-boundaries.md)
before requesting additional access.

For current-versus-history reconciliation and freshness/completeness rules, read
[`references/current-state.md`](references/current-state.md). Current `SHOW`
metadata is separate from Account Usage history; report stale, incomplete, or
disagreeing surfaces instead of selecting one source silently.

For model-neutral live control-plane evidence, use the shared read-only collector:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface pipeline --connection <approved-readonly-profile> \
  --output ./snowflake-pipeline-collector.json
```

Pass the collector receipt as `collector_receipt` to the analyzer (or map its
`datasets.task_history`, `dynamic_table_refresh_history`, and `copy_history` rows
to nodes). It intentionally cannot infer graph edges or call `SYSTEM$PIPE_STATUS`;
supply those as separately collected, redacted evidence for the named pipe. If
`truncation_possible` is true, narrow or partition the window before claiming run
coverage or absence. An ingested receipt with no edges is incomplete, never a
healthy graph. The analyzer also binds the receipt to the exact vendored pipeline
SQL hash and expected Account Usage views; a self-consistent but foreign receipt
cannot prove completeness.

Collect the separate near-live control plane with the reviewed SHOW projection:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface pipeline-current --connection <approved-readonly-profile> \
  --output ./snowflake-pipeline-current.json
```

Attach that unmodified receipt at root key `current_state_receipt`, and map its
four datasets to `current_state.nodes`. Set `current_state.observed_at` to the
receipt's `collected_at`. The analyzer verifies the exact receipt schema, sources,
vendored template hashes, canonical receipt hash, freshness, row bounds, dataset
names, and reviewed projections. It then requires a one-to-one object identity,
kind, and status match between current nodes and receipt rows. Missing, stale,
truncated, altered, foreign, or payload-mismatched receipts fail closed and cannot
support evidence or graph completeness.

## Instructions

### 1. Identify the symptom and preserve evidence

Write down the exact object names, UTC incident window, user-visible symptom, and
searchable error text. Preserve the first failing query ID or pipe status before
any retry. If the user supplied only a downstream red status, ask for its
predecessor graph rather than guessing.

Use these read-only surfaces:

- Tasks: `SHOW TASKS`, `TASK_HISTORY`, and `TASK_DEPENDENTS`.
- Streams: `SHOW STREAMS` and `DESCRIBE STREAM`.
- Dynamic tables: `SHOW DYNAMIC TABLES`,
  `DYNAMIC_TABLE_REFRESH_HISTORY`, and `DYNAMIC_TABLE_GRAPH_HISTORY`.
- Snowpipe: `SYSTEM$PIPE_STATUS`, `COPY_HISTORY`, stage/prefix metadata, and
  cloud notification delivery evidence.

The exact queries and retention caveats are in
[`references/observability-queries.md`](references/observability-queries.md).

### 2. Run the deterministic classifier

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_pipeline_state.py" \
  --input ./snowflake-pipeline-evidence.json
```

The script is pure classification. Its report distinguishes observed evidence
from derived findings and includes all supplied dependency chains. Expected finding codes:

- `STREAM_STALE`: offset is outside retained change history or the stream reports
  stale. Plan replacement plus bounded, idempotent backfill; do not reset offsets
  silently.
- `CHANGE_TRACKING_MISSING`: incremental dynamic-table refresh cannot see source
  change history. Capture DDL and determine whether a full reinitialization is
  required.
- `SCHEMA_DRIFT`: incompatible columns/types, dropped source, or stream-read
  failure. Use additive/explicit migration reasoning and preserve object identity.
- `LAG_BREACH`: actual lag exceeds target lag. Separate upstream blockage from
  refresh-duration/warehouse capacity constraints.
- `TASK_SUSPENDED` / `TASK_FAILED`: inspect root/child state and predecessor
  completion. A child can be skipped because a parent failed; a retry can replay
  partial side effects.
- `DYNAMIC_REFRESH_FAILED`: refresh history contains an explicit failed run.
- `PIPE_NOTIFICATION_GAP` / `PIPE_LOAD_FAILURE`: distinguish event routing/path
  problems from file/COPY errors before replaying anything.
- `DUPLICATE_DELIVERY`: duplicate rows or rate are present. Find the first retry or
  replay boundary and prove target idempotence.
- `TASK_SKIPPED` / `TASK_OVERLAP`: task history exposes missed or concurrent schedule
  intervals; reconcile predecessor state, run group, and partial commits before a
  retry.
- `IDEMPOTENCY_UNPROVEN`, `DEDUPLICATION_UNVERIFIED`, and `REPLAY_RISK`: the evidence
  does not prove a stable delivery key, target uniqueness/MERGE behavior, or a bounded
  replay window. Hold replay and report the exact missing proof.
- `PIPE_NOTIFICATION_DUPLICATE`: notification identity repeats; reconcile it to file
  identity and `COPY_HISTORY` before replay.

### 3. Walk every supplied dependency branch

Read every entry in `causal_chains` from first to last. The classification
`dependency_order_not_proven_causality` is deliberate: an upstream finding is a
recovery candidate, not proof that it caused the endpoint symptom. Report every
independent branch. If `graph_complete` is false, list `dangling_edges`, call the
chain incomplete, and request the missing node/history before a root-cause claim.

### 4. Produce ordered recovery, not a command dump

For each finding, state:

1. What was observed and where it came from.
2. What is derived versus hypothesized.
3. The next read-only check that can disambiguate the cause.
4. The approved change/replay tier, if the operator asks for a runbook.
5. Data-loss, duplicate, compute-cost, or freshness tradeoffs.
6. The rollback or stop condition.

Use [`references/recovery-matrix.md`](references/recovery-matrix.md). A stale
stream, lost change-tracking history, or source replacement is never repaired by
blind retry. A task retry is considered only after partial-commit and idempotence
evidence. Snowpipe replay waits for file identity and target-key reconciliation.

### 5. Verify post-fix invariants

Do not declare success on a green task run alone. Collect fresh evidence and
verify the report’s invariants: complete graph, non-stale streams, retained
incremental history, successful predecessor chain, acknowledged freshness,
reconciled pipe/COPY/file history, zero unexplained duplicates, and a recorded
replay boundary.

## Output format

Return a compact incident receipt with:

- **Scope/time:** objects, UTC window, evidence sources, and privilege limitations.
- **Dependency chains:** every upstream-first node path, redacted error/status
  evidence, dangling edges, and an explicit not-proven-causality label.
- **Findings:** observed, derived classification, confidence, and unknowns.
- **Ordered recovery:** numbered read-only checks followed by explicitly approved
  change/replay tiers; no automatic mutation.
- **Post-fix invariants:** the checks that must be green before closure.
- **Data safety:** records at risk, duplicate risk, retention boundary, and
  rollback/stop condition.

## Error Handling

If the evidence file is malformed, the analyzer exits with code 2 and reports the
input error; fix the receipt rather than interpreting partial JSON. If Snowflake
access is unavailable, use a pasted/redacted snapshot and label collection source,
timestamp, and privilege gaps. If no finding is emitted, say “no matching signal
in supplied evidence,” not “pipeline healthy.” If the graph is disconnected,
report the dependency graph as incomplete and request the missing edge or predecessor
history. If a user requests an automatic resume, refresh, recreate, replay, or
DDL/DML action, stop at the approval boundary and return the read-only checks and
data-loss conditions that must precede it.

## Examples

### Stale stream behind a lagging dynamic table

Given `STREAM_STALE` on `orders_stream`, a failed `orders_task`, and
`LAG_BREACH` on `orders_dt`, report the stream as the earliest supplied upstream
finding and verify whether it explains the downstream symptom. Preserve its retention/offset evidence, plan a replacement plus bounded
idempotent backfill, and require fresh stream, task, lag, and duplicate invariants.
Do not recommend deleting the checkpoint or merely increasing `TARGET_LAG`.

### Snowpipe receives events but loads nothing

Given `SYSTEM$PIPE_STATUS` evidence that messages are received but not forwarded,
classify `PIPE_NOTIFICATION_GAP`, compare stage/prefix and cloud-event routing,
then reconcile file inventory to `COPY_HISTORY`. Do not replay every file until
file identity and target-key idempotence are proven.

## References

- [`references/observability-queries.md`](references/observability-queries.md) —
  current read-only SQL surfaces for every supported object.
- [`references/recovery-matrix.md`](references/recovery-matrix.md) — failure
  classes, ordered recovery, data-loss boundaries, and invariants.
- [`references/replay-and-overlap.md`](references/replay-and-overlap.md) — run
  overlap/skips, idempotency proof, deduplication, and replay holds.
- [`references/privilege-and-boundaries.md`](references/privilege-and-boundaries.md)
  — least-privilege, redaction, and advisory-mode rules.
- [`references/source-notes.md`](references/source-notes.md) — research scope and
  primary Snowflake documentation links; re-check live docs for current syntax.
- [`references/current-state.md`](references/current-state.md) — current control-plane
  metadata, history reconciliation, freshness, and graph completeness contract.
