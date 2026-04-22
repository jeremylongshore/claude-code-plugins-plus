# `thread_id` Discipline — Fail Loud On Missing, Scope Per Tenant

> P16 is the single most common LangGraph production incident: multi-turn agent
> "forgets everything" because the caller never passed `thread_id`. No error
> raised, no log line. Every invocation gets a fresh `MemorySaver`/`PostgresSaver`
> entry under a blank key.

## Why This Happens Silently

LangGraph's checkpointer reads `config["configurable"]["thread_id"]` at invoke time. If the key is missing, the checkpointer either (a) uses `None` as the thread key (which is valid from the DB's perspective — it just maps to a specific row that all "no thread" calls share across tenants, which is worse than no memory), or (b) creates a fresh transient state. Neither path raises. The conversation history from turn 1 vanishes by turn 2 and the only signal is user-visible: "the bot keeps introducing itself."

## Fix: Middleware That Raises

Wrap your entry point. Refuse to call `graph.invoke` / `graph.ainvoke` without a `thread_id`.

```python
from typing import Any

def require_thread_id(config: dict[str, Any]) -> dict[str, Any]:
    """Raise if thread_id is missing. Return config unchanged otherwise.

    Call this at every application boundary before invoking the graph.
    Fails loudly so P16 surfaces in tests, not in production conversation logs.
    """
    configurable = (config or {}).get("configurable", {})
    thread_id = configurable.get("thread_id")
    if not thread_id:
        raise ValueError(
            "thread_id missing from config['configurable']. "
            "Every graph invocation must carry a thread_id for checkpointing. "
            "See langchain-langgraph-checkpointing skill."
        )
    if not isinstance(thread_id, str):
        raise TypeError(
            f"thread_id must be str (typically a UUID string), got {type(thread_id).__name__}"
        )
    return config
```

Attach it at every call site:

```python
config = {"configurable": {"thread_id": user_session.thread_id}}
require_thread_id(config)
result = graph.invoke(state, config=config)
```

For FastAPI, extract into a dependency:

```python
from fastapi import Depends, Header, HTTPException

async def get_thread_config(x_thread_id: str = Header(...)) -> dict:
    return {"configurable": {"thread_id": x_thread_id}}

@app.post("/chat")
async def chat(req: ChatRequest, config: dict = Depends(get_thread_config)):
    return await graph.ainvoke(req.state, config=config)
```

The `Header(...)` with no default forces FastAPI to 422 any request missing `X-Thread-Id`. Failure surfaces at the edge, not deep inside the agent loop.

## Generating `thread_id` Values

A `thread_id` is just a string. The checkpointer treats it as opaque. Use UUID4 (36 chars including dashes) unless you have a reason not to:

```python
import uuid
thread_id = str(uuid.uuid4())   # e.g. "f47ac10b-58cc-4372-a567-0e02b2c3d479"
```

Why UUID4 (not a sequential counter):

- Globally unique across processes — two workers generating threads concurrently cannot collide.
- No enumeration: a leaked URL with `thread_id=42` reveals conversation #42 exists; `thread_id=f47ac10b-...` reveals nothing.
- Stable across restarts, deploys, DB migrations.

Length matters because `PostgresSaver` indexes on `thread_id` — 36-char UUIDs add ~36 bytes per index entry, negligible. If you need shorter (SMS workflows, QR codes), use `uuid.uuid4().hex[:16]` for a 16-char hex with 64 bits of entropy.

## Where To Store `thread_id`

| Application shape | Storage |
|---|---|
| Web chat UI | Cookie or `localStorage`, keyed per logged-in user (or per session for anon) |
| Mobile app | Keychain / Keystore, rotated per conversation |
| API clients | Client generates on first call, sends as `X-Thread-Id` header on every subsequent call |
| Batch jobs | Deterministic from job id: `thread_id = f"batch-{job_id}"` |
| Slack/Discord bot | `thread_id = f"{workspace_id}:{channel_id}:{thread_ts}"` — one thread_id per platform thread |

Never store `thread_id` in the agent's own state. It is a *key to* the state, not *inside* the state.

## Tenant Scoping — Prevent Cross-Tenant Leaks

In a multi-tenant system, two users in different orgs MUST NOT share a thread_id. Bake the tenant into the key:

```python
def tenant_thread_id(tenant_id: str, user_id: str, conversation_id: str) -> str:
    return f"{tenant_id}:{user_id}:{conversation_id}"
```

This maps one-to-one to LangGraph's keyspace — `PostgresSaver` treats `"acme:alice:conv-1"` and `"globex:alice:conv-1"` as completely separate rows. Add an integration test:

```python
def test_tenants_do_not_share_state():
    graph = builder.compile(checkpointer=PostgresSaver.from_conn_string(DB_URI))
    cfg_a = {"configurable": {"thread_id": "acme:alice:conv-1"}}
    cfg_b = {"configurable": {"thread_id": "globex:alice:conv-1"}}

    graph.invoke({"messages": [HumanMessage("secret acme info")]}, cfg_a)
    state_b = graph.get_state(cfg_b)
    assert state_b.values.get("messages", []) == []  # globex sees nothing from acme
```

This pairs with P33 (retriever-level tenant isolation) — both must hold for a multi-tenant production system to be safe.

## Rotation

For security-sensitive workflows (financial, healthcare), rotate `thread_id` on a schedule or on logout. Do not reuse a dead thread's id — checkpoint history is still there until you explicitly delete it. To fully retire a conversation:

```python
# PostgresSaver exposes a delete hook via the underlying DB.
# The cleanest path is SQL on the checkpoint tables:
# DELETE FROM checkpoints WHERE thread_id = 'old-thread-id';
# DELETE FROM checkpoint_writes WHERE thread_id = 'old-thread-id';
# DELETE FROM checkpoint_blobs WHERE thread_id = 'old-thread-id';
```

Run this from a maintenance script, not from user-facing code. Wrap in a transaction so a partial delete cannot leave orphaned blobs.

## What NOT To Do

- Do not derive `thread_id` from the prompt hash. Two users typing "hello" get the same thread and see each other's history.
- Do not use `int` thread ids unless you cast to `str`. Some DB drivers silently coerce in ways that break later lookups.
- Do not log the full `thread_id` in unredacted access logs if it encodes tenant/user info — hash it first.
- Do not compile the graph without a checkpointer and then expect `thread_id` to do anything. Without a checkpointer, `thread_id` is a no-op.
