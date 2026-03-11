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
---
# Databricks Common Errors

## Overview
Quick reference for the top Databricks errors and their solutions.

## Prerequisites
- Databricks CLI/SDK installed
- API credentials configured
- Access to cluster/job logs

## Instructions

### Step 1: Identify the Error
Check error message in job run output, cluster logs, or notebook cells.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.

## Output
- Identified error cause
- Applied fix
- Verified resolution

## Error Handling

### CLUSTER_NOT_READY
**Error Message:**
```
ClusterNotReadyException: Cluster is not in a valid state
```

**Cause:** Cluster is starting, terminating, or in error state.

**Solution:**
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import State

w = WorkspaceClient()
cluster = w.clusters.get("cluster-id")

if cluster.state in [State.PENDING, State.RESTARTING]:
    # Wait for cluster
    w.clusters.wait_get_cluster_running("cluster-id")
elif cluster.state == State.TERMINATED:
    # Start cluster
    w.clusters.start("cluster-id")
    w.clusters.wait_get_cluster_running("cluster-id")
elif cluster.state == State.ERROR:
    # Check termination reason
    print(f"Error: {cluster.termination_reason}")
```

---

### SPARK_DRIVER_OOM (Out of Memory)
**Error Message:**
```
java.lang.OutOfMemoryError: Java heap space
SparkException: Job aborted due to stage failure
```

**Cause:** Driver or executor running out of memory.

**Solution:**
```python
# Increase driver memory in cluster config
{
    "spark.driver.memory": "8g",
    "spark.executor.memory": "8g",
    "spark.sql.shuffle.partitions": "200"  # HTTP 200 OK
}

# Or use more efficient operations
# WRONG: collect() on large data
all_data = df.collect()  # DON'T DO THIS

# RIGHT: process in chunks or use distributed operations
df.write.format("delta").save("/path")  # Keep data distributed
```

---

### DELTA_CONCURRENT_WRITE
**Error Message:**
```
ConcurrentAppendException: Files were added by a concurrent update
ConcurrentDeleteReadException: A concurrent operation modified files
```

**Cause:** Multiple jobs writing to same Delta table simultaneously.

**Solution:**
```python
# Option 1: Retry with isolation level
df.write \
    .format("delta") \
    .option("isolationLevel", "Serializable") \
    .mode("append") \
    .save("/path")

# Option 2: Use merge with retry logic
from delta.tables import DeltaTable
import time

def merge_with_retry(source_df, target_path, merge_condition, retries=3):
    for attempt in range(retries):
        try:
            delta_table = DeltaTable.forPath(spark, target_path)
            delta_table.alias("t").merge(
                source_df.alias("s"),
                merge_condition
            ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
            return
        except Exception as e:
            if "Concurrent" in str(e) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
```

---

### PERMISSION_DENIED
**Error Message:**
```
PermissionDeniedException: User does not have permission
PERMISSION_DENIED: User does not have READ on table
```

**Cause:** Missing Unity Catalog or workspace permissions.

**Solution:**
```sql
-- Grant table permissions (Unity Catalog)
GRANT SELECT ON TABLE catalog.schema.table TO `user@company.com`;
GRANT ALL PRIVILEGES ON SCHEMA catalog.schema TO `data-team`;

-- Check current permissions
SHOW GRANTS ON TABLE catalog.schema.table;

-- For workspace objects (Admin required)
databricks permissions update jobs --job-id 123 --json '{
  "access_control_list": [{
    "user_name": "user@company.com",
    "permission_level": "CAN_MANAGE_RUN"
  }]
}'
```

---

### INVALID_PARAMETER_VALUE
**Error Message:**
```
InvalidParameterValue: Instance type not supported
Invalid Spark version
```

**Cause:** Wrong cluster configuration for workspace/cloud.

**Solution:**
```python
# Get valid node types for your workspace
w = WorkspaceClient()
node_types = list(w.clusters.list_node_types())
for nt in node_types[:5]:
    print(f"{nt.node_type_id}: {nt.memory_mb}MB, {nt.num_cores} cores")

# Get valid Spark versions
versions = list(w.clusters.spark_versions())
for v in versions[:5]:
    print(v.key)
```

---

### SCHEMA_MISMATCH
**Error Message:**
```
AnalysisException: Cannot merge incompatible data types
Delta table schema does not match
```

**Cause:** Source data schema doesn't match target table.

**Solution:**
```python
# Option 1: Enable schema evolution
df.write \
    .format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("/path")

# Option 2: Explicit schema alignment
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

target_schema = spark.table("target_table").schema

# Cast columns to match
for field in target_schema:
    if field.name in df.columns:
        df = df.withColumn(field.name, col(field.name).cast(field.dataType))

# Option 3: Check differences before write
source_cols = set(df.columns)
target_cols = set(spark.table("target").columns)
print(f"Missing in source: {target_cols - source_cols}")
print(f"Extra in source: {source_cols - target_cols}")
```

---

### RATE_LIMIT_EXCEEDED
**Error Message:**
```
RateLimitExceeded: Too many requests
HTTP 429: Rate limit exceeded  # HTTP 429 Too Many Requests
```

**Cause:** Too many API calls in short period.

**Solution:**
```python
# See databricks-rate-limits skill for full implementation
from databricks.sdk.errors import TooManyRequests
import time

def api_call_with_backoff(operation, max_retries=5):
    for attempt in range(max_retries):
        try:
            return operation()
        except TooManyRequests:
            delay = 2 ** attempt
            print(f"Rate limited, waiting {delay}s...")
            time.sleep(delay)
    raise Exception("Max retries exceeded")
```

---

### JOB_RUN_FAILED
**Error Message:**
```
RunState: FAILED
Run terminated with error: Task failed with error
```

**Cause:** Various - check run details for specific error.

**Solution:**
```bash
# Get detailed run info
databricks runs get --run-id 12345  # port 12345 - example/test

# Get run output (stdout/stderr)
databricks runs get-output --run-id 12345

# Common fixes by task type:
# - Notebook: Check cell output for exception
# - Python: Check stderr for traceback
# - JAR: Check cluster driver logs
# - SQL: Check query execution details
```

```python
# Programmatic debugging
w = WorkspaceClient()
run = w.jobs.get_run(run_id=12345)  # port 12345 - example/test

print(f"State: {run.state.life_cycle_state}")
print(f"Result: {run.state.result_state}")
print(f"Message: {run.state.state_message}")

for task in run.tasks:
    print(f"Task {task.task_key}: {task.state.result_state}")
    if task.state.result_state == "FAILED":
        output = w.jobs.get_run_output(task.run_id)
        print(f"Error: {output.error}")
```

## Examples

### Quick Diagnostic Commands
```bash
# Check cluster status
databricks clusters get --cluster-id abc123

# Get recent job runs
databricks runs list --job-id 456 --limit 5  # 456 = configured value

# Check workspace permissions
databricks permissions get jobs --job-id 456

# Validate cluster config
databricks clusters create --json '{"cluster_name":"test",...}' --dry-run
```

### Escalation Path
1. Collect evidence with `databricks-debug-bundle`
2. Check [Databricks Status](https://status.databricks.com)
3. Search [Databricks Community](https://community.databricks.com)
4. Contact support with workspace ID and request ID

## Resources
- [Databricks Error Messages](https://docs.databricks.com/dev-tools/api/latest/error-messages.html)
- [Troubleshooting Guide](https://docs.databricks.com/clusters/troubleshooting.html)
- [Delta Lake Troubleshooting](https://docs.databricks.com/delta/troubleshooting.html)

## Next Steps
For comprehensive debugging, see `databricks-debug-bundle`.