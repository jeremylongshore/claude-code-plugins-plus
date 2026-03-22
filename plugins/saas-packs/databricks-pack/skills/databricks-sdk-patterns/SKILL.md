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
tags: [saas, databricks, api, python]

---
# Databricks SDK Patterns

## Overview
Production-ready patterns for the Databricks Python SDK (`databricks-sdk`). Covers singleton client initialization, typed error handling, cluster lifecycle management, type-safe job construction, and pagination. Uses real SDK exception classes and API shapes.

## Prerequisites
- `databricks-sdk>=0.20.0` installed
- Authentication configured (see `databricks-install-auth`)
- Python 3.10+

## Instructions

### Step 1: Singleton Client with Profile Support
Each `WorkspaceClient` holds an HTTP session and re-authenticates. Cache instances.

```python
from databricks.sdk import WorkspaceClient, AccountClient
from functools import lru_cache

@lru_cache(maxsize=4)
def get_client(profile: str = "DEFAULT") -> WorkspaceClient:
    """Cached WorkspaceClient — one per profile."""
    return WorkspaceClient(profile=profile)

@lru_cache(maxsize=1)
def get_account_client() -> AccountClient:
    """Account-level client for multi-workspace operations."""
    return AccountClient(
        host="https://accounts.cloud.databricks.com",
        account_id="00000000-0000-0000-0000-000000000000",
    )

# Usage
w = get_client()
w_prod = get_client("production")
```

### Step 2: Structured Error Handling
The SDK raises typed exceptions from `databricks.sdk.errors`. Distinguish transient (retryable) from permanent failures.

```python
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Callable
from databricks.sdk.errors import (
    NotFound,
    PermissionDenied,
    TooManyRequests,
    TemporarilyUnavailable,
    ResourceConflict,
    InvalidParameterValue,
    ResourceAlreadyExists,
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

def safe_call(func: Callable, *args, **kwargs) -> Result:
    """Execute a Databricks API call with structured error classification."""
    try:
        return Result(value=func(*args, **kwargs))
    except NotFound as e:
        return Result(error=f"Not found: {e.message}", retryable=False)
    except PermissionDenied as e:
        return Result(error=f"Permission denied: {e.message}", retryable=False)
    except InvalidParameterValue as e:
        return Result(error=f"Invalid parameter: {e.message}", retryable=False)
    except ResourceAlreadyExists as e:
        return Result(error=f"Already exists: {e.message}", retryable=False)
    except ResourceConflict as e:
        return Result(error=f"Conflict: {e.message}", retryable=False)
    except TooManyRequests as e:
        return Result(error=f"Rate limited (retry after {e.retry_after_secs}s)", retryable=True)
    except TemporarilyUnavailable as e:
        return Result(error=f"Unavailable: {e.message}", retryable=True)

# Usage
result = safe_call(w.clusters.get, cluster_id="0123-456789-abcde")
if result.ok:
    print(f"Cluster state: {result.value.state}")
elif result.retryable:
    print(f"Retry later: {result.error}")
else:
    print(f"Permanent failure: {result.error}")
```

### Step 3: Cluster Lifecycle Context Manager
Ensure ephemeral clusters are terminated even on exceptions.

```python
from contextlib import contextmanager
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import State

@contextmanager
def managed_cluster(w: WorkspaceClient, **cluster_config):
    """Create a cluster, yield it, terminate on exit."""
    cluster = w.clusters.create_and_wait(**cluster_config)
    try:
        yield cluster
    finally:
        if cluster.state in (State.RUNNING, State.PENDING, State.RESIZING):
            w.clusters.delete(cluster_id=cluster.cluster_id)
            print(f"Terminated cluster {cluster.cluster_id}")

# Usage — cluster auto-cleaned even if job fails
with managed_cluster(w,
    cluster_name="ephemeral-etl",
    spark_version="14.3.x-scala2.12",
    node_type_id="i3.xlarge",
    num_workers=2,
    autotermination_minutes=30,
) as cluster:
    run = w.jobs.submit(
        run_name="one-off",
        tasks=[SubmitTask(
            task_key="task1",
            existing_cluster_id=cluster.cluster_id,
            notebook_task=NotebookTask(notebook_path="/Repos/team/etl/main"),
        )],
    ).result()
```

