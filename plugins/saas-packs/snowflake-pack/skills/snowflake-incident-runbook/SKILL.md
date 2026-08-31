---
name: snowflake-incident-runbook
description: 'Execute Snowflake incident response with triage, rollback, and postmortem
  using real SQL diagnostics.

  Use when responding to Snowflake outages, investigating query failures,

  or running post-incident reviews for pipeline failures.

  Trigger with phrases like "snowflake incident", "snowflake outage",

  "snowflake down", "snowflake on-call", "snowflake emergency".

  '
allowed-tools: Read, Grep, Bash(curl:*), Bash(snow connection test:*), Bash(snowsql:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- data-warehouse
- analytics
- snowflake
compatibility: Designed for Claude Code
---
# Snowflake Incident Runbook

## Overview

Coordinate evidence-first response to Snowflake connectivity, authentication,
query, warehouse, task, stream, and Snowpipe incidents. Separate Snowflake service
health from account configuration and downstream-system failures. Contain impact
with the least destructive reversible action, verify recovery at the data boundary,
and retain a complete timeline.

Use **Read** and **Grep** only on sanitized logs and approved runbooks. Use
`Bash(curl:*)` only for the official Snowflake status endpoint or an exact URL from
Snowflake's supported connectivity workflow. Use `Bash(snowsql:*)` only through an
approved named connection and a reviewed read-only SQL file; never place passwords,
private keys, tokens, or SQL containing sensitive literals on a command line.

## Prerequisites

- Organization-owned severity, response-time, escalation, evidence, and
  communication policies. Snowflake does not define the organization's incident SLA.
- Named incident commander, operations lead, communications lead, data owner,
  security contact, and cost/change approver as applicable.
- Approved read-only connection profile and least-privileged diagnostic role.
- Expected account, region, authentication method, workload role, warehouses,
  task graphs, streams, pipes, source-of-truth stores, and downstream consumers.
- UTC time source and a durable incident timeline with restricted access.
- Explicit approval boundary for task/warehouse suspension, resource-monitor
  changes, stream recreation, Time Travel recovery, routing, or replay.
- Recovery identifiers: last known-good query/task/load receipts and the current
  retention evidence for any object that might need Time Travel or `UNDROP`.

## Instructions

### Step 1: Declare scope and protect evidence

Record start time, observed impact, affected workloads/regions, detection source,
incident owner, and next update time. Capture exact query IDs, task graph/run IDs,
pipe names, load files, client errors, and login-failure UUIDs before retrying.

Redact query text, bind values, staged URLs, account identifiers, IP addresses, and
authentication material from broadly shared artifacts. Do not paste output from
unbounded history queries into chat or tickets.

### Step 2: Separate platform health from account health

Check the official [Snowflake status page](https://status.snowflake.com) for the
affected region/component and record its timestamp. A green status page does not
prove the account, identity provider, private-connectivity path, cloud storage,
warehouse, or workload is healthy.

From the affected execution environment, test the approved connection. With an
existing SnowSQL profile, a minimal read-only probe is:

```bash
snowsql -c incident-readonly \
  -q 'SELECT CURRENT_TIMESTAMP(), CURRENT_ACCOUNT(), CURRENT_REGION();'
```

Do not fall back to literal credentials or a guessed login URL. Use Snowflake CLI's
`snow connection test` or the Python Connector diagnostics for network isolation
when those are the organization's approved tools.

### Step 3: Bound the live history query

Use Information Schema query-history functions for current triage with a bounded
time window and `RESULT_LIMIT`. Use Account Usage for longer analysis, recognizing
that `QUERY_HISTORY` can lag by up to 45 minutes and `LOGIN_HISTORY` can lag by up
to 120 minutes. A missing fresh row in either delayed view is not proof of absence.

Select identifiers, status, error, context, and timing columns. Avoid `query_text`,
`bind_values`, and full login details unless specifically authorized. See
[incident diagnostics](references/incident-diagnostics.md) for reviewed queries.

### Step 4: Classify the incident path

- **Connectivity/authentication:** correlate client error, supported connection
  diagnostic, status evidence, login UUID, account identifier, `LOGIN_NAME`, clock,
  and key fingerprint or identity-provider evidence.
- **Queries/warehouse:** distinguish compilation, execution, queueing, blocking,
  spill, retry, cancellation, client fetch, and resource-monitor suspension.
- **Tasks:** query bounded `TASK_HISTORY`; account for function arguments being
  applied before outer filters and distinguish scheduled, running, skipped,
  failed, and canceled records.
- **Streams:** inspect `SHOW STREAMS`, especially `stale` and `stale_after`. After
  `stale_after`, a stream can become stale at any time; do not depend on a read that
  happens to succeed.
- **Snowpipe:** use `SYSTEM$PIPE_STATUS` and bounded `COPY_HISTORY` to distinguish
  queue/event problems, path/pattern mismatch, partial or failed loads, duplicates,
  and file-format/data errors.

### Step 5: Choose the least destructive containment

Contain one failing workload before changing shared infrastructure. Examples
include pausing the upstream producer, stopping a retry storm, suspending a verified
task or root graph under approval, or isolating a bad data batch.

Do not increase a resource-monitor credit quota, detach a monitor, switch to
unapproved compute, or resize a warehouse merely to make queries run. Resource
monitors can suspend standard warehouses at configured thresholds, but they do not
control every serverless/AI cost surface and are not exact per-credit controls.
Any cost-control change requires its owner and a reversal plan.

Do not `DROP` or `CREATE OR REPLACE` a stale stream during triage. When a stream is
truly stale, Snowflake requires recreation to resume tracking, and historical or
unconsumed change records are no longer accessible through that stream. First
identify an authoritative backfill source, exact boundary, deduplication key,
reconciliation query, and approved replay plan.

### Step 6: Recover without overwriting the evidence source

For suspected table corruption or a bad DML statement, create a separately named
Time Travel recovery clone in an isolated recovery schema using the approved
timestamp or statement ID. Never use `CREATE OR REPLACE` against the affected table
as the first recovery step. Validate row counts, keys, constraints, grants/policies,
and downstream expectations before an approved swap or repair.

Use `UNDROP` only within retained Time Travel history and only after checking name
conflicts and selecting the intended dropped object. If an object with the same name
exists, `UNDROP` fails; do not drop the replacement reflexively.

For a task graph, verify the graph and containment state before resumption.
Snowflake requires child tasks to be resumed before the root; the documented
`SYSTEM$TASK_DEPENDENTS_ENABLE` function can resume dependents from the root. Test
one controlled run and reconcile its side effects before restoring the schedule.

### Step 7: Verify end to end

Require new query/task/load identifiers and validate the real data boundary:

- representative read/write path succeeds under the workload identity;
- expected task graph steps complete once;
- pipe files show correct terminal status and row counts;
- stream/replay results reconcile without gaps or duplicates;
- warehouse/resource-monitor state matches the approved configuration; and
- downstream consumers meet the incident's recovery criteria.

Do not declare resolution from a successful connection or SQL status alone.

### Step 8: Communicate and learn

Publish updates on the organization's cadence with observed impact, current
hypothesis, evidence, containment, risk, owner, and next update. At closure, record
UTC timeline, root and contributing causes, detection/control gaps, recovery
receipts, customer/data impact, cost impact from authoritative billing evidence,
and owned corrective actions. Do not insert guessed credit totals or durations.

## Output

Produce an incident bundle containing:

- incident identifier, organization-defined severity, roles, scope, and UTC timeline;
- platform status and account/workload health evidence kept distinct;
- sanitized query, login, task, stream, pipe, warehouse, and destination receipts;
- hypotheses with supporting and contradicting evidence;
- every mutation's approver, exact target, before/after state, and reversal;
- recovery and end-to-end reconciliation evidence;
- current disposition: `INVESTIGATING`, `CONTAINED`, `MONITORING`, `RESOLVED`, or
  `ESCALATED`; and
- postmortem causes, impact, lessons, owners, due dates, and verification method.

## Examples

### Safe stale-stream decision

```markdown
- Observation: STALE is TRUE; STALE_AFTER is in the past
- Containment: upstream producer paused; affected task remains suspended
- Prohibited shortcut: no DROP/CREATE OR REPLACE executed
- Backfill source: authoritative immutable source identified
- Boundary: last reconciled business key and source timestamp retained
- Plan: create new stream after approved backfill, replay idempotently, reconcile
- Status: CONTAINED, not yet RESOLVED
```

### Safe table recovery

Create `INCIDENT_RECOVERY.USERS_BEFORE_BAD_DML` from the affected table at the
approved point before the bad statement. Validate that clone separately. Do not
overwrite `PROD.USERS` until the data owner approves the exact repair or swap and
the rollback path is proven.

## Error Handling

| Condition | Required response |
|---|---|
| Status page and account evidence disagree | Continue account/network triage; retain both timestamps |
| Diagnostic role lacks visibility | Request narrow evidence from an authorized operator; do not elevate silently |
| Delayed Account Usage view lacks fresh event | Use bounded Information Schema/current client evidence and mark latency |
| Resource monitor suspended compute | Preserve monitor evidence and obtain cost-owner approval before any change |
| Stream is or may be stale | Contain consumers; design source-specific recovery before recreation |
| Time Travel point is outside retention | Stop clone/undrop attempts and escalate to the data owner/support |
| Recovery clone does not reconcile | Leave production unchanged and investigate the selected point/boundary |
| Task graph run may duplicate side effects | Keep schedule contained until idempotency and destination state are proven |
| Evidence leaks sensitive data | Restrict/delete exposed copies under policy and issue a redacted replacement |

## Resources

- [Snowflake Status](https://status.snowflake.com)
- [Information Schema QUERY_HISTORY](https://docs.snowflake.com/en/sql-reference/functions/query_history)
- [Account Usage QUERY_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [TASK_HISTORY](https://docs.snowflake.com/en/sql-reference/functions/task_history)
- [Streams and staleness](https://docs.snowflake.com/en/user-guide/streams-intro)
- [Snowpipe troubleshooting](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-ts)
- [Resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
- [Time Travel clones](https://docs.snowflake.com/en/sql-reference/sql/create-clone)
- [UNDROP TABLE](https://docs.snowflake.com/en/sql-reference/sql/undrop-table)
- [Task graphs](https://docs.snowflake.com/en/user-guide/tasks-graphs)
