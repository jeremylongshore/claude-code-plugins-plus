---
name: snowflake-pipeline-guardian
description: |
  Analyze Snowflake pipelines spanning tasks, streams, dynamic tables, and
  Snowpipe from bounded read-only evidence. Use when a pipeline is stale,
  skipped, suspended, lagging, duplicating rows, or missing notifications;
  trigger with "stream stale", "task suspended", "dynamic table lag", or
  "Snowpipe not loading". The skill returns evidence gaps, bounded hypotheses,
  and an ordered recovery plan; it never mutates Snowflake.
allowed-tools: Read, Bash(python3:*)
argument-hint: "[pipeline-evidence-bundle.json]"
version: 3.16.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Model-agnostic workflow; requires Python 3.10+; optional Snowflake CLI for live read-only evidence collection
tags: [saas, snowflake, pipelines, tasks, streams, dynamic-tables, snowpipe]
---

# Snowflake Pipeline Guardian

## Overview

Pipeline symptoms cross object boundaries, but dependency order does not prove
causality. This skill classifies a bounded evidence bundle, walks supplied
dependency paths, and keeps observed facts, derived findings, hypotheses, and
unknowns separate.

Use [`scripts/analyze_pipeline_state.py`](scripts/analyze_pipeline_state.py) for
deterministic classification. Read
[`references/current-state.md`](references/current-state.md) before collecting
live evidence and
[`references/recovery-matrix.md`](references/recovery-matrix.md) before writing a
recovery plan.

## Hard boundaries

- Read-only diagnosis only. Never execute or emit runnable DDL, DML, task
  execution, refresh, resume, stream replacement, pipe refresh, or replay SQL.
- Never call an empty, privilege-hidden, stale, capped, context-mismatched, or
  untrusted result healthy or complete.
- Never treat current control-plane state as historical run proof, or lagged
  Account Usage history as current state.
- Never infer causality from graph order or a current/history disagreement.
- Never request or retain raw SQL text, object names, query IDs, file or stage
  paths, notification endpoints, integration names, free-text errors, or raw
  `SYSTEM$PIPE_STATUS` JSON. Use the reviewed hashed projections only.
- Never use `SYSTEM$STREAM_HAS_DATA` for diagnosis; calling it can affect a
  stream's staleness behavior.
- Treat hashes as pseudonymous operational data, not anonymization.

## Trusted evidence contract

The live collector has six reviewed schema-2 surface types:

1. `pipeline`: explicit half-open UTC history for task runs, dynamic-table
   refreshes, and copy loads.
2. `pipeline-task-current`: current role-visible task inventory.
3. `pipeline-stream-current`: current role-visible stream inventory.
4. `pipeline-dynamic-table-current`: current role-visible dynamic-table
   inventory.
5. `pipeline-pipe-current`: current role-visible pipe inventory.
6. `pipeline-pipe-status`: one selector-bound, privacy-projected status receipt
   for each pipe in the current pipe inventory; zero status receipts are correct
   only when that inventory is empty.

Each receipt must be live CLI output with exactly one same-statement
`execution_context`, the reviewed SQL/template/result hashes, exact datasets,
finite documented state/status domains, the exact fixed `non_claims`, the
declared cap, no collector error, and a valid self-hash. Invalid receipts never
reach finding classification. All receipts must
agree on organization/account, collector user, primary role and role type,
secondary roles, and UTC timezone. Their observations may span at most 15
minutes and may be at most 15 minutes old.

Receipt self-hashes are integrity checks, not trust anchors. Put the complete
receipts in one `collector_receipts` array, calculate the canonical bundle digest
at a separate trusted local boundary, record it separately, and then supply it to
the analyzer:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_pipeline_state.py" \
  --input ./pipeline-evidence-bundle.json --print-input-sha256

python3 "${CLAUDE_SKILL_DIR}/scripts/analyze_pipeline_state.py" \
  --input ./pipeline-evidence-bundle.json \
  --trusted-input-sha256 "sha256:<separately-recorded-digest>" \
  --evaluated-at "<explicit-UTC-evaluation-time>"
```

A matching digest proves only byte identity with the operator-recorded bundle.
It is not a signature, collector identity, or proof of Snowflake origin.
Offline-normalized pipeline receipts are diagnostic-only and cannot support
positive completeness claims.

## Prerequisites

Choose an explicit UTC history window no longer than seven days. Both bounds are
required and the end is exclusive:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface pipeline --connection <approved-readonly-profile> \
  --window-start <window-start-UTC> \
  --window-end <exclusive-window-end-UTC> \
  --output ./pipeline-history.json
```

Collect each current inventory surface once under the same authorization
context:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface pipeline-task-current --connection <approved-readonly-profile> \
  --output ./pipeline-task-current.json
