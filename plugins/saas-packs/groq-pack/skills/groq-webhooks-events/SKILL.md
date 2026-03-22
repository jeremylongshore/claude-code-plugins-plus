---
name: groq-webhooks-events
description: |
  Build event-driven architectures with Groq streaming, batch processing, and async patterns.
  Use when setting up real-time SSE endpoints, batch processing pipelines,
  or event-driven LLM processing with Groq.
  Trigger with phrases like "groq streaming", "groq events",
  "groq SSE", "groq batch", "groq async", "groq event-driven".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, webhooks]

---
# Groq Events & Async Patterns

## Overview
Build event-driven architectures around Groq's inference API. Groq does not provide native webhooks, but its sub-second latency enables unique patterns: real-time SSE streaming, batch processing with callbacks, queue-based pipelines, and event processors that use Groq as an LLM classification/extraction engine.

## Prerequisites
- `groq-sdk` installed, `GROQ_API_KEY` set
- Queue system for batch patterns (BullMQ, Redis, SQS)
- Understanding of Server-Sent Events (SSE) for streaming

## Instructions

### Step 1: SSE Streaming Endpoint
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

### Step 2: Batch Processing with BullMQ
```typescript
import { Queue, Worker } from "bullmq";
import Groq from "groq-sdk";
import { randomUUID } from "crypto";

const groq = new Groq();
const groqQueue = new Queue("groq-batch", { connection: { host: "localhost" } });

// Enqueue a batch of prompts
async function submitBatch(
  prompts: string[],
  callbackUrl: string,
  model = "llama-3.1-8b-instant"
): Promise<string> {
  const batchId = randomUUID();

  for (const [index, prompt] of prompts.entries()) {
    await groqQueue.add("inference", {
      batchId,
      index,
      prompt,
      model,
      callbackUrl,
      total: prompts.length,
    });
  }

  return batchId;
}

// Worker processes queue items
const worker = new Worker("groq-batch", async (job) => {
  const { prompt, model, callbackUrl, batchId, index, total } = job.data;

  const completion = await groq.chat.completions.create({
    model,
    messages: [{ role: "user", content: prompt }],
    temperature: 0,
  });

  const result = {
    batchId,
    index,
    total,
    content: completion.choices[0].message.content,
    model: completion.model,
    usage: completion.usage,
  };

  // Fire callback on completion
  if (callbackUrl) {
    await fetch(callbackUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: "groq.batch.item_completed",
        data: result,
      }),
    });
  }

  return result;
}, {
  connection: { host: "localhost" },
  concurrency: 5,
  limiter: { max: 25, duration: 60_000 },  // 25 RPM to stay under limits
});
```

### Step 3: Webhook Event Processor
```typescript
// Use Groq as an LLM engine to process incoming webhook events
async function processWebhookEvent(event: any) {
  // Classify event type and extract key data using fast 8B model
  const classification = await groq.chat.completions.create({
    model: "llama-3.1-8b-instant",
    messages: [
      {
        role: "system",
        content: `Classify this webhook event and extract key fields.
Respond with JSON: {"type": string, "priority": "high"|"medium"|"low", "summary": string, "action": string}`,
      },
      { role: "user", content: JSON.stringify(event) },
    ],
    response_format: { type: "json_object" },
    temperature: 0,
    max_tokens: 200,
  });

  return JSON.parse(classification.choices[0].message.content!);
}

// Express webhook receiver
app.post("/webhook", async (req, res) => {
  const event = req.body;

  // Acknowledge immediately (don't block the sender)
  res.status(202).json({ received: true });

  // Process asynchronously with Groq
  const analysis = await processWebhookEvent(event);

  if (analysis.priority === "high") {
    await notifySlack(`High priority event: ${analysis.summary}`);
  }

  await logEvent({ raw: event, analysis });
});
```

### Step 4: Scheduled Health Monitor
```typescript
// Periodic Groq API health check with latency tracking
async function monitorGroqHealth() {
  const models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"];
  const results: Record<string, any> = {};

  for (const model of models) {
    const start = performance.now();
    try {
      const completion = await groq.chat.completions.create({
        model,
        messages: [{ role: "user", content: "OK" }],
        max_tokens: 1,
      });
      results[model] = {
        status: "ok",
        latencyMs: Math.round(performance.now() - start),
        tokensPerSec: completion.usage!.completion_tokens / ((completion.usage as any).completion_time || 1),
      };
    } catch (err: any) {
      results[model] = {
        status: "error",
        latencyMs: Math.round(performance.now() - start),
        error: `${err.status}: ${err.message}`,
      };
    }
  }

  return results;
}

// Run every 5 minutes
setInterval(() => monitorGroqHealth().then(console.log), 5 * 60_000);
```

### Step 5: Python Async Batch Processing
```python
import asyncio
from groq import AsyncGroq

client = AsyncGroq()

async def process_batch(prompts: list[str], model: str = "llama-3.1-8b-instant"):
    """Process prompts concurrently with rate limit awareness."""
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

    async def process_one(prompt: str):
        async with semaphore:
            return await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
            )

    results = await asyncio.gather(
        *[process_one(p) for p in prompts],
        return_exceptions=True,
    )

    return [
        r.choices[0].message.content if not isinstance(r, Exception) else str(r)
        for r in results
    ]
```

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

## Resources
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [Groq Text Generation (streaming)](https://console.groq.com/docs/text-chat)
- [BullMQ Documentation](https://docs.bullmq.io/)

## Next Steps
For performance optimization, see `groq-performance-tuning`.
