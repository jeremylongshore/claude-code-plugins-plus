# Checkpointer Comparison — Pick One Per Environment

> LangGraph 1.0.x ships four checkpointers. They are not interchangeable. Picking
> the wrong one is the difference between a dev-mode demo that loses state on
> process restart (P22) and a production system whose Postgres checkpoint table
> becomes a latency hotspot under load.

## Matrix

| Checkpointer | Import | Persistence | Concurrency | Latency (write) | Use when |
|---|---|---|---|---|---|
| `MemorySaver` | `langgraph.checkpoint.memory` | Process-local dict. Lost on restart. | Single-process. | ~microseconds. | Dev / pytest / notebooks. Anything throwaway. |
| `SqliteSaver` | `langgraph.checkpoint.sqlite` | File on disk. Shared with same-host processes. | File-lock serialization. | ~1-5 ms. | Single-host apps, CLI tools, desktop agents. Not for multi-worker web backends. |
| `PostgresSaver` | `langgraph.checkpoint.postgres` | Postgres DB. Durable, shared, backed up. | Row-level locking; serializable transactions. | ~5-15 ms. | Staging and prod for sync apps. Works everywhere Postgres works. |
| `AsyncPostgresSaver` | `langgraph.checkpoint.postgres.aio` | Same schema as sync. | `asyncpg` pool; scales to thousands of concurrent threads. | ~5-15 ms. | FastAPI / async web backends, long-running LangGraph servers, high-concurrency production. |

Storage overhead per step is typically **1-10 KB** of serialized state (JSON + pickle headers) plus a small index entry. A year-long conversation of 2,000 turns with 3 KB average state fits in ~6 MB per thread. Index-wise, `PostgresSaver` maintains a B-tree on `(thread_id, checkpoint_id)`; size grows ~20 bytes per checkpoint plus the data row itself.

## Decision Tree

1. **Are you in a test / notebook / dev script?** → `MemorySaver`.
2. **Do you run multiple processes/workers that need to share state?** → not `MemorySaver`.
3. **Is this a single-host CLI or desktop app?** → `SqliteSaver`.
4. **Is this a web backend with multiple workers, or do you need durability + backup?** → `PostgresSaver` (sync) or `AsyncPostgresSaver` (async).
5. **Is your web framework async (FastAPI, Starlette, Litestar)?** → `AsyncPostgresSaver`. Sync `PostgresSaver` inside an async endpoint blocks the event loop (see P48 for the streaming analog).

## Canonical Init — MemorySaver (dev)

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

No setup, no connection, no migration. State dies with the process. Perfect for pytest fixtures and REPL experimentation.

## Canonical Init — PostgresSaver (prod, sync)

```python
from langgraph.checkpoint.postgres import PostgresSaver
import os

DB_URI = os.environ["DATABASE_URL"]  # e.g. postgresql://user:pass@host:5432/agent_state

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()          # Idempotent. Run on startup. Run after every langgraph upgrade (P20).
    graph = builder.compile(checkpointer=checkpointer)
    result = graph.invoke(
        {"messages": [...]},
        config={"configurable": {"thread_id": "user-123"}},
    )
```

The context manager shape matters — it owns the connection pool. In a real service, wrap `setup()` + `compile()` in your app's startup hook (FastAPI `@app.lifespan`, Flask `app.before_first_request`).

## Canonical Init — AsyncPostgresSaver (prod, async)

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()
        app.state.graph = builder.compile(checkpointer=checkpointer)
        yield

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(req: ChatRequest):
    result = await app.state.graph.ainvoke(
        {"messages": [...]},
        config={"configurable": {"thread_id": req.thread_id}},
    )
    return result
```

Always `ainvoke`/`astream` on the async saver. Mixing sync `invoke` with `AsyncPostgresSaver` raises at runtime.

## Pool Sizing (Postgres)

`asyncpg` default pool is 10 connections. For a LangGraph server handling N concurrent streams, budget **at least N+2** connections (one per active graph, plus headroom for setup checks). Set `max_size` explicitly:

```python
async with AsyncPostgresSaver.from_conn_string(DB_URI, max_size=50) as cp:
    ...
```

If you share the Postgres instance with your application DB, use a separate pool for LangGraph — a stuck graph invocation will starve your app's connections otherwise.

## What Breaks When You Swap

- `MemorySaver` → `SqliteSaver`: state survives restart, but writes serialize on the file lock. Two workers will queue.
- `SqliteSaver` → `PostgresSaver`: good upgrade. Run `.setup()` in a migration script; do **not** expect old SQLite checkpoints to migrate automatically (they will not).
- `PostgresSaver` → `AsyncPostgresSaver`: only switch if your endpoints are async. Mixing is worse than either.
- Any saver → a newer `langgraph` version: run `.setup()` again in staging **before** production. Old rows without the new schema read as empty (P20).

## When Not To Checkpoint At All

For short one-shot runs (classification, extraction, single-turn Q&A), there is no memory to persist. Using a checkpointer adds 5-15 ms per call with no benefit. Compile without one:

```python
graph = builder.compile()  # No checkpointer. state only lives during invoke().
```

Reserve checkpointers for multi-turn, HITL, or long-running graphs where state survival or time-travel is a requirement.
