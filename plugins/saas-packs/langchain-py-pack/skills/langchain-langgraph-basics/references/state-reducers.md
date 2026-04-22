# State Reducers

Every list-shaped field in a LangGraph `TypedDict` state needs a reducer.
Without one, node returns and `Command(update=...)` calls *replace* the field
instead of merging. This is pain-catalog entry P18 and the #1 reason a resumed
graph loses its prior message history.

## Built-in reducers

| Reducer | Import | Behavior | When to use |
|---|---|---|---|
| `add_messages` | `from langgraph.graph.message import add_messages` | Append + dedupe by `id`; overwrites existing messages when ids match | `list[AnyMessage]` / `list[BaseMessage]` — the default for chat |
| `operator.add` | `import operator` | Concatenate lists (or sum numerics) | Plain `list[str]` / `list[int]` / `list[dict]` scratchpads |
| `max` | built-in | Keep the larger value | Monotonic counters, timestamps |
| `min` | built-in | Keep the smaller value | Best-so-far tracking |

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
import operator

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]  # dedupe by id
    observations: Annotated[list[str], operator.add]     # concat
    best_score: Annotated[float, max]                    # monotonic
    earliest_hit: Annotated[float, min]                  # monotonic
    user_id: str                                         # scalar — no reducer needed
```

## `add_messages` — the non-obvious behavior

`add_messages` does not just concatenate. It matches incoming messages by `id`
and replaces existing entries, which is how LangGraph supports message edits
and tool-call retries:

```python
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages

existing = [HumanMessage("hi", id="1"), AIMessage("hello", id="2")]
new = [AIMessage("hello there", id="2")]  # same id as existing

merged = add_messages(existing, new)
# merged == [HumanMessage("hi", id="1"), AIMessage("hello there", id="2")]
```

This is why you must always include stable `id`s on messages you construct
manually. If you build messages without ids, every node return appends a new
entry and the history grows unboundedly.

## Writing a custom reducer

When built-ins don't cover your merge semantics — set union, dict merge,
time-ordered deque — write a two-arg function:

```python
from typing import Annotated, TypedDict

def dict_merge(left: dict, right: dict) -> dict:
    """Shallow dict merge; right wins on key collision."""
    return {**left, **right}

def set_union(left: list[str], right: list[str]) -> list[str]:
    """Treat lists as sets, deduplicate preserving insertion order."""
    seen = {}
    for item in list(left) + list(right):
        seen[item] = None
    return list(seen.keys())

class State(TypedDict):
    metadata: Annotated[dict, dict_merge]
    visited_nodes: Annotated[list[str], set_union]
```

Reducers are called every time the graph merges a node return or a
`Command(update=...)` payload into state. They must be pure functions — no
side effects, no global mutation. LangGraph may call them during replay.

## Validating reducers are wired

```python
graph = builder.compile(checkpointer=checkpointer)
print(graph.get_graph().draw_mermaid())
# Annotated fields render as `messages: list[AnyMessage] (add_messages)`.
# If a list field shows just `messages: list` with no reducer name, it's missing.
```

Also worth a runtime check at first invocation:

```python
import inspect
from langgraph.graph.state import StateGraph

# StateGraph inspects Annotated metadata at compile time. Pull out the
# channel spec and assert every list field has a reducer callable.
for name, channel in graph.channels.items():
    if hasattr(channel, "reducer"):
        assert channel.reducer is not None, f"Missing reducer on {name}"
```

## The one that breaks most teams

Resuming an interrupted graph with `Command(update={"messages": [new]})` when
`messages` has no reducer:

```python
# BAD — no reducer, update replaces messages entirely
class State(TypedDict):
    messages: list[AnyMessage]  # no Annotated, no reducer

# Resume wipes prior history:
graph.invoke(Command(update={"messages": [new_msg]}), config)
# state["messages"] is now [new_msg], losing everything before
```

```python
# GOOD — reducer makes update append
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Resume appends (or replaces-by-id):
graph.invoke(Command(update={"messages": [new_msg]}), config)
# state["messages"] is prior_history + [new_msg]
```

## References

- [LangGraph: State and reducers](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [LangGraph: `add_messages`](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.message.add_messages)
- [LangGraph: Custom reducers](https://langchain-ai.github.io/langgraph/how-tos/state-reducers/)
- Pain catalog: P18
