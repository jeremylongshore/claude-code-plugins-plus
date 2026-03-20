---
name: databricks-sdk-patterns
description: |
  Apply production-ready Databricks SDK patterns for Python and REST API.
  Use when implementing Databricks integrations, refactoring SDK usage,
  or establishing team coding standards for Databricks.
  Trigger with phrases like "databricks SDK patterns", "databricks best practices",
  "databricks code patterns", "idiomatic databricks".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Databricks SDK Patterns

## Overview
Production-ready patterns for the Databricks Python SDK (`databricks-sdk`). These patterns cover client initialization, error handling, resource lifecycle management, and type-safe job construction.

## Prerequisites
- Completed `databricks-install-auth` setup
- `databricks-sdk` v0.20+ installed (`pip install databricks-sdk`)
- Understanding of Python context managers and dataclasses

## Instructions

### Step 1: Implement Singleton Client
Avoid creating multiple `WorkspaceClient` instances. Each one re-authenticates and holds its own HTTP session.

```python
from databricks.sdk import WorkspaceClient
from functools import lru_cache

@lru_cache(maxsize=1)
def get_workspace_client(profile: str = "DEFAULT") -> WorkspaceClient:
    """Return a singleton WorkspaceClient, cached per profile."""
    return WorkspaceClient(profile=profile)

# Usage throughout your codebase
w = get_workspace_client()
w_prod = get_workspace_client(profile="production")
```

For multi-workspace scripts, use `AccountClient` at the account level:
```python
from databricks.sdk import AccountClient

a = AccountClient(
    host="https://accounts.cloud.databricks.com",
    account_id="your-account-id",
)
for workspace in a.workspaces.list():
    print(f"{workspace.workspace_name}: {workspace.deployment_name}")
```

### Step 2: Add Error Handling Wrapper
Wrap API calls with structured error handling that distinguishes transient from permanent failures.

```python
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional
from databricks.sdk.errors import (
    NotFound,
    PermissionDenied,
    TooManyRequests,
    TemporarilyUnavailable,
    ResourceConflict,
)

T = TypeVar("T")

@dataclass
class Result(Generic[T]):
    value: Optional[T] = None
    error: Optional[str] = None
    retryable: bool = False

    @property
    def ok(self) -> bool:
        return self.error is None

def safe_api_call(func, *args, **kwargs) -> Result:
    """Execute a Databricks API call with structured error handling."""
    try:
        return Result(value=func(*args, **kwargs))
    except NotFound as e:
        return Result(error=f"Not found: {e.message}", retryable=False)
    except PermissionDenied as e:
        return Result(error=f"Permission denied: {e.message}", retryable=False)
    except TooManyRequests as e:
        return Result(error=f"Rate limited (retry after {e.retry_after_secs}s)", retryable=True)
    except TemporarilyUnavailable as e:
        return Result(error=f"Service unavailable: {e.message}", retryable=True)
    except ResourceConflict as e:
        return Result(error=f"Conflict: {e.message}", retryable=False)

# Usage
result = safe_api_call(w.clusters.get, cluster_id="abc-123")
if result.ok:
    print(f"Cluster state: {result.value.state}")
elif result.retryable:
    print(f"Transient error, retry: {result.error}")
else:
    print(f"Permanent failure: {result.error}")
```

### Step 3: Context Manager for Cluster Lifecycle
Ensure clusters are cleaned up after use, even on exceptions.

```python
from contextlib import contextmanager
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import ClusterDetails, State

@contextmanager
def managed_cluster(w: WorkspaceClient, cluster_config: dict):
    """Start a cluster, yield it, and terminate on exit."""
    cluster = w.clusters.create_and_wait(**cluster_config)
    try:
        yield cluster
    finally:
        if cluster.state in (State.RUNNING, State.PENDING, State.RESIZING):
            w.clusters.delete(cluster_id=cluster.cluster_id)
            print(f"Terminated cluster {cluster.cluster_id}")

# Usage
config = {
    "cluster_name": "ephemeral-etl",
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "i3.xlarge",
    "num_workers": 2,
    "autotermination_minutes": 30,
}

with managed_cluster(w, config) as cluster:
    print(f"Running on cluster {cluster.cluster_id}")
    # Do work...
    w.jobs.run_now(job_id=123)
# Cluster is auto-terminated here
```

### Step 4: Type-Safe Job Builder
Use the SDK's dataclass types instead of raw dicts for job configuration. This catches schema errors at construction time.

