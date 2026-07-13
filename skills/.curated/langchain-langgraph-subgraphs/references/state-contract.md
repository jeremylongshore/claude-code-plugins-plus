# Shared-State Contract Across Subgraph Boundaries

LangGraph subgraphs run on **independent state schemas**. The propagation rules
across the parent-child boundary are not documented as a matrix in the official
docs, so this file is the definitive reference for this pack.

Anchor: pain-catalog entry **P21** ("Subgraph state is isolated by default; keys
do not bubble up") plus **P18** ("`Command.update` replaces list fields without
a reducer").

## The state-propagation matrix

For any key `K`:

| Parent schema | Child schema | What happens to `K` at the boundary |
|---|---|---|
| declared | declared | **Propagates both directions.** Parent value is passed in; child updates flow out. If the type is a collection, the reducer on the **parent's** `TypedDict` controls merge on return |
| declared | not declared | Child **cannot read or write** `K`. Parent value is preserved unchanged across the subgraph call |
| not declared | declared | Child has a **local-only** `K`. Child can read and write it during the subgraph run, but **discarded on return** (this is the P21 trap) |
| not declared | not declared | Key does not exist anywhere. Reading returns `None` (or raises `KeyError` depending on `TypedDict` mode) |

## The subset rule

A safe pattern is to make the **child schema a superset** of the keys the
parent wants to share, plus any private scratch fields. Treat shared keys as an
explicit contract.

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

# The shared contract, declared once and referenced by both schemas
class _Shared(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    session_id: str
    tenant_id: str

class ParentState(_Shared):
    plan: list[str]
    current_step: int

class ExecutorState(_Shared):
    tool_result: dict | None
    retries: int
```

Both schemas inherit from `_Shared`, so the contract is single-sourced. Adding
a new shared key is a one-line change to `_Shared` and both `TypedDict`s pick
it up. This is the mechanism for avoiding P21 at its source.

## Reducers must match on both sides

A list key declared on both schemas but with different reducers silently does
the wrong thing on one side:

```python
# BAD — parent appends, child replaces. After a subgraph call, parent's
# message history is silently replaced with just the subgraph's additions.
class ParentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class ChildState(TypedDict):
    messages: list[AnyMessage]   # no reducer -> replace semantics (P18)
```

```python
# GOOD — identical reducer on both sides
class ParentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class ChildState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

## Explicit bubble-up with `Command(graph=Command.PARENT)`

If you need to pass a field *up* that the parent does not want in its own
schema (e.g. an error code for logging only), use `Command` instead of adding
to the shared contract:

```python
from langgraph.types import Command

def child_emits_signal(state: ExecutorState) -> Command:
    return Command(
        graph=Command.PARENT,
        update={"error_code": "RATE_LIMIT_HIT"},
        goto="retry_with_backoff",
    )
```

`Command(graph=Command.PARENT, update={...})` forces `error_code` onto the
parent's state regardless of whether the parent's `TypedDict` declares it.
LangGraph accepts dynamic keys on `update` even when not in the schema (as of
1.0.x) — though declaring them in the schema is still preferred for type safety.

## Versioned schema contracts for reusable subgraphs

A subgraph shipped as a library should export the `SHARED_KEYS` it expects from
any parent:

```python
# executor_subgraph/contract.py
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

SHARED_KEYS = frozenset({"messages", "session_id", "tenant_id"})
SCHEMA_VERSION = "1.2.0"

class ExecutorInputs(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    session_id: str
    tenant_id: str
```

In CI, add a test that fails if `SHARED_KEYS` changes without a major-version
bump — that is the mechanism that catches P21 at PR review instead of in
production. Parents import and assert:

```python
from executor_subgraph.contract import SHARED_KEYS, SCHEMA_VERSION
assert SHARED_KEYS.issubset(ParentState.__annotations__.keys())
```

## Common misreads of P21 to avoid

1. "I'll just use `state.update(...)` inside the child — that bypasses the
   schema." It does not. The final state that returns to the parent is still
   filtered against the parent's schema.
2. "I'll add the key to only the parent schema; the child can set it anyway."
   The child cannot write keys it does not declare — they are dropped from the
   child's returned state.
3. "Reducers are optional." For any list/dict field that is shared, the reducer
   is load-bearing — see P18 in the pain catalog.

## Related pain-catalog entries

- **P18** — `Command.update` replaces list fields without a reducer
- **P19** — `stream_mode` choice affects how subgraph updates are surfaced to the caller
- **P21** — Subgraph state is isolated by default (the entry this skill anchors)
