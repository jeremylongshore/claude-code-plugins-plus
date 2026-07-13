# `astream_events(version="v2")` Event Filtering

> How to drop thousands of lifecycle events before they hit the browser.
> Pin: `langchain-core 1.0.x`, `langgraph 1.0.x`.
> Pain-catalog anchors: P47 (event flood), P67 (`astream_log` deprecation).

## Why filter at all

`astream_events(version="v2")` is the canonical event API in LangChain 1.0 (replaces the soft-deprecated `astream_log()`). On a mid-sized invocation — say, a ReAct agent with one tool call and a 400-token response — it emits:

- ~10 `on_chain_start` / `on_chain_end` pairs (one per runnable in the LCEL tree)
- ~400 `on_chat_model_stream` events (one per token)
- 2-4 `on_tool_start` / `on_tool_end` pairs
- ~5 `on_chat_model_start` / `on_chat_model_end` pairs (one per LLM call)
- Plus `on_parser_start` / `on_parser_end`, `on_retriever_start`, etc.

Total: **~450-500 events for a single 5-second invocation**, most of them internal plumbing the browser doesn't need. Forward all of them to a browser via SSE and the tab freezes on a long run (P47). A 60-second agent invocation can emit 3,000+ events.

The fix is server-side filtering.

## The v2 event taxonomy

Each event is a dict:

```python
{
    "event": "on_chat_model_stream",   # one of the canonical names below
    "name": "ChatAnthropic",           # the component name
    "run_id": "a1b2c3...",             # unique per runnable invocation
    "tags": ["seq:step:2"],            # optional tag set
    "metadata": {"langgraph_node": "agent", ...},
    "data": {...},                     # payload varies per event
    "parent_ids": [...],               # ancestor run_ids
}
```

### Canonical event names (stable in v2)

| Event | Emitted by | `data` payload | Good for |
|-------|-----------|----------------|----------|
| `on_chat_model_start` | LLM start | `{"input": ...}` | Progress "Calling model..." |
| `on_chat_model_stream` | LLM token delta | `{"chunk": AIMessageChunk}` | **Live tokens** |
| `on_chat_model_end` | LLM end | `{"output": AIMessage}` | Token-usage update |
| `on_tool_start` | Tool call start | `{"input": ...}` | Progress "Calling tool X..." |
| `on_tool_end` | Tool call end | `{"output": ...}` | Progress "Tool X done" |
| `on_chain_start` | Any runnable start | varies | **Skip** — too noisy |
| `on_chain_stream` | Runnable yield | varies | Skip — internal |
| `on_chain_end` | Any runnable end | varies | Skip — too noisy |
| `on_parser_start` / `on_parser_end` | Output parser | varies | Skip |
| `on_retriever_start` / `on_retriever_end` | Retriever | `{"documents": [...]}` | Debug / observability |
| `on_prompt_start` / `on_prompt_end` | Prompt template | varies | Skip |

### Forward, drop, or aggregate — the three decisions

```python
FORWARD_TO_CLIENT = {
    "on_chat_model_stream",   # live tokens
    "on_tool_start",          # progress "Using tool X"
    "on_tool_end",             # progress "Tool X returned"
}

AGGREGATE_SERVER_SIDE = {
    "on_chat_model_end",      # update token counter, don't forward full AIMessage
}

DROP = {
    "on_chain_start", "on_chain_end", "on_chain_stream",
    "on_parser_start", "on_parser_end",
    "on_prompt_start", "on_prompt_end",
    "on_chat_model_start",    # redundant with node update
    "on_retriever_start", "on_retriever_end",  # forward only if building a debug view
}
```

## A production filter function

