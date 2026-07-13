# langchain-langgraph-human-in-loop — One-Pager

Build LangGraph 1.0 human-in-the-loop approval flows that actually pause cleanly — JSON-serializable state, reducer-safe resume, and a UI wire format that survives concurrent approvals.

## The Problem

Teams add `interrupt_before=["send_email"]` expecting a clean pause, and the first test crashes with `TypeError: Object of type datetime is not JSON serializable` — because an earlier node stashed `datetime.utcnow()` into state and the error surfaces only at the interrupt boundary, not on node completion (P17). A week later the human clicks "approve" with an edited argument, the graph resumes via `Command(update={"messages": [decision]})`, and the prior message history vanishes because `messages` was never annotated with `add_messages` (P18). Both bugs look like LangGraph brokenness; both are state-schema violations that only the interrupt path exercises.

## The Solution

Treat graph state as a JSON document (str/int/float/bool/list/dict only — ISO-string any `datetime`, base64 any `bytes`, `.model_dump()` any Pydantic), always declare reducers for list fields, and define one approval-decision wire format: `{"decision": "approve"|"reject"|"edit", "edits": {...}, "approver": "...", "reason": "..."}`. Choose interrupt granularity with a three-row decision tree (`interrupt_before`: gate expensive tool; `interrupt_after`: review tool output; inline `interrupt()`: mid-node collect + resume). Resume with `Command(resume=decision)`; route to `END` on reject; validate state with a pre-interrupt middleware in CI.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers adding approval gates to LangGraph 1.0 agents (Slack/web HITL), platform teams wiring approval UIs to LangGraph workflows, researchers doing mid-trajectory RLHF-style corrections |
| **What** | Three-style interrupt decision tree, JSON-serializable state invariant with a pre-interrupt scanner, `Command(resume=...)` / `Command(update=..., resume=...)` contract, approval UI wire format (GET pending / POST decision / optimistic-concurrency), audit-log pattern, safe-cancellation routing, 3 deep references |
| **When** | After `langchain-langgraph-basics` and `langchain-langgraph-checkpointing` (you need a checkpointer first), before wiring any irreversible tool (DB mutation, email send, purchase, deploy) |

## Key Features

1. **JSON-only state invariant with a pre-interrupt scanner** — A tiny middleware that walks state with `json.dumps(state, default=None)` before any interrupt-flagged node and raises a typed `NonSerializableStateError` with the offending key path — fails the test, not production
2. **Three-style interrupt decision tree** — `interrupt_before=[node]` for expensive-tool gates, `interrupt_after=[node]` for reviewing a tool result, inline `interrupt({"kind": "..."})` for mid-node structured prompts — with concrete "use this when" criteria
3. **Approval UI wire format** — Exact JSON schema for GET `/approvals/pending` (lists paused threads with state diffs) and POST `/approvals/{thread_id}/decision` (idempotent, includes `expected_checkpoint_id` for optimistic concurrency) — wires cleanly to Slack Block Kit or a React form

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
