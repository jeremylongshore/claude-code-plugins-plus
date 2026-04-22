# langchain-langgraph-streaming — One-Pager

Pick the right LangGraph 1.0 `stream_mode`, wire SSE/WebSocket without proxy buffering gotchas, and filter `astream_events(v2)` before it floods the browser.

## The Problem

Ship `stream_mode="values"` to a token-level chat UI and every token re-renders the full conversation state — overdraw, tab freeze, users blame the model. Ship `"messages"` to a per-node progress bar and the bar never advances because you're receiving tokens, not node transitions. The same UI that worked on localhost then hangs forever on Cloud Run or behind Nginx because default proxy buffering holds the last chunk (P46). Forward raw `astream_events(version="v2")` straight to the browser and a 30-second agent emits thousands of lifecycle events — `on_chain_start`, `on_tool_end`, one per token, per node, per runnable — and the browser's message queue crashes the tab (P47). Three picks, three production failure modes, all silent.

## The Solution

This skill walks the three LangGraph 1.0 `stream_mode` options with a decision matrix (`"messages"` for token-level chat UI, `"updates"` for per-node progress bar, `"values"` for debugger/time-travel, combined list for hybrid dashboards); a production-grade FastAPI SSE endpoint with the required headers (`X-Accel-Buffering: no`, `Cache-Control: no-cache`, `Connection: keep-alive`) plus a heartbeat to keep idle connections open; a server-side `astream_events(version="v2")` filter that drops everything except `on_chat_model_stream` tokens and optionally `on_tool_start`/`on_tool_end` for progress; a WebSocket variant with reconnect-by-`thread_id` resume from checkpointer state; and a proxy-readiness checklist because localhost is not production. Pinned to LangGraph 1.0.x.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Frontend/backend engineers wiring live-token chat UIs, per-node progress bars, or debug/time-travel views on top of LangGraph 1.0 agents |
| **What** | Stream-mode decision matrix, FastAPI SSE endpoint template with anti-buffering headers and heartbeat, `astream_events(v2)` server-side filter, WebSocket reconnect-by-`thread_id`, proxy-readiness checklist, 4 references (stream-mode-comparison, sse-endpoint-template, astream-events-filtering, websocket-and-reconnect) |
| **When** | When you first wire a LangGraph agent to a browser — before it ships past localhost; also when diagnosing a stream that works locally but hangs over production proxies, or a UI that freezes on long invocations |

## Key Features

1. **Stream-mode decision matrix** — Three modes (`"messages"` / `"updates"` / `"values"`) mapped to UI type, payload shape, overdraw risk, and typical bandwidth; combined-mode syntax (`stream_mode=["updates", "messages"]`) for hybrid dashboards; one table picks the right mode in seconds
2. **Proxy-ready SSE endpoint** — FastAPI `StreamingResponse` with `X-Accel-Buffering: no`, `Cache-Control: no-cache`, `Connection: keep-alive`, proper `text/event-stream` content type, 15-second heartbeat pings for idle streams, and reverse-proxy snippets for Nginx / Traefik / Cloud Run that actually flush chunks
3. **`astream_events(v2)` server-side filter** — Forwards only `on_chat_model_stream` tokens (and optionally `on_tool_start` / `on_tool_end` for progress), drops thousands of runnable lifecycle events before they reach the browser; compression and backpressure patterns for long invocations

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
