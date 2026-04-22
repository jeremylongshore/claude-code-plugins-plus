# langchain-debug-bundle — One-Pager

Produce a reproducible, sanitized diagnostic bundle for a LangChain / LangGraph incident — env manifest, filtered `astream_events(v2)` transcript, callback stack, LangSmith trace URL — so a debug colleague can reproduce the failure without a live terminal.

## The Problem

An on-call engineer pages you: the agent loops, tools return nothing, the user sees "I could not find the answer." Without a bundle, the next engineer has no reproducible snapshot — no graph state, no event stream, no version manifest, no trace URL. Custom callbacks attached at definition time never fire on subgraphs (P28). Raw `astream_events(v2)` dumps flood thousands of events per invocation (P47) and crash the viewer. Ad-hoc prints leak API keys into Slack.

## The Solution

This skill produces a tar.gz bundle with an env manifest (`manifest.yaml`: Python, OS, `pip show` versions, model IDs, env-var *names*), a filtered `astream_events(version="v2")` JSONL transcript (drop lifecycle noise, keep `on_chat_model_stream` / `on_tool_*` / `on_chain_*` errors), a callback stack captured via `config["callbacks"]` so it propagates into subgraphs (P28), the LangSmith trace URL pulled from the active `RunTree`, and a post-write sanitization pass that redacts API keys and PII. Typical bundle size 1-10 MB; filtered event count 50-200 per invocation.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | On-call engineers triaging a LangChain/LangGraph production incident, authors preparing a Discord bug report, or anyone archiving a post-mortem artifact |
| **What** | `bundle-<timestamp>.tar.gz` containing `manifest.yaml`, `events.jsonl`, `callbacks.txt`, `langsmith.url`, `MANIFEST.yaml` index; a triage decision tree; 4 references (env manifest, event capture, callback propagation, sanitization) |
| **When** | During or immediately after an incident, before closing the terminal session — the active process state and trace URL are load-bearing |

## Key Features

1. **Filtered `astream_events(v2)` JSONL transcript** — Server-side filter drops lifecycle noise (`on_chain_start`/`on_chain_end`) and keeps `on_chat_model_stream` + `on_tool_*` + any `*_error` event; typical invocation drops from 2000+ events to 50-200 (P47, P67)
2. **Propagating callback stack via `config["callbacks"]`** — `DebugCallbackHandler` passed at invoke time (not bound via `with_config`) so it fires inside subgraphs and `create_react_agent` inner loops (P28)
3. **Pre-upload sanitization pass** — Regex-based redaction of `sk-*`, `sk-ant-*`, `AIza*`, Bearer tokens, cookies, and configurable PII patterns before the tar.gz is written; plus env-var *names only* in the manifest (never values)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
