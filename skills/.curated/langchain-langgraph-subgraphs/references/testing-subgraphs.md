# Testing Subgraphs in Isolation

The defensive move that catches both P21 (state contract) and P28 (callback
scoping) at PR review instead of in production: **every subgraph ships with a
standalone unit test that does not require the parent graph**.

## Why isolation testing

Composed systems that fail only in composition are expensive to debug. A
subgraph that passes its own test suite but breaks when wired into a parent is
almost always hitting one of:

1. A key the parent expects on return is not declared in the child's schema (P21)
2. A list reducer on the parent differs from the child's (P18)
3. The parent passes callbacks via `.with_config(...)` instead of `config[...]`
   at invoke time, so child events go silent (P28)

Isolation tests pin the child's side of each contract. Composition tests then
verify the parent correctly holds up the other half.

## Fixture pattern

```python
import pytest
from langchain_core.messages import HumanMessage
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.checkpoint.memory import MemorySaver

@pytest.fixture
def fake_llm():
    """Deterministic LLM — returns canned responses in order."""
    return FakeListChatModel(
        responses=[
            '{"tool_result": {"done": true, "result": 42}}',
            '{"summary": "task complete"}',
        ]
    )

@pytest.fixture
def executor_graph(fake_llm):
    """Subgraph under test, compiled with an in-memory checkpointer."""
    from myapp.executor_subgraph import build_executor
    return build_executor(llm=fake_llm).compile(checkpointer=MemorySaver())

@pytest.fixture
def base_state():
    """Matches the SHARED_KEYS contract; any subgraph under test consumes this."""
    return {
        "messages": [HumanMessage("do the thing")],
        "session_id": "test-session",
        "tenant_id": "test-tenant",
    }
```

## Assert the shared-key contract on return

This is the direct defense against P21. Every shared key the parent expects to
read must be in the output state after the subgraph runs:

```python
from myapp.executor_subgraph.contract import SHARED_KEYS

def test_executor_returns_every_shared_key(executor_graph, base_state):
    out = executor_graph.invoke(
        base_state,
        config={"configurable": {"thread_id": "t"}, "recursion_limit": 5},
    )
    missing = SHARED_KEYS - set(out.keys())
    assert not missing, f"executor dropped shared keys: {missing} (P21)"
```

If the subgraph ever stops returning a shared key, this test fails at PR
review. The message points at P21 so the next engineer knows exactly where to
look.

## Assert state shape at intermediate nodes

LangGraph checkpointers let you inspect state after each node. This catches
mutations that a single final-state assertion would miss:

```python
def test_executor_writes_tool_result_before_summarize(executor_graph, base_state):
    config = {"configurable": {"thread_id": "step-by-step"},
              "recursion_limit": 5}

    # Invoke once; walk checkpoints.
    executor_graph.invoke(base_state, config=config)
    history = list(executor_graph.get_state_history(config))

    # history[-1] is earliest; history[0] is latest
    states_by_node = {snap.next[0] if snap.next else "END": snap.values
                      for snap in history}
    assert "run_tool" in states_by_node or "summarize" in states_by_node
    # tool_result must exist by the time summarize runs
    for snap in reversed(history):
        if snap.next and snap.next[0] == "summarize":
            assert snap.values.get("tool_result") is not None
            break
```

## Assert callbacks propagate (P28)

A capturing handler exercises the exact path P28 describes. If callbacks are
plumbed correctly at invocation time, every chain/tool/LLM event fires; if the
subgraph was built with `.with_config(callbacks=[...])` by mistake, the parent
events still fire but sub-events are missing.

```python
from langchain_core.callbacks import BaseCallbackHandler

class CaptureHandler(BaseCallbackHandler):
    def __init__(self):
        self.events: list[str] = []
    def on_chain_start(self, serialized, inputs, **kw):
        name = (serialized or {}).get("name", "?")
        self.events.append(f"chain_start:{name}")
    def on_chat_model_start(self, serialized, messages, **kw):
        self.events.append("llm_start")
    def on_tool_start(self, serialized, input_str, **kw):
        self.events.append(f"tool_start:{(serialized or {}).get('name', '?')}")

def test_executor_callbacks_see_all_nodes(executor_graph, base_state):
    handler = CaptureHandler()
    executor_graph.invoke(
        base_state,
        config={
            "configurable": {"thread_id": "cb-test"},
            "recursion_limit": 5,
            "callbacks": [handler],
        },
    )
    # At minimum, every node's on_chain_start should fire
    run_tool_seen = any("run_tool" in e for e in handler.events)
    summarize_seen = any("summarize" in e for e in handler.events)
    assert run_tool_seen and summarize_seen, (
        f"P28 regression — events: {handler.events}"
    )
```

## Assert the subgraph is robust against missing parent keys

Parents may add keys over time. A subgraph that crashes when a future parent
adds an unrelated key is fragile. Test with an intentionally bloated state:

```python
def test_executor_ignores_unknown_parent_keys(executor_graph, base_state):
    bloated = {
        **base_state,
        "parent_only_plan": ["a", "b"],
        "parent_only_current_step": 3,
    }
    out = executor_graph.invoke(
        bloated,
        config={"configurable": {"thread_id": "bloat"}, "recursion_limit": 5},
    )
    # Executor should run fine; parent-only keys are simply not used
    assert "messages" in out
```

## Assert reducer compatibility (P18 defense)

If the subgraph shares a list field, write a test that invokes twice on the
same `thread_id` and asserts the list grew:

```python
def test_executor_messages_append_not_replace(executor_graph, base_state):
    config = {"configurable": {"thread_id": "reducer-check"}, "recursion_limit": 5}
    first = executor_graph.invoke(base_state, config=config)
    assert len(first["messages"]) >= 1

    follow = {**first, "messages": first["messages"] + [HumanMessage("again")]}
    second = executor_graph.invoke(follow, config=config)
    assert len(second["messages"]) > len(first["messages"]), (
        "messages were replaced, not appended — missing add_messages reducer (P18)"
    )
```

## CI wiring

Add these tests under a `tests/subgraphs/` directory, one file per subgraph.
Run on every PR. A minimum bar before the skill's subgraph is allowed to be
composed into a parent:

```
tests/
  subgraphs/
    test_executor_contract.py      # SHARED_KEYS / reducer / callback / bloat
    test_specialist_contract.py    # same four suites
    test_planner_contract.py
```

## Related pain-catalog entries

- **P18** — Reducer compatibility (covered by the `messages` append test)
- **P21** — Shared-key contract (covered by the `SHARED_KEYS` assertion)
- **P28** — Callback scoping (covered by the `CaptureHandler` test)
- **P43** — `FakeListChatModel` missing `response_metadata` — guard token
  assertions behind `isinstance(llm, FakeListChatModel)` where needed
- **P55** — Recursion budget — set an explicit low `recursion_limit` in tests
  so a regression into an infinite loop fails fast