### Step 4: Type-Safe Job Builder
Use SDK dataclasses instead of raw dicts for compile-time safety.

```python
from databricks.sdk.service.jobs import (
    CreateJob, JobCluster, Task, NotebookTask,
    CronSchedule, JobEmailNotifications, WebhookNotifications, Webhook,
)
from databricks.sdk.service.compute import ClusterSpec, AutoScale

def build_etl_job(
    name: str,
    notebook_path: str,
    cron: str,
    alert_email: str,
    webhook_id: str | None = None,
) -> CreateJob:
    """Build a fully-typed ETL job definition."""
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
        schedule=CronSchedule(quartz_cron_expression=cron, timezone_id="UTC"),
        email_notifications=JobEmailNotifications(on_failure=[alert_email]),
        webhook_notifications=WebhookNotifications(
            on_failure=[Webhook(id=webhook_id)] if webhook_id else []
        ),
        max_concurrent_runs=1,
    )

# Create the job
job_def = build_etl_job(
    name="daily-sales-etl",
    notebook_path="/Repos/team/etl/sales_pipeline",
    cron="0 0 6 * * ?",
    alert_email="oncall@company.com",
)
created = w.jobs.create(**job_def.as_dict())
print(f"Job created: {created.job_id}")
```

### Step 5: Paginated Collection with Progress
The SDK auto-paginates via iterators. Wrap for progress tracking and filtering.

```python
from typing import Iterator

def collect_with_progress(iterator: Iterator, label: str, batch_log: int = 100) -> list:
    """Drain a paginated iterator with progress logging."""
    items = []
    for i, item in enumerate(iterator, 1):
        items.append(item)
        if i % batch_log == 0:
            print(f"  {label}: {i} items fetched...")
    print(f"  {label}: {len(items)} total")
    return items

# Usage
all_jobs = collect_with_progress(w.jobs.list(), "Jobs")
all_clusters = collect_with_progress(w.clusters.list(), "Clusters")
running = [c for c in all_clusters if c.state == State.RUNNING]
print(f"Running: {len(running)}/{len(all_clusters)} clusters")
```

## Output
- Singleton `WorkspaceClient` with profile-based caching
- `Result[T]` wrapper for typed, structured error handling
- Context manager for ephemeral cluster lifecycle
- Type-safe job builder using SDK dataclasses
- Pagination helper with progress logging

## Error Handling
| SDK Exception | HTTP Code | Retryable | Typical Cause |
|--------------|-----------|-----------|---------------|
| `NotFound` | 404 | No | Resource deleted or wrong ID |
| `PermissionDenied` | 403 | No | Token lacks required scope |
| `InvalidParameterValue` | 400 | No | Wrong type or value in API call |
| `ResourceAlreadyExists` | 409 | No | Duplicate name or conflicting create |
| `ResourceConflict` | 409 | No | Job already running |
| `TooManyRequests` | 429 | Yes | Rate limit exceeded |
| `TemporarilyUnavailable` | 503 | Yes | Control plane overloaded |

## Examples

### Health Check Script
```python
w = get_client()
me = w.current_user.me()
print(f"User: {me.user_name}")
print(f"Host: {w.config.host}")
print(f"Auth: {w.config.auth_type}")
print(f"Running clusters: {sum(1 for c in w.clusters.list() if c.state == State.RUNNING)}")
print(f"Jobs defined: {sum(1 for _ in w.jobs.list())}")
```

### Multi-Workspace Inventory
```python
acct = get_account_client()
for ws in acct.workspaces.list():
    ws_client = WorkspaceClient(host=f"https://{ws.deployment_name}.cloud.databricks.com")
    clusters = list(ws_client.clusters.list())
    running = [c for c in clusters if c.state == State.RUNNING]
    print(f"{ws.workspace_name}: {len(running)} running / {len(clusters)} total")
```

## Resources
- [Databricks SDK for Python](https://docs.databricks.com/aws/en/dev-tools/sdk-python)
- [SDK Error Classes](https://databricks-sdk-py.readthedocs.io/en/latest/errors.html)
- [SDK GitHub](https://github.com/databricks/databricks-sdk-py)

## Next Steps
Apply patterns in `databricks-core-workflow-a` for Delta Lake ETL.
