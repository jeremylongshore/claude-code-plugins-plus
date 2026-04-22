# LangGraph 1.0 `stream_mode` Comparison

> Deep reference for `graph.astream(input, config, stream_mode=...)`. Pin: `langgraph 1.0.x`.
> Upstream docs: <https://langchain-ai.github.io/langgraph/how-tos/streaming/>, <https://langchain-ai.github.io/langgraph/concepts/streaming/>.

## The three modes at a glance

| Mode | Emits | Payload shape | Emit rate | Typical use | Overdraw risk |
|------|-------|---------------|-----------|-------------|---------------|
| `"messages"` | LLM token chunks | `tuple[AIMessageChunk, metadata_dict]` | ~30-80 tokens/sec per active model call | Live-token chat UI | **Low** — append single token to DOM |
| `"updates"` | Per-node state *diff* | `dict[node_name, partial_state]` | 1 per node execution (typically 2-20 per invocation) | Progress bar, status line, "Working on X..." | **Low** — discrete ticks |
| `"values"` | Full state snapshot after each step | `dict[full_state]` | 1 per node execution (same cadence as `updates`) | Debug / time-travel / replay | **High** — entire state on every tick; token-level UIs overdraw |

All three are async iterators over the same underlying superstep execution. They differ only in what each iteration yields.

## Mode 1 — `stream_mode="messages"` (token-level)

Yields `(chunk, metadata)` tuples where `chunk` is an `AIMessageChunk` (a delta, not a full message) and `metadata` describes which node and which LLM call produced it.

```python
async for chunk, metadata in graph.astream(
    {"messages": [HumanMessage("Hello")]},
    config={"configurable": {"thread_id": "u-42"}},
    stream_mode="messages",
):
    # chunk is an AIMessageChunk — content is typically a single token string
    # or a content-block delta (see langchain-content-blocks skill)
    if chunk.content:
        print(chunk.content, end="", flush=True)
```

### Payload sample (messages)

```python
# First token
(AIMessageChunk(content="Hello"), {"langgraph_node": "agent", "langgraph_step": 1, "ls_model_name": "claude-sonnet-4-6"})
# Second token
(AIMessageChunk(content=","), {...})
# Third token
(AIMessageChunk(content=" how"), {...})
# Final tokens include usage_metadata on the last chunk only
(AIMessageChunk(content="?", usage_metadata={"input_tokens": 12, "output_tokens": 4, "total_tokens": 16}), {...})
```

### When `"messages"` is right

- Live chat UI where the model's answer should type out character-by-character
- Voice-chat token streaming to a TTS engine
- Partial-response UX (e.g., grey "still thinking" text that gets replaced)

### When `"messages"` is wrong

- A progress bar that should tick by *step*, not by *token* (use `"updates"`)
- A debug view that needs the entire graph state (use `"values"`)
- A one-shot non-LLM workflow (no LLM tokens to stream — the iterator will be empty or only contain tool outputs that come through different mechanisms)

### Gotcha — content blocks in chunks

On Claude, `chunk.content` can be a `list[dict]` during tool-use turns, not a `str`. Use the content-block extractor from the `langchain-content-blocks` skill, or call `chunk.text` if you only want text portions.

---

## Mode 2 — `stream_mode="updates"` (per-node diffs)

Yields a dict whose keys are node names and whose values are the partial state the node just wrote. One emit per node execution.

```python
async for update in graph.astream(
    {"messages": [HumanMessage("Research X")]},
    config={"configurable": {"thread_id": "u-42"}},
    stream_mode="updates",
):
    for node_name, state_diff in update.items():
        await websocket.send_json({"type": "node_update", "node": node_name, "diff": state_diff})
```

### Payload sample (updates)

```python
# After the 'planner' node runs
{"planner": {"plan": ["search", "summarize", "format"]}}
# After the 'search' node runs
{"search": {"results": [{"url": "...", "snippet": "..."}]}}
# After the 'summarize' node runs
{"summarize": {"summary": "The topic is ..."}}
# Finally
{"__end__": {...}}
```

### When `"updates"` is right

- Per-node progress bar ("Planning..." → "Searching..." → "Summarizing...")
- Status sidebar showing which node is currently active
- Dashboard that aggregates per-step metrics (latency, tokens, tool calls)

### When `"updates"` is wrong

