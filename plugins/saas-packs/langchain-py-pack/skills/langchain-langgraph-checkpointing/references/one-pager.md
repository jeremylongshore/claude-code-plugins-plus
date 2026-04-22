# langchain-langgraph-checkpointing — One-Pager

Persist LangGraph agent state correctly with `MemorySaver` and `PostgresSaver` — `thread_id` discipline, JSON-serializable state rules, time-travel, and schema migration that does not silently drop old checkpoints.

## The Problem

A chatbot forgets every turn because the caller never passed `thread_id` in `config["configurable"]` — LangGraph silently spawns a fresh state per invocation, no error, no log (P16). A `datetime` or Pydantic object lands in state and survives every node transition, then blows up with `TypeError: Object of type datetime is not JSON serializable` the moment `interrupt_before` triggers at a HITL boundary (P17). Upgrading `langgraph` in staging appears clean until a user returns and their entire history is gone — `PostgresSaver` did not auto-migrate the checkpoint schema, and the new reader treats old rows as empty state (P20). Meanwhile, every line of `ConversationBufferMemory` from the 0.x codebase now raises `ImportError` because legacy memory was removed in 1.0 (P40), and Deep Agent runs accumulate megabytes of virtual-FS scratch notes in state until checkpoint writes stall (P51).

## The Solution

Require `thread_id` at the application boundary via middleware that raises on missing, keep state primitives-only (TypedDict with `str` / `int` / `float` / `bool` / `list` / `dict`, datetimes as ISO strings, Pydantic via `model_dump()`), pick the checkpointer by environment (`MemorySaver` for dev/tests, `PostgresSaver.from_conn_string(...)` for staging and prod, `AsyncPostgresSaver` for high-concurrency), run `.setup()` on startup and after every `langgraph` upgrade, and use `graph.get_state_history(config)` + `graph.update_state(config, values, as_node=...)` to time-travel for incident debugging. Pinned to LangGraph 1.0.x with four deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend engineers adding persistent memory to chat agents; researchers building reproducible multi-turn experiments; ops teams debugging stateful agent incidents with time-travel |
| **What** | Checkpointer selection matrix, `thread_id` middleware, JSON state-shape rules table, Postgres setup + migration runbook, time-travel + replay recipes, 4 references (checkpointer-comparison, thread-id-discipline, json-serializability-rules, time-travel-and-replay) |
| **When** | When adding chat memory, migrating from `ConversationBufferMemory`, time-traveling an agent state to debug an incident, or sizing a Postgres checkpoint DB for production |

## Key Features

1. **Checkpointer comparison matrix** — `MemorySaver` / `SqliteSaver` / `PostgresSaver` / `AsyncPostgresSaver` side-by-side on persistence, concurrency, latency, and when-to-use; picks one per environment instead of picking the wrong one everywhere
2. **`thread_id` enforcement middleware** — Fail-closed wrapper that raises `ValueError` if `config["configurable"].get("thread_id")` is missing, plus UUID generation + tenant-scoping recipes so multi-tenant state never cross-leaks
3. **JSON-serializable state rules** — TypedDict-with-primitives rule, explicit serializers for `datetime` / `Decimal` / Pydantic / enums, and a safe reducer pattern so interrupts never raise `TypeError` at the HITL boundary

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
