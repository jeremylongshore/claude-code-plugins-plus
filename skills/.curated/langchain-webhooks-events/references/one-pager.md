# langchain-webhooks-events — One-Pager

Dispatch LangChain 1.0 chain/agent events to external systems — webhooks, Kafka, Redis Streams, SNS — without blocking the chain or losing visibility into subagent tool calls.

## The Problem

Teams wire per-token webhook dispatch via FastAPI `BackgroundTasks` and wonder why their analytics pipeline is always N seconds late — `BackgroundTasks` run **after** the response closes (P60), not during the stream. Others attach a `BaseCallbackHandler` to the top-level agent and never see a single event from the subagent's tool calls — custom callbacks are **not** inherited by subgraphs; they must be passed via `config["callbacks"]` at invocation, not via `Runnable.with_config` at definition (P28). Meanwhile `astream_events(v2)` emits thousands of events per invocation (P47) — forwarding every one raw to Kafka saturates the topic, and the first sync `chain.invoke()` inside an async endpoint blocks the entire event loop (P48).

## The Solution

This skill teaches an async `BaseCallbackHandler` that fires-and-forgets dispatch via `asyncio.create_task()` inside `on_tool_end` / `on_llm_end`, never blocking the chain. Callbacks are passed via `config["callbacks"]` at invoke time so they propagate into subgraphs. An event taxonomy tells you which `on_*` events to forward (the interesting ones: `on_tool_end`, `on_chain_end` for named subgraphs) and which to drop (`on_chain_start` noise, P47). A target-matrix covers HTTP webhooks, Kafka, Redis Streams, and SNS — each with delivery guarantees, typical latency, and dead-letter patterns. Idempotency keys are built from `run_id + event_type + step_index`, HMAC-signed for webhooks, retried with 1s/5s/30s exponential backoff before the final DLQ write. Pinned to LangChain 1.0.x with four deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers wiring LangChain chains into real-time systems — per-tool webhooks, per-run telemetry to Kafka/Redis, fan-out to analytics and downstream workers |
| **What** | Async `BaseCallbackHandler` with fire-and-forget dispatch, subgraph-aware callback wiring, event-taxonomy filter, per-target dispatch matrix (HTTP/Kafka/Redis/SNS), idempotency key scheme, HMAC-signed webhooks with 1s/5s/30s retry + DLQ, 4 references |
| **When** | Firing webhooks mid-chain (per-tool, per-stage), pushing telemetry to Kafka/Redis Streams, dispatching events to multiple subscribers without blocking the stream, debugging subagent silence, replacing broken `BackgroundTasks` dispatch |

## Key Features

1. **Async fire-and-forget handler** — `BaseCallbackHandler` subclass uses `asyncio.create_task()` inside `on_tool_end` so dispatch never blocks the chain's forward progress; typical webhook latency budget kept under 500ms per event
2. **Subgraph-aware propagation** — Callbacks passed via `config["callbacks"]` at `invoke(...)` time (not `with_config`) so they fire from child subgraphs and tool-calling subagents (P28), plus a debug probe to prove propagation is working
3. **Per-target dispatch matrix** — HTTP webhook (at-least-once, HMAC-signed, 1s/5s/30s retry), Kafka (at-least-once, idempotent producer), Redis Streams (at-least-once with consumer groups), SNS (best-effort fan-out) — each with failure mode, DLQ pattern, and idempotency-key convention (`run_id + event_type + step_index`)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions. Cross-reference `langchain-langgraph-streaming` (in this pack) for browser-facing SSE — this skill is for server-to-server dispatch only.
