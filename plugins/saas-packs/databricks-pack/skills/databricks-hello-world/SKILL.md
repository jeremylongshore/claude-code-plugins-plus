---
name: databricks-hello-world
description: |
  Create a minimal working Databricks example with cluster and notebook.
  Use when starting a new Databricks project, testing your setup,
  or learning basic Databricks patterns.
  Trigger with phrases like "databricks hello world", "databricks example",
  "databricks quick start", "first databricks notebook", "create cluster".
allowed-tools: Read, Write, Edit, Bash(databricks:*), Bash(python:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, databricks, testing]

---
# Databricks Hello World

## Overview
Create your first Databricks cluster and notebook via the REST API and Python SDK. Covers single-node dev clusters, SQL warehouses, notebook upload, one-time job runs, and Delta Lake smoke tests.

## Prerequisites
- Completed `databricks-install-auth` setup
- Workspace access with cluster creation permissions
- Valid API credentials in env vars or `~/.databrickscfg`

## Instructions

### Step 1: Create a Single-Node Dev Cluster
```bash
# POST /api/2.0/clusters/create
databricks clusters create --json '{
  "cluster_name": "hello-world-dev",
  "spark_version": "14.3.x-scala2.12",
  "node_type_id": "i3.xlarge",
  "autotermination_minutes": 30,
  "num_workers": 0,
  "spark_conf": {
    "spark.databricks.cluster.profile": "singleNode",
    "spark.master": "local[*]"
  },
  "custom_tags": {
    "ResourceClass": "SingleNode"
  }
}'
# Returns: {"cluster_id": "0123-456789-abcde123"}
```

Or via Python SDK:
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import AutoScale

w = WorkspaceClient()

# create_and_wait blocks until cluster reaches RUNNING state
cluster = w.clusters.create_and_wait(
    cluster_name="hello-world-dev",
    spark_version="14.3.x-scala2.12",
    node_type_id="i3.xlarge",
    num_workers=0,
    autotermination_minutes=30,
    spark_conf={
        "spark.databricks.cluster.profile": "singleNode",
        "spark.master": "local[*]",
    },
)
print(f"Cluster ready: {cluster.cluster_id} ({cluster.state})")
```

### Step 2: Create and Upload a Notebook
```python
import base64
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat, Language

w = WorkspaceClient()

notebook_source = """
# Databricks notebook source
# COMMAND ----------

# Simple DataFrame
data = [("Alice", 28), ("Bob", 35), ("Charlie", 42)]
df = spark.createDataFrame(data, ["name", "age"])
display(df)

# COMMAND ----------

# Write as Delta table
df.write.format("delta").mode("overwrite").saveAsTable("default.hello_world")

# COMMAND ----------

# Read it back and verify
result = spark.table("default.hello_world")
display(result)
assert result.count() == 3, "Expected 3 rows"
print("Hello from Databricks!")
"""

me = w.current_user.me()
notebook_path = f"/Users/{me.user_name}/hello_world"

w.workspace.import_(
    path=notebook_path,
    format=ImportFormat.SOURCE,
    language=Language.PYTHON,
    content=base64.b64encode(notebook_source.encode()).decode(),
    overwrite=True,
)
print(f"Notebook created at: {notebook_path}")
```

### Step 3: Run the Notebook as a One-Time Job
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import SubmitTask, NotebookTask

w = WorkspaceClient()

# POST /api/2.1/jobs/runs/submit — no persistent job definition needed
run = w.jobs.submit(
    run_name="hello-world-run",
    tasks=[
        SubmitTask(
            task_key="hello",
            existing_cluster_id="0123-456789-abcde123",  # from Step 1
            notebook_task=NotebookTask(
                notebook_path=f"/Users/{w.current_user.me().user_name}/hello_world",
            ),
        )
    ],
).result()  # .result() blocks until run completes

print(f"Run {run.run_id}: {run.state.result_state}")
# Expect: "Run 12345: SUCCESS"
```

### Step 4: Create a Serverless SQL Warehouse
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Serverless warehouses start in seconds and cost ~$0.07/DBU
warehouse = w.warehouses.create_and_wait(
    name="hello-warehouse",
    cluster_size="2X-Small",
    auto_stop_mins=10,
    warehouse_type="PRO",
    enable_serverless_compute=True,
)
print(f"Warehouse ready: {warehouse.id}")

# Run SQL against it
result = w.statement_execution.execute_statement(
    warehouse_id=warehouse.id,
    statement="SELECT current_timestamp() AS now, current_user() AS who",
)
print(result.result.data_array)
```

### Step 5: Verify Everything via CLI
```bash
# List clusters
databricks clusters list --output json | jq '.[] | {id: .cluster_id, name: .cluster_name, state: .state}'

# List workspace contents
databricks workspace list /Users/$(databricks current-user me --output json | jq -r .userName)/

# Get run results
databricks runs list --limit 5 --output json | jq '.runs[] | {run_id: .run_id, name: .run_name, state: .state.result_state}'

# Clean up — terminate the dev cluster (saves money)
databricks clusters delete --cluster-id 0123-456789-abcde123
```

## Output
- Single-node development cluster created and running
- Hello world notebook uploaded to workspace
- Successful notebook execution via runs/submit API
- Serverless SQL warehouse operational
- Delta table `default.hello_world` created

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `QUOTA_EXCEEDED` | Workspace cluster limit reached | Terminate unused clusters or request quota increase |
| `INVALID_PARAMETER_VALUE: Invalid node type` | Instance type unavailable in region | Run `databricks clusters list-node-types` for valid types |
| `RESOURCE_ALREADY_EXISTS` | Notebook path occupied | Pass `overwrite=True` to `workspace.import_()` |
| `INVALID_STATE: Cluster is not running` | Cluster still starting or terminated | Call `w.clusters.ensure_cluster_is_running(cluster_id)` |
| `PERMISSION_DENIED` | Missing cluster create entitlement | Admin must grant "Allow cluster creation" in workspace settings |

## Examples

### Quick Node Type Discovery
```python
w = WorkspaceClient()
# Find cheapest general-purpose instance types
node_types = w.clusters.list_node_types()
for nt in sorted(node_types.node_types, key=lambda x: x.memory_mb)[:5]:
    print(f"{nt.node_type_id}: {nt.memory_mb}MB RAM, {nt.num_cores} cores")
```

### List Available Spark Versions
```python
w = WorkspaceClient()
for v in w.clusters.spark_versions().versions:
    if "LTS" in v.name:
        print(f"{v.key}: {v.name}")
```

## Resources
- [Clusters API](https://docs.databricks.com/api/workspace/clusters)
- [Jobs API — Submit Run](https://docs.databricks.com/api/workspace/jobs/submit)
- [Workspace API](https://docs.databricks.com/api/workspace/workspace)
- [SQL Statement Execution API](https://docs.databricks.com/api/workspace/statementexecution)

## Next Steps
Proceed to `databricks-local-dev-loop` for local development setup.
