# Capturing `astream_events(version="v2")` for a Debug Bundle

Streaming events are the richest evidence in a debug bundle — every token, every
tool call, every node transition. They are also the most dangerous: a single
invocation of a 4-node graph on a 2000-token response emits 2000+ events. Dump
it raw and the JSONL file is 50 MB; load it in jq and your laptop hangs.

Related pain-catalog entries: P47 (events flood), P67 (`astream_log` soft-deprecated).

## The event taxonomy (v2)

| Event                    | Volume       | Keep? | Why |
|--------------------------|--------------|-------|-----|
| `on_chat_model_start`    | 1 per call   | Yes   | Captures prompt, model params |
| `on_chat_model_stream`   | 1 per token  | Yes (sample) | Reconstructs the actual response |
| `on_chat_model_end`      | 1 per call   | Yes   | Usage metadata, stop reason |
| `on_tool_start`          | 1 per call   | Yes   | Tool name + args |
| `on_tool_end`            | 1 per call   | Yes   | Tool output |
| `on_tool_error`          | rare         | **Always** | Primary diagnostic signal |
| `on_chain_start`         | 1 per node   | No (noise) | Drop unless debugging graph structure |
| `on_chain_end`           | 1 per node   | No (noise) | Drop unless debugging graph structure |
| `on_chain_stream`        | 1 per chunk  | No    | Duplicates `on_chat_model_stream` |
| `on_retriever_start`     | 1 per query  | Yes   | What did we search for? |
| `on_retriever_end`       | 1 per query  | Yes   | What did we get back? |
| `on_parser_start`/`end`  | 1 per parser | No    | Low signal |
| `on_prompt_start`/`end`  | 1 per prompt | No    | Low signal |
| `on_custom_event`        | varies       | Yes   | User-emitted, probably important |

Default **keep set** that works for 90% of incidents:

```python
KEEP_EVENTS = {
    "on_chat_model_start",
    "on_chat_model_end",
    "on_tool_start",
    "on_tool_end",
    "on_tool_error",
    "on_retriever_start",
    "on_retriever_end",
    "on_custom_event",
}
# Plus: all events whose type ends in "_error"
# Plus: sampled `on_chat_model_stream` (every Nth chunk, N≈10)
```

## Capture pattern

```python
import json, itertools
from pathlib import Path

async def capture_events(graph, inputs, config, out_path: Path,
                         keep: set[str] = None,
                         stream_sample_every: int = 10) -> int:
    """Run the graph once, write filtered v2 events as JSONL.

    Returns the number of events written (typical: 50-200 for an agent call).
    """
    keep = keep or KEEP_EVENTS
    stream_counter = itertools.count()
    written = 0
    with out_path.open("w") as f:
        async for evt in graph.astream_events(inputs, config=config, version="v2"):
            name = evt["event"]
            # Sample streaming tokens; keep every Nth
            if name == "on_chat_model_stream":
                if next(stream_counter) % stream_sample_every != 0:
                    continue
            # Keep anything in the whitelist OR any error event
            if name in keep or name.endswith("_error"):
                # Strip the runnable instance (not JSON-serializable)
                evt_out = {
                    "event": name,
                    "name": evt.get("name"),
                    "run_id": evt.get("run_id"),
                    "tags": evt.get("tags"),
                    "metadata": evt.get("metadata"),
                    "data": _scrub_data(evt.get("data", {})),
                }
                f.write(json.dumps(evt_out, default=str) + "\n")
                written += 1
    return written


def _scrub_data(data: dict) -> dict:
    """Convert LangChain objects to JSON-safe dicts.

    AIMessage, ToolMessage, etc. have a .dict() method that serializes cleanly.
    """
    out = {}
    for k, v in data.items():
        if hasattr(v, "model_dump"):       # Pydantic v2
            out[k] = v.model_dump()
        elif hasattr(v, "dict"):            # Pydantic v1 fallback
            out[k] = v.dict()
        elif isinstance(v, dict):
            out[k] = {kk: _scrub_data({"_": vv})["_"] for kk, vv in v.items()}
        else:
            out[k] = v
    return out
```

Sampling `on_chat_model_stream` at every 10th chunk is the single biggest size
win — a 2000-token response goes from 2000 events to 200. The reconstructed
response quality is still good enough for triage because `on_chat_model_end`
captures the full final message.

## JSONL schema

Each line is one JSON object. Fields that matter for triage:

```json
{
  "event": "on_tool_error",
  "name": "search_orders",
  "run_id": "<uuid>",
  "tags": ["graph:route_intent", "seq:4"],
  "metadata": {"langgraph_node": "call_tool", "langgraph_step": 4},
  "data": {
    "input": {"tool_call_id": "tc_xyz", "name": "search_orders", "args": {"customer_id": "[REDACTED]"}},
    "error": "psycopg.errors.ConnectionFailure: connection refused",
    "error_type": "ConnectionFailure"
  }
}
```

`metadata.langgraph_node` and `langgraph_step` are the single most useful fields
for reproducing the failure path through the graph.

## Replay pattern

A colleague reading the bundle can replay the event stream to understand the
flow without reconnecting to the LLM:

```python
import json

with open("events.jsonl") as f:
    for line in f:
        evt = json.loads(line)
        if evt["event"] == "on_tool_start":
            print(f"[step {evt['metadata']['langgraph_step']}] → tool {evt['name']}({evt['data']['input']['args']})")
        elif evt["event"] == "on_tool_end":
            print(f"  ← {evt['data']['output']!r:.120}")
        elif evt["event"].endswith("_error"):
            print(f"  !! {evt['data'].get('error_type')}: {evt['data'].get('error')}")
```

## Size budget

| Scenario                         | Raw events  | Filtered (keep-set + 1:10 sample) |
|----------------------------------|-------------|-----------------------------------|
| Single LLM call, 500 output tokens | ~520      | ~55 |
| Agent call, 3 tool uses            | ~2,100    | ~110 |
| Multi-turn graph, 10 nodes         | ~8,000    | ~200 |
| Deep agent, 25 recursion steps     | ~20,000   | ~450 |

A 450-event JSONL is ~500 KB — fits in an email, loads in any editor.

## Do NOT use `astream_log`

`astream_log()` is soft-deprecated in 1.0 (P67). It emits a different shape and
no longer receives new event types. Any diagnostic tooling written against it
will break on the next minor version.

## Failure modes

| Symptom                          | Cause                                      | Fix |
|----------------------------------|--------------------------------------------|-----|
| JSONL is empty                   | Graph invocation raised before first event | Wrap the `astream_events` iterator in try/except and still write manifest |
| JSONL has no subgraph events     | Callbacks attached via `with_config`       | See [callback-propagation.md](callback-propagation.md) — use `config["callbacks"]` |
| 100 MB+ JSONL                    | No filter applied, or stream-sample disabled | Enforce `KEEP_EVENTS` whitelist; sample 1:10 minimum |
| `TypeError: not JSON serializable` | A tool returned a custom object            | `_scrub_data` missed a type — add a `model_dump`/`dict` fallback |
