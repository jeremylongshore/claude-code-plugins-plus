# langchain-langgraph-subgraphs — One-Pager

Compose LangGraph 1.0 subgraphs correctly — shared state-key propagation, `Send` / `Command(graph=...)` dispatch, callback scoping, and testing each subgraph in isolation.

## The Problem

Parent graph calls a compiled child subgraph; the child node sets `state["answer"] = "42"`; the parent's next node reads `state["answer"]` and gets `None`. No error, no warning. The reason is pain-catalog entry P21: LangGraph subgraphs run on an **independent state schema**, and only keys declared in *both* parent and child `TypedDict` schemas propagate. Add an observability callback at parent invocation via `Runnable.with_config(callbacks=[...])` and it never fires on tool calls inside the subgraph — that is P28: callbacks bind at definition time and LangGraph creates a fresh runtime per subgraph, so child tool events are invisible to parent handlers. Both failures look like "my code is silently broken" rather than throwing, and both waste hours before the developer realizes subgraphs are not just "nested nodes."

## The Solution

This skill walks the shared-state contract (which keys must exist in both schemas and which reducers must match), the three dispatch patterns (compiled subgraph as a node, `Send(graph, state)` for fan-out, `Command(graph=Parent, update=...)` to bubble results up), callback propagation via `config["callbacks"]` at invocation time (not at definition time), per-subgraph `recursion_limit` budgets (each subgraph gets its own independent budget), and a testing pattern that exercises subgraphs standalone with `FakeListChatModel` and a `MemorySaver`. Pinned to LangGraph 1.0.x with four deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Architects and senior engineers composing multi-stage LangGraph 1.0 workflows — planner + executor pairs, hierarchical agent teams, reusable subgraph libraries |
| **What** | Shared-state contract matrix, dispatch decision tree (node vs `Send` vs `Command`), callback-scoping pattern via `config["callbacks"]`, per-subgraph recursion budgets, isolation testing, 4 references (state-contract, dispatch-patterns, callback-scoping, testing-subgraphs) |
| **When** | After `langchain-langgraph-basics` (L25) — whenever a single `StateGraph` crosses ~8 nodes, owns two unrelated responsibilities, or needs to be shipped as a reusable library artifact |

## Key Features

1. **State-propagation matrix** — A four-row table naming what happens to key `K` declared in parent only / child only / both / neither, so the "silent `None`" failure (P21) becomes a lookup, not a debugging session
2. **Dispatch decision tree** — When to invoke a compiled subgraph as a plain node, when to fan out with `Send(graph, state)`, when to bubble results up with `Command(graph=ParentGraph, update=...)`, and when to promote the subgraph to a separate service
3. **Callback-scoping recipe** — Always pass observability callbacks via `config["callbacks"]` at invocation time so they propagate into every subgraph; never via `Runnable.with_config(callbacks=[...])` which binds at definition and leaves subgraphs invisible (P28)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
