# Agent & LangGraph Execution Traps

Pain-catalog anchors: **P09, P10, P16, P17, P55, P56**.

Six errors that show up once you move beyond a single `llm.invoke(...)` into agent loops, multi-turn chat, and conditional graphs. The common thread: LangGraph silently does the wrong thing on missing config or mis-typed state, and you only discover it because answers look wrong, memory looks empty, or the loop never stops.

Last verified against `langgraph==1.0.0`, `langchain-core==1.0.0`.

---

## E10 — `GraphRecursionError: Recursion limit of 25 reached without hitting a stop condition.`

**Pain:** P10, P55

**Where you see it:** Vague agent prompt ("help me with my account"), or a graph with many parallel branches. Cost spike visible in your dashboard **before** the exception surfaces.

**Cause:** `create_react_agent` and `StateGraph.compile()` default to `recursion_limit=25`. This counts *total supersteps*, **not loop iterations** — a complex conditional with many parallel branches can hit 25 without looping. Vague prompts never converge to a tool-stop condition. There is no default cost cap.

**Diagnose first:**

```python
from langchain_core.callbacks import BaseCallbackHandler

class StepLogger(BaseCallbackHandler):
    def __init__(self):
        self.step = 0
    def on_chain_start(self, serialized, inputs, **kwargs):
        self.step += 1
        print(f"[step {self.step}] chain_start: {serialized.get('name')}")

agent.invoke(inp, config={"configurable": {"thread_id": "debug"},
                          "callbacks": [StepLogger()],
                          "recursion_limit": 30})
```

Count the actual step count. If it is linear (5–10 steps), you probably need to raise the limit. If it is a loop (the same two node names alternate), you have a convergence bug.

**Fix — cap and detect early:**

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model=llm, tools=tools)

# For interactive use: 5-10 is enough for good prompts; bigger is a bug.
config = {"configurable": {"thread_id": tid}, "recursion_limit": 10}
```

**Fix — add a terminal edge on repeated tool calls:**

```python
def _should_stop(state):
    recent = [m for m in state["messages"][-6:] if getattr(m, "tool_calls", None)]
    if len(recent) >= 3 and all(
        r.tool_calls[0]["name"] == recent[0].tool_calls[0]["name"] for r in recent
    ):
        return "end"  # same tool 3× in last 6 msgs → give up
    return "continue"
```

Wire this into a conditional edge with `add_conditional_edges(node, _should_stop, {"continue": "agent", "end": END})`. Pair with a token-budget middleware that raises on per-session cost exceeded.

---

## E11 — `AgentExecutor` returns `"I couldn't find the answer"` on every tool call (no exception)

**Pain:** P09

**Where you see it:** Legacy code still using `AgentExecutor`. Tool raised an exception but the user-facing response is a generic apology. Nothing in logs.

**Cause:** `AgentExecutor.invoke()` defaults `handle_parsing_errors=True` and catches **tool exceptions**, passing `str(exc)` as the next observation. If the exception serializes to an empty string (common for `HTTPError` with no body, or a `ValidationError` with no message), the loop continues without signal, runs out of iterations, and returns a generic failure.

**Fix — inspect intermediate steps:**

```python
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    return_intermediate_steps=True,  # CRITICAL
    handle_parsing_errors=False,     # re-raise so you see the real error
)
result = executor.invoke({"input": q})
for step in result.get("intermediate_steps", []):
    action, observation = step
    print(action, "→", observation)
```

**Fix — migrate to LangGraph `create_react_agent`:**

```python
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(model=llm, tools=tools)
# Raises tool exceptions by default. No silent swallowing.
```

LangGraph's `create_react_agent` uses provider-native tool calling (no free-text parsing) and does not catch tool exceptions silently. On a 0.3 → 1.0 migration this error usually vanishes by itself.

---

## E12 — Multi-turn chat forgets everything between calls, no exception

**Pain:** P16

**Where you see it:** Agent answers "what is my name?" correctly in turn 1, then forgets in turn 2. No traceback, no warning, no log.

**Cause:** LangGraph checkpointers key state by `config["configurable"]["thread_id"]`. If you omit it, **every invocation gets a fresh state**. No warning. This is the #1 silent LangGraph bug.

**Fix — require `thread_id` at your app boundary:**

```python
def invoke_agent(user_id: str, message: str):
    cfg = {"configurable": {"thread_id": f"user:{user_id}"}}
    return agent.invoke({"messages": [("user", message)]}, config=cfg)
