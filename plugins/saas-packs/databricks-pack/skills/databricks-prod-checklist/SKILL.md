---
name: databricks-prod-checklist
description: |
  Execute Databricks production deployment checklist and rollback procedures.
  Use when deploying Databricks jobs to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "databricks production", "deploy databricks",
  "databricks go-live", "databricks launch checklist".
allowed-tools: Read, Bash(databricks:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, deployment]

---
# Databricks Production Checklist

## Overview
Complete checklist for deploying Databricks jobs and pipelines to production. Covers security hardening, infrastructure validation, code quality gates, job configuration, deployment commands, monitoring setup, and rollback procedures.

## Prerequisites
- Staging environment tested and verified
- Production workspace access with service principal
- Unity Catalog configured with prod catalogs
- Monitoring and alerting ready (see `databricks-observability`)

## Instructions

### Step 1: Pre-Deployment Security
- [ ] Service principal configured for automated runs (not personal PAT)
- [ ] Secrets in Databricks Secret Scopes (not env vars or hardcoded)
- [ ] Token expiration set (max 90 days)
- [ ] Unity Catalog grants follow least privilege
- [ ] Cluster policies enforced for cost/security guardrails
- [ ] IP access lists configured in Admin Console
- [ ] Audit logging verified via `system.access.audit`

### Step 2: Infrastructure Validation
- [ ] Instance pool created for fast cluster startup
- [ ] Node types validated for workload (compute-optimized for streaming, memory-optimized for ML)
- [ ] Autoscaling configured with sensible min/max workers
- [ ] Spot instances enabled for worker nodes (on-demand for driver)
- [ ] Auto-termination disabled for job clusters (they terminate on completion)

```bash
# Verify infrastructure
databricks clusters list-node-types --output json | jq '.[0:5] | .[].node_type_id'
databricks instance-pools list --output json | jq '.[] | {id: .instance_pool_id, name: .instance_pool_name}'
```

### Step 3: Code Quality Gates
- [ ] Unit tests passing locally (`pytest tests/unit/`)
- [ ] Integration tests passing on staging data
- [ ] No `.collect()` on large datasets
- [ ] No hardcoded credentials or paths
- [ ] Error handling covers all failure modes
- [ ] Delta Lake best practices: MERGE for upserts, OPTIMIZE scheduled
- [ ] Logging is production-appropriate (structured, no PII)

```bash
# Run tests and validate bundle
pytest tests/ -v --tb=short
databricks bundle validate -t prod
```

### Step 4: Job Configuration
```yaml
# resources/prod_etl.yml
resources:
  jobs:
    prod_etl_pipeline:
      name: "prod-etl-pipeline"
      tags:
        environment: production
        team: data-engineering
        cost_center: analytics

      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "America/New_York"

      email_notifications:
        on_failure: ["oncall@company.com"]
        on_success: ["data-team@company.com"]

      webhook_notifications:
        on_failure:
          - id: "slack-notification-destination-id"

      max_concurrent_runs: 1
      timeout_seconds: 14400  # 4 hours

      tasks:
        - task_key: bronze_ingest
          job_cluster_key: etl_cluster
          notebook_task:
            notebook_path: src/pipelines/bronze.py
          timeout_seconds: 3600

        - task_key: silver_transform
          depends_on: [{task_key: bronze_ingest}]
          job_cluster_key: etl_cluster
          notebook_task:
            notebook_path: src/pipelines/silver.py

        - task_key: gold_aggregate
          depends_on: [{task_key: silver_transform}]
          job_cluster_key: etl_cluster
          notebook_task:
            notebook_path: src/pipelines/gold.py

      job_clusters:
        - job_cluster_key: etl_cluster
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "i3.xlarge"
            autoscale:
              min_workers: 2
              max_workers: 8
            spark_conf:
              spark.sql.shuffle.partitions: "200"
              spark.databricks.delta.optimizeWrite.enabled: "true"
              spark.databricks.delta.autoCompact.enabled: "true"
            aws_attributes:
              availability: SPOT_WITH_FALLBACK
              first_on_demand: 1
```

