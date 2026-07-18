---
name: clickhouse-incident-runbook
description: |
  ClickHouse incident response — triage, diagnose, and remediate server issues
  using system tables, kill stuck queries, and execute recovery procedures.
  Use when ClickHouse is slow, unresponsive, OOM-killed, out of disk, backing up
  merges, or producing errors in production and you need an on-call playbook.
  Trigger with "clickhouse incident", "clickhouse outage", "clickhouse down",
  "clickhouse emergency", "clickhouse on-call", "clickhouse broken".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- database
- analytics
- clickhouse
- olap
compatibility: Designed for Claude Code
---
# ClickHouse Incident Runbook

## Overview

Step-by-step procedures for triaging and resolving ClickHouse incidents using
built-in system tables and SQL commands. Start here: assess severity, run quick
triage, walk the decision tree, then jump to the matching remediation procedure.

## Prerequisites

- Network access to the ClickHouse HTTP interface (default port `8123`) or a
  working `clickhouse-client`.
- A user with rights to read `system.*` tables and issue `KILL QUERY` / `ALTER`.
- Shell access to the host or container for P1 restarts (`systemctl`, `docker`,
  or `kubectl`).

## Severity Levels

| Level | Definition | Response | Examples |
|-------|------------|----------|----------|
| P1 | ClickHouse unreachable / all queries failing | < 15 min | Server down, OOM, disk full |
| P2 | Degraded performance / partial failures | < 1 hour | Slow queries, merge backlog |
| P3 | Minor impact / non-critical errors | < 4 hours | Single table issue, warnings |
| P4 | No user impact | Next business day | Monitoring gaps, optimization |

## Instructions

Work the incident top to bottom: triage, classify with the decision tree, then
apply the matching procedure.

### 1. Quick triage (run first)

```bash
# 1. Is ClickHouse alive? (8123 is the default ClickHouse HTTP interface port)
curl -sf 'http://localhost:8123/ping' && echo "UP" || echo "DOWN"

# 2. Can it answer a query?
curl -sf 'http://localhost:8123/?query=SELECT+1' && echo "OK" || echo "QUERY FAILED"

# 3. Check ClickHouse Cloud status
curl -sf 'https://status.clickhouse.cloud' | head -5
```

```sql
-- 4. Server health snapshot (run if server responds)
SELECT
    version()                          AS version,
    formatReadableTimeDelta(uptime())  AS uptime,
    (SELECT count() FROM system.processes) AS running_queries,
    (SELECT value FROM system.metrics WHERE metric = 'MemoryTracking')
        AS memory_bytes,
    (SELECT count() FROM system.merges) AS active_merges;

-- 5. Recent errors
SELECT event_time, exception_code, exception, substring(query, 1, 200) AS q
FROM system.query_log
WHERE type = 'ExceptionWhileProcessing'
  AND event_time >= now() - INTERVAL 10 MINUTE
ORDER BY event_time DESC
LIMIT 10;
```

### 2. Decision tree — classify the failure

```
Server responds to ping?
├─ NO → Check process/container status, disk space, OOM killer logs
│       └─ Container/process dead → Restart, check logs
│       └─ Disk full → Emergency: drop old partitions, expand disk
│       └─ OOM killed → Reduce max_memory_usage, add RAM
└─ YES → Queries succeeding?
    ├─ NO → Check error codes below
    │   └─ Auth errors (516) → Verify credentials, check user exists
    │   └─ Too many queries (202) → Kill stuck queries, reduce concurrency
    │   └─ Memory exceeded (241) → Kill large queries, reduce max_threads
    └─ YES but slow → Performance triage below
```

### 3. Apply the matching remediation

Each branch maps to a full procedure (SQL + shell, copy-paste ready) in
[references/remediation-procedures.md](references/remediation-procedures.md):

- **P1: Server down / OOM** — inspect `dmesg`/`journalctl`, restart, verify.
- **P1: Disk full** — find largest tables, drop old partitions, check `system.disks`.
- **P2: Stuck queries** — inspect `system.processes`, `KILL QUERY` by id/user/elapsed.
- **P2: Too many parts** — check part counts, raise `parts_to_throw_insert`, batch inserts.
- **P2: Memory pressure** — rank by `memory_usage`, kill the largest, cap `max_memory_usage`.
- **P3: Replication lag** — inspect `system.replicas` for queue and replica gaps.

### 4. Collect evidence and communicate

Once mitigated, export the error window and post status updates. Templates and
`INTO OUTFILE` exports are in
[references/evidence-and-comms.md](references/evidence-and-comms.md).

## Output

Working through this runbook produces:

- A **severity classification** (P1–P4) and the identified failure class.
- **Remediation actions applied** — killed query ids, dropped partitions,
  restarted service, or adjusted settings.
- A **recovery confirmation** (`SELECT version()` / `SELECT 1` succeeds again).
- **Forensic artifacts** for the postmortem: `/tmp/incident-queries.json` and
  `/tmp/incident-metrics.tsv`, plus a filled-in postmortem document.

## Error Handling

| Symptom | Likely Cause | First Action |
|---------|-------------|--------------|
| All queries fail | Server down | Check process, restart |
| Inserts fail | Too many parts | `KILL QUERY` long merges, raise limit |
| Selects slow | Memory pressure | Kill large queries, add filters |
| Disk alerts | No TTL / no cleanup | Drop old partitions |
| Replication lag | Network / merge backlog | Check `system.replicas` |

If the server does not respond to `ping` at all, do not keep issuing SQL — move
straight to the P1 host-level checks (process, disk, OOM logs) before anything else.

## Examples

**Kill a runaway query (P2).** Triage shows one query pinning memory; classify as
"queries succeeding but slow", then from the stuck-query procedure:

```sql
KILL QUERY WHERE query_id = 'abc-123-def';
```

**Emergency disk reclaim (P1).** Ping fails and the host is out of disk; the
disk-full procedure drops the oldest partition to restore writes:

```sql
ALTER TABLE analytics.events DROP PARTITION '202301';
```

Full multi-step walkthroughs for every severity live in
[references/remediation-procedures.md](references/remediation-procedures.md); the
post-incident export and comms templates live in
[references/evidence-and-comms.md](references/evidence-and-comms.md).

## Resources

- [ClickHouse Cloud Status](https://status.clickhouse.cloud)
- [System Tables Reference](https://clickhouse.com/docs/operations/system-tables)
- [KILL QUERY](https://clickhouse.com/docs/sql-reference/statements/kill)
- Related skill: `clickhouse-data-handling` for data-compliance follow-up.
