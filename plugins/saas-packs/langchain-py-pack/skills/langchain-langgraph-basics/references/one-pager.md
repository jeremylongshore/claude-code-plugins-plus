# langchain-langgraph-basics — One-Pager

Build a correct LangGraph 1.0 StateGraph without silent halts, list replacement, or mystery `GraphRecursionError`s.

## The Problem

A conditional edge whose router returns a string that isn't in `path_map` halts the graph without reaching `END` — no exception, no log line, just a silent stop (P56). A `Command(update={"messages": [msg]})` wipes your entire message history because the `messages` field wasn't annotated with an `add_messages` reducer (P18). `GraphRecursionError: Recursion limit of 25 reached` fires on a graph with no loop because the limit counts supersteps, not iterations (P55). And a `langgraph` minor version bump silently reads old `PostgresSaver` rows as empty state because checkpoint schemas don't auto-migrate (P20).

## The Solution

This skill walks through a LangGraph 1.0 `StateGraph` end to end: a `TypedDict` state with `Annotated[list, add_messages]` reducers on every list field, node functions that return partial-state dicts, edges plus conditional edges with a `path_map` that always includes `END`, compilation with a checkpointer, a `recursion_limit` sized to the graph's superstep count, and invocation with an explicit `thread_id` in `config["configurable"]`. Pinned to `langgraph 1.0.x` with four deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers and researchers building their first LangGraph 1.0 agent or multi-step workflow. Comfortable with LangChain, new to `StateGraph`. |
| **What** | Typed state with reducers, node/edge wiring, conditional-edge defensive patterns, recursion-limit sizing, checkpointer compile, thread-scoped invocation, 4 references (state-reducers, conditional-edges, recursion-limits, first-graph-walkthrough) |
| **When** | Writing your first `StateGraph`, diagnosing why a graph halted without reaching `END`, picking `recursion_limit`, or migrating from legacy `AgentExecutor` to `create_react_agent` from LangGraph |

## Key Features

1. **Reducer-safe TypedDict state** — Every list field uses `Annotated[list, add_messages]` (or `operator.add`, or a custom merger), so `Command(update=...)` appends instead of replaces (fixes P18)
2. **Defensive conditional edges** — Router functions are explicitly typed to return keys from a bounded `Literal` set, and `path_map` always maps an `END` fallback so unknown returns land there instead of halting silently (fixes P56)
3. **Recursion-limit sizing guide** — Superstep counts for common shapes (simple ReAct ~15, planner+executor ~30, deep-agent 50+) with a runbook for diagnosing `GraphRecursionError` (fixes P55)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
