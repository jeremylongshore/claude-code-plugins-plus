# Persistent Chat History

## The P22 Failure

`InMemoryChatMessageHistory` lives in the process heap. Every deploy, OOM kill, or autoscale event wipes every user's conversation. On multi-worker deploys it is worse: each worker has its own copy, so a second request from the same user may land on a worker that never saw the first turn.

`RunnableWithMessageHistory` accepts any `BaseChatMessageHistory` — wire a persistent backend.

## Redis-Backed History (Default Choice)

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory

def history_factory(session_id: str) -> RedisChatMessageHistory:
    return RedisChatMessageHistory(
        session_id=session_id,
        url="redis://history:6379/2",
        ttl=60 * 60 * 24 * 14,  # 14 days
    )

chain_with_history = RunnableWithMessageHistory(
    chain,
    history_factory,
    input_messages_key="input",
    history_messages_key="history",
)
```

Operational notes:

- `ttl` is mandatory. Without it, abandoned sessions pile up forever.
- Pin the Redis namespace per tenant (`session_id` prefix) to avoid collision and to support per-tenant purge.
- Size the Redis instance for worst-case turn count. 10k active users * 20 turns * 1KB ≈ 200MB — small, but monitor it.
- `RedisChatMessageHistory` uses `rpush` + `lrange`. Read/write is O(1) / O(n) respectively; truncate long histories before persisting (see trim policy below).

## Postgres-Backed History

Use when compliance requires relational storage, or when you already pay for managed Postgres and want one fewer dependency.

```python
from langchain_postgres import PostgresChatMessageHistory
import psycopg

conn = psycopg.connect(os.environ["POSTGRES_URL"])
PostgresChatMessageHistory.create_tables(conn, "chat_history")

def history_factory(session_id: str) -> PostgresChatMessageHistory:
    return PostgresChatMessageHistory(
        "chat_history",
        session_id,
        sync_connection=conn,
    )
```

Trade-off: Postgres is durable and queryable, but each append is a synchronous write with higher latency than Redis. Cache recent turns in memory if per-request latency matters.

## LangGraph Checkpointer as History

`LangGraph 1.0` offers first-class thread state via `AsyncPostgresSaver` / `AsyncSqliteSaver`. For graph-style agents this is strictly better than `RunnableWithMessageHistory` — the checkpoint captures the full state machine, not just messages.

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph

async with AsyncPostgresSaver.from_conn_string(os.environ["POSTGRES_URL"]) as saver:
    await saver.setup()
    graph = builder.compile(checkpointer=saver)
    result = await graph.ainvoke(
        {"messages": [("user", "...")]},
        config={"configurable": {"thread_id": session_id}},
    )
```

## Migrating Off `InMemoryChatMessageHistory`

1. Replace the factory function — nothing else changes if you use `RunnableWithMessageHistory`.
2. Backfill is usually not needed; prior sessions were going to be lost on restart regardless.
3. Add an integration test that restarts the worker mid-conversation and asserts the next turn still sees the earlier messages.
4. Add a dashboard for history size per session. Pages > 100 turns are bugs or abuse.

## Trim Policy

Long histories cost tokens linearly. Apply one of:

- **Last-N window**: keep the latest 20-40 turns. Simple, bounded cost.
- **Summarization compaction**: summarize older turns into a system-message summary. Use LangGraph's `SummarizationNode` or a periodic cron that rewrites old sessions.
- **Token budget trim**: keep messages until a token budget is hit, oldest first. Most accurate for cost control.

## Checklist

- [ ] No production path uses `InMemoryChatMessageHistory`.
- [ ] `ttl` set on every `RedisChatMessageHistory`.
- [ ] Tenant isolation in session keys.
- [ ] Restart test exists and is wired into CI.
- [ ] Trim policy is chosen and implemented.
