# Resume Patterns

Five resume shapes cover every HITL flow in practice. This reference has the
exact code for each, plus the reducer discipline that keeps P18 from biting.

## Preamble: the `Command` type

```python
from langgraph.types import Command
```

`Command` has three fields that matter for HITL:

| Field | Purpose | When to use |
|-------|---------|-------------|
| `resume` | Value returned from inline `interrupt()` and recorded on checkpoint | Always on resume |
| `update` | State patch applied via reducers | When the human edits state |
| `goto` | Force routing to a specific node (or `END`) | When rejection bypasses nodes |

## Pattern 1 — Plain approve (no edits)

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": thread_id}}
graph.invoke(Command(resume="approved"), config)
```

- `resume="approved"` is just a marker. For `interrupt_before` / `interrupt_after`
  nodes, no node reads it — but the checkpoint records it for audit.
- For inline `interrupt()`, the value is returned from the `interrupt()` call.
  So `resume` here is the node's input for decision logic.

## Pattern 2 — Approve with edits

```python
graph.invoke(
    Command(
        update={"draft": edited_draft},   # merged via reducer
        resume="approved",
    ),
    config,
)
```

**P18 landmine:** without a reducer, `update` *replaces* the field. If `draft`
is a dict and you pass a partial, you lose the rest:

```python
# Before: state["draft"] = {"to": "a@b.com", "subject": "Hi", "body": "Hello"}
Command(update={"draft": {"subject": "Updated Hi"}})
# After (no reducer): state["draft"] = {"subject": "Updated Hi"}  # to and body GONE
```

**Fix — merge at the call site:**

```python
current = graph.get_state(config).values
merged_draft = {**current["draft"], "subject": "Updated Hi"}
graph.invoke(Command(update={"draft": merged_draft}, resume="approved"), config)
```

**Better — declare a dict reducer:**

```python
def merge_dict(left: dict, right: dict) -> dict:
    return {**left, **right}

class AgentState(TypedDict):
    draft: Annotated[dict, merge_dict]
```

Now partials merge automatically.

## Pattern 3 — Reject and route to `END`

### 3a. Conditional edge (preferred)

Graph topology carries the rejection logic:

```python
from langgraph.graph import END

def route_after_approval(state: AgentState) -> str:
    if state.get("last_decision") == "rejected":
        return END
    return "send_email"

builder.add_conditional_edges("await_approval", route_after_approval, {
    "send_email": "send_email",
    END: END,
})
```

Resume with the rejection recorded in state:

```python
graph.invoke(
    Command(
        update={"last_decision": "rejected", "reject_reason": reason},
        resume="rejected",
    ),
    config,
)
```

The next superstep runs `route_after_approval`, sees `rejected`, routes to END.

### 3b. `Command(goto=END)` at resume time

```python
from langgraph.graph import END
graph.invoke(Command(resume="rejected", goto=END), config)
```

Less preferred — routing logic leaks into the HTTP layer. But sometimes
necessary (e.g., you cannot modify the compiled graph).

## Pattern 4 — Partial approval (approve arg X, reject arg Y)

The human approves most of the tool call but wants to drop one argument:

```python
# Agent planned to send an email AND CC legal@. Human approves email, rejects CC.
current = graph.get_state(config).values
edited = {**current["draft"]}
edited["cc"] = []  # drop CCs
graph.invoke(
    Command(
        update={
            "draft": edited,
            "last_decision": "partial_approval",
            "decision_notes": "Approved without CC",
        },
        resume="approved",
    ),
    config,
)
```

For the UI, render an editable form of `state["draft"]` — each field becomes
an input the human can modify. POST back the full edited dict; merge
server-side.

## Pattern 5 — Inline `interrupt()` with structured return

```python
from langgraph.types import interrupt

def confirm_purchase(state: PurchaseState) -> PurchaseState:
    decision = interrupt({
        "kind": "confirm_purchase",
        "items": state["cart"],
        "total_usd": state["total"],
    })
    # decision is the value caller sent via Command(resume=<value>)
    if not decision["approved"]:
        return {**state, "status": "cancelled", "cancel_reason": decision.get("reason")}
    return {**state, "status": "confirmed", "approver": decision["approver"]}
