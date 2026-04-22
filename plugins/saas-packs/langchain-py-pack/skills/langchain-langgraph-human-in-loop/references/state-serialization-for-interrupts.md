# State Serialization for Interrupts

Pain catalog entry P17:

> `interrupt_before=[node]` raises `TypeError: Object of type <custom> is not
> JSON serializable` the moment a node tries to interrupt. The failure surfaces
> only at the interrupt boundary, not on node completion.

This reference is the complete, field-tested list of what breaks and how to
fix it.

## Why it fails at the interrupt, not at the node

LangGraph's checkpointers (`MemorySaver`, `PostgresSaver`, `SqliteSaver`,
`RedisSaver`) serialize the full state to JSON on every **superstep** — the
atomic unit between one node finishing and the next starting. Most graph
flows cross supersteps without touching the checkpointer's *persist-on-disk*
path aggressively — but the interrupt path **always** persists, because that
is how resume works.

So a `datetime` field in state makes every node pass its unit test, the graph
runs happily through five supersteps, and then the moment you hit
`interrupt_before=["send_email"]` the checkpointer serializes state,
`json.dumps` raises, and the error bubbles up from deep in LangGraph
internals.

## Forbidden types (complete list)

| Python type | Why it fails | Convert to |
|------------|--------------|------------|
| `datetime.datetime` | No JSON type | `dt.isoformat()` — ISO 8601 string |
| `datetime.date` | No JSON type | `d.isoformat()` |
| `datetime.timedelta` | No JSON type | `td.total_seconds()` (float) |
| `bytes` / `bytearray` | No JSON type | `base64.b64encode(b).decode()` |
| `set` / `frozenset` | Not in JSON spec | `sorted(s)` — lists are JSON |
| `tuple` | Silently becomes list, reducer may not expect it | Use `list` explicitly |
| `uuid.UUID` | No JSON type | `str(u)` |
| `decimal.Decimal` | No JSON type | `str(d)` (exact) or `float(d)` (lossy) |
| `pathlib.Path` | No JSON type | `str(p)` |
| `enum.Enum` member | No JSON type | `e.value` or `e.name` |
| Pydantic `BaseModel` (pre-v2 non-JSON fields) | `json.dumps` can't recurse | `.model_dump(mode="json")` in v2 |
| `dataclass` instances | No JSON serializer | `dataclasses.asdict(obj)` |
| `numpy.ndarray` | No JSON type | `arr.tolist()` |
| `numpy.float32` / `numpy.int64` | Not Python scalars | `float(x)` / `int(x)` |
| `pandas.DataFrame` | No JSON type | `df.to_dict(orient="records")` |
| Custom class instances | No default serializer | `to_dict()` method or `vars(obj)` |
| `Exception` instances | Not JSON | `{"type": type(e).__name__, "msg": str(e)}` |
| `io.BytesIO` / file handles | Not JSON, not meaningful across processes | Store a reference (URL, path) not the handle |

## Permitted types (the complete allowlist)

- `None`
- `bool`
- `int`
- `float` (but NOT `float("nan")`, `float("inf")`, `float("-inf")` — JSON forbids them)
- `str`
- `list` of permitted types (recursive)
- `dict` with `str` keys and permitted values (recursive)

That is it. If a type is not in this list, convert it at the node boundary.

## The `float("nan")` trap

`json.dumps(float("nan"))` returns `"NaN"` by default (Python-specific
extension). `PostgresSaver`'s writer uses `json.dumps(..., allow_nan=False)` on
some backends, which raises `ValueError: Out of range float values are not JSON
compliant`. Always sanitize:

```python
import math

def clean_float(x: float) -> float | None:
    return None if math.isnan(x) or math.isinf(x) else x
```

## Pre-interrupt scanner middleware

Drop this in `common/state_scanner.py` and import from every skill-under-test:

```python
import json
from typing import Any

class NonSerializableStateError(TypeError):
    """Raised when state cannot be checkpointed."""

def assert_json_serializable(state: dict[str, Any], *, path: str = "state") -> None:
    """Walk state depth-first and raise a typed error with the key path.

    Use as a sanity check at the end of any node that precedes an interrupt,
    or run as CI middleware after every node invocation in test mode.
    """
    _walk(state, path)

def _walk(v: Any, path: str) -> None:
    if v is None or isinstance(v, (bool, int, str)):
        return
    if isinstance(v, float):
        import math
        if math.isnan(v) or math.isinf(v):
            raise NonSerializableStateError(
                f"{path} is {v!r} — JSON forbids NaN/Inf. Replace with None or a sentinel."
            )
        return
    if isinstance(v, list):
        for i, item in enumerate(v):
            _walk(item, f"{path}[{i}]")
        return
    if isinstance(v, dict):
        for k, val in v.items():
            if not isinstance(k, str):
                raise NonSerializableStateError(
                    f"{path} has non-string key {k!r} ({type(k).__name__}). "
                    f"JSON objects require string keys."
                )
            _walk(val, f"{path}.{k}")
        return
    raise NonSerializableStateError(
        f"{path} is {type(v).__name__}, not JSON-serializable. "
        f"See state-serialization-for-interrupts.md for conversions."
    )
```

Wire as a LangGraph callback or call at node exits:

```python
def classify_node(state: AgentState) -> AgentState:
    state = {**state, "classified_at": datetime.utcnow().isoformat()}  # NOT datetime object
    assert_json_serializable(state)  # dev/CI only; omit in prod for perf
    return state
```

## Test harness that exercises the interrupt path

Unit tests that call `node(state)` directly do NOT exercise the checkpointer.
You must invoke the compiled graph and trigger a pause:

```python
import pytest
from langgraph.checkpoint.memory import MemorySaver

@pytest.fixture
def graph():
    builder = StateGraph(AgentState)
    # ... add nodes / edges ...
    return builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["send_email"],
    )

def test_graph_reaches_interrupt_without_serialization_error(graph):
    config = {"configurable": {"thread_id": "test-1"}}
    # This is the only way to catch P17. If state has a datetime buried
    # in it, this raises TypeError.
    graph.invoke({"messages": [("user", "send the email")]}, config)
    snapshot = graph.get_state(config)
    assert snapshot.next == ("send_email",), "Graph did not pause at send_email"

def test_resume_preserves_message_history(graph):
    config = {"configurable": {"thread_id": "test-2"}}
    graph.invoke({"messages": [("user", "hello")]}, config)
    # ... build up state with multiple messages ...
    pre_resume = graph.get_state(config).values["messages"]
    graph.invoke(Command(resume="approved"), config)
    post_resume = graph.get_state(config).values["messages"]
    assert len(post_resume) >= len(pre_resume), "History lost on resume (P18)"
```

Both tests are mandatory. The first catches P17 at CI time; the second
catches P18 at CI time.

## Pydantic in state: the right way

If your domain types are Pydantic models, do not store the model instance in
state. Store `.model_dump(mode="json")` — which recursively converts
`datetime`, `UUID`, `Decimal`, etc. to JSON-safe values:

```python
from pydantic import BaseModel

class EmailDraft(BaseModel):
    to: str
    subject: str
    body: str
    scheduled_for: datetime

class AgentState(TypedDict):
    draft: dict  # serialized EmailDraft, not EmailDraft itself

def draft_node(state: AgentState) -> AgentState:
    model = EmailDraft(to="...", subject="...", body="...", scheduled_for=datetime.utcnow())
    return {**state, "draft": model.model_dump(mode="json")}  # JSON-safe dict

def send_node(state: AgentState) -> AgentState:
    model = EmailDraft.model_validate(state["draft"])  # revive if needed
    # ... use model.scheduled_for as datetime ...
    return state
```

Revive in the node that needs the typed form, checkpoint the dict. Symmetric
at every boundary.

## What about `MessagesState` / `add_messages`?

`langchain_core.messages.AnyMessage` subclasses (`HumanMessage`, `AIMessage`,
`ToolMessage`, `SystemMessage`) are serializable by LangGraph's message
encoder out of the box. You do NOT need to dump them manually. `add_messages`
reducer handles append semantics.

Where people get bitten: custom subclasses of `BaseMessage` that add Python
fields. The default encoder drops unknown fields silently, which can lose
data across a resume. Keep message types stock; put custom fields in a
sibling state key as a plain dict.