```

Repeat with `pipeline-stream-current`, `pipeline-dynamic-table-current`, and
`pipeline-pipe-current`. For every hash in `current_pipes`, collect exactly one
status receipt using its corresponding validated three-part unquoted identifier
inside the trusted operator environment:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect_snowflake_evidence.py" \
  --surface pipeline-pipe-status --connection <approved-readonly-profile> \
  --pipe DATABASE.SCHEMA.PIPE --output ./pipeline-pipe-status.json
```

The raw pipe selector is not receipt evidence. A successful receipt binds its
fingerprint to the account-scoped object hash and hashes a receipt-only SQL
rendering where that scoped hash replaces the selector. The analyzer recomputes
both bindings. An error receipt retains only the reviewed template digest and a
null selector fingerprint, so it cannot expose a dictionary-testable pipe name.
Do not place the raw identifier in the bundle. History-window timestamps are safe
selector values and are retained so the analyzer can recompute the rendered
history-query digest.

History is capped independently at 5,000 task, refresh, and copy rows. Current
inventories are capped at 10,000 objects each; reaching a cap is incomplete.
Task completions are considered settled only through observation minus 45
minutes, completed dynamic-table refreshes through observation minus 3 hours,
and completed copy loads through observation minus 48 hours. Executing refreshes
are excluded. The receipt records each exact `settled_through_utc`. Evidence
after a settlement cutoff is unknown, not absent.

See [`references/observability-queries.md`](references/observability-queries.md)
for the exact field and nonclaim map, and
[`references/privilege-and-boundaries.md`](references/privilege-and-boundaries.md)
before requesting access.

## Instructions

1. Establish the UTC incident window, affected pseudonymous object key, symptom,
   and existing privilege limits. Preserve the trusted bundle before any change.
2. Supply and report one explicit `evaluated_at`, then check `evidence_trust`,
   `collector_ingestion`, `evidence_coverage`, `evidence_gaps`, and
   `graph_complete` before reading findings. A validated six-surface bundle is
   still only role-visible evidence; it does not prove account-wide inventory.
3. Walk every supplied dependency branch upstream. Label graph order
   `dependency_order_not_proven_causality`; list missing nodes and edges instead
   of guessing.
4. Separate current state from settled history. A current task state cannot fill
   a history latency gap, and absence from settled history cannot establish that
   a current object never ran.
5. Produce read-only disambiguation checks and a recovery plan with approval,
   data-loss, duplicate, cost, rollback, and stop boundaries. Do not emit the
   mutation commands.
6. After an operator-approved change, recollect all required surfaces and create
   a new independently digested bundle. A single green run is not recovery proof.

Key finding families include streams that may be stale, confirmed stale streams,
suspended or failed tasks, dynamic-refresh failures and lag breaches, pipe
notification/load gaps, partial/failed/skipped copy loads, skipped or overlapping
task runs, duplicate delivery, and unproven replay idempotence. Missing settled
evidence produces an unknown, never a healthy finding.

## Output

Return a compact incident receipt containing:

- trusted-input status, receipt surfaces, UTC window, settlement cutoffs, caps,
  and privilege limitations;
- pseudonymous dependency paths with an explicit not-proven-causality label;
- observed facts, derived findings, hypotheses, and unknowns;
- ordered read-only checks and a separately approval-gated recovery plan;
- post-change evidence requirements, duplicate/data-loss risk, and stop criteria.

Do not echo receipt rows, selectors, raw identifiers, or collector error text.

## Error Handling

If the input is malformed, untrusted, stale, incomplete, capped, or inconsistent,
report the exact evidence class that failed and suppress positive claims. If no
finding matches, say “no matching signal in supplied evidence,” not “pipeline
healthy.” If collection fails, preserve the sanitized error code locally and
report that the affected surface is unavailable; never paste free-text CLI or
Snowflake errors into the incident receipt.

## Examples

- A current task is suspended while its matching task-history interval is still
  inside the 45-minute latency tail: report the current state as observed and the
  historical cause as unknown.
- One pipe lacks its selector-bound status receipt: report pipe coverage
  incomplete even when every other surface and the bundle digest validate.

## References

- [`references/current-state.md`](references/current-state.md) — schema-2 bundle,
  freshness, settlement, caps, and current/history nonclaims.
- [`references/observability-queries.md`](references/observability-queries.md) —
  six reviewed read-only surfaces.
- [`references/recovery-matrix.md`](references/recovery-matrix.md) — recovery
  tradeoffs and invariants.
- [`references/replay-and-overlap.md`](references/replay-and-overlap.md) — replay,
  overlap, and idempotency holds.
- [`references/privilege-and-boundaries.md`](references/privilege-and-boundaries.md)
  — least privilege, privacy, and mutation boundaries.
- [`references/source-notes.md`](references/source-notes.md) — official Snowflake
  sources and review date.
