---
name: groq-webhooks-events
description: |
  Implement Groq webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Groq event notifications securely.
  Trigger with phrases like "groq webhook", "groq events",
  "groq webhook signature", "handle groq events", "groq notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Groq Events & Async Patterns

## Overview
Build event-driven architectures around Groq's ultra-fast LLM inference API. Groq does not provide native webhooks, but its sub-second response times at `api.groq.com` enable unique patterns: real-time streaming, batch processing with callbacks, and event-driven pipelines where Groq acts as the processing engine within your webhook infrastructure.

## Prerequisites
- Groq API key stored in `GROQ_API_KEY` environment variable
- Groq SDK installed (`npm install groq-sdk` or `pip install groq`)
- Queue system for batch processing (BullMQ, Celery)
- Understanding of Groq model options (llama, mixtral, gemma)

## Event Patterns

| Pattern | Trigger | Use Case |
|---------|---------|----------|
| Streaming SSE | Client request | Real-time chat responses |
| Batch completion callback | Queue job finishes | Document processing pipeline |
| Webhook processor | Incoming webhook | Process events with Groq LLM |
| Health monitor | Scheduled check | API availability tracking |

## Instructions

### Step 1: Real-Time Streaming with SSE
```typescript
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY! });

// Express SSE endpoint
app.post("/api/chat/stream", async (req, res) => {
  const { messages, model } = req.body;

  res.writeHead(200, {  # HTTP 200 OK
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
  });

  const stream = await groq.chat.completions.create({
    model: model || "llama-3.3-70b-versatile",
    messages,
    stream: true,
    max_tokens: 2048,  # 2048: 2 KB
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content;
    if (content) {
      res.write(`data: ${JSON.stringify({ content })}\n\n`);
    }
  }

  res.write("data: [DONE]\n\n");
  res.end();
});
```

### Step 2: Batch Processing with Callbacks
```typescript
import { Queue, Worker } from "bullmq";

const groqQueue = new Queue("groq-batch");

// Queue a batch of prompts with callback webhook
async function queueBatch(prompts: string[], callbackUrl: string) {
  const batchId = crypto.randomUUID();

  for (const [index, prompt] of prompts.entries()) {
    await groqQueue.add("inference", {
      batchId,
      index,
      prompt,
      callbackUrl,
      totalItems: prompts.length,
    });
  }

  return batchId;
}

const worker = new Worker("groq-batch", async (job) => {
  const { prompt, callbackUrl, batchId, index, totalItems } = job.data;

  const completion = await groq.chat.completions.create({
    model: "llama-3.3-70b-versatile",
    messages: [{ role: "user", content: prompt }],
  });

  const result = {
    batchId,
    index,
    content: completion.choices[0].message.content,
    usage: completion.usage,
    model: completion.model,
    processingTime: completion.usage?.total_time,
  };

  // Fire callback webhook on completion
  await fetch(callbackUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event: "groq.batch_item.completed",
      data: result,
    }),
  });

  return result;
});
```

### Step 3: Webhook Event Processor
```typescript
// Use Groq to process incoming webhook events with LLM
async function processWebhookWithGroq(event: any) {
  const completion = await groq.chat.completions.create({
    model: "llama-3.1-8b-instant",
    messages: [
      {
        role: "system",
        content: "Classify this event and extract key information. Respond with JSON.",
      },
      {
        role: "user",
        content: JSON.stringify(event),
      },
    ],
    response_format: { type: "json_object" },
    temperature: 0,
  });

  return JSON.parse(completion.choices[0].message.content!);
}
```

### Step 4: Monitor API Health
```typescript
async function checkGroqHealth(): Promise<boolean> {
  try {
    const start = Date.now();
    await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "ping" }],
      max_tokens: 1,
    });
    const latency = Date.now() - start;
    console.log(`Groq health: OK (${latency}ms)`);
    return true;
  } catch (error) {
    console.error("Groq health check failed:", error);
    return false;
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited (429) | Too many requests | Implement exponential backoff, use queue |
| Model unavailable | Service capacity | Fall back to smaller model variant |
| Streaming disconnect | Network timeout | Implement reconnection with last token |
| JSON parse error | Malformed response | Use `response_format` and validate output |

## Examples

### Python Async Batch
```python
import asyncio
from groq import AsyncGroq

client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

async def process_batch(prompts: list[str]):
    tasks = [
        client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": p}],
        )
        for p in prompts
    ]
    return await asyncio.gather(*tasks)
```

## Resources
- [Groq API Documentation](https://console.groq.com/docs)
- [Groq Models](https://console.groq.com/docs/models)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)

## Next Steps
For deployment setup, see `groq-deploy-integration`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale