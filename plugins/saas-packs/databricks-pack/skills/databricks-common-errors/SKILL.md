---
name: databricks-common-errors
description: |
  Diagnose and fix Databricks common errors and exceptions.
  Use when encountering Databricks errors, debugging failed jobs,
  or troubleshooting cluster and notebook issues.
  Trigger with phrases like "databricks error", "fix databricks",
  "databricks not working", "debug databricks", "spark error".
allowed-tools: Read, Grep, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, debugging]

---
# Databricks Common Errors

## Overview
Quick-reference diagnostic guide for the most frequent Databricks errors. Covers cluster failures, Spark OOM, Delta Lake conflicts, permissions, schema mismatches, rate limits, and job run failures with real SDK/SQL solutions.

## Prerequisites
- Databricks CLI configured
- Access to cluster/job logs
- `databricks-sdk` installed for programmatic debugging

## Instructions

### Step 1: Identify the Error Source
```bash
# Get failed run details
databricks runs get --run-id $RUN_ID --output json | jq '{
  state: .state.result_state,
  message: .state.state_message,
  tasks: [.tasks[] | {key: .task_key, state: .state.result_state, error: .state.state_message}]
}'
```

### Step 2: Match and Fix

---

### CLUSTER_NOT_READY / INVALID_STATE
```
ClusterNotReadyException: Cluster 0123-456789-abcde is not in a RUNNING state
```
**Cause:** Cluster is starting, terminating, or in error state.

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import State

w = WorkspaceClient()
cluster = w.clusters.get(cluster_id="0123-456789-abcde")

if cluster.state in (State.PENDING, State.RESTARTING):
    w.clusters.ensure_cluster_is_running("0123-456789-abcde")
elif cluster.state == State.TERMINATED:
    w.clusters.start_and_wait(cluster_id="0123-456789-abcde")
elif cluster.state == State.ERROR:
    reason = cluster.termination_reason
    print(f"Cluster error: {reason.code} — {reason.parameters}")
    # Common: CLOUD_PROVIDER_LAUNCH_FAILURE, INSTANCE_POOL_CLUSTER_FAILURE
```

---

### SPARK_DRIVER_OOM
```
java.lang.OutOfMemoryError: Java heap space
SparkException: Job aborted due to stage failure
```
**Cause:** Driver or executor running out of memory.

```python
# Fix 1: Increase memory via cluster Spark config
spark_conf = {
    "spark.driver.memory": "8g",
    "spark.executor.memory": "8g",
    "spark.sql.shuffle.partitions": "400",  # reduce skew
}

# Fix 2: Never collect() large datasets
# BAD:  all_data = df.collect()
# GOOD: df.write.format("delta").saveAsTable("catalog.schema.results")

# Fix 3: Broadcast small tables instead of shuffling
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_lookup_df), "key")
```

---

### DELTA_CONCURRENT_WRITE
```
ConcurrentAppendException: Files were added by a concurrent update
ConcurrentDeleteReadException: A concurrent operation modified files
```
**Cause:** Multiple jobs writing to the same Delta table simultaneously.

```python
from delta.tables import DeltaTable
import time

def merge_with_retry(spark, source_df, target_table, merge_key, max_retries=3):
    """MERGE with retry for concurrent write conflicts."""
    for attempt in range(max_retries):
        try:
            target = DeltaTable.forName(spark, target_table)
            (target.alias("t")
                .merge(source_df.alias("s"), f"t.{merge_key} = s.{merge_key}")
                .whenMatchedUpdateAll()
                .whenNotMatchedInsertAll()
                .execute())
            return
        except Exception as e:
            if "Concurrent" in str(e) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
```

---

### PERMISSION_DENIED
```
PERMISSION_DENIED: User does not have SELECT on TABLE catalog.schema.table
PermissionDeniedException: User does not have permission MANAGE on cluster
```
**Cause:** Missing Unity Catalog grants or workspace permissions.

```sql
-- Fix Unity Catalog permissions (requires GRANT privilege)
GRANT USAGE ON CATALOG analytics TO `data-team`;
GRANT USAGE ON SCHEMA analytics.silver TO `data-team`;
GRANT SELECT ON TABLE analytics.silver.orders TO `data-team`;

-- Check current grants
SHOW GRANTS ON TABLE analytics.silver.orders;
```

```bash
# Fix workspace object permissions
databricks permissions update jobs --job-id 123 --json '{
  "access_control_list": [{
    "user_name": "user@company.com",
    "permission_level": "CAN_MANAGE_RUN"
  }]
}'
```

---

### INVALID_PARAMETER_VALUE
```
InvalidParameterValue: Instance type xyz not supported in region us-east-1
Invalid spark_version: 13.x.x-scala2.12
```
**Cause:** Wrong cluster config for the workspace region.

```python
w = WorkspaceClient()

# List valid node types for this workspace
for nt in sorted(w.clusters.list_node_types().node_types, key=lambda x: x.memory_mb)[:10]:
    print(f"{nt.node_type_id}: {nt.memory_mb}MB, {nt.num_cores} cores")

# List valid Spark versions
for v in w.clusters.spark_versions().versions:
    if "LTS" in v.name:
        print(f"{v.key}: {v.name}")
```

---

### SCHEMA_MISMATCH
```
AnalysisException: A schema mismatch detected when writing to the Delta table
```
**Cause:** Source schema doesn't match target table.

```python
# Option 1: Enable schema evolution
df.write.format("delta").option("mergeSchema", "true").mode("append").saveAsTable("target")

# Option 2: Identify differences
source_cols = set(df.columns)
target_cols = set(spark.table("target").columns)
print(f"Missing in source: {target_cols - source_cols}")
print(f"Extra in source: {source_cols - target_cols}")

# Option 3: Cast to match target schema
target_schema = spark.table("target").schema
for field in target_schema:
    if field.name in df.columns:
        df = df.withColumn(field.name, col(field.name).cast(field.dataType))
```

---

### JOB_RUN_FAILED
```
RunState: FAILED — Run terminated with error
```

```python
w = WorkspaceClient()
run = w.jobs.get_run(run_id=12345)

print(f"State: {run.state.life_cycle_state}")
print(f"Result: {run.state.result_state}")
print(f"Message: {run.state.state_message}")

# Check each task
for task in run.tasks:
    if task.state.result_state and task.state.result_state.value == "FAILED":
        output = w.jobs.get_run_output(task.run_id)
        print(f"Task '{task.task_key}' failed: {output.error}")
        if output.error_trace:
            print(f"Traceback:\n{output.error_trace[:500]}")
```

---

### HTTP 429 — RATE_LIMIT_EXCEEDED
See `databricks-rate-limits` skill for full retry patterns.

```python
from databricks.sdk.errors import TooManyRequests
import time

def call_with_backoff(operation, max_retries=5):
    for attempt in range(max_retries):
        try:
            return operation()
        except TooManyRequests as e:
            wait = e.retry_after_secs or (2 ** attempt)
            print(f"Rate limited, waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Max retries exceeded")
```

## Output
- Error identified and categorized
- Fix applied from matching error pattern
- Resolution verified

## Error Handling
| Error Code | HTTP | Category | Quick Fix |
|-----------|------|----------|-----------|
| `CLUSTER_NOT_READY` | - | Compute | `ensure_cluster_is_running()` |
| `OutOfMemoryError` | - | Spark | Increase memory, avoid `.collect()` |
| `ConcurrentAppendException` | - | Delta | MERGE with retry, serialize writes |
| `PERMISSION_DENIED` | 403 | Auth | `GRANT` in Unity Catalog |
| `INVALID_PARAMETER_VALUE` | 400 | Config | Check `list_node_types()` |
| `AnalysisException` | - | Schema | `mergeSchema=true` |
| `FAILED` run state | - | Job | Check `get_run_output()` for traceback |
| `Too Many Requests` | 429 | Rate Limit | Exponential backoff with `Retry-After` |

## Examples

### Quick Diagnostic Commands
```bash
databricks clusters get --cluster-id $CID | jq '{state, termination_reason}'
databricks runs list --job-id $JID --limit 5 | jq '.runs[] | {run_id, state: .state.result_state}'
databricks permissions get jobs --job-id $JID
```

### Escalation Path
1. Check [Databricks Status](https://status.databricks.com)
2. Collect evidence with `databricks-debug-bundle`
3. Search [Community Forum](https://community.databricks.com)
4. Contact support with workspace ID and request ID from error response

## Resources
- [Troubleshooting Guide](https://docs.databricks.com/aws/en/resources/troubleshooting)
- [Delta Lake Troubleshooting](https://docs.databricks.com/aws/en/delta/best-practices)
- [Resource Limits](https://docs.databricks.com/aws/en/resources/limits)

## Next Steps
For comprehensive debugging, see `databricks-debug-bundle`.
