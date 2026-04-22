# First Graph Walkthrough

Annotated, line-by-line walkthrough of a minimal 3-node LangGraph 1.0
`StateGraph`. Demonstrates typed state with one reducer, a conditional edge
with `END` in `path_map`, and invocation with an explicit `thread_id`.

Target: a loop that plans, executes, and decides whether to continue or stop.
7 supersteps at most, safe at `recursion_limit=15`.

## Complete working example

```python
from typing import Annotated, Literal, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
import operator


# 1. STATE ------------------------------------------------------------------
class AgentState(TypedDict):
    # Reducer: add_messages dedupes by id, appends otherwise (P18)
    messages: Annotated[list[AnyMessage], add_messages]
    # Reducer: operator.add concatenates lists
    scratchpad: Annotated[list[str], operator.add]
    # Scalars: no reducer, updates replace
    step_count: int
    done: bool


# 2. NODES ------------------------------------------------------------------
def plan(state: AgentState) -> dict:
    """Plan the next step. Returns partial state — reducer merges."""
    plan_text = f"Step {state['step_count'] + 1}: think about it"
    return {
        "messages": [AIMessage(f"Planning: {plan_text}", id=f"plan-{state['step_count']}")],
        "scratchpad": [plan_text],
        "step_count": state["step_count"] + 1,
    }


def execute(state: AgentState) -> dict:
    """Pretend to execute. In a real agent, bind tools here."""
    result = f"Executed step {state['step_count']}"
    return {
        "messages": [AIMessage(result, id=f"exec-{state['step_count']}")],
        "done": state["step_count"] >= 3,  # stop after 3 iterations
    }


# 3. ROUTER -----------------------------------------------------------------
# Literal return type lets mypy catch typos and ensures every arm is handled
def should_continue(state: AgentState) -> Literal["execute", "end"]:
    if state["done"] or state["step_count"] >= 10:
        return "end"
    return "execute"


# 4. GRAPH ------------------------------------------------------------------
builder = StateGraph(AgentState)
builder.add_node("plan", plan)
builder.add_node("execute", execute)

builder.add_edge(START, "plan")

# path_map ALWAYS includes END — unknown router returns route here (P56)
builder.add_conditional_edges(
    "plan",
    should_continue,
    path_map={"execute": "execute", "end": END},
)
builder.add_edge("execute", "plan")  # loop back

# 5. COMPILE ----------------------------------------------------------------
checkpointer = MemorySaver()  # swap to PostgresSaver in prod (P20)
graph = builder.compile(checkpointer=checkpointer)


# 6. INVOKE -----------------------------------------------------------------
config = {
    "configurable": {"thread_id": "demo-1"},  # required for checkpointing (P16)
    "recursion_limit": 15,                    # supersteps, not iterations (P55)
}

initial: AgentState = {
    "messages": [HumanMessage("Start", id="user-0")],
    "scratchpad": [],
    "step_count": 0,
    "done": False,
}

result = graph.invoke(initial, config)
print(result["scratchpad"])
# ['Step 1: think about it', 'Step 2: think about it', 'Step 3: think about it']
print(len(result["messages"]))
# 7  (1 human + 3 plan AIMessages + 3 exec AIMessages)
```

## What each decision buys you

### Line-by-line rationale

| Block | Why it's written this way |
|---|---|
| `messages: Annotated[list[AnyMessage], add_messages]` | Without the `Annotated` reducer, `Command(update={"messages": [...]})` would replace history instead of append (P18) |
| Stable `id=f"plan-{state['step_count']}"` | `add_messages` dedupes by id. Without stable ids, retries would duplicate messages |
| `scratchpad: Annotated[list[str], operator.add]` | Plain list field still needs a reducer to concatenate on update |
| `step_count: int` (no reducer) | Scalars always replace; reducer would be no-op noise |
| `Literal["execute", "end"]` on router | Mypy catches `return "End"` typos; every arm must be covered |
| `path_map={"execute": "execute", "end": END}` | END as a fallback key prevents silent halt (P56) |
| `MemorySaver()` | In-process only. `PostgresSaver` for prod, and re-run `setup()` on every version bump (P20) |
| `"thread_id": "demo-1"` | Checkpointer keys state by thread_id. Missing it silently resets memory (P16) |
| `"recursion_limit": 15` | 4 iterations × 2 supersteps/iteration + START = 9. 15 is 1.5x headroom (P55) |

## Verifying the graph

After compile, render the graph and eyeball the reducers:

```python
print(graph.get_graph().draw_mermaid())
```

Output (simplified):

```
graph TD;
  __start__ --> plan;
  plan -.-> execute;
  plan -.-> __end__;
  execute --> plan;
```

The dashed arrows (`-.->`) mark conditional edges. Solid arrows are
unconditional. If you see a dashed arrow without a visible target in
`path_map`, that's P56 waiting to happen.

## Extending the example

### Add a real LLM

Replace the hardcoded plan/execute with a chat model call. See
`langchain-model-inference` for provider-safe initialization.

```python
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0, timeout=30)

def plan(state: AgentState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response], "step_count": state["step_count"] + 1}
```

### Add a tool call

Bind tools to the LLM and route to an `execute_tools` node when the model
returns tool_calls. See the `langgraph.prebuilt.ToolNode` helper.

### Swap to Postgres

```python
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

pool = ConnectionPool(os.environ["POSTGRES_URL"])
checkpointer = PostgresSaver(pool)
checkpointer.setup()  # run after every langgraph upgrade (P20)
graph = builder.compile(checkpointer=checkpointer)
```

## References

- [LangGraph: Low-level concepts](https://langchain-ai.github.io/langgraph/concepts/low_level/)
- [LangGraph: Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [LangGraph: MemorySaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.memory.MemorySaver)
- [LangGraph: PostgresSaver](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.postgres.PostgresSaver)
- Pain catalog: P16, P18, P20, P55, P56
