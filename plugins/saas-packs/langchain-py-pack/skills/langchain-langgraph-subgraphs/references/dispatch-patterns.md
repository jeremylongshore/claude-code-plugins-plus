# Dispatch Patterns: Node vs `Send` vs `Command(graph=PARENT)`

Four ways a parent graph can talk to a subgraph. Picking the wrong one turns
what should be clean composition into duct-tape. This reference is the decision
tree.

## Decision tree — when to use what

```
Do you need a subgraph at all?
├── Will the logic be reused by a different parent graph?       -> subgraph
├── Does it own a distinct failure/retry/recursion budget?      -> subgraph
├── Does it have a non-trivial internal state machine?          -> subgraph
├── Does it need to be versioned/shipped independently?         -> subgraph
├── None of the above but > ~8 related nodes?                   -> subgraph
└── Otherwise                                                   -> inline function / plain node

Once you've committed to a subgraph, pick the dispatch:

Parent calls child exactly once, serially, with a known state subset?
   -> A. Compiled subgraph as a node  (simplest, use this by default)

Parent dispatches N parallel children, N depends on runtime state?
   -> B. Send(graph, state) fan-out   (reducers on shared keys merge results)

Child needs to short-circuit the parent flow and hand control back directly?
   -> C. Command(graph=Command.PARENT, update=..., goto=...)  (escape hatch)

Child is heavy enough to deserve its own process / scaling / deploy?
   -> D. Separate service + HTTP / queue (not a subgraph anymore)
```

## A. Compiled subgraph as a node

The default. The compiled child is passed to `add_node` exactly like a function.

```python
from langgraph.graph import StateGraph, END

def build_executor(llm) -> StateGraph:
    return (
        StateGraph(ExecutorState)
        .add_node("run_tool", run_tool_node)
        .add_node("summarize", summarize_node)
        .add_edge("run_tool", "summarize")
        .add_edge("summarize", END)
        .set_entry_point("run_tool")
        .compile()
    )

executor_graph = build_executor(llm)

parent = (
    StateGraph(ParentState)
    .add_node("plan", planner_node)
    .add_node("execute", executor_graph)   # compiled subgraph as a node
    .add_node("finalize", finalize_node)
    .add_edge("plan", "execute")
    .add_edge("execute", "finalize")
    .set_entry_point("plan")
    .compile()
)
```

**When it is right:** a planner-executor pipeline, a data-enrichment pass
between stages, a nested tool-calling loop that should be reusable.

**Sizing:** 1 parent + 2-4 subgraphs is the typical planner-executor shape.

**Gotchas:** only keys in `SHARED_KEYS` propagate (P21). The subgraph gets its
own `recursion_limit` budget (P55).

## B. `Send(graph, state)` fan-out

Parallel dispatch. One conditional edge returns a list of `Send` objects; each
`Send` invokes the named graph/node with its own state slice.

```python
from langgraph.types import Send

def dispatch_specialists(state: ParentState) -> list[Send]:
    """Fan out one subgraph call per plan item. N is runtime-determined."""
    return [
        Send(
            "specialist_graph",
            {
                "messages": state["messages"],
                "session_id": state["session_id"],
                "tenant_id": state["tenant_id"],
                "topic": topic,                # topic is specialist-only
            },
        )
        for topic in state["plan"]
    ]

parent.add_conditional_edges("plan", dispatch_specialists, ["specialist_graph"])
```

**When it is right:** one planner decides to run M research queries in parallel;
a router invokes 3 specialists concurrently; a batch step dispatches N
per-tenant subgraphs.

**Sizing:** `Send` is cheap — dispatching 10-50 parallel children is routine.
At 100+ consider a queue-based worker pool instead.

**Gotchas:**
- Each `Send` state is evaluated independently — **no shared scratch across
  siblings**. If two parallel specialists need to see each other's output,
  use two sequential subgraph-as-node calls instead.
- The parent's reducer on shared keys is what merges results when the parallel
  children return. Without an `add_messages`-style reducer on the parent side
  (P18), you will lose all but one result.
- `recursion_limit` applies **per `Send`**, not globally for the fan-out.

## C. `Command(graph=Command.PARENT, update=..., goto=...)`

Inside a subgraph node, return a `Command` that jumps control back to the
parent with an explicit state update. Use sparingly — it breaks the "subgraph
returns cleanly to its compose point" abstraction.

```python
from langgraph.types import Command

def specialist_early_exit(state: ExecutorState) -> Command:
    """If the first tool call already finished the task, skip the rest of the
    subgraph and jump straight to the parent's finalize node."""
    if state.get("tool_result", {}).get("done"):
        return Command(
            graph=Command.PARENT,
            update={"messages": [AIMessage("done early")]},
            goto="finalize",
        )
    # normal in-subgraph update
    return {"retries": state.get("retries", 0) + 1}
```

**When it is right:** a rare early-exit that needs to bypass the rest of the
subgraph's teardown. A fatal child error that must bubble up with context. A
fast-path where invoking the full subgraph is wasted work.

**Gotchas:**
- `goto` names a **parent** node — not a subgraph node. Omitting `goto` returns
  control to the point the subgraph was invoked, which is usually what you
  want.
- `update` can include keys not in the parent's schema (LangGraph 1.0.x
  permits this), but do not rely on it — declare the keys for type safety.
- Mixing `Command(graph=Command.PARENT)` with `Send` fan-out causes surprising
  interleaving. Do not combine in the same subgraph without careful testing.

## D. Separate service (not a subgraph)

Sometimes the right answer is "this is not a subgraph anymore." Signals that a
subgraph should be promoted to a separate service:

- It owns its own infrastructure (a GPU, a large model, a specialized DB)
- It has a different scaling profile (bursty vs steady)
- It needs to be deployable and restartable independently
- Multiple unrelated parent graphs call it (cross-product coupling)
- It has its own security boundary (tenant isolation, PII handling)

At that point, wrap it as an HTTP/gRPC/queue-based service and call it from a
plain node in the parent graph — not a subgraph. The state contract becomes an
API contract.

## Sizing reference

| Shape | Typical subgraph count | Dispatch |
|---|---|---|
| Planner-executor | 2-4 | A (node) |
| Hierarchical agent team (supervisor + specialists) | N specialists | B (`Send`) |
| Stage pipeline (fetch -> enrich -> summarize -> store) | 3-4 | A (node) in sequence |
| Reusable library (shared across parents) | any | A (node) + versioned contract |
| Early-exit optimization | 1 (within the child) | C (`Command`) |

## Related pain-catalog entries

- **P18** — Reducers are required for list fields that merge across `Send` fan-out
- **P19** — `stream_mode="updates"` is usually what you want when observing subgraph output
- **P21** — Only shared keys propagate (all dispatches)
- **P55** — Per-subgraph `recursion_limit` budget applies independently