```python
from databricks.sdk.service.jobs import (
    CreateJob,
    JobCluster,
    Task,
    NotebookTask,
    CronSchedule,
    JobEmailNotifications,
)
from databricks.sdk.service.compute import ClusterSpec, AutoScale

def build_etl_job(name: str, notebook_path: str, schedule_cron: str) -> CreateJob:
    """Build a fully-typed ETL job configuration."""
    return CreateJob(
        name=name,
        job_clusters=[
            JobCluster(
                job_cluster_key="etl_cluster",
                new_cluster=ClusterSpec(
                    spark_version="14.3.x-scala2.12",
                    node_type_id="i3.xlarge",
                    autoscale=AutoScale(min_workers=1, max_workers=4),
                ),
            )
        ],
        tasks=[
            Task(
                task_key="main",
                job_cluster_key="etl_cluster",
                notebook_task=NotebookTask(notebook_path=notebook_path),
            )
        ],
        schedule=CronSchedule(
            quartz_cron_expression=schedule_cron,
            timezone_id="UTC",
        ),
        email_notifications=JobEmailNotifications(
            on_failure=["oncall@company.com"],
        ),
    )

# Create the job
job_config = build_etl_job(
    name="daily-sales-etl",
    notebook_path="/Repos/team/etl/sales_pipeline",
    schedule_cron="0 0 6 * * ?",
)
created = w.jobs.create(**job_config.as_dict())
print(f"Created job {created.job_id}")
```

### Step 5: Pagination Helper
The SDK paginates list results automatically via iterators, but when you need all results at once or want progress tracking:

```python
from typing import Callable, Iterator

def collect_with_progress(iterator: Iterator, label: str, batch_size: int = 100) -> list:
    """Collect paginated results with progress logging."""
    items = []
    for i, item in enumerate(iterator, 1):
        items.append(item)
        if i % batch_size == 0:
            print(f"  {label}: fetched {i} items...")
    print(f"  {label}: {len(items)} total")
    return items

# Usage
all_jobs = collect_with_progress(w.jobs.list(), "Jobs")
all_clusters = collect_with_progress(w.clusters.list(), "Clusters")
running = [c for c in all_clusters if c.state == State.RUNNING]
print(f"Running clusters: {len(running)}/{len(all_clusters)}")
```

## Output
- Singleton `WorkspaceClient` with profile-based caching
- `Result` wrapper for type-safe, structured error handling
- Context manager for auto-terminating ephemeral clusters
- Type-safe job builder using SDK dataclasses (no raw dicts)
- Pagination helper with progress logging

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `databricks.sdk.errors.NotFound` | Resource deleted or wrong ID | Validate IDs before use; handle gracefully in cleanup |
| `databricks.sdk.errors.PermissionDenied` | Token lacks required scope | Use service principal with correct Unity Catalog grants |
| `databricks.sdk.errors.InvalidParameterValue` | Wrong type in job config | Use SDK dataclasses instead of raw dicts for compile-time safety |
| `databricks.sdk.errors.ResourceAlreadyExists` | Duplicate cluster/job name | Add unique suffix or check-before-create pattern |
| `AttributeError` on SDK objects | SDK version mismatch | Pin `databricks-sdk>=0.20.0` in requirements.txt |

## Examples

### Health Check Script
```python
w = get_workspace_client()
me = w.current_user.me()
print(f"Authenticated as: {me.user_name}")
print(f"Workspace: {w.config.host}")
print(f"Active clusters: {sum(1 for c in w.clusters.list() if c.state == State.RUNNING)}")
print(f"Jobs defined: {sum(1 for _ in w.jobs.list())}")
```

### Multi-Workspace Inventory
```python
a = AccountClient()
for ws in a.workspaces.list():
    w = WorkspaceClient(host=f"https://{ws.deployment_name}.cloud.databricks.com")
    clusters = list(w.clusters.list())
    running = [c for c in clusters if c.state == State.RUNNING]
    print(f"{ws.workspace_name}: {len(running)} running / {len(clusters)} total clusters")
```

## Resources
- [Databricks SDK for Python](https://docs.databricks.com/dev-tools/sdk-python.html)
- [SDK API Reference](https://databricks-sdk-py.readthedocs.io/)
- [SDK Source on GitHub](https://github.com/databricks/databricks-sdk-py)

## Next Steps
Apply patterns in `databricks-core-workflow-a` for Delta Lake ETL.
