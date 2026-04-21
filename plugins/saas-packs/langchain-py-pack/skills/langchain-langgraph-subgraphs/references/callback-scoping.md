# Callback Scoping Across Subgraphs

Pain-catalog entry **P28**: a `BaseCallbackHandler` attached to the parent
runnable never fires on inner agent tool calls. This is the second silent
failure in subgraph composition (after P21), and the one most likely to be
caught in production when the tracing dashboard is missing half the spans.

## Why this happens

LangGraph creates a fresh runtime per subgraph. Callbacks in LangChain are
attached to `RunnableConfig`, which is passed through the runtime. When a
`Runnable` is configured at **definition time** via
`.with_config(callbacks=[tracer])`, the callback is baked into the parent
runtime only. Child subgraphs spawn their own runtime, do not inherit the
parent's bound config, and the tracer never sees their events.

When callbacks are passed at **invocation time** via
`runnable.invoke(inputs, config={"callbacks": [tracer]})`, LangGraph propagates
the config down into every subgraph's runtime. The tracer sees everything.

The fix is one line, but it is counterintuitive because for non-LangGraph
Runnables `.with_config(callbacks=[...])` does work. This is LangGraph-specific
behavior.

## The wrong way

```python
from langchain_core.callbacks import BaseCallbackHandler

class Tracer(BaseCallbackHandler):
    def on_chat_model_start(self, *a, **kw): print("LLM start")
    def on_tool_start(self, *a, **kw):        print("tool start")
    def on_chain_start(self, *a, **kw):       print("chain start")

# WRONG — binds to parent runtime only. Subgraph tool/LLM events are lost.
traced = parent_graph.with_config(callbacks=[Tracer()])
traced.invoke({"messages": [HumanMessage("...")], "session_id": "s1"},
              config={"configurable": {"thread_id": "s1"}})
```

You will see `chain start` for the parent nodes and nothing for anything inside
a subgraph. LangSmith dashboards show a truncated trace with "gaps" where the
subgraph ran.

## The right way

```python
# RIGHT — pass callbacks in config at invocation time; propagates to all subgraphs.
parent_graph.invoke(
    {"messages": [HumanMessage("...")], "session_id": "s1"},
    config={
        "configurable": {"thread_id": "s1"},
        "callbacks": [Tracer()],
    },
)
```

Every tool call, LLM call, and chain boundary in every subgraph fires through
the tracer.

## Covering every invocation path

The rule extends to `ainvoke`, `astream`, `astream_events`, `batch`:

```python
# async
await parent_graph.ainvoke(state, config={"callbacks": [tracer], ...})

async for chunk in parent_graph.astream(state, config={"callbacks": [tracer], ...}):
    ...

async for event in parent_graph.astream_events(state, version="v2",
                                               config={"callbacks": [tracer], ...}):
    ...

parent_graph.batch(states, config={"callbacks": [tracer], ...})
```

A single missed invocation path in a rarely-hit retry code path is enough to
hide subgraph events.

## Helper: centralize config construction

To avoid this bug recurring across dozens of invocation sites, build configs in
one place:

```python
from typing import Any
from langchain_core.runnables import RunnableConfig

def app_config(*, thread_id: str,
               callbacks: list | None = None,
               recursion_limit: int = 25,
               **extra: Any) -> RunnableConfig:
    """Always call this to build a config. Never hand-roll one."""
    cfg: RunnableConfig = {
        "configurable": {"thread_id": thread_id, **extra},
        "recursion_limit": recursion_limit,
    }
    if callbacks:
        cfg["callbacks"] = callbacks
    return cfg

# Usage
parent_graph.invoke(state, config=app_config(thread_id="s1", callbacks=[Tracer()]))
```

A lint rule in CI (`grep -r "with_config(callbacks=" --include="*.py"`) catches
regressions.

## Debugging a "missing callback" gap

1. Does the tracer fire on any event? If not, it is not registered at all.
2. Does it fire on parent nodes but not child ones? Classic P28. Move to
   `config["callbacks"]` at the invocation site.
3. Does it fire on subgraph chain-start but not on LLM calls inside the
   subgraph? Check that the subgraph's LLM was built without its own
   conflicting `.with_config(callbacks=[])` that overrode the inherited config.
4. Does it fire in sync invocations but not async? Check the async handler
   methods (`on_chat_model_start` has async variants for async code paths —
   `BaseCallbackHandler` supports both; `AsyncCallbackHandler` is sync-incompatible).

## Capturing handler for tests

Pair with the [Testing Subgraphs](testing-subgraphs.md) reference:

```python
class CaptureHandler(BaseCallbackHandler):
    def __init__(self):
        self.events: list[str] = []

    def on_chain_start(self, serialized, inputs, **kwargs):
        name = serialized.get("name") if serialized else "?"
        self.events.append(f"chain_start:{name}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.events.append(f"tool_start:{serialized.get('name', '?')}")

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.events.append("llm_start")

def test_callbacks_propagate_to_subgraph():
    handler = CaptureHandler()
    parent_graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": "t"},
                "callbacks": [handler]},
    )
    # Assert we saw events from BOTH parent and child
    parent_events = [e for e in handler.events if "planner" in e]
    child_events = [e for e in handler.events if "executor" in e]
    assert parent_events, "no parent events captured"
    assert child_events, "P28: callbacks did not propagate to subgraph"
```

## Related pain-catalog entries

- **P28** — Custom callbacks are not inherited by subgraphs (the entry this
  reference anchors)
- **P19** — `astream_events(version="v2")` emits a different event stream;
  most subgraph-aware tracing uses it
- **P01** — `ChatAnthropic.stream()` delays token counts; pair with callback
  scoping to get cost dashboards right