- You need streaming tokens inside a single node (combine with `"messages"` — see below)
- You need the full state, not just the diff (use `"values"`)

### Gotcha — empty diffs

Nodes that only route (e.g., conditional edges) emit no state change. Your client should handle empty-diff updates as "node-ran" signals, not errors.

---

## Mode 3 — `stream_mode="values"` (full state)

Yields the entire graph state after each node runs.

```python
async for state in graph.astream(
    {"messages": [HumanMessage("Debug this")]},
    config={"configurable": {"thread_id": "u-42"}},
    stream_mode="values",
):
    # state is the complete graph state — all fields, not just what changed
    await debugger.record_snapshot(state)
```

### Payload sample (values)

```python
# After node 1 runs
{"messages": [HumanMessage("Debug this"), AIMessage("Let me start...")],
 "plan": ["search", "summarize"], "results": [], "summary": ""}
# After node 2 runs — entire state again, with updated fields
{"messages": [HumanMessage("Debug this"), AIMessage("Let me start..."),
              AIMessage("I need to search for X")],
 "plan": ["search", "summarize"], "results": [{...}], "summary": ""}
```

### When `"values"` is right

- Debugger / time-travel view where you need every intermediate state
- State replay for test recording
- Observability pipelines that snapshot state to a data lake

### When `"values"` is wrong

- **Any browser UI with significant state size** — the payload scales with state. A 20-step agent whose state includes message history will ship ~20× the final state size. Browsers overdraw, tabs freeze (this is the P19 failure mode)
- Production user-facing UX — use `"updates"` or `"messages"` instead
- Any path where bandwidth matters

---

## Combining modes with a list

Pass a list to get multiple streams interleaved into one iterator. Each emit is a `(mode, payload)` tuple.

```python
async for mode, payload in graph.astream(
    {"messages": [HumanMessage("Research X")]},
    config={"configurable": {"thread_id": "u-42"}},
    stream_mode=["updates", "messages"],
):
    if mode == "updates":
        for node_name, diff in payload.items():
            await websocket.send_json({"type": "progress", "node": node_name})
    elif mode == "messages":
        chunk, metadata = payload
        if chunk.content:
            await websocket.send_json({"type": "token", "text": chunk.content})
```

### When combined modes are right

- Dashboard that shows both a per-node progress bar *and* streaming tokens in the active node's pane
- Debug tool that captures full state (`values`) and also logs token timing (`messages`)

### Gotcha — ordering

Combined-mode events come in execution order but the interleave is not guaranteed to be line-synchronous. Don't rely on "update came before any token" — use the metadata fields (`langgraph_step`, `langgraph_node`) to correlate.

---

## The combined-mode ordering picture

```
superstep 1: planner node
  -> emit ("updates", {"planner": {"plan": [...]}})

superstep 2: agent node (LLM call)
  -> emit ("messages", (chunk_1, meta))  [token "The"]
  -> emit ("messages", (chunk_2, meta))  [token " plan"]
  -> emit ("messages", (chunk_3, meta))  [token " is"]
  -> ... ~80 tokens ...
  -> emit ("updates", {"agent": {"messages": [final_ai_msg]}})

superstep 3: tool node
  -> emit ("updates", {"tool": {"results": [...]}})
```

A ~5-second invocation on a 400-token response emits roughly:

- `"messages"` mode: ~400 events
- `"updates"` mode: ~4 events
- `"values"` mode: ~4 events, each ~state-size bytes
- Combined `["messages", "updates"]`: ~404 events

## Non-LLM pathways

If your graph has nodes that don't invoke an LLM (pure tool calls, DB queries, transformations), `"messages"` mode yields nothing from those nodes. Use `astream_events(version="v2")` with tool-event filtering (see `astream-events-filtering.md`) if you need to stream tool progress.

## Summary decision tree

```
Do you need LLM tokens rendered live in the UI?
├── Yes → stream_mode="messages"
│         (combine with "updates" if you also need node progress)
└── No, I need per-step progress
    ├── Full state for debug/replay? → stream_mode="values"
    └── Just what changed (most UIs) → stream_mode="updates"
```

## Sources

- [LangGraph streaming how-to](https://langchain-ai.github.io/langgraph/how-tos/streaming/)
- [LangGraph streaming concepts](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- Pack pain catalog: `docs/pain-catalog.md` entry P19
