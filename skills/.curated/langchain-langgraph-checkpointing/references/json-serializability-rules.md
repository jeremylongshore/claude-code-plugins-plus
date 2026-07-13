# JSON-Serializability Rules For LangGraph State

> P17 is a delayed-action bug: a non-JSON value enters state at node N, survives
> every transition, then raises `TypeError: Object of type <X> is not JSON
> serializable` the moment `interrupt_before`, a HITL pause, or a checkpoint
> write triggers — often many steps later, far from the line that introduced it.

## The One Rule

**State fields must be JSON-serializable primitives or recursive structures of them.** That is it. The entire rule.

The checkpointer serializes state with Python's `json.dumps` by default (with some pickle fallback for compatibility, but do not rely on pickle for production). If `json.dumps(state)` raises, the checkpointer raises.

## Allowed Types

| Type | Notes |
|---|---|
| `str` | No restrictions. UTF-8 safe. |
| `int` | Any size. |
| `float` | `NaN` / `Infinity` are valid Python floats but **invalid JSON** — will raise. Filter or coerce. |
| `bool` | `True` / `False`. |
| `None` | Becomes JSON `null`. |
| `list[T]` | Where `T` is itself allowed. |
| `dict[str, T]` | Keys MUST be strings. `dict[int, str]` becomes `dict[str, str]` after round-trip. |
| `tuple` | Serialized as list, returns as list. Type changes across round-trip. |

`LangChain` message objects (`HumanMessage`, `AIMessage`, etc.) are explicitly handled — they have `.model_dump()` built in, and LangGraph registers a custom serializer. Safe to put in state as-is, typically under a field with the `add_messages` reducer (P18).

## Forbidden Types (Direct)

| Type | Why | Workaround |
|---|---|---|
| `datetime.datetime` / `datetime.date` | No JSON representation. | ISO string: `dt.isoformat()`. Parse back with `datetime.fromisoformat(s)`. |
| `datetime.timedelta` | Same. | Store as seconds (`int` or `float`). |
| `decimal.Decimal` | `json.dumps` raises `TypeError`. | Store as string, convert on read. Never as `float` (precision loss). |
| `uuid.UUID` | Same. | `str(uuid_obj)`; parse with `UUID(s)` on read. |
| `pathlib.Path` | Same. | `str(path)`. |
| `set` / `frozenset` | No JSON equivalent. | Convert to sorted `list`. |
| `bytes` / `bytearray` | Binary data. | Base64 string: `base64.b64encode(b).decode()`. |
| `enum.Enum` | Depends on base type. | Store `.value` (typically `str` or `int`); reconstruct with `MyEnum(value)`. |
| Arbitrary custom class | Unless it subclasses `BaseModel` or has `__dict__` of primitives. | Define an explicit `to_state()` / `from_state()` pair. |
| Pydantic `BaseModel` instance | LangGraph does not auto-dump nested Pydantic models in every code path. | Use `.model_dump(mode="json")` before storing; reconstruct with `Model.model_validate(d)` on read. |
| `numpy.ndarray` | Binary. | `.tolist()` on write; `np.array(lst)` on read. For large arrays, store a reference (S3 URL, DB key) not the bytes. |
| Open file / socket / DB cursor | Stateful resources. | Never in state. Pass via `config["configurable"]` or recreate on demand. |

## Pattern: TypedDict With Only Primitives

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    # Built-in LangChain serializer handles messages.
    messages: Annotated[list[AnyMessage], add_messages]

    # Primitives only below.
    user_id: str                      # ok
    turn_count: int                   # ok
    last_action_at: str                # ISO string — NOT a datetime
    pending_approval: bool             # ok
    metadata: dict[str, str]           # string keys + string values
    scratch: list[str]                 # list of strings

    # Example compound field that stays safe:
    plan: list[dict[str, str]]         # [{"step": "...", "status": "pending"}]
```

Avoid this:

```python
class BrokenState(TypedDict):
    created_at: datetime              # P17 time bomb
    amount_owed: Decimal              # raises on serialize
    user_profile: UserProfile          # Pydantic — may or may not round-trip depending on path
    visited_urls: set[str]            # silently becomes list; equality tests fail
```

## Pattern: Serializer Helpers For Non-Primitive Inputs

Do not scatter `isoformat()` calls across 20 nodes. Centralize:

```python
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


def to_state(v: Any) -> Any:
    """Coerce common non-JSON types into JSON-safe primitives.

    Call at node output boundaries before returning state updates.
    """
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, set):
        return sorted(v)
    if isinstance(v, bytes):
        import base64
        return base64.b64encode(v).decode()
    if isinstance(v, dict):
        return {str(k): to_state(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [to_state(x) for x in v]
    return v


def from_state_datetime(s: str) -> datetime:
    return datetime.fromisoformat(s)


def from_state_decimal(s: str) -> Decimal:
    return Decimal(s)
```

Usage in a node:

```python
def record_purchase(state: AgentState) -> dict:
    now = datetime.utcnow()
    price = Decimal("19.99")
    return {
        "last_action_at": to_state(now),
        "metadata": {**state["metadata"], "price": to_state(price)},
    }
```

## Pattern: Pydantic Models

Pydantic v2 has explicit JSON support. Always use `mode="json"` when dumping to state:

```python
from pydantic import BaseModel


class Invoice(BaseModel):
    id: str
    amount: Decimal          # Pydantic handles Decimal → str with mode="json"
    issued_at: datetime      # → ISO string


def finalize_invoice(state: AgentState, inv: Invoice) -> dict:
    return {"last_invoice": inv.model_dump(mode="json")}

def read_invoice(state: AgentState) -> Invoice:
    return Invoice.model_validate(state["last_invoice"])
```

`mode="json"` is the critical argument. The default `model_dump()` returns Python objects (`Decimal`, `datetime`, `UUID`) — which then trip the serializer.

## Catching P17 Early With A Test

Add an integration test that exercises `interrupt_before` on every HITL path. This forces a JSON round-trip of the full state:

```python
def test_state_is_checkpointable_at_interrupt():
    graph = builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["human_approval"],
    )
    result = graph.invoke(initial_state, config={"configurable": {"thread_id": "t1"}})
    # If any non-JSON value made it into state, the interrupt raises here.
    snapshot = graph.get_state({"configurable": {"thread_id": "t1"}})
    assert snapshot.values is not None
```

Run it on every state-schema change. A caught P17 in CI is cheap; a caught P17 in a Friday-evening incident is not.

## When You Really Need Non-Primitive State

Two honest escape hatches:

1. **Reference, not value.** Store the S3 key, the DB row id, or the URL. Re-fetch in nodes that need the full object. Checkpoint stays small.
2. **Custom Serde.** `langgraph.checkpoint.serde.jsonplus` supports custom type registration, but this is advanced and ties your checkpoints to a specific serde version. Avoid unless you have measured and confirmed the reference pattern is wrong for your workload.

## Quick Sanity Check

Before compiling a new graph, run this in a REPL:

```python
import json
sample_state = {...}    # a realistic starting state
json.dumps(sample_state)  # if this raises, the checkpointer will too
```

Two seconds. Catches P17 on the spot.
