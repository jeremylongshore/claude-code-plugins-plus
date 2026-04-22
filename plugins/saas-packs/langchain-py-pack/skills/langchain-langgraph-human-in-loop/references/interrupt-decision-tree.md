# Interrupt Decision Tree

LangGraph 1.0 ships three interrupt mechanisms. Picking the wrong one gives
you a UX that either pauses too early (approving before you can see the draft),
too late (approving after the email already went out), or with the wrong
payload shape (UI has to guess what the human is reviewing).

## The three styles

| Style | Where configured | Pauses | State visible to human |
|-------|------------------|--------|-----------------------|
| `interrupt_before=[...]` | `graph.compile(...)` | Before node runs | State *entering* the node |
| `interrupt_after=[...]` | `graph.compile(...)` | After node completes | State *after* the node's mutation |
| Inline `interrupt(payload)` | Inside a node function | At that line | Whatever you passed as `payload` |

## `interrupt_before` — gate expensive/irreversible tools

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

builder = StateGraph(AgentState)
builder.add_node("draft_email", draft_node)
builder.add_node("send_email", send_node)
builder.add_edge("draft_email", "send_email")
builder.add_edge("send_email", END)

graph = builder.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["send_email"],
)
```

**Use when:** the node is irreversible. Sending an email, charging a card,
shipping a deploy, writing to a production DB, calling an external webhook.

**Human sees:** state *before* the node ran. For `send_email`, they see the
draft sitting in `state["draft"]`.

**Resume:** `graph.invoke(Command(resume="approved"), config)` executes the
node. `Command(resume="rejected")` — you need a conditional edge to skip it
(see safe-cancellation in SKILL.md Step 5); `resume` alone does not skip.

**Trap:** if you also list the node in `interrupt_after`, it pauses twice
(before and after). Rarely useful.

## `interrupt_after` — review a node's output

```python
graph = builder.compile(
    checkpointer=MemorySaver(),
    interrupt_after=["draft_email"],
)
```

**Use when:** you want a human to review what the node just produced. Common
for LLM drafts — the model wrote an email, the human edits it, then approves
forwarding to the send node.

**Human sees:** state *after* the node's mutation — the draft is now in state.

**Resume with edits:**
```python
graph.invoke(
    Command(update={"draft": {**state["draft"], "subject": edited}}, resume="approved"),
    config,
)
```

The next node (`send_email`) runs with the edited state.

**Trap:** the node has already done its work. If `draft_email` logged a
telemetry event or made a side-effectful API call, that already happened.
Only gate idempotent nodes here; irreversible ones go in `interrupt_before`.

## Inline `interrupt(payload)` — structured mid-node prompt

```python
from langgraph.types import interrupt

def validate_purchase(state: AgentState) -> AgentState:
    items = state["cart"]
    total = sum(i["price"] for i in items)

    # Collect structured input from the human
    decision = interrupt({
        "kind": "confirm_purchase",
        "items": items,
        "total": total,
        "currency": "USD",
    })
    # `decision` is whatever the caller sent via Command(resume=...)

    if not decision.get("approved"):
        return {**state, "status": "cancelled", "notes": decision.get("notes")}
    return {**state, "status": "confirmed", "approver": decision["approver"]}
```

**Use when:**
- The prompt payload varies by runtime state (a purchase needs price, a
  deploy needs a diff, an escalation needs a risk score).
- You want multiple interrupt points inside one node.
- You need the return value from the human to flow directly into node logic
  (the other two styles pause *outside* node code).

**Human sees:** the payload you passed to `interrupt(...)`. No free state
snooping — you decide what to show. Safer for multi-tenant because you
strip PII at the payload-construction site.

**Resume:** `graph.invoke(Command(resume={"approved": True, "notes": "..."}), config)`.
The value is returned from `interrupt()` inside the node.

**Trap:** inline `interrupt()` still serializes state at the pause boundary.
P17 applies here too — JSON-only state invariant holds regardless of which
interrupt style you pick.

## Decision criteria (choose one)

Answer these in order:

1. **Is the node irreversible?** → `interrupt_before`. Stop reading.
2. **Is the node producing content the human must review/edit?** → `interrupt_after`.
3. **Do you need a structured prompt with runtime-computed fields?** → inline `interrupt()`.
4. **All three could work?** → `interrupt_before` is cheapest to reason about.
   The human-visible state is the input, which matches the mental model of "am
   I OK with this tool being called with these args?"

## Multiple interrupts per graph

A single graph can list many nodes in `interrupt_before` and `interrupt_after`.
Each pause checkpoints independently. The `next` field on the snapshot tells
you which node is about to run.

```python
graph = builder.compile(
    checkpointer=saver,
    interrupt_before=["send_email", "charge_card", "deploy_release"],
    interrupt_after=["draft_email", "compose_announcement"],
)
```

A thread can hit multiple interrupts during one run. The UI lists them via
`graph.get_state(config)` — `snapshot.next` reveals the current pause point.

## What interrupts do NOT do

- **They do not create parallel approval branches.** If you need concurrent
  approvers (two reviewers must both approve), coordinate above the graph —
  collect both signatures, then send a single resume.
- **They do not enforce SLAs.** If the human never approves, the thread sits
  paused forever. Add a sweeper that routes to `END` with `rejected` after N
  hours if pending.
- **They do not authenticate the approver.** Your HTTP layer does that;
  LangGraph trusts whoever calls `invoke(Command(resume=...))`.

## Cross-check: interrupts vs tools that ask

An alternative to interrupts is a "human_approval" *tool* the agent calls.
The tool posts to a queue, waits, and returns the decision as a tool result.

| Property | Interrupt | Approval tool |
|----------|-----------|---------------|
| Graph pauses cleanly, resumable from checkpoint | Yes | No — tool call blocks or times out |
| Agent can reason about why approval is needed | Limited (state only) | Yes (free-form tool prompt) |
| Works across graph restarts (process crash) | Yes (checkpoint survives) | Only if tool is idempotent and awaitable |
| Cost of adoption | Medium (serialization discipline) | Low (just another tool) |

Interrupts are better for hard gates (the tool *must not* run without
approval). Approval tools are better for soft gates (the agent *asks* when
unsure, proceeds autonomously most of the time).
