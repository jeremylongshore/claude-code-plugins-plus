# WebSocket Streaming + Reconnect-by-`thread_id`

> WebSocket variant of the LangGraph streaming pattern, with mid-stream reconnect
> that resumes from the checkpointer. Pin: `langgraph 1.0.x`, `fastapi >= 0.110`.
> Pain-catalog anchors: P16 (missing `thread_id`), P48 (sync in async).

## When to use WebSocket instead of SSE

| Criterion | SSE | WebSocket |
|-----------|-----|-----------|
| Server-to-client only | Yes | Yes |
| Client-to-server mid-stream (e.g., "cancel") | No (requires second HTTP call) | Yes |
| Auto-reconnect built in | Yes (EventSource) | No (roll your own) |
| Behind Cloudflare Free | Often buffered | Always works |
| Binary payloads | Inefficient (base64) | Native |
| Browser support | Everywhere | Everywhere (mostly — check corporate proxies) |
| Proxy gotchas | Buffering (P46) | Fewer, but some firewalls drop long-idle sockets |

Rule of thumb: **SSE for one-way live tokens to a browser. WebSocket when the user may cancel, interrupt, or send follow-up messages mid-stream.**

## Minimal WebSocket endpoint

```python
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from app.graph import build_graph

app = FastAPI()
# Postgres checkpointer so state survives pod restarts (P22)
checkpointer = PostgresSaver.from_conn_string("postgresql://...")
graph = build_graph(checkpointer=checkpointer)


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """Bidirectional stream for a single conversation thread.

    Client sends: {"type": "user_message", "text": "..."}
    Server sends: {"type": "token", "text": "..."} | {"type": "tool_start", ...} | ...
    """
    await websocket.accept()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg["type"] == "user_message":
                await _stream_response(websocket, msg["text"], config)
            elif msg["type"] == "cancel":
                # Cancel handling — see "Cancellation" below
                break
            else:
                await websocket.send_json({"type": "error", "message": f"Unknown type: {msg['type']}"})

    except WebSocketDisconnect:
        # Client disconnected mid-stream. State is persisted in the checkpointer,
        # so reconnect with the same thread_id resumes where we left off.
        pass


async def _stream_response(ws: WebSocket, user_input: str, config: dict):
    async for chunk, metadata in graph.astream(
        {"messages": [HumanMessage(user_input)]},
        config=config,
        stream_mode="messages",
    ):
        text = chunk.text if hasattr(chunk, "text") else None
        if not text and isinstance(chunk.content, str):
            text = chunk.content
        if text:
            await ws.send_json({
                "type": "token",
                "text": text,
                "node": metadata.get("langgraph_node"),
            })
    await ws.send_json({"type": "done"})
```

## Reconnect and resume

Because LangGraph checkpointers persist state per `thread_id`, reconnecting with the same `thread_id` picks up the conversation history automatically — **but** `graph.astream(user_input, ...)` starts a *new* invocation, not a resume of an in-flight one.

Two reconnect patterns:

### Pattern A — Reconnect between turns (the common case)

The client disconnects after the previous response finished. On reconnect, just send the next user message:

```javascript
// Client
let ws = new WebSocket(`wss://api.example.com/ws/${threadId}`);

ws.addEventListener("open", () => {
  // Safe to send immediately — checkpointer has the prior messages
  ws.send(JSON.stringify({type: "user_message", text: "Follow-up question"}));
});

ws.addEventListener("close", () => {
  // Auto-reconnect with exponential backoff
  setTimeout(() => connect(), Math.min(backoffMs *= 2, 30000));
});
```

The server doesn't need to know a reconnect happened. The checkpointer handles history; the new `astream` call runs normally.

### Pattern B — Resume mid-stream (the hard case)

The client disconnects *during* a response. Two options:

1. **Discard the in-flight response, replay the last user message on reconnect.** Simple; the user sees the agent re-answer. Works because LangGraph is deterministic enough on re-run for most workflows, and the checkpoint ensures no double-tool-execution (the checkpointer records tool results before re-running).

2. **Resume from checkpoint.** Explicitly read the last checkpoint and emit its content to catch the client up, then continue streaming if the invocation is still running server-side (it may not be — LangGraph's default is to stop when the client disconnects).

```python
async def resume_or_new(ws: WebSocket, user_input: str | None, config: dict):
    """If a prior invocation left partial state, replay it to the client.
    Otherwise start fresh.
    """
    # Read the current checkpoint
    state = await graph.aget_state(config)
    prior_messages = state.values.get("messages", [])

    # Tell the client what already exists (so it can render history)
    await ws.send_json({
        "type": "history",
        "messages": [{"role": m.type, "content": str(m.content)} for m in prior_messages],
    })

    if user_input:
        await _stream_response(ws, user_input, config)