### Step 5: Deploy
```bash
# Pre-flight checks
echo "=== Pre-flight ==="
databricks bundle validate -t prod
databricks workspace list /Shared/.bundle/ 2>/dev/null || echo "First deploy"
databricks secrets list-scopes | grep prod

# Deploy
echo "=== Deploying ==="
databricks bundle deploy -t prod

# Verify deployment
databricks bundle summary -t prod

# Trigger verification run
echo "=== Verification ==="
RUN_ID=$(databricks bundle run prod_etl_pipeline -t prod --output json | jq -r '.run_id')
echo "Verification run: $RUN_ID"

# Wait and check result
databricks runs get --run-id $RUN_ID --output json | jq '.state'
```

### Step 6: Post-Deploy Monitoring
```python
from databricks.sdk import WorkspaceClient
from datetime import datetime

w = WorkspaceClient()

def check_job_health(job_id: int) -> dict:
    """Post-deploy health check."""
    runs = list(w.jobs.list_runs(job_id=job_id, completed_only=True, limit=10))
    if not runs:
        return {"status": "NO_RUNS", "healthy": False}

    successful = sum(1 for r in runs if r.state.result_state.value == "SUCCESS")
    success_rate = successful / len(runs)

    durations = [
        (r.end_time - r.start_time) / 60000
        for r in runs if r.end_time and r.start_time
    ]
    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        "healthy": success_rate > 0.9 and runs[0].state.result_state.value == "SUCCESS",
        "success_rate": f"{success_rate:.0%}",
        "avg_duration_min": f"{avg_duration:.1f}",
        "last_run": runs[0].state.result_state.value,
        "last_run_time": datetime.fromtimestamp(runs[0].start_time / 1000).isoformat(),
    }
```

### Step 7: Rollback Procedure
```bash
#!/bin/bash
set -euo pipefail
# rollback.sh <job_id>

JOB_ID=$1
echo "=== ROLLBACK: Job $JOB_ID ==="

# 1. Pause the schedule
echo "Pausing schedule..."
databricks jobs update --job-id $JOB_ID --json '{"settings": {"schedule": null}}'

# 2. Cancel any active runs
echo "Cancelling active runs..."
databricks runs list --job-id $JOB_ID --active-only --output json | \
  jq -r '.runs[]?.run_id' | \
  xargs -I {} databricks runs cancel --run-id {}

# 3. Redeploy previous bundle version
echo "Redeploying previous version..."
git checkout HEAD~1 -- resources/ src/
databricks bundle deploy -t prod

# 4. Restore schedule
echo "Re-enabling schedule..."
databricks jobs reset --job-id $JOB_ID --json-file resources/prod_etl.json

# 5. Trigger verification
echo "Running verification..."
databricks jobs run-now --job-id $JOB_ID

echo "=== ROLLBACK COMPLETE ==="
```

## Output
- Pre-deployment checklist verified
- Production job deployed via Asset Bundles
- Verification run completed successfully
- Monitoring health check operational
- Rollback procedure documented and tested

## Error Handling
| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Job Failed | `result_state = FAILED` | P1 | Page oncall, check `get_run_output` |
| Long Running | Duration > 2x average | P2 | Investigate cluster sizing |
| 3+ Consecutive Failures | Success rate drops below 70% | P1 | Trigger rollback |
| Data Quality Failed | DLT expectations failed | P2 | Check source data quality |

## Examples

### Production Health Dashboard
```sql
SELECT job_id, job_name,
       COUNT(*) AS total_runs,
       SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) AS successes,
       ROUND(AVG(execution_duration) / 60000, 1) AS avg_minutes,
       MAX(start_time) AS last_run
FROM system.lakeflow.job_run_timeline
WHERE start_time > current_timestamp() - INTERVAL 7 DAYS
GROUP BY job_id, job_name
ORDER BY total_runs DESC;
```

## Resources
- [Deployment Modes](https://docs.databricks.com/aws/en/dev-tools/bundles/deployment-modes)
- [Job Configuration](https://docs.databricks.com/aws/en/jobs/)
- [Cluster Best Practices](https://docs.databricks.com/aws/en/compute/configure)

## Next Steps
For version upgrades, see `databricks-upgrade-migration`.
