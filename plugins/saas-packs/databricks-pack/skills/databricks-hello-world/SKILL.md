---
name: databricks-hello-world
description: |
  Create a minimal working Databricks example with cluster and notebook.
  Use when starting a new Databricks project, testing your setup,
  or learning basic Databricks patterns.
  Trigger with phrases like "databricks hello world", "databricks example",
  "databricks quick start", "first databricks notebook", "create cluster".
allowed-tools: Read, Write, Edit, Bash(databricks:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks Hello World

## Overview
Create your first Databricks cluster and notebook to verify setup.

## Prerequisites
- Completed `databricks-install-auth` setup
- Valid API credentials configured
- Workspace access with cluster creation permissions

## Instructions

### Step 1: Create a Cluster
```bash
# Create a small development cluster via CLI
databricks clusters create --json '{
  "cluster_name": "hello-world-cluster",
  "spark_version": "14.3.x-scala2.12",
  "node_type_id": "Standard_DS3_v2",
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
```

### Step 2: Create a Notebook
```python
# hello_world.py - upload as notebook
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create notebook content
notebook_content = """
# Databricks Hello World

# COMMAND ----------

# Simple DataFrame operations
data = [("Alice", 28), ("Bob", 35), ("Charlie", 42)]
df = spark.createDataFrame(data, ["name", "age"])
display(df)

# COMMAND ----------

# Delta Lake example
df.write.format("delta").mode("overwrite").save("/tmp/hello_world_delta")

# COMMAND ----------

# Read it back
df_read = spark.read.format("delta").load("/tmp/hello_world_delta")
display(df_read)

# COMMAND ----------

print("Hello from Databricks!")
"""

import base64
w.workspace.import_(
    path="/Users/your-email/hello_world",
    format="SOURCE",
    language="PYTHON",
    content=base64.b64encode(notebook_content.encode()).decode(),
    overwrite=True
)
print("Notebook created!")
```

### Step 3: Run the Notebook
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import Task, NotebookTask, RunNow

w = WorkspaceClient()

# Create a one-time run
run = w.jobs.submit(
    run_name="hello-world-run",
    tasks=[
        Task(
            task_key="hello",
            existing_cluster_id="your-cluster-id",
            notebook_task=NotebookTask(
                notebook_path="/Users/your-email/hello_world"
            )
        )
    ]
)

# Wait for completion
result = w.jobs.get_run(run.response.run_id).result()
print(f"Run completed with state: {result.state.result_state}")
```

### Step 4: Verify with CLI
```bash
# List clusters
databricks clusters list

# Get cluster status
databricks clusters get --cluster-id your-cluster-id

# List workspace contents
databricks workspace list /Users/your-email/

# Get run output
databricks runs get-output --run-id your-run-id
```

## Output
- Development cluster created and running
- Hello world notebook created in workspace
- Successful notebook execution
- Delta table created at `/tmp/hello_world_delta`

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Cluster quota exceeded` | Workspace limits | Terminate unused clusters |
| `Invalid node type` | Wrong instance type | Check available node types |
| `Notebook path exists` | Duplicate path | Use `overwrite=True` |
| `Cluster pending` | Startup in progress | Wait for `RUNNING` state |
| `Permission denied` | Insufficient privileges | Request workspace admin access |

## Examples

### Interactive Cluster (Cost-Effective Dev)
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import ClusterSpec

w = WorkspaceClient()

# Create single-node cluster for development
cluster = w.clusters.create_and_wait(
    cluster_name="dev-cluster",
    spark_version="14.3.x-scala2.12",
    node_type_id="Standard_DS3_v2",
    num_workers=0,
    autotermination_minutes=30,
    spark_conf={
        "spark.databricks.cluster.profile": "singleNode",
        "spark.master": "local[*]"
    }
)
print(f"Cluster created: {cluster.cluster_id}")
```

### SQL Warehouse (Serverless)
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create SQL warehouse for queries
warehouse = w.warehouses.create_and_wait(
    name="hello-warehouse",
    cluster_size="2X-Small",
    auto_stop_mins=15,
    warehouse_type="PRO",
    enable_serverless_compute=True
)
print(f"Warehouse created: {warehouse.id}")
```

### Quick DataFrame Test
```python
# Run in notebook or Databricks Connect
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Create sample data
df = spark.range(1000).toDF("id")  # 1000: 1 second in ms
df = df.withColumn("value", df.id * 2)

# Show results
df.show(5)
print(f"Row count: {df.count()}")
```

## Resources
- [Databricks Quickstart](https://docs.databricks.com/getting-started/index.html)
- [Cluster Configuration](https://docs.databricks.com/clusters/configure.html)
- [Notebooks Guide](https://docs.databricks.com/notebooks/index.html)
- [Delta Lake Quickstart](https://docs.databricks.com/delta/quick-start.html)

## Next Steps
Proceed to `databricks-local-dev-loop` for local development setup.