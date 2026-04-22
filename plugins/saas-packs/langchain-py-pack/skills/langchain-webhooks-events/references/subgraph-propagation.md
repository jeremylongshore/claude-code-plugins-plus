# Subgraph Propagation — Why `config["callbacks"]` is Required

P28 is the silent bug that destroys observability: a `BaseCallbackHandler`
attached via `Runnable.with_config(callbacks=[handler])` is **not** inherited
by LangGraph subgraphs. The outer agent fires callbacks; the inner subagent's
tool calls are completely dark. This reference explains why and gives a
repeatable fix + propagation probe.

## The mechanism

LangChain 1.0 has two ways to attach callbacks to a `Runnable`:

| Method | When bound | Inherited by subgraphs? |
|---|---|---|
| `runnable.with_config({"callbacks": [h]})` | At definition | **No** — captured in the parent runnable's config, not the invocation config |
| `runnable.invoke(x, config={"callbacks": [h]})` | At invocation | **Yes** — config flows through every child `Runnable.invoke` call |

LangGraph creates a child `Runnable` per node and subgraph. The child receives
the config from the parent's invocation context. Callbacks bound at
*definition* time are trapped in the parent's scope. Callbacks passed in
config flow down.

## The wrong pattern (P28)

```python
from langgraph.prebuilt import create_react_agent

inner_agent = create_react_agent(model=llm, tools=[search_tool])
outer_graph = (
    StateGraph(State)
    .add_node("plan", planner)
    .add_node("execute", inner_agent)   # subgraph
    .add_edge("plan", "execute")
    .compile()
)

# WRONG — handler bound at definition; does NOT propagate
agent_with_cb = outer_graph.with_config({"callbacks": [dispatch_handler]})
await agent_with_cb.ainvoke({"messages": [...]})
# Result: dispatch fires on 'plan' and 'execute' entry,
# but NOT on search_tool invocation inside inner_agent. Dark.
```

## The right pattern

```python
await outer_graph.ainvoke(
    {"messages": [...]},
    config={
        "callbacks": [dispatch_handler],
        "configurable": {"thread_id": "t1"},
    },
)
# Result: dispatch fires on every tool call everywhere in the graph —
# including deeply nested subgraphs and their tools.
```

The rule: **every invocation site that might hit a subgraph must pass
callbacks through config**. There is no way to "register" a callback once and
have it apply to nested invocations.

## Propagation probe

Before shipping, verify the callbacks reach every level:

```python
from collections import Counter
from langchain_core.callbacks import AsyncCallbackHandler

class EventCounter(AsyncCallbackHandler):
    """Counts events by the runnable name that emitted them.
    Useful for asserting subgraph propagation in tests."""
    def __init__(self):
        self.counts: Counter[str] = Counter()

    async def on_chain_start(self, serialized, inputs, *, run_id, **kwargs):
        name = kwargs.get("name") or (serialized or {}).get("name") or "<anon>"
        self.counts[f"chain_start:{name}"] += 1

    async def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
        name = (serialized or {}).get("name") or "<anon>"
        self.counts[f"tool_start:{name}"] += 1

# Test:
counter = EventCounter()
await outer_graph.ainvoke(
    {"messages": [HumanMessage("find the user and summarize")]},
    config={"callbacks": [counter]},
)

# If subgraph propagation works, you see both outer and inner names:
assert "chain_start:plan" in counter.counts
assert "chain_start:execute" in counter.counts   # subgraph entry
assert "tool_start:search_tool" in counter.counts  # tool inside subgraph
```

If `tool_start:search_tool` is **missing**, callbacks are not propagating —
you bound them at definition, not invocation.

## Per-subgraph event filtering

Once callbacks propagate, you often want different dispatch rules for the
outer graph vs subgraphs. Use the `kwargs["name"]` or the `tags` list:

```python
class ScopedDispatchHandler(AsyncCallbackHandler):
    """Dispatch only events from named subgraphs we care about."""

    SUBGRAPH_ALLOWLIST = {"execute", "retrieval", "synthesis"}

    async def on_chain_end(self, outputs, *, run_id, **kwargs):
        name = kwargs.get("name", "")
        if name not in self.SUBGRAPH_ALLOWLIST:
            return
        self._dispatch("chain_end", {"name": name, "run_id": str(run_id)})
```

Alternative: tag the subgraph nodes explicitly when building the graph, then
filter on tags:

```python
graph.add_node("execute", inner_agent, metadata={"tags": ["subgraph", "customer-visible"]})

# In handler:
tags = kwargs.get("tags", []) or []
if "customer-visible" not in tags:
    return
```

Tags are more stable than names because node names can change without breaking
downstream filtering code.

## run_id continuity across subgraphs

Every callback receives a `run_id` kwarg. In subgraphs, the child's `run_id`
differs from the parent's — but the `parent_run_id` kwarg links them.

```python
async def on_tool_end(self, output, *, run_id, parent_run_id=None, **kwargs):
    # Build a call tree for debugging:
    self.call_tree[run_id] = parent_run_id
```

Your idempotency key uses the handler's *init-time* `run_id` (the logical chain
invocation id), not the per-callback `run_id`. The per-callback `run_id` is
for correlating events within a single invocation.

## Callbacks + `astream_events` interaction

If you use both `astream_events(version="v2")` AND a callback handler, the
handler fires during event emission. Both mechanisms see the same events.
Typical pattern:

- Callback handler → dispatch to external sinks (webhooks, Kafka)
- `astream_events` consumer → forward filtered events to SSE stream for UI

Do not use one for both purposes — the coupling makes testing hard and the
event shapes differ.

## Debugging a dark subagent

Symptoms:
- Handler fires on outer nodes, silent on inner nodes
- No exceptions, no warnings — just no events
- `langchain.debug=True` output shows the inner runnable executing

Steps:

1. Check invoke site — is config passed?
   ```python
   await graph.ainvoke(x, config={"callbacks": [h]})  # right
   await graph.with_config({"callbacks": [h]}).ainvoke(x)  # wrong
   ```
2. Install the `EventCounter` probe above and assert inner names appear.
3. If step 2 passes but your dispatch handler still misses events — check
   event filtering. You may be filtering out the inner events by name /
   runnable type (`on_chain_start` for `RunnableLambda` is often silenced).
4. If none of the above — check that you're subclassing `AsyncCallbackHandler`
   (not `BaseCallbackHandler`) and that your handler methods are `async def`.
   Mixing sync/async leads to silent skips.

## Cross-ref to debug-bundle skill

The pack's `langchain-debug-bundle` skill has the full P28 triage flowchart,
including LangSmith/OTEL correlation patterns. Use this reference for dispatch
propagation, that skill for observability propagation.

## Cross-references

- [Async Callback Handler](async-callback-handler.md) — the handler subclass this relies on
- [Dispatch Targets](dispatch-targets.md) — where events go once they reach the handler
- [Idempotency and Retry](idempotency-and-retry.md) — how `run_id` fits into idempotency keys