```python
import json
from typing import AsyncIterator

async def filtered_events(
    graph,
    inputs: dict,
    config: dict,
) -> AsyncIterator[dict]:
    """Filter v2 events to only what the browser needs.

    Drops ~90% of events before they leave the server. For a typical
    400-token, one-tool-call agent invocation this reduces the stream
    from ~450 events to ~410 (400 tokens + ~4 tool events + 4 progress
    markers). Most of the savings comes from dropping `on_chain_*`.
    """
    async for event in graph.astream_events(inputs, config=config, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            # chunk.content may be a list[dict] on Claude tool-use turns
            text = chunk.text if hasattr(chunk, "text") else None
            if not text and isinstance(chunk.content, str):
                text = chunk.content
            if text:
                yield {
                    "type": "token",
                    "text": text,
                    "node": event["metadata"].get("langgraph_node"),
                }

        elif kind == "on_tool_start":
            yield {
                "type": "tool_start",
                "tool": event["name"],
                "input": str(event["data"].get("input", ""))[:200],  # cap size
            }

        elif kind == "on_tool_end":
            output = event["data"].get("output")
            yield {
                "type": "tool_end",
                "tool": event["name"],
                "output": str(output)[:200] if output is not None else None,
            }

        elif kind == "on_chat_model_end":
            # Don't forward full AIMessage — just usage for the token counter
            output = event["data"].get("output")
            usage = getattr(output, "usage_metadata", None) if output else None
            if usage:
                yield {"type": "usage", "usage": dict(usage)}

        # Everything else is dropped.
```

## Wiring into SSE

```python
from fastapi.responses import StreamingResponse

async def sse_from_events(thread_id: str, user_input: str):
    config = {"configurable": {"thread_id": thread_id}}
    async for msg in filtered_events(graph, {"messages": [HumanMessage(user_input)]}, config):
        event_name = msg.pop("type")
        yield f"event: {event_name}\ndata: {json.dumps(msg, default=str)}\n\n"
    yield "event: done\ndata: {}\n\n"


@app.get("/events")
async def events(thread_id: str, q: str):
    return StreamingResponse(
        sse_from_events(thread_id, q),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
```

## Alternative — `astream_events` on specific components only

If you control the graph layout, you can tag specific runnables and filter by tag. This avoids the emit-then-drop work entirely.

```python
# When building the graph:
tagged = some_runnable.with_config(tags=["client-visible"])

# When streaming:
async for event in graph.astream_events(
    inputs,
    config=config,
    version="v2",
    include_tags=["client-visible"],
):
    # Only events from tagged components reach here
    ...
```

`include_tags`, `include_names`, and `include_types` are constructor-level filters that LangChain honors internally. For large graphs, prefer these over post-hoc Python-side filtering — they're faster.

## Compression for long events

Tool outputs and retriever results can be large (a retrieved document may be kilobytes). If you must forward them, compress or truncate:

```python
elif kind == "on_retriever_end":
    docs = event["data"].get("documents", [])
    yield {
        "type": "retrieval",
        "count": len(docs),
        # Only include snippets, not full content
        "previews": [d.page_content[:200] for d in docs[:3]],
    }
```

For raw debugging, route the full-fidelity stream to a server-side log (or LangSmith — which uses the same event stream internally), and send only the filtered summary to the browser.

## Backpressure

If the browser can't keep up (slow network, Safari tab in background), `StreamingResponse` buffers in memory. On a 3-minute agent run with 10K events, this can eat hundreds of MB per connection.

Handle by:

1. Dropping `on_chat_model_stream` events when the queue depth exceeds a threshold (client will see a gap and catch up on the next flush).
2. Coalescing: batch N tokens into a single event when the client is slow.
3. Using WebSocket with explicit flow control (see `websocket-and-reconnect.md`).

```python
import asyncio

class BoundedEventQueue:
    def __init__(self, maxsize: int = 1000):
        self.q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self.dropped = 0

    async def put(self, item):
        try:
            self.q.put_nowait(item)
        except asyncio.QueueFull:
            self.dropped += 1
            # Drop oldest token events; keep tool events (low rate, high signal)
            if item.get("type") == "token":
                return
            await self.q.put(item)  # block for non-token events
```

## Migrating from `astream_log()` (P67)

`astream_log()` is soft-deprecated in 1.0.x (removal in 2.0). Migration:

```python
# OLD (deprecated)
async for log_patch in chain.astream_log({"input": "..."}):
    for op in log_patch.ops:
        if op["path"].startswith("/logs/ChatOpenAI/streamed_output_str"):
            token = op["value"]
            ...

# NEW (v2)
async for event in chain.astream_events({"input": "..."}, version="v2"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        token = chunk.text if hasattr(chunk, "text") else chunk.content
        ...
```

v2 events are simpler to filter (flat `event` name) and provide structured data objects, not JSONPatch operations.

## Sources

- [LangChain streaming events](https://python.langchain.com/docs/how_to/streaming/#using-stream-events)
- [LangGraph streaming how-to](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- Pack pain catalog: `docs/pain-catalog.md` entries P47, P67