```

**Fix — fail loud on missing `thread_id`:**

```python
from langchain_core.runnables import RunnableLambda

def _assert_thread_id(state, config=None):
    tid = (config or {}).get("configurable", {}).get("thread_id")
    if not tid:
        raise ValueError("thread_id is required on config['configurable']")
    return state

guarded = RunnableLambda(_assert_thread_id) | agent
```

Wire this as middleware (or the first node of your graph) so CI and staging catch the missing `thread_id` before production does.

**Verify memory is working:**

```python
# Turn 1
agent.invoke({"messages": [("user", "my name is Alex")]}, config=cfg)
# Turn 2 — must remember "Alex"
out = agent.invoke({"messages": [("user", "what is my name?")]}, config=cfg)
assert "Alex" in out["messages"][-1].content
```

---

## E13 — `TypeError: Object of type datetime is not JSON serializable` at `interrupt_before` / checkpoint save

**Pain:** P17

**Where you see it:** Graph runs fine until the first `interrupt_before=[node]` boundary or the first checkpoint save. Then crashes on state serialization.

**Cause:** `InMemorySaver` / `PostgresSaver` / `SqliteSaver` serialize state as JSON on every superstep. Non-primitives — `datetime`, `bytes`, `Decimal`, `set`, custom classes, Pydantic models with non-primitive fields — break serialization. The error surfaces only at the serialization boundary (interrupt or checkpoint write), not when the offending value was added to state.

**Fix — keep state JSON-primitive only:**

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    created_at_iso: str          # NOT datetime
    payload_b64: str             # NOT bytes
    amount_cents: int            # NOT Decimal
    tags: list[str]              # NOT set
```

Serialize at the boundary:

```python
from datetime import datetime, timezone

def node_add_timestamp(state: State) -> State:
    return {"created_at_iso": datetime.now(timezone.utc).isoformat()}
```

**Fix — for complex types, register a custom serde:**

```python
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
saver = PostgresSaver(conn, serde=JsonPlusSerializer())  # handles Pydantic v2, datetime, Decimal
```

`JsonPlusSerializer` covers most common types but still rejects arbitrary classes. When in doubt: convert to primitives at the node boundary.

**Test before prod:** Force a checkpoint save in CI with a representative state payload. `pickle` serialization "works locally" only because `InMemorySaver` in-process does not strictly enforce JSON-safety — but `PostgresSaver` does.

---

## E14 — Graph halts without reaching `END`; no exception, no log

**Pain:** P56

**Where you see it:** Graph invocation returns the input state unchanged, or a partial state. No error. `graph.get_state(cfg)` shows the graph as `done` but nodes you expected to run never executed.

**Cause:** `add_conditional_edges(node, router, path_map)` where `router` returns a string **not** in `path_map` causes the graph to end without signal on some 1.0 versions. Typo in a router return value, a new condition added without updating `path_map`, or a default-case fall-through all trigger this.

**Fix — always include a default route AND assert return value:**

```python
ROUTES = {"retrieve": "retrieve_node", "answer": "answer_node", "end": END}

def router(state) -> str:
    val = "end"
    if not state.get("has_context"):
        val = "retrieve"
    elif state.get("needs_answer"):
        val = "answer"
    assert val in ROUTES, f"router returned {val!r}, not in {list(ROUTES)}"
    return val

graph.add_conditional_edges("planner", router, ROUTES)
```

**Fix — use `END` explicitly as a fallback, never omit it:**

```python
from langgraph.graph import END
ROUTES = {"retrieve": "retrieve_node", END: END}  # always allow termination
```

**Debug:** Inspect the final state to confirm which nodes actually ran:

```python
state = graph.get_state(cfg)
print("next:", state.next)          # what would run next
print("checkpoint:", state.config)  # last checkpoint id
print("values:", state.values)      # last seen state
```

If `state.next` is empty but the state does not look complete, a router sent the graph to nowhere.

## Sources

- Pain catalog: `docs/pain-catalog.md` (P09, P10, P16, P17, P55, P56)
- [LangGraph concepts](https://langchain-ai.github.io/langgraph/concepts/)
- [LangGraph persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [`create_react_agent` reference](https://langchain-ai.github.io/langgraph/reference/prebuilt/)
- [LangGraph state & reducers](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [Recursion limit docs](https://langchain-ai.github.io/langgraph/concepts/low_level/#recursion-limit)
