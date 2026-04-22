# LangGraph Test Patterns Reference

LangGraph 1.0 tests need three things the chain tests don't:

1. A fresh `thread_id` per test (state is scoped to threads)
2. A fresh checkpointer per test (or explicit reset)
3. Per-node state assertions, not just final-output assertions

## Per-test `thread_id` + `MemorySaver`

```python
import uuid
import pytest
from langgraph.checkpoint.memory import MemorySaver

@pytest.fixture
def graph_config():
    """Fresh thread_id per test — prevents state leakage between tests."""
    return {"configurable": {"thread_id": str(uuid.uuid4())}}

@pytest.fixture
def checkpointer():
    """Per-test MemorySaver — prevents test N from seeing test N-1's checkpoints."""
    return MemorySaver()

@pytest.fixture
def compiled_graph(fake_chat, checkpointer):
    from my_app.graphs import build_graph
    return build_graph(fake_chat).compile(checkpointer=checkpointer)
```

Using a session-scoped `MemorySaver` or a shared `thread_id` guarantees flaky
tests — the third test sees state from the first two. Always per-test.

## State assertions per node

The naive graph test asserts on the final output dict only. That hides bugs in
intermediate nodes. Assert the shape at each node:

```python
def test_plan_then_execute(compiled_graph, graph_config, fake_chat):
    fake_chat.responses = [
        "step 1\nstep 2\nstep 3",  # plan node
        "done",                    # execute node
    ]
    result = compiled_graph.invoke({"goal": "deploy"}, graph_config)

    assert result["plan"] == ["step 1", "step 2", "step 3"]
    assert result["status"] == "done"

    # State history — every checkpoint the graph created:
    history = list(compiled_graph.get_state_history(graph_config))
    # Order: newest first
    assert history[0].values["status"] == "done"
    assert history[-1].values == {"goal": "deploy"}
    # Every node wrote a checkpoint:
    assert len(history) >= 3  # start + plan + execute
```

## Time-travel debugging on a failing test

When an intermediate node produces the wrong shape, `get_state_history` gives
you every checkpoint. Replay from any of them:

```python
def test_debug_failing_node(compiled_graph, graph_config, fake_chat):
    fake_chat.responses = ["bad plan output", "done"]
    compiled_graph.invoke({"goal": "deploy"}, graph_config)

    history = list(compiled_graph.get_state_history(graph_config))
    # Find the checkpoint right before the failing node ran:
    pre_failure = next(h for h in history if h.next == ("plan",))

    # Replay with a corrected input:
    fake_chat.responses = ["step 1\nstep 2\nstep 3", "done"]
    new_result = compiled_graph.invoke(None, pre_failure.config)
    assert new_result["plan"] == ["step 1", "step 2", "step 3"]
```

`pre_failure.config` carries the `checkpoint_id`; `invoke(None, config)`
resumes from that checkpoint. This is the fastest way to bisect a multi-node
graph without rerunning earlier nodes.

## Subgraph isolation tests (cross-ref `langchain-langgraph-subgraphs`, P21)

Parent graphs cannot see subgraph state unless the key is declared in the
parent's state schema (pain L30). Test this explicitly:

```python
from langgraph.graph import StateGraph
from typing import TypedDict

class ParentState(TypedDict):
    goal: str
    subgraph_result: str  # MUST be declared for the parent to see it

class ChildState(TypedDict):
    goal: str
    subgraph_result: str
    internal_scratch: str  # lives only in child, never visible to parent

def test_subgraph_state_contract(compiled_parent_graph, graph_config):
    """Assert the parent sees exactly the keys the schema declares — no more."""
    result = compiled_parent_graph.invoke({"goal": "x"}, graph_config)
    assert "subgraph_result" in result
    assert "internal_scratch" not in result  # opaque by design
```

If you forget to add `subgraph_result` to `ParentState`, the parent's
`get_state` returns without it silently — this test catches that regression.
See the pack's `langchain-langgraph-subgraphs` skill for the full
state-contract playbook (pain anchor L30 / P21).

## Testing streaming graphs

`graph.stream(...)` yields one event per node per step. Assert on the event
sequence:

```python
async def test_streaming_plan_then_execute(compiled_graph, graph_config, fake_chat):
    fake_chat.responses = ["step 1\nstep 2", "done"]
    events = []
    async for event in compiled_graph.astream(
        {"goal": "deploy"},
        graph_config,
        stream_mode="updates",
    ):
        events.append(event)

    # One update per node:
    assert any("plan" in e for e in events)
    assert any("execute" in e for e in events)
```

For `stream_mode="values"` you get the full state after each step; for
`"updates"` you get the delta only.

## Interrupts and human-in-the-loop (HITL)

Graphs with `interrupt_before=["human_review"]` pause before a node. Tests
need to step through manually:

```python
def test_interrupt_before_review(compiled_graph_with_interrupt, graph_config, fake_chat):
    fake_chat.responses = ["plan A"]
    # First invoke stops at the interrupt:
    compiled_graph_with_interrupt.invoke({"goal": "x"}, graph_config)

    state = compiled_graph_with_interrupt.get_state(graph_config)
    assert state.next == ("human_review",)

    # Simulate human approval by updating state, then resume:
    compiled_graph_with_interrupt.update_state(
        graph_config,
        {"approved": True},
        as_node="human_review",
    )
    final = compiled_graph_with_interrupt.invoke(None, graph_config)
    assert final["status"] == "approved"
```

## Performance expectations

| Graph shape | Fake model | Target |
|-------------|------------|--------|
| 3-node linear | `FakeChatWithUsage` | < 50ms |
| 5-node with one subgraph | `FakeChatWithUsage` | < 150ms |
| With VCR replay (integration) | real model, replayed | 500ms - 2s |
| With interrupt + resume | fake | < 100ms |

If a fake-model graph test exceeds 200ms, check for accidental sleeps,
real-network calls, or a non-fake embedder still hitting a local vector DB
cold-start.

## Gotchas

- `MemorySaver` is in-memory — does not persist across test processes.
  Fine for unit tests. For integration tests that must survive a restart,
  use `SqliteSaver` with a per-test file path in `tmp_path`.
- `update_state` with `as_node="X"` writes a checkpoint *as if* node X had
  run. Forgetting `as_node=` writes as an anonymous update and the graph
  resumes from the wrong step.
- Tests that use `graph.stream` must either `await` an async stream or call
  `list(graph.stream(...))` on sync — easy to mix up and get a coroutine
  back instead of events.
