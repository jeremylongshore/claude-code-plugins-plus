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
---
# Databricks Production Checklist

## Overview
Complete checklist for deploying Databricks jobs and pipelines to production.

## Prerequisites
- Staging environment tested and verified
- Production workspace access
- Unity Catalog configured
- Monitoring and alerting ready

## Instructions

### Step 1: Pre-Deployment Configuration

#### Security
- [ ] Service principal configured for automation
- [ ] Secrets in Databricks Secret Scopes (not env vars)
- [ ] Token expiration set (max 90 days)
- [ ] Unity Catalog permissions configured
- [ ] Cluster policies enforced
- [ ] IP access lists configured

#### Infrastructure
- [ ] Production cluster pool configured
- [ ] Instance types validated for workload
- [ ] Autoscaling configured appropriately
- [ ] Spot instance ratio set (cost vs reliability)

### Step 2: Code Quality Verification

#### Testing
- [ ] Unit tests passing
- [ ] Integration tests on staging data
- [ ] Data quality tests defined
- [ ] Performance benchmarks met

```bash
# Run tests via Asset Bundles
databricks bundle validate -t prod
databricks bundle run -t staging test-job

# Verify test results
databricks runs get --run-id $RUN_ID | jq '.state.result_state'
```

#### Code Review
- [ ] No hardcoded credentials
- [ ] Error handling covers all failure modes
- [ ] Logging is production-appropriate
- [ ] Delta Lake best practices followed
- [ ] No `collect()` on large datasets

### Step 3: Job Configuration

```yaml
# resources/prod_job.yml
resources:
  jobs:
    etl_pipeline:
      name: "prod-etl-pipeline"
      tags:
        environment: production
        team: data-engineering
        cost_center: analytics

      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "America/New_York"

      email_notifications:
        on_failure:
          - "oncall@company.com"
        on_success:
          - "data-team@company.com"

      webhook_notifications:
        on_failure:
          - id: "slack-webhook-id"

      max_concurrent_runs: 1
      timeout_seconds: 14400  # 14400: 4 hours

      tasks:
        - task_key: bronze_ingest
          job_cluster_key: etl_cluster
          notebook_task:
            notebook_path: /Repos/prod/pipelines/bronze
          timeout_seconds: 3600  # 3600: timeout: 1 hour

        - task_key: silver_transform
          depends_on:
            - task_key: bronze_ingest
          job_cluster_key: etl_cluster
          notebook_task:
            notebook_path: /Repos/prod/pipelines/silver

      job_clusters:
        - job_cluster_key: etl_cluster
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "Standard_DS3_v2"
            num_workers: 4
            autoscale:
              min_workers: 2
              max_workers: 8
            spark_conf:
              spark.sql.shuffle.partitions: "200"  # HTTP 200 OK
              spark.databricks.delta.optimizeWrite.enabled: "true"
            instance_pool_id: "prod-pool-id"
```

### Step 4: Deployment Commands

```bash
# Pre-flight checks
echo "=== Pre-flight Checks ==="
databricks workspace list /Repos/prod/  # Verify repo exists
databricks clusters list | grep prod    # Verify pools/clusters
databricks secrets list-scopes          # Verify secrets

# Deploy with Asset Bundles
echo "=== Deploying ==="
databricks bundle deploy -t prod

# Verify deployment
databricks bundle summary -t prod
databricks jobs list | grep prod-etl

# Manual trigger to verify
echo "=== Verification Run ==="
RUN_ID=$(databricks jobs run-now --job-id $JOB_ID | jq -r '.run_id')
echo "Run ID: $RUN_ID"

# Monitor run
databricks runs get --run-id $RUN_ID --wait
```

### Step 5: Monitoring Setup

```python
# monitoring/health_check.py
from databricks.sdk import WorkspaceClient
from datetime import datetime, timedelta

def check_job_health(w: WorkspaceClient, job_id: int) -> dict:
    """Check job health metrics."""
    # Get recent runs
    runs = list(w.jobs.list_runs(
        job_id=job_id,
        completed_only=True,
        limit=10,
    ))

    if not runs:
        return {"status": "NO_RUNS", "healthy": False}

    # Calculate success rate
    successful = sum(1 for r in runs if r.state.result_state == "SUCCESS")
    success_rate = successful / len(runs)

    # Calculate average duration
    durations = [
        (r.end_time - r.start_time) / 1000 / 60  # 1000: minutes
        for r in runs if r.end_time
    ]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Check last run
    last_run = runs[0]
    last_state = last_run.state.result_state

    return {
        "status": "HEALTHY" if success_rate > 0.9 else "DEGRADED",
        "healthy": success_rate > 0.9 and last_state == "SUCCESS",
        "success_rate": success_rate,
        "avg_duration_minutes": avg_duration,
        "last_run_state": last_state,
        "last_run_time": datetime.fromtimestamp(last_run.start_time / 1000),  # 1 second in ms
    }
```

### Step 6: Rollback Procedure

```bash
#!/bin/bash
# rollback.sh - Emergency rollback procedure

JOB_ID=$1
PREVIOUS_VERSION=$2

echo "=== ROLLBACK INITIATED ==="
echo "Job: $JOB_ID"
echo "Target Version: $PREVIOUS_VERSION"

# 1. Pause the job
echo "Pausing job..."
databricks jobs update --job-id $JOB_ID --json '{"settings": {"schedule": null}}'

# 2. Cancel active runs
echo "Cancelling active runs..."
databricks runs list --job-id $JOB_ID --active-only | \
  jq -r '.runs[].run_id' | \
  xargs -I {} databricks runs cancel --run-id {}

# 3. Reset to previous version
echo "Rolling back to version $PREVIOUS_VERSION..."
databricks bundle deploy -t prod --force

# 4. Re-enable schedule
echo "Re-enabling schedule..."
# (restore from backup config)

# 5. Trigger verification run
echo "Triggering verification run..."
databricks jobs run-now --job-id $JOB_ID

echo "=== ROLLBACK COMPLETE ==="
```

## Output
- Deployed production job
- Health checks passing
- Monitoring active
- Rollback procedure documented

## Error Handling
| Alert | Condition | Severity |
|-------|-----------|----------|
| Job Failed | `result_state = FAILED` | P1 |
| Long Running | Duration > 2x average | P2 |
| Consecutive Failures | 3+ failures in a row | P1 |
| Data Quality | Expectations failed | P2 |

## Examples

### Production Health Dashboard Query
```sql
-- Job health metrics (Unity Catalog system tables)
SELECT
  job_id,
  job_name,
  COUNT(*) as total_runs,
  SUM(CASE WHEN result_state = 'SUCCESS' THEN 1 ELSE 0 END) as successes,
  AVG(execution_duration) / 60000 as avg_minutes,  # 60000: 1 minute in ms
  MAX(start_time) as last_run
FROM system.lakeflow.job_run_timeline
WHERE start_time > current_timestamp() - INTERVAL 7 DAYS
GROUP BY job_id, job_name
ORDER BY total_runs DESC
```

### Pre-Production Verification
```bash
# Comprehensive pre-prod check
databricks bundle validate -t prod && \
databricks bundle deploy -t prod --dry-run && \
echo "Validation passed, ready to deploy"
```

## Resources
- [Databricks Production Best Practices](https://docs.databricks.com/dev-tools/bundles/best-practices.html)
- [Job Configuration](https://docs.databricks.com/workflows/jobs/jobs.html)
- [Monitoring Guide](https://docs.databricks.com/administration-guide/workspace/monitoring.html)

## Next Steps
For version upgrades, see `databricks-upgrade-migration`.