---
name: databricks-incident-runbook
description: |
  Execute Databricks incident response procedures with triage, mitigation, and postmortem.
  Use when responding to Databricks-related outages, investigating job failures,
  or running post-incident reviews for pipeline failures.
  Trigger with phrases like "databricks incident", "databricks outage",
  "databricks down", "databricks on-call", "databricks emergency", "job failed".
allowed-tools: Read, Grep, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Incident Runbook

## Overview
Rapid incident response procedures for Databricks-related outages.

## Prerequisites
- Access to Databricks workspace
- CLI configured with appropriate permissions
- Access to monitoring dashboards
- Communication channels (Slack, PagerDuty)

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Production data pipeline down | < 15 min | Critical ETL failed, data not updating |
| P2 | Degraded performance | < 1 hour | Slow queries, partial failures |
| P3 | Non-critical issues | < 4 hours | Dev cluster issues, delayed non-critical jobs |
| P4 | No user impact | Next business day | Monitoring gaps, documentation |

## Quick Triage

```bash
#!/bin/bash
set -euo pipefail
# quick-triage.sh - Run this first during any incident

echo "=== Databricks Quick Triage ==="
echo "Time: $(date)"
echo ""

# 1. Check Databricks status
echo "--- Databricks Status ---"
curl -s https://status.databricks.com/api/v2/status.json | jq '.status.description'
echo ""

# 2. Check workspace connectivity
echo "--- Workspace Connectivity ---"
databricks workspace list / --output json | jq -r '.[] | .path' | head -5
if [ $? -eq 0 ]; then
    echo "Workspace: CONNECTED"
else
    echo "Workspace: CONNECTION FAILED"
fi
echo ""

# 3. Check recent job failures
echo "--- Recent Job Failures (last 1 hour) ---"
databricks runs list --limit 20 --output json | \
    jq -r '.runs[] | select(.state.result_state == "FAILED") | "\(.run_id): \(.run_name) - \(.state.state_message)"'
echo ""

# 4. Check cluster status
echo "--- Running Clusters ---"
databricks clusters list --output json | \
    jq -r '.clusters[] | select(.state == "RUNNING" or .state == "ERROR") | "\(.cluster_id): \(.cluster_name) [\(.state)]"'
echo ""

# 5. Check for errors in last hour
echo "--- Recent Errors ---"
# Query system tables via SQL warehouse or notebook
```

## Decision Tree

```
Job/Pipeline failing?
├─ YES: Is it a single job or multiple?
│   ├─ SINGLE JOB → Check job-specific issues
│   │   ├─ Cluster failed to start → Check cluster events
│   │   ├─ Code error → Check task output/logs
│   │   ├─ Data issue → Check source data
│   │   └─ Permission error → Check grants
│   │
│   └─ MULTIPLE JOBS → Likely infrastructure issue
│       ├─ Check Databricks status page
│       ├─ Check workspace quotas
│       └─ Check network connectivity
│
└─ NO: Is it a performance issue?
    ├─ Slow queries → Check query plan, cluster sizing
    ├─ Slow cluster startup → Check instance availability
    └─ Data freshness → Check upstream pipelines
```

## Immediate Actions by Error Type

### Job Failed - Code Error

```bash
# 1. Get run details
RUN_ID="your-run-id"
databricks runs get --run-id $RUN_ID

# 2. Get detailed error output
databricks runs get-output --run-id $RUN_ID | jq '.error'

# 3. Check task-level errors
databricks runs get --run-id $RUN_ID | jq '.tasks[] | select(.state.result_state == "FAILED") | {task: .task_key, error: .state.state_message}'

# 4. If notebook task, get notebook output
# (View in UI or use jobs API to get cell outputs)
```

### Cluster Failed to Start

```bash
# 1. Check cluster events
CLUSTER_ID="your-cluster-id"
databricks clusters events --cluster-id $CLUSTER_ID --limit 20

# 2. Common causes and fixes
# - QUOTA_EXCEEDED: Terminate unused clusters
# - CLOUD_PROVIDER_LAUNCH_ERROR: Check instance availability
# - DRIVER_UNREACHABLE: Network/firewall issue

# 3. Quick fix - restart cluster
databricks clusters restart --cluster-id $CLUSTER_ID

# 4. Check cluster logs
databricks clusters get --cluster-id $CLUSTER_ID | jq '.termination_reason'
```

### Permission/Auth Errors

```bash
# 1. Check current user
databricks current-user me

# 2. Check job permissions
databricks permissions get jobs --job-id $JOB_ID

# 3. Check table permissions (run in notebook)
# SHOW GRANTS ON TABLE catalog.schema.table

# 4. Fix: Grant necessary permissions
databricks permissions update jobs --job-id $JOB_ID --json '{
  "access_control_list": [{
    "user_name": "user@company.com",
    "permission_level": "CAN_MANAGE_RUN"
  }]
}'
```

### Data Quality Failures

