# Recursion Limits

`recursion_limit` on LangGraph defaults to **25**. The name is misleading — it
is not a loop counter. It counts **total supersteps**, and a superstep is one
synchronous round of node executions. A linear graph with enough nodes can hit
25 without any loop; a graph with parallel branches inflates the count further.
This is pain-catalog entry P55.

## What counts as a superstep

One superstep = one batch of nodes that run in parallel after a state update.

- Entering `START` and dispatching to the first node: **1 superstep**
- Each sequential node transition: **+1 superstep**
- A `Send`-based fan-out to N parallel nodes: **+1 superstep** (not +N — parallel branches share a step)
- The merge node after a fan-out: **+1 superstep**
- Reaching `END`: the run stops, no additional count

```
START -> plan (1) -> execute (2) -> validate (3) -> END      # 3 supersteps
START -> plan (1) -> [exec_a, exec_b, exec_c] (2) -> merge (3) -> END    # 3 supersteps
```

## Typical budgets

| Graph shape | Description | Supersteps | Suggested `recursion_limit` |
|---|---|---|---|
| Simple ReAct (plan → tool → observe → end) | 3-4 node loop, 2-3 iterations | 6-12 | 15 |
| Planner + executor + validator | 3-stage pipeline with 1-2 retries | 12-25 | 30 |
| Chain-of-thought with reflection | Plan, act, reflect, revise, act, done | 15-30 | 40 |
| Deep agent (sub-planners, scratch FS) | Nested planning, branch merge, summary | 30-60 | 75 |
| Fan-out N parallel branches + merge | Depends on depth, not on N (parallel branches share a step) | 2 × max_depth | 2 × max_depth + 10 headroom |

Default 25 is safe for simple ReAct, dangerous for anything planner-shaped.

## Sizing your graph

Add a step counter to state and log every node entry:

```python
from typing import Annotated, TypedDict
import operator

class State(TypedDict):
    step_count: Annotated[int, operator.add]  # each node increments by 1
    # ... rest of state

def instrument(fn):
    """Wrap a node to log superstep count."""
    def wrapped(state: State) -> dict:
        print(f"[superstep ~{state['step_count']}] {fn.__name__}")
        update = fn(state)
        return {**update, "step_count": 1}  # operator.add increments
    return wrapped

builder.add_node("plan", instrument(plan))
builder.add_node("execute", instrument(execute))
```

Run one invocation and read the log. Pick `recursion_limit` = observed max +
50% headroom.

## Diagnosing `GraphRecursionError` on a non-looping graph

If a graph that clearly doesn't loop hits `GraphRecursionError`, the usual
cause is one of:

1. **A conditional edge loops on a condition that never terminates.** The
   router returns "retry" forever because the retry counter is never
   incremented. Fix: increment a counter in state and short-circuit at N
   retries.

2. **A fan-out fans to more branches than expected.** A router returning
   `[Send(...) for t in state["tasks"]]` where `tasks` grew unboundedly.
   Fix: cap the task list or batch into chunks of K.

3. **A subgraph is counted at the parent budget.** Subgraphs consume the
   parent's recursion budget by default. Fix: compile the subgraph with its
   own higher `recursion_limit`, or restructure so it runs as a tool call
   rather than an inline subgraph.

4. **The graph really is that long.** Planner + executor + validator +
   summarizer + formatter = 5 nodes × 5 iterations = 25 supersteps. Raise
   the limit.

## Raising the limit

```python
config = {
    "configurable": {"thread_id": "user-42"},
    "recursion_limit": 50,  # supersteps, not iterations
}
result = graph.invoke(inputs, config)
```

There is no hard upper bound, but be deliberate. A runaway graph at
`recursion_limit=1000` will burn tokens and wall time before it errors.
Pair high limits with a per-session token budget (see
`langchain-cost-tuning`) and a wall-clock timeout.

## Subgraph refactor

When a graph hits recursion limits because one stage is complex, extract
that stage into a subgraph with its own budget:

```python
# The complex executor stage becomes its own graph
exec_builder = StateGraph(ExecutorState)
# ... build the executor subgraph ...
exec_graph = exec_builder.compile()  # no checkpointer — inherit from parent

# Parent graph invokes the subgraph as a node
def execute_node(state: ParentState) -> dict:
    sub_config = {"recursion_limit": 30}  # subgraph has its own budget
    sub_result = exec_graph.invoke({"task": state["task"]}, sub_config)
    return {"result": sub_result["output"]}

parent_builder.add_node("execute", execute_node)
```

The parent budget now only counts "execute" as 1 superstep, regardless of how
many supersteps the subgraph internally consumes.

## References

- [LangGraph: Recursion limit](https://langchain-ai.github.io/langgraph/how-tos/recursion-limit/)
- [LangGraph: Supersteps concept](https://langchain-ai.github.io/langgraph/concepts/low_level/#graphs)
- [LangGraph: Subgraphs](https://langchain-ai.github.io/langgraph/concepts/low_level/#subgraphs)
- Pain catalog: P55, P10 (related — agent loops on vague prompts)
