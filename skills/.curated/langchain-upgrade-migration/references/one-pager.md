# langchain-upgrade-migration — One-Pager

Ship a LangChain 1.0 / LangGraph 1.0 migration from a 0.2 or 0.3 codebase without breaking production, with a named breaking-change map, codemod patterns, and a phased rollout.

## The Problem

The first process restart after `pip install -U langchain` explodes with `ImportError: cannot import name 'ChatOpenAI' from 'langchain.chat_models'` — because `langchain.chat_models`, `langchain.chains.LLMChain`, `langchain.memory.ConversationBufferMemory`, and `langchain.agents.initialize_agent` were all removed in 1.0. The cascade keeps hitting: `LLMChain is not defined`, `ConversationBufferMemory has no attribute 'save_context'`, agents returning a new `ToolCall` shape that no longer matches the old `AgentAction.tool` / `.tool_input` accessors. Worst case, the agent looks like it works but silently drops tool results because `intermediate_steps` now yields `(ToolCall, observation)` tuples instead of `(AgentAction, observation)`.

## The Solution

A phased, reversible migration: (1) pre-flight audit with grep patterns against P38/P39/P40/P41/P42/P66/P67 anchors to inventory every 0.3 usage; (2) pin-together package upgrade (`langchain >= 1.0`, `langchain-core >= 0.3`, `langchain-anthropic >= 1.0` alongside `anthropic >= 0.40`); (3) codemod each removed API to its 1.0 replacement — `LLMChain` → LCEL, `initialize_agent` → `create_react_agent` from LangGraph, `ConversationBufferMemory` → LangGraph checkpointer, `astream_log` → `astream_events(version="v2")`; (4) integration test on shadow traffic before promoting to production.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python backend engineers on LangChain 0.2.x or 0.3.x who have `LLMChain`, `initialize_agent`, `ConversationBufferMemory`, or `langchain.chat_models` imports in their codebase and need to move to 1.0 without a multi-day outage. |
| **What** | A pre-flight grep audit, a breaking-changes matrix with 7+ named changes, codemod before/after snippets, a pinned `requirements.txt` fragment, and a phased rollout playbook (feature-flag, dual-write for chat histories, rollback plan). |
| **When** | Before bumping `langchain` past 1.0 in any production service; also when a scheduled dependency refresh surfaces an `ImportError` on `langchain.chat_models` / `langchain.chains` / `langchain.agents` / `langchain.memory` on the next deploy. |

## Key Features

1. **Pain-anchored change matrix** — Every breaking change is tagged to a pain code (P38 `ChatOpenAI` import, P39 `LLMChain` removal, P40 `ConversationBufferMemory` removal, P41 `initialize_agent` removal, P42 `intermediate_steps` shape drift, P66 `langchain-anthropic` 1.0 peer dep, P67 `astream_log` deprecation) with the exact 1.0 replacement.
2. **Codemod patterns, not theory** — Side-by-side 0.3 → 1.0 snippets for the five most common usages: LCEL replacement of `LLMChain`, `create_react_agent` replacement of `initialize_agent`, LangGraph checkpointer replacement of `ConversationBufferMemory`, `astream_events(version="v2")` replacement of `astream_log`, and `AgentAction` → `ToolCall` field rename.
3. **Phased rollout with a rollback plan** — Staging-first toggle, per-module migration order, dual-write for persistent chat histories during cutover, and an explicit pin-back `requirements.txt` to revert in under five minutes if shadow traffic regresses.

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
