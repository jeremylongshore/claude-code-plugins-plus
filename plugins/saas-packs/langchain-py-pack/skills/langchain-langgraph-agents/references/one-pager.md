# langchain-langgraph-agents — One-Pager

Build a correct LangGraph 1.0 ReAct agent with `create_react_agent` — typed tools, error propagation, recursion caps, and stop conditions that actually stop.

## The Problem

`create_react_agent` defaults to `recursion_limit=25`: a vague prompt like "help me with my account" loops to the cap and surfaces a `GraphRecursionError` only after burning $5+ in tool and completion tokens (P10). The legacy `AgentExecutor` it replaced swallowed tool exceptions as empty-string observations with `handle_parsing_errors=True`, so "I couldn't find the answer" was actually a silent `ValueError` the model never saw (P09). And `initialize_agent` no longer exists — code that worked on LangChain 0.2 raises `ImportError` on 1.0 (P41), with the tuple shape of `intermediate_steps` changed from `AgentAction.tool` to `ToolCall.tool_name` (P42).

## The Solution

This skill walks through `create_react_agent(model, tools, checkpointer=MemorySaver())` with typed `@tool` definitions (Pydantic schemas, docstring under the 1024-char cap — P11), explicit `recursion_limit` per expected agent depth (5-10 interactive, 20-30 planner), raise-by-default tool errors (no more silent crashes), and middleware that enforces a per-session token budget. Includes a decision matrix for `create_react_agent` vs custom `StateGraph` vs the legacy `AgentExecutor`, and a concrete before/after migration table. Pinned to `langgraph 1.0.x` + `langchain-core 1.0.x`.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers and researchers building production ReAct-style agents who have LangGraph basics (L25) and are now wiring tools |
| **What** | Typed `@tool` definitions, `create_react_agent` invocation, `recursion_limit` + cost-cap middleware, tool-call counter nodes, raise-by-default error propagation, 4 references (tool-definition-patterns, loop-caps-and-budgets, agent-executor-migration, error-propagation) |
| **When** | After `langchain-langgraph-basics` (L25), when writing your first tool-calling agent, migrating from `AgentExecutor` / `initialize_agent`, or diagnosing an agent that loops on vague prompts |

## Key Features

1. **Provider-native tool enforcement** — `create_react_agent` uses the provider's tool-calling API, so the allowlist is enforced at the wire level; the model cannot hallucinate a tool name that isn't in `tools=[...]` (P32)
2. **Raise-by-default tool errors** — Tool exceptions propagate as `GraphInterrupt` / real tracebacks instead of empty-string observations the agent silently ignores (P09); custom error-handler nodes re-enable tolerant behavior where you need it
3. **Bounded recursion and cost** — `recursion_limit=5-10` for interactive, 20-30 for planners; middleware caps per-session tokens and early-stops on repeated tool calls before the default 25-step ceiling fires `GraphRecursionError` (P10)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