```

Resume:

```python
graph.invoke(
    Command(resume={"approved": True, "approver": "jeremy@intentsolutions.io"}),
    config,
)
```

The dict is returned from `interrupt(...)` inside the node. Type it tightly —
use a `TypedDict` or a Pydantic model the UI validates against.

## Reducer cookbook

| Field shape | Typical reducer | Import |
|------------|-----------------|--------|
| `list[AnyMessage]` (conversation history) | `add_messages` | `from langgraph.graph.message import add_messages` |
| `list[dict]` (append-only events, approvals log) | `lambda l, r: l + r` | n/a |
| `dict` (draft with partial edits) | `lambda l, r: {**l, **r}` | n/a |
| `set[str]` serialized as list (tags) | `lambda l, r: sorted(set(l) | set(r))` | n/a |
| Counter / accumulator (`int`) | `lambda l, r: l + r` | n/a |
| Scalar (latest-wins, default) | None (omit reducer) | n/a |

Declare with `Annotated`:

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    approvals: Annotated[list[dict], lambda l, r: l + r]
    draft: Annotated[dict, lambda l, r: {**l, **r}]
    total_tokens: Annotated[int, lambda l, r: l + r]
    last_decision: str  # no reducer — latest-wins
```

## Audit log: write order matters

```
1. Validate optimistic-concurrency (expected_checkpoint_id)
2. Write audit log entry (before any mutation)
3. graph.invoke(Command(...))  # may succeed or fail
4. If invoke failed, mark audit entry with outcome="error"
   If invoke succeeded, mark outcome="applied"
```

Writing the audit entry BEFORE the mutation means you can reconstruct what
*should* have happened even if the mutation crashed. Writing after means you
lose the evidence on crash.

Schema:

```python
class ApprovalAuditEntry(BaseModel):
    id: UUID
    thread_id: str
    checkpoint_id: str          # the checkpoint the approver saw
    decision: Literal["approve", "reject", "edit"]
    edits: dict | None          # diff applied
    approver: str               # email or user ID
    reason: str | None
    requested_at: datetime
    applied_at: datetime | None # null until invoke returns
    outcome: Literal["pending", "applied", "error", "conflict"]
    error_message: str | None
```

Store this in your own DB (Postgres table, Firestore collection, whatever) —
NOT in LangGraph state. The audit log survives thread deletion, state
migrations, and LangGraph upgrades.

## Checkpoint ID vs thread ID (quick reference)

- `thread_id` — your app-level conversation or session identifier. Stable.
- `checkpoint_id` — monotonic ID within a thread. Every superstep creates
  one. Changes on every `invoke()` even if state is unchanged.

The HITL optimistic-concurrency check compares `checkpoint_id`, not
`thread_id`. Two approvers opening the same thread see the same
`thread_id` but the same `checkpoint_id` only if neither has acted yet.
First to POST wins; second gets 409.

## Gotcha: `Command(resume=...)` after graph already completed

```python
graph.invoke({"input": "hi"}, config)  # runs to END, no interrupts
graph.invoke(Command(resume="approved"), config)  # ???
```

Behavior depends on the LangGraph version. Safest: check
`snapshot.next` before resuming:

```python
snapshot = graph.get_state(config)
if not snapshot.next:
    raise HTTPException(410, "Thread already completed; nothing to resume")
```

Return `410 Gone` from the approval endpoint — the UI can refresh and drop
the stale pending entry.

## Gotcha: resume on a different checkpointer instance

If your app restarts between pause and resume, the in-process `MemorySaver`
loses state. The thread is gone. Always use `PostgresSaver` or `SqliteSaver`
for any non-ephemeral HITL flow.

```python
# WRONG in production — state lost on pod restart
saver = MemorySaver()

# RIGHT — state survives restarts
from langgraph.checkpoint.postgres import PostgresSaver
saver = PostgresSaver.from_conn_string("postgresql://...")
saver.setup()
```

Run `.setup()` after every `langgraph` package upgrade (P20).