```

Keeping a long-running invocation alive across disconnect requires running it in a background task detached from the WebSocket context (e.g., `asyncio.create_task` at session level, or a job queue). For most chat UIs, Pattern A is sufficient — users restart their turn on reconnect.

## Cancellation

If the user clicks "stop," the WebSocket handler must cancel the in-flight `astream` iteration:

```python
@app.websocket("/ws/{thread_id}")
async def ws(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    config = {"configurable": {"thread_id": thread_id}}
    active_task: asyncio.Task | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg["type"] == "user_message":
                if active_task and not active_task.done():
                    active_task.cancel()
                active_task = asyncio.create_task(
                    _stream_response(websocket, msg["text"], config)
                )
            elif msg["type"] == "cancel":
                if active_task and not active_task.done():
                    active_task.cancel()
                await websocket.send_json({"type": "cancelled"})

    except WebSocketDisconnect:
        if active_task:
            active_task.cancel()
```

When the task is cancelled, LangGraph drops the in-flight superstep but keeps the last checkpoint — the user can retry or the next turn will pick up from a consistent state.

## Half-open connection detection

A WebSocket can appear open on both ends while the underlying TCP is dead (e.g., laptop sleep, NAT timeout). Detect by sending periodic pings:

```python
async def keepalive(ws: WebSocket):
    while True:
        await asyncio.sleep(30)
        try:
            await ws.send_json({"type": "ping"})
        except Exception:
            break  # send failed — socket is dead
```

The client should respond with `{"type": "pong"}`. If no pong in 60 seconds, assume dead.

Browser WebSocket API does *not* expose ping/pong frames at the application level — you must implement them as regular messages.

## Always require `thread_id` at the boundary (P16)

If your WebSocket URL doesn't include a `thread_id`, somewhere in your handler someone will call `graph.astream(inputs)` without one, and every turn will have amnesia with no error. Enforce at the route:

```python
@app.websocket("/ws/{thread_id}")
async def ws(websocket: WebSocket, thread_id: str):
    if not thread_id or not _is_valid_thread_id(thread_id):
        await websocket.close(code=1008, reason="Invalid thread_id")
        return
    # ...
```

Consider adding middleware that raises if `config["configurable"]["thread_id"]` is missing — there's an example in the `langchain-middleware-patterns` skill.

## Never call `.invoke()` or `.stream()` sync in an async handler (P48)

```python
# WRONG — blocks the event loop; one slow stream blocks every connection
@app.websocket("/ws/{thread_id}")
async def ws(websocket: WebSocket, thread_id: str):
    for chunk in graph.stream(...):
        await websocket.send_json(...)

# RIGHT — always async
@app.websocket("/ws/{thread_id}")
async def ws(websocket: WebSocket, thread_id: str):
    async for chunk in graph.astream(...):
        await websocket.send_json(...)
```

Add a lint rule: in any file that imports `WebSocket` or has `async def`, ban `graph.invoke(` and `graph.stream(` (the sync variants).

## Testing the WebSocket path

```python
# pytest + httpx + websockets
from fastapi.testclient import TestClient

def test_ws_stream(client: TestClient):
    with client.websocket_connect("/ws/t-1") as ws:
        ws.send_json({"type": "user_message", "text": "Hi"})
        # Expect at least one token event
        first = ws.receive_json()
        assert first["type"] in {"token", "tool_start"}
        # Drain to done
        while True:
            msg = ws.receive_json()
            if msg["type"] == "done":
                break
```

For reconnect testing, close the first WebSocket mid-stream, open a second with the same `thread_id`, verify the checkpointer preserved history.

## Sources

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [LangGraph checkpointers](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [LangGraph streaming how-to](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- Pack pain catalog: `docs/pain-catalog.md` entries P16, P22, P48
