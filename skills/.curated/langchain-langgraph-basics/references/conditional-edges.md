# Conditional Edges

`add_conditional_edges` is where most first-time LangGraph graphs silently
break. A router function that returns a value not in `path_map` halts the
graph without reaching `END` — no exception, no log, just a quiet stop
(pain-catalog P56).

## Signature

```python
StateGraph.add_conditional_edges(
    source: str,
    path: Callable[[State], str | list[str] | Literal[...]],
    path_map: dict[str, str] | list[str] | None = None,
)
```

Four usable shapes:

| Form | `path_map` | When to use |
|---|---|---|
| Router returns node names directly | `None` | Router returns "node_a" or "node_b" literally — fragile, easy to break on rename |
| Router returns keys, `path_map` translates | `{"key_a": "node_a", "key_b": "node_b"}` | **Recommended** — decouples router vocab from graph topology |
| Router returns a list of names (fan-out) | `None` or dict | Parallel branching via `Send` |
| Router returns a `Literal`-typed key | `{"key": "node", ...}` | Adds static type safety via mypy |

## The defensive pattern

```python
from typing import Literal
from langgraph.graph import StateGraph, START, END

def should_continue(state: State) -> Literal["execute", "end", "retry"]:
    if state["failed_attempts"] > 3:
        return "end"
    if state["needs_retry"]:
        return "retry"
    return "execute"

builder.add_conditional_edges(
    "validator",
    should_continue,
    path_map={
        "execute": "executor",
        "retry":   "executor",  # two keys can point to same node
        "end":     END,         # ALWAYS include END as a fallback key
    },
)
```

Three rules that prevent P56:

1. **Type the router with `Literal[...]`.** Mypy will flag a `return "Execute"`
   typo. Runtime errors surface at type-check time, not in production.
2. **Always include `END` in `path_map`.** Even if your router never intends to
   return "end," having it as a valid route means unknown returns route to END
   instead of halting silently. If you detect an unknown return, log loudly.
3. **Assert the router return is a `path_map` key** during dev:

   ```python
   def should_continue(state: State) -> Literal["execute", "end"]:
       result = "end" if state["done"] else "execute"
       assert result in {"execute", "end"}, f"Unknown route: {result!r}"
       return result
   ```

## Fan-out with `Send`

For parallel branching (one planner fan-outs to N executors), the router
returns a list of `Send` objects:

```python
from langgraph.types import Send

def dispatch(state: State) -> list[Send]:
    return [Send("executor", {"task": t}) for t in state["tasks"]]

builder.add_conditional_edges("planner", dispatch, ["executor"])
```

Each `Send` becomes one node invocation in the next superstep. This inflates
superstep count linearly with fan-out — see [Recursion Limits](recursion-limits.md)
for sizing.

## Testing conditional routes

Every branch of the router should have a unit test that asserts the return
value is in `path_map`:

```python
import pytest
from typing import get_args

PATH_MAP = {"execute": "executor", "retry": "executor", "end": END}

@pytest.mark.parametrize("state,expected", [
    ({"failed_attempts": 0, "needs_retry": False}, "execute"),
    ({"failed_attempts": 0, "needs_retry": True},  "retry"),
    ({"failed_attempts": 5, "needs_retry": False}, "end"),
])
def test_router_covers_all_paths(state, expected):
    result = should_continue(state)
    assert result == expected
    assert result in PATH_MAP, f"Router returned {result!r}, not in path_map"
```

One test per `Literal` arm. If you add a new return value to the router, the
test suite fails until you extend both `path_map` and the parametrize list.

## Common mistakes

### Returning a bare string instead of a key

```python
# BAD — "Retry" (capital R) is not in path_map
def router(state): return "Retry"  # P56 triggered
```

### `path_map=None` with renamed nodes

```python
def router(state): return "executor"  # matches a node name today

builder.add_conditional_edges("planner", router)  # no path_map

# Six months later a teammate renames "executor" to "worker".
# Router still returns "executor" — graph silently halts.
```

Always use `path_map` even when router returns match node names. The map is the
contract.

### Async router missing `await`

```python
async def router(state): return "end"

# BAD — passing the coroutine, not the value
builder.add_conditional_edges("node", router)  # works, but must not be called as await router()
```

`add_conditional_edges` accepts both sync and async routers. Don't add `await`
yourself — the compiled graph handles it.

## References

- [LangGraph: Conditional edges](https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges)
- [LangGraph: `add_conditional_edges` API](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph.add_conditional_edges)
- [LangGraph: `Send` API for fan-out](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Send)
- Pain catalog: P56
