---
name: groq-webhooks-events
description: 'Build event-driven architectures with Groq streaming, batch processing,
  and async patterns.

  Use when setting up real-time SSE endpoints, batch processing pipelines,

  or event-driven LLM processing with Groq.

  Trigger with phrases like "groq streaming", "groq events",

  "groq SSE", "groq batch", "groq async", "groq event-driven".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- webhooks
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Events & Async Patterns

## Overview

Build event-driven architectures around Groq's inference API. Groq does not provide native webhooks, but its sub-second latency enables unique patterns: real-time SSE streaming, batch processing with callbacks, queue-based pipelines, and event processors that use Groq as an LLM classification/extraction engine.

This skill uses **Read**, **Write**, and **Edit** to scaffold and update these handlers in your codebase, and **curl** to exercise the resulting endpoints. Step 1 (the SSE endpoint) is inline below; the batch, webhook-processor, health-monitor, and Python async patterns live in [references/implementation.md](references/implementation.md).

## Prerequisites

- `groq-sdk` (Node) or `groq` (Python) installed, `GROQ_API_KEY` set
- Queue system for batch patterns (BullMQ, Redis, SQS)
- Understanding of Server-Sent Events (SSE) for streaming

## Authentication

Groq authenticates with a single API key. Export `GROQ_API_KEY` in the environment
and the SDK reads it automatically — never hard-code the key or embed it in a request
body. The key is a bearer credential; treat it like any secret (env var or secrets
manager, never committed). No per-request auth headers are needed when the SDK is
constructed with `new Groq()` / `AsyncGroq()`.

## Instructions

Write each handler as a file in your project (`Read`/`Write`/`Edit`), then drive it
with `curl` to confirm behavior.

### Step 1: SSE Streaming Endpoint

Stream tokens to the browser as they are generated. Set the `text/event-stream`
headers, disable proxy buffering with `X-Accel-Buffering: no`, and write one
`data:` frame per token, ending with a `done` event.

```typescript
import Groq from "groq-sdk";
import express from "express";

const groq = new Groq();
const app = express();
app.use(express.json());

app.post("/api/chat/stream", async (req, res) => {
  const { messages, model = "llama-3.3-70b-versatile" } = req.body;

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",  // Disable nginx buffering
  });

  try {
    const stream = await groq.chat.completions.create({
      model,
      messages,
      stream: true,
      max_tokens: 2048,
    });

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content;
      if (content) {
        res.write(`data: ${JSON.stringify({ content, type: "token" })}\n\n`);
      }
    }

    res.write(`data: ${JSON.stringify({ type: "done" })}\n\n`);
  } catch (err: any) {
    res.write(`data: ${JSON.stringify({ type: "error", message: err.message })}\n\n`);
  }

  res.end();
});
```

### Steps 2–5: Batch, Webhook Processor, Health Monitor, Python Async

The remaining patterns follow the same shape — Groq as a fast inference engine behind
a queue or an event loop. Each is documented in full, with runnable code, in
[references/implementation.md](references/implementation.md):

- **Step 2 — Batch processing with BullMQ**: enqueue prompts, process with a
  rate-limited worker (`concurrency: 5`, `limiter: 25 RPM`), fire a callback per item.
- **Step 3 — Webhook event processor**: ack the sender with `202` immediately, then
  classify/extract the event asynchronously with `llama-3.1-8b-instant`.
- **Step 4 — Scheduled health monitor**: ping each model with a one-token request on
  an interval, tracking latency and tokens/sec.
- **Step 5 — Python async batch**: `asyncio.Semaphore` + `gather` for concurrent
  processing without a queue.

## Output

Each pattern produces a distinct, observable artifact you can assert against:

- **SSE endpoint** — a `text/event-stream` response: one `data: {"content":…,"type":"token"}` frame per token, terminated by `data: {"type":"done"}` (or a `type:"error"` frame on failure).
- **Batch worker** — a `groq.batch.item_completed` callback POST per prompt, carrying `batchId`, `index`, `total`, `content`, `model`, and token `usage`.
- **Webhook processor** — an immediate `202 {"received": true}` ack, followed by a background classification object `{type, priority, summary, action}`.
- **Health monitor** — a per-model record `{status, latencyMs, tokensPerSec}` (or `{status:"error", error}`) logged each interval.

See [references/examples.md](references/examples.md) for the concrete payloads.

## Event Pattern Summary

| Pattern | Groq Model | Latency | Use Case |
|---------|-----------|---------|----------|
| SSE streaming | `llama-3.3-70b-versatile` | ~200ms TTFT | Real-time chat |
| Batch queue | `llama-3.1-8b-instant` | ~80ms TTFT | Document processing |
| Webhook processor | `llama-3.1-8b-instant` | ~80ms TTFT | Event classification |
| Health monitor | `llama-3.1-8b-instant` | ~80ms TTFT | Uptime tracking |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| SSE disconnect | Client timeout or network | Implement reconnection with last-event-id |
| Batch item fails | Rate limit or model error | Queue retry with exponential backoff |
| Webhook timeout | Processing takes too long | Acknowledge immediately (202), process async |
| Health check 429 | Monitoring consuming quota | Reduce check frequency, use smallest model |

## Examples

Worked, runnable examples — consuming the SSE endpoint with `curl`, submitting a
batch and receiving callbacks, and classifying an inbound webhook — are in
[references/examples.md](references/examples.md). A minimal first call:

```bash
curl -N -X POST http://localhost:3000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Explain SSE in one sentence."}]}'
```

## Resources

- [Full implementation walkthrough](references/implementation.md) — Steps 2–5 with runnable code
- [Worked examples](references/examples.md) — curl calls and expected payloads
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [Groq Text Generation (streaming)](https://console.groq.com/docs/text-chat)
- [BullMQ Documentation](https://docs.bullmq.io/)

For performance optimization, see the `groq-performance-tuning` skill.
