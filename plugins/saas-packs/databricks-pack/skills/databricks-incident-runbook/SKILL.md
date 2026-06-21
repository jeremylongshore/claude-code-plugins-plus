---
name: databricks-incident-runbook
description: 'Execute Databricks incident response procedures with triage, mitigation,
  and postmortem.

  Use when responding to Databricks-related outages, investigating job failures,

  or running post-incident reviews for pipeline failures.

  Trigger with phrases like "databricks incident", "databricks outage",

  "databricks down", "databricks on-call", "databricks emergency", "job failed".

  '
allowed-tools: Bash(databricks:*), Bash(curl:*), Bash(jq:*)
argument-hint: '[severity] [job_id?]'
version: 1.0.1
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- databricks
- incident-response
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---

> [!WARNING]
> **DEPRECATED — to be removed in `databricks-pack@2.0.0`.**
>
> This v1 skill is replaced in the v2 rebuild. **Migrate to:** `databricks-cluster-forensics` + `databricks-streaming-guardian`.
> See [the pack README → Migration: v1 → v2](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/blob/main/plugins/saas-packs/databricks-pack/README.md#migration-v1--v2) for the full map and rationale.

# Databricks Incident Runbook

## Overview

Rapid incident response for Databricks: triage script, decision tree, immediate actions by error type, communication templates, evidence collection, and postmortem template. Designed for on-call engineers to follow during live incidents.

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Production pipeline down | < 15 min | Critical ETL failed, data not updating |
| P2 | Degraded performance | < 1 hour | Slow queries, partial failures, stale data |
| P3 | Non-critical issues | < 4 hours | Dev cluster issues, non-critical job delays |
| P4 | No user impact | Next business day | Monitoring gaps, cleanup needed |

## Prerequisites

Before this runbook runs, the responder must have:

- **Databricks CLI v2** installed and on PATH (`databricks --version` returns ≥ 0.200.0). Install: `pip install databricks-cli` or `brew install databricks/tap/databricks-cli`.
- **Authentication** to the affected workspace via one of:
  - **PAT** (Personal Access Token) — `databricks configure --token`, paste a token from the workspace User Settings → Developer → Access Tokens page. Fastest for on-call; OK for short-lived incident sessions.
  - **OAuth U2M** — `databricks auth login --host https://<workspace>.cloud.databricks.com` for human-in-the-loop sessions with auto-refresh.
  - **OAuth M2M** — service principal client-credentials grant, for automated incident bots; env vars `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET`.
- **`jq`** on PATH (used to parse JSON from CLI output and status APIs). Install: `apt install jq` or `brew install jq`.
- **`curl`** on PATH (used to hit `status.databricks.com` and internal status pages). Comes standard on every modern Linux/macOS install.
- **Read permission** on the workspace's job runs + cluster events (granted by default to anyone with workspace access; not all workspaces enable strict RBAC). Without it the triage script returns empty `runs[]` arrays even when failures exist.
- **Workspace URL + workspace ID** known and recorded in the incident ticket — needed for the comms templates in `## Examples`.

If any of these is missing, fix it before starting triage. Running this skill without auth produces misleading output ("API: UNREACHABLE") that wastes early-incident minutes.

## Instructions

### Step 1: Quick Triage (Run First)

```bash
#!/bin/bash
set -euo pipefail
echo "=== DATABRICKS TRIAGE $(date -u +%H:%M:%S\ UTC) ==="

# 1. Is Databricks itself down?
echo "--- Platform Status ---"
curl -s https://status.databricks.com/api/v2/status.json | \
  jq -r '.status.description // "UNKNOWN"'

# 2. Can we reach the workspace?
echo "--- Workspace ---"
if databricks current-user me --output json 2>/dev/null | jq -r .userName; then
    echo "API: CONNECTED"
else
    echo "API: UNREACHABLE — check VPN/firewall/token"
fi

# 3. Recent failures
echo "--- Failed Runs (last 1h) ---"
databricks runs list --limit 20 --output json 2>/dev/null | \
  jq -r '.runs[]? | select(.state.result_state == "FAILED") |
    "\(.run_id): \(.run_name // "unnamed") — \(.state.state_message // "no message")"' || \
  echo "Could not fetch runs"

# 4. Cluster health
echo "--- Clusters in ERROR state ---"
databricks clusters list --output json 2>/dev/null | \
  jq -r '.[]? | select(.state == "ERROR") |
    "\(.cluster_id): \(.cluster_name) — \(.termination_reason.code // "unknown")"' || \
  echo "Could not fetch clusters"
```

### Step 2: Decision Tree

```
Is the issue affecting production data pipelines?
├─ YES: Is it a single job or multiple?
│   ├─ SINGLE JOB
│   │   ├─ Cluster failed to start → Step 3a
│   │   ├─ Code/logic error → Step 3b
│   │   ├─ Data quality issue → Step 3c
│   │   └─ Permission error → Step 3d
│   │
│   └─ MULTIPLE JOBS → Likely infrastructure
│       ├─ Check platform status (status.databricks.com)
│       ├─ Check workspace quotas (Admin Console)
│       └─ Check network/VPN connectivity
│
└─ NO: Is it performance?
    ├─ Slow queries → Check query plan, warehouse sizing
    ├─ Slow cluster startup → Check instance availability
    └─ Data freshness → Check upstream dependencies
```

### Step 3a: Cluster Failed to Start

```bash
CLUSTER_ID="your-cluster-id"

# Get termination reason
databricks clusters get --cluster-id $CLUSTER_ID | \
  jq '{state, termination_reason}'

# Check recent events
databricks clusters events --cluster-id $CLUSTER_ID --limit 10 | \
  jq '.events[] | "\(.timestamp): \(.type) — \(.details // "none")"'

# Common fixes:
# QUOTA_EXCEEDED → Terminate idle clusters
# CLOUD_PROVIDER_LAUNCH_FAILURE → Check instance availability in region
# DRIVER_UNREACHABLE → Network/security group issue

# Quick fix: restart
databricks clusters start --cluster-id $CLUSTER_ID
```

### Step 3b: Code/Logic Error

```bash
RUN_ID="your-run-id"

# Get run details and error
databricks runs get --run-id $RUN_ID | jq '{
  state: .state,
  tasks: [.tasks[]? | {key: .task_key, result: .state.result_state, error: .state.state_message}]
}'

# Get task output for failed tasks
databricks runs get-output --run-id $RUN_ID | jq '{
  error: .error,
  trace: (.error_trace // "" | .[0:1000])  # cap trace at 1000 chars so the postmortem payload stays under Slack's 4KB block limit and Datadog's 8KB event limit
}'

# Repair failed tasks only (skip successful ones)
databricks runs repair --run-id $RUN_ID --rerun-tasks FAILED
```

### Step 3c: Data Quality Issue

```sql
-- Quick data sanity check
SELECT COUNT(*) AS total_rows,
       COUNT(DISTINCT id) AS unique_ids,
       SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) AS null_amounts,
       MIN(created_at) AS oldest,
       MAX(created_at) AS newest
FROM prod_catalog.silver.orders
WHERE created_at > current_timestamp() - INTERVAL 1 DAY;

-- Check recent table changes
DESCRIBE HISTORY prod_catalog.silver.orders LIMIT 10;

-- Restore to previous version if corrupted
RESTORE TABLE prod_catalog.silver.orders TO VERSION AS OF 5;
```

### Step 3d: Permission Error

```bash
# Check current user
databricks current-user me

# Check job permissions
databricks permissions get jobs --job-id $JOB_ID

# Fix permissions
databricks permissions update jobs --job-id $JOB_ID --json '{
  "access_control_list": [{
    "user_name": "service-principal@company.com",
    "permission_level": "CAN_MANAGE_RUN"
  }]
}'
```

### Step 4: Communication

Post the internal Slack and external status-page updates. **Templates with cadence rules + executive-escalation form** are in [`references/communication-templates.md`](references/communication-templates.md). Copy the bracketed-field versions; consistency matters more than artistry under incident pressure.

### Step 5: Evidence Collection

Run the evidence-collection script to bundle `run.json` + `output.json` + (if cluster-side failure) `cluster.json` + `events.json` into a tarball for the postmortem. **Script + per-artifact reference** in [`references/evidence-collection.md`](references/evidence-collection.md).

### Step 6: Postmortem

Fill in the postmortem template within 48 hours of resolution. Archive to your team's incident-archive at `/incidents/<YYYY-MM-DD>-<slug>.md`. **Template + blameless-doc rules** in [`references/postmortem-template.md`](references/postmortem-template.md).

## Output

- Issue triaged and severity assigned
- Root cause identified via decision tree
- Immediate remediation applied
- Stakeholders notified with structured updates
- Evidence collected for postmortem

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach API | Token expired or VPN down | Re-auth: `databricks auth login` |
| `runs repair` fails | Run too old for repair | Create new run with same config |
| `RESTORE TABLE` fails | VACUUM already cleaned old versions | Restore from backup or replay pipeline |
| Cluster restart loops | Init script failing | Check cluster events for init script errors |

## Examples

### One-Line Health Checks

```bash
# Last 5 runs for a job
databricks runs list --job-id $JID --limit 5 | jq '.runs[] | "\(.state.result_state): \(.run_name)"'

# Quick cluster restart
databricks clusters restart --cluster-id $CID && echo "Restart initiated"

# Cancel all active runs for a job
databricks runs list --job-id $JID --active-only | jq -r '.runs[].run_id' | \
  xargs -I{} databricks runs cancel --run-id {}
```

## Resources

- [Databricks Status](https://status.databricks.com)
- [Support Portal](https://help.databricks.com)
- [Community Forum](https://community.databricks.com)

## Next Steps

- **For data handling + compliance** (GDPR deletion, PII masking, retention) post-incident: see `databricks-data-handling`.
- **For root-cause analysis on cluster-side failures** (OOM, cold starts, spot interruptions): see `databricks-cluster-forensics` once that skill ships in v2.
- **For cost-impact accounting** of the incident window (job-cluster restarts, all-purpose-cluster fallbacks during the outage): see `databricks-cost-leak-hunter` (pilot v2 skill).
- **For permanent observability** so the next incident gets caught earlier: see `databricks-observability` for system-table alerting + Prometheus integration.
- **Postmortem template** is `## Output` § 4 above; archive completed postmortems to the team's incident-archive tag in the workspace (`/incidents/<YYYY-MM-DD>-<slug>.md`).
