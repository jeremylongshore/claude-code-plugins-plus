---
name: databricks-incident-runbook
description: |
  Execute Databricks incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Databricks-related outages, investigating job failures,
  or running post-incident reviews for pipeline failures.
  Trigger with phrases like "databricks incident", "databricks outage",
  "databricks down", "databricks on-call", "databricks emergency", "job failed".
allowed-tools: Read, Grep, Bash(databricks:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, incident-response]

---
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
  trace: (.error_trace // "" | .[0:1000])
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

#### Internal (Slack)
```
:red_circle: **P1 INCIDENT: [Brief Description]**

**Status:** INVESTIGATING
**Impact:** [What data/users are affected]
**Started:** [Time UTC]
**Current Action:** [What you're doing now]
**Next Update:** [+30 min]

**IC:** @[your-name]
```

#### External (Status Page)
```
**Data Pipeline Delay**
We are experiencing delays in data processing.
Dashboard data may be up to [X] hours stale.
Started: [Time] UTC
Status: Actively investigating
Next update: [Time] UTC
```

### Step 5: Evidence Collection
```bash
#!/bin/bash
INCIDENT_ID=$1
RUN_ID=$2
CLUSTER_ID=$3

mkdir -p "incident-$INCIDENT_ID"

# Collect everything
databricks runs get --run-id $RUN_ID --output json > "incident-$INCIDENT_ID/run.json" 2>&1
databricks runs get-output --run-id $RUN_ID --output json > "incident-$INCIDENT_ID/output.json" 2>&1

if [ -n "$CLUSTER_ID" ]; then
    databricks clusters get --cluster-id $CLUSTER_ID --output json > "incident-$INCIDENT_ID/cluster.json" 2>&1
    databricks clusters events --cluster-id $CLUSTER_ID --limit 50 --output json > "incident-$INCIDENT_ID/events.json" 2>&1
fi

tar -czf "incident-$INCIDENT_ID.tar.gz" "incident-$INCIDENT_ID"
echo "Evidence: incident-$INCIDENT_ID.tar.gz"
```

### Step 6: Postmortem Template
```markdown
## Incident: [Title]

**Date:** YYYY-MM-DD | **Duration:** Xh Ym | **Severity:** P[1-4]
**IC:** [Name]

### Summary
[1-2 sentences: what happened and what was the impact]

### Timeline (UTC)
| Time | Event |
|------|-------|
| HH:MM | Alert fired / issue detected |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Resolved |

### Root Cause
[Technical explanation]

### Impact
- Tables affected: [list]
- Data staleness: [hours]
- Users affected: [count/teams]

### Action Items
| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| P1 | [Preventive fix] | [Name] | [Date] |
| P2 | [Monitoring gap] | [Name] | [Date] |
```

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
For data handling and compliance, see `databricks-data-handling`.
