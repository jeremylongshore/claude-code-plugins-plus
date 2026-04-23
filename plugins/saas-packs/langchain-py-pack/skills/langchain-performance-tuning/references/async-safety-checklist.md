# Async Safety Checklist

## P48 — Sync-in-Async Blocks the Loop

A single `chain.invoke(...)` call inside an `async def` FastAPI handler pins the entire event loop during the LLM round-trip. With one gunicorn worker at 20 concurrent requests, tail latency collapses because requests 2-20 queue on request 1.

### Detection

Grep pattern covering the hot spots:

```bash
rg -n 'async def' -A 50 \
  | rg -n '\b(invoke|stream|batch|get_relevant_documents|similarity_search)\(' \
  | rg -v '\b(ainvoke|astream|abatch|aget_relevant_documents|asimilarity_search|astream_events)\('
```

Any match is a bug. Fix by prefixing the method with `a`:

| Sync method | Async replacement |
|-------------|-------------------|
| `chain.invoke` | `chain.ainvoke` |
| `chain.stream` | `chain.astream` or `chain.astream_events(version="v2")` |
| `chain.batch` | `chain.abatch` |
| `retriever.get_relevant_documents` | `retriever.aget_relevant_documents` |
| `vectorstore.similarity_search` | `vectorstore.asimilarity_search` |
| `tool.run` | `tool.arun` |

### Runtime Guard

Add to a CI linter:

```python
# tests/test_no_sync_in_async.py
import ast, pathlib

SYNC_METHODS = {"invoke", "stream", "batch"}

def test_no_sync_invoke_inside_async():
    for path in pathlib.Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for call in ast.walk(node):
                    if (
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and call.func.attr in SYNC_METHODS
                    ):
                        raise AssertionError(
                            f"{path}:{call.lineno} sync .{call.func.attr}() inside async def"
                        )
```

## P59 — Async Retriever Connection Leaks

Retrievers backed by Postgres / pgvector / OpenSearch / Redis may open connections that never close under cancellation. Symptom: pool exhaustion after a burst of cancelled requests.

### FastAPI Lifespan Pattern

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.vs = await build_vectorstore()     # opens pool
    app.state.retriever = app.state.vs.as_retriever()
    try:
        yield
    finally:
        await app.state.vs.aclose()              # closes pool on shutdown

app = FastAPI(lifespan=lifespan)
```

Never create a retriever per request. The async context manager on many retrievers is not always a no-op — leaks show up as climbing `pg_stat_activity` counts hours into a load test.

## P60 — `BackgroundTasks` Fires After the Response

FastAPI's `BackgroundTasks` runs *after* the response body is sent. It is the wrong primitive for per-token SSE dispatch — the tokens arrive *after* the client already got the final response.

### Wrong

```python
@app.post("/chat")
async def chat(req: Req, bg: BackgroundTasks):
    bg.add_task(stream_tokens_to_user, req)   # fires after response — too late
    return {"status": "streaming"}
```

### Right — SSE / WebSocket

```python
from sse_starlette.sse import EventSourceResponse

@app.post("/chat")
async def chat(req: Req):
    async def gen():
        async for event in chain.astream_events({"input": req.text}, version="v2"):
            if event["event"] == "on_chat_model_stream":
                yield {"data": event["data"]["chunk"].content}
    return EventSourceResponse(gen())
```

`astream_events(version="v2")` is the LangChain 1.0 event API. Token-level TTFT instrumentation hangs off the first `on_chat_model_stream` event — see P01.

## P01 — Token Counts Lag in Streaming

Streaming responses do not deliver `usage_metadata` on every chunk. Final counts arrive in the last event (or via callback). Do not trust any per-chunk token totals until the stream closes.

```python
tokens = 0
async for event in chain.astream_events({"input": q}, version="v2"):
    if event["event"] == "on_chat_model_end":
        usage = event["data"]["output"].usage_metadata
        tokens = usage["total_tokens"]   # first reliable read is here
```

## Master Checklist

- [ ] Grep for sync methods inside `async def` returns zero.
- [ ] All retrievers close pools in a FastAPI `lifespan`.
- [ ] No streaming is dispatched via `BackgroundTasks`.
- [ ] TTFT measured from first `on_chat_model_stream` event.
- [ ] Token usage read only on `on_chat_model_end`.
- [ ] CI linter for sync-in-async is green.
