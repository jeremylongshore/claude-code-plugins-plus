# Callback Propagation into Subgraphs

This is the single most common reason a debug bundle comes back empty from the
inside of a LangGraph agent: the `DebugCallbackHandler` fires on the outer
chain, then goes silent the moment the graph crosses into a subgraph,
`create_react_agent` inner loop, or a tool-executed sub-chain.

Pain-catalog anchor: **P28 — custom callbacks are not inherited by subgraphs**.

## The rule in one sentence

**Pass callbacks via `config["callbacks"]` at invocation time. Do not bind
them via `Runnable.with_config(callbacks=[...])` at definition time.**

## Why

LangGraph creates a child runtime per subgraph. Configuration passed at invoke
time propagates down through the `RunnableConfig` that is threaded through
every node call. Configuration bound at definition time is attached to the
parent `Runnable` only — the child runtime builds its own config from scratch.

A concise way to hold it: **definition-time config is for the node's own
execution; invoke-time config is for the whole tree below it.**

## Wrong vs right

### Wrong — callback binds at definition; fires only on outer chain

```python
from langchain_core.callbacks import BaseCallbackHandler

class DebugCallback(BaseCallbackHandler):
    def __init__(self, out):
        self.out = out
    def on_tool_start(self, *a, **kw): self.out.append(("tool_start", a, kw))

debug = DebugCallback(out=[])

# DO NOT DO THIS for diagnostics
agent = create_react_agent(model, tools).with_config(callbacks=[debug])
# agent.invoke(...)  # debug.out captures outer events only; inner tool calls silent
```

### Right — callback passed at invoke; propagates everywhere

```python
agent = create_react_agent(model, tools)

debug = DebugCallback(out=[])
result = agent.invoke(
    {"messages": [("user", "...")]},
    config={
        "configurable": {"thread_id": "t-1"},
        "callbacks": [debug],                # <-- propagates into subgraphs
        "max_concurrency": 5,
    },
)
# debug.out now contains events from every node, every tool, every inner subgraph
```

Same rule applies to `ainvoke`, `stream`, `astream`, and `astream_events`.

## `DebugCallbackHandler` — a minimal capture

A bundle-friendly callback records just enough to reconstruct what happened,
without loading the process memory with every token:

```python
from langchain_core.callbacks import BaseCallbackHandler
import time, json

class DebugCallbackHandler(BaseCallbackHandler):
    """Records tool calls, LLM start/end, and errors.

    Deliberately DOES NOT record per-token stream chunks — that is the job of
    the astream_events JSONL capture. Callbacks are for coarse-grained stack
    context; events are for fine-grained traces.
    """

    def __init__(self) -> None:
        self.records: list[dict] = []
        self._start: dict[str, float] = {}

    def _ts(self) -> float:
        return time.monotonic()

    def on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None, **kw):
        self._start[str(run_id)] = self._ts()
        self.records.append({
            "kind": "llm_start",
            "run_id": str(run_id),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
            "model": serialized.get("kwargs", {}).get("model"),
            "message_count": len(messages[0]) if messages else 0,
        })

    def on_llm_end(self, response, *, run_id, **kw):
        dt = self._ts() - self._start.pop(str(run_id), self._ts())
        usage = {}
        for gen in response.generations:
            for g in gen:
                meta = getattr(g.message, "usage_metadata", None) or {}
                usage = meta
        self.records.append({
            "kind": "llm_end",
            "run_id": str(run_id),
            "duration_ms": int(dt * 1000),
            "usage_metadata": usage,
        })

    def on_tool_start(self, serialized, input_str, *, run_id, parent_run_id=None, **kw):
        self._start[str(run_id)] = self._ts()
        self.records.append({
            "kind": "tool_start",
            "run_id": str(run_id),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
            "tool": serialized.get("name"),
            "input": input_str[:500],   # cap payload; full input lives in events.jsonl
        })

    def on_tool_end(self, output, *, run_id, **kw):
        dt = self._ts() - self._start.pop(str(run_id), self._ts())
        self.records.append({
            "kind": "tool_end",
            "run_id": str(run_id),
            "duration_ms": int(dt * 1000),
            "output_snippet": str(output)[:500],
        })

    def on_tool_error(self, error, *, run_id, **kw):
        self.records.append({
            "kind": "tool_error",
            "run_id": str(run_id),
            "error_type": type(error).__name__,
            "error_message": str(error)[:1000],
        })

    def dump_jsonl(self, path) -> int:
        """Serialize records to JSONL, return count."""
        with open(path, "w") as f:
            for r in self.records:
                f.write(json.dumps(r) + "\n")
        return len(self.records)
```

The `run_id` / `parent_run_id` pair is how you reconstruct the callback stack
in a post-hoc reader — they form a tree.

## Verifying propagation

Before you ship a debug bundle, confirm callbacks actually fired inside the
subgraph. A useful smoke test:

```python
debug = DebugCallbackHandler()
agent.invoke({"messages": [("user", "what time is it?")]},
             config={"callbacks": [debug], "configurable": {"thread_id": "smoke"}})

# Expect: at least one tool_start record with parent_run_id set (i.e. called
# from inside the agent subgraph, not from the top-level invoke)
assert any(r["kind"] == "tool_start" and r["parent_run_id"] for r in debug.records), \
    "No callbacks fired inside subgraph — P28 regression"
```

If that assertion fails, the callback was bound at definition time somewhere
in the chain construction. Grep for `with_config(callbacks=` and move all of
them to the invoke-time config.

## Interaction with other `config` keys

`config["callbacks"]` coexists with other propagating keys:

| Key | Propagates? | Common use |
|---|---|---|
| `callbacks` | Yes (into subgraphs) | Diagnostic handlers |
| `configurable.thread_id` | Yes | LangGraph checkpointer key |
| `configurable.tenant_id` | Yes | Per-request retriever factory |
| `max_concurrency` | Yes (to `.batch()` children) | P08 |
| `recursion_limit` | Yes | P10, P55 |
| `tags` | Yes | Free-form metadata for traces |
| `metadata` | Yes | LangSmith trace annotations |

A diagnostic invocation should set all of: `callbacks`, `tags` (e.g.
`["debug-bundle", incident_id]`), and `metadata` (e.g.
`{"incident_id": "INC-2026-0421-A"}`) so the resulting LangSmith trace is
immediately findable.
