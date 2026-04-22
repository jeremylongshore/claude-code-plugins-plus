# Per-Environment Checkpointer

LangGraph checkpointers persist graph state so a workflow survives process restart, pod rescheduling, and human-in-the-loop resumption. Picking the right one per env is not optional — `MemorySaver` in staging or prod is P22 (history lost on restart) waiting to happen.

## Decision Matrix

| Env | Recommended saver | Storage | Why |
|-----|-------------------|---------|-----|
| `dev` (local) | `MemorySaver` | In-process dict | Zero setup, fast iteration, restart-tolerance not needed |
| `dev` (shared) | `SqliteSaver` | `checkpoints.db` file | Survives `pytest` restarts; single-writer OK |
| `test` / `ci` | `SqliteSaver` (in-memory URI) | `:memory:` | Same API as prod, resets per test |
| `staging` | `PostgresSaver` or `AsyncPostgresSaver` | Managed Postgres | Matches prod, catches schema drift early |
| `prod` (sync) | `PostgresSaver` | Managed Postgres | Battle-tested, supports human-in-the-loop `interrupt` |
| `prod` (async, FastAPI) | `AsyncPostgresSaver` | Managed Postgres | Non-blocking in async event loop |
| `prod` (horizontal scale) | `AsyncPostgresSaver` + advisory locks | Managed Postgres | One thread per thread_id; lock prevents concurrent writes |

Redis savers exist (community packages) but are typically a worse fit — Postgres gives you durability + queryability for the audit trail you will want.

## Factory

```python
# src/my_service/adapters/checkpointer.py
from __future__ import annotations
from typing import Literal
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

Env = Literal["dev", "staging", "prod", "test"]

def checkpointer_for(env: Env) -> BaseCheckpointSaver:
    if env in ("dev", "test"):
        return MemorySaver()
    # staging and prod: Postgres. Async variant for FastAPI.
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from my_service.config.settings import get_settings

    dsn = get_settings().postgres_dsn
    assert dsn is not None, f"POSTGRES_DSN required when env={env!r}"
    return AsyncPostgresSaver.from_conn_string(dsn.get_secret_value())
```

## Wire Into a Graph

```python
# src/my_service/services/support/graph.py
from langgraph.graph import StateGraph, END
from my_service.adapters.checkpointer import checkpointer_for
from my_service.config.settings import get_settings

def build_support_graph():
    builder = StateGraph(SupportState)
    # ... add nodes, edges ...
    builder.set_entry_point("triage")
    builder.add_edge("respond", END)

    saver = checkpointer_for(get_settings().env)
    return builder.compile(checkpointer=saver)
```

## First-Run Schema Setup

`PostgresSaver` and `AsyncPostgresSaver` need tables. Call `setup()` on startup once per environment:

```python
# src/my_service/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from my_service.adapters.checkpointer import checkpointer_for
from my_service.config.settings import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    saver = checkpointer_for(get_settings().env)
    if hasattr(saver, "setup"):
        await saver.setup()  # idempotent; creates tables if missing
    app.state.checkpointer = saver
    yield

app = FastAPI(lifespan=lifespan)
```

Running `setup()` every boot is safe — it is idempotent. For tighter control, run it as a migration step before deploy.

## Migrating Between Savers

When moving `dev` → `staging` → `prod`, the checkpoint **schema** is stable (LangGraph manages it). The **data** is not portable between savers (nor should it be — dev state should not follow you into prod). The migration is:

1. Point staging at its own Postgres. Run `setup()`. Deploy.
2. Smoke-test: start a graph in staging, restart the pod, confirm `get_state(config)` returns the interrupted state.
3. Repeat for prod with a separate DSN.

If you need to move **user data** (not checkpoints) between tenants or envs, that is a domain-level job — export via the graph's state snapshot, not by copying checkpointer tables.

## Connection Pooling

In async prod deployments, pass a pool explicitly rather than using `from_conn_string`:

```python
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

pool = AsyncConnectionPool(
    conninfo=dsn,
    min_size=2,
    max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": 0},
    open=False,
)
await pool.open()
saver = AsyncPostgresSaver(pool)
```

`prepare_threshold=0` avoids Postgres prepared-statement caching issues behind pgbouncer in transaction mode.

## Thread and Checkpoint IDs

Every `invoke` / `astream` takes `config={"configurable": {"thread_id": "..."}}`. In a multi-tenant service, namespace the thread:

```python
thread_id = f"tenant:{tenant_id}:session:{session_id}"
```

This keeps tenant data partitionable in the checkpoints table — useful for data deletion on churn (GDPR) and for blast-radius containment if a tenant's data is compromised.

## Relation to `RunnableWithMessageHistory`

If you are not using LangGraph, the equivalent P22 fix is swapping `InMemoryChatMessageHistory` for a persistent backend in `adapters/history.py`:

```python
# src/my_service/adapters/history.py
def history_for(session_id: str, tenant_id: str) -> BaseChatMessageHistory:
    env = get_settings().env
    if env == "dev":
        return InMemoryChatMessageHistory()
    from langchain_postgres import PostgresChatMessageHistory
    return PostgresChatMessageHistory(
        table_name="chat_history",
        session_id=f"tenant:{tenant_id}:session:{session_id}",
        sync_connection=..., # from settings
    )
```

Same decision matrix applies. Same P22 protection.

## Cross-Reference

- Sibling skill `langchain-langgraph-checkpointing` (L27) — when it lands — owns the deep dive on checkpoint schema, state snapshots, and resumption patterns. This reference covers only the selection-per-env decision.
- Pain catalog entry **P22** — in-memory history on process restart.