```sql
-- Quick data quality check
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT id) as unique_ids,
    SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amounts,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM catalog.schema.table
WHERE created_at > current_timestamp() - INTERVAL 1 DAY;

-- Check for recent changes
DESCRIBE HISTORY catalog.schema.table LIMIT 10;

-- Restore to previous version if needed
RESTORE TABLE catalog.schema.table TO VERSION AS OF 5;
```

## Communication Templates

### Internal (Slack)
```
:red_circle: **P1 INCIDENT: [Brief Description]**

**Status:** INVESTIGATING
**Impact:** [Describe user/business impact]
**Started:** [Time]
**Current Action:** [What you're doing now]
**Next Update:** [Time]

**Incident Commander:** @[name]
**Thread:** [link]
```

### External (Status Page)
```
**Data Pipeline Delay**

We are experiencing delays in data processing. Some reports may show stale data.

**Impact:** Dashboard data may be up to [X] hours delayed
**Started:** [Time] UTC
**Current Status:** Our team is actively investigating

We will provide updates every 30 minutes.

Last updated: [Timestamp]
```

## Post-Incident

### Evidence Collection

```bash
#!/bin/bash
# collect-incident-evidence.sh

INCIDENT_ID=$1
RUN_ID=$2
CLUSTER_ID=$3

mkdir -p "incident-$INCIDENT_ID"

# Job run details
databricks runs get --run-id $RUN_ID > "incident-$INCIDENT_ID/run_details.json"
databricks runs get-output --run-id $RUN_ID > "incident-$INCIDENT_ID/run_output.json"

# Cluster info
if [ -n "$CLUSTER_ID" ]; then
    databricks clusters get --cluster-id $CLUSTER_ID > "incident-$INCIDENT_ID/cluster_info.json"
    databricks clusters events --cluster-id $CLUSTER_ID --limit 50 > "incident-$INCIDENT_ID/cluster_events.json"
fi

# Create summary
cat << EOF > "incident-$INCIDENT_ID/summary.md"
# Incident $INCIDENT_ID

**Date:** $(date)
**Run ID:** $RUN_ID
**Cluster ID:** $CLUSTER_ID

## Evidence Collected
- run_details.json
- run_output.json
- cluster_info.json
- cluster_events.json
EOF

tar -czf "incident-$INCIDENT_ID.tar.gz" "incident-$INCIDENT_ID"
echo "Evidence collected: incident-$INCIDENT_ID.tar.gz"
```

### Postmortem Template

```markdown
## Incident: [Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P[1-4]
**Incident Commander:** [Name]

### Summary
[1-2 sentence description of what happened]

### Timeline (UTC)
| Time | Event |
|------|-------|
| HH:MM | [First alert/detection] |
| HH:MM | [Investigation started] |
| HH:MM | [Root cause identified] |
| HH:MM | [Mitigation applied] |
| HH:MM | [Incident resolved] |

### Root Cause
[Technical explanation of what went wrong]

### Impact
- **Data Impact:** [Tables affected, rows impacted]
- **Users Affected:** [Number, types]
- **Duration:** [How long data was unavailable/stale]
- **Financial Impact:** [If applicable]

### Detection
- **How detected:** [Alert, user report, monitoring]
- **Time to detect:** [Minutes from issue start]
- **Detection gap:** [What could have caught this sooner]

### Response
- **Time to respond:** [Minutes from detection]
- **What worked:** [Effective response actions]
- **What didn't:** [Ineffective actions, dead ends]

### Action Items
| Priority | Action | Owner | Due Date |
|----------|--------|-------|----------|
| P1 | [Preventive measure] | [Name] | [Date] |
| P2 | [Monitoring improvement] | [Name] | [Date] |
| P3 | [Documentation update] | [Name] | [Date] |

### Lessons Learned
1. [Key learning 1]
2. [Key learning 2]
3. [Key learning 3]
```

## Instructions

### Step 1: Quick Triage
Run the triage script to identify the issue source.

### Step 2: Follow Decision Tree
Determine if the issue is Databricks-side or code/data issue.

### Step 3: Execute Immediate Actions
Apply the appropriate remediation for the error type.

### Step 4: Communicate Status
Update internal and external stakeholders.

### Step 5: Collect Evidence
Document everything for postmortem.

## Output
- Issue identified and categorized
- Remediation applied
- Stakeholders notified
- Evidence collected for postmortem

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Can't access workspace | Token expired | Re-authenticate |
| CLI commands fail | Network issue | Check VPN |
| Logs unavailable | Cluster terminated | Check cluster events |
| Restore fails | Retention exceeded | Check vacuum settings |

## Examples

### One-Line Job Health Check
```bash
databricks runs list --job-id $JOB_ID --limit 5 --output json | \
    jq -r '.runs[] | "\(.start_time): \(.state.result_state)"'
```

### Quick Cluster Restart
```bash
databricks clusters restart --cluster-id $CLUSTER_ID && \
    echo "Cluster restart initiated"
```

## Resources
- [Databricks Status Page](https://status.databricks.com)
- [Databricks Support](https://help.databricks.com)
- [Community Forum](https://community.databricks.com)

## Next Steps
For data handling, see `databricks-data-handling`.