---
name: perplexity-webhooks-events
description: |
  Build event-driven architectures around Perplexity Sonar API with streaming,
  batch pipelines, and scheduled search monitoring.
  Trigger with phrases like "perplexity streaming", "perplexity events",
  "perplexity batch search", "perplexity news monitor", "perplexity SSE".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, webhooks]

---
# Perplexity Events & Async Patterns

## Overview
Build event-driven architectures around Perplexity Sonar API. Perplexity does not have webhooks -- all interactions are request/response. Event patterns are built using streaming SSE, job queues for batch processing, and cron-triggered monitoring.

## Event Patterns

| Pattern | Trigger | Use Case |
|---------|---------|----------|
| Streaming SSE | Client request | Real-time search with progressive rendering |
| Batch queue | Job submission | Research automation, report generation |
| Scheduled search | Cron job | News monitoring, trend alerts, competitive intel |
| Citation pipeline | Post-processing | Source verification, link validation |

## Prerequisites
- `openai` package installed
- `PERPLEXITY_API_KEY` set
- Queue system (BullMQ, SQS) for batch patterns
- Cron scheduler for monitoring patterns

## Instructions

### Step 1: Streaming Search (Server-Sent Events)
```typescript
import OpenAI from "openai";
import express from "express";

const perplexity = new OpenAI({
  apiKey: process.env.PERPLEXITY_API_KEY!,
  baseURL: "https://api.perplexity.ai",
});

const app = express();
app.use(express.json());

app.post("/api/search/stream", async (req, res) => {
  const { query, model = "sonar" } = req.body;

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });

  try {
    const stream = await perplexity.chat.completions.create({
      model,
      messages: [{ role: "user", content: query }],
      stream: true,
      max_tokens: 2048,
    });

    let fullText = "";
    for await (const chunk of stream) {
      const text = chunk.choices[0]?.delta?.content || "";
      fullText += text;

      res.write(`data: ${JSON.stringify({ type: "text", content: text })}\n\n`);

      // Citations arrive in the final chunk
      const citations = (chunk as any).citations;
      if (citations) {
        res.write(`data: ${JSON.stringify({ type: "citations", urls: citations })}\n\n`);
      }
    }

    res.write(`data: ${JSON.stringify({ type: "done", totalLength: fullText.length })}\n\n`);
  } catch (err: any) {
    res.write(`data: ${JSON.stringify({ type: "error", message: err.message })}\n\n`);
  }

  res.end();
});
```

### Step 2: Batch Research Pipeline
```typescript
import { Queue, Worker } from "bullmq";

const searchQueue = new Queue("perplexity-research", {
  connection: { host: "localhost", port: 6379 },
});

async function submitResearchBatch(
  queries: string[],
  callbackUrl: string,
  model: string = "sonar-pro"
) {
  const batchId = crypto.randomUUID();

  for (const query of queries) {
    await searchQueue.add("search", { batchId, query, callbackUrl, model }, {
      attempts: 3,
      backoff: { type: "exponential", delay: 2000 },
    });
  }

  return { batchId, totalQueries: queries.length };
}

const worker = new Worker("perplexity-research", async (job) => {
  const { query, callbackUrl, batchId, model } = job.data;

  const response = await perplexity.chat.completions.create({
    model,
    messages: [{ role: "user", content: query }],
    max_tokens: 2048,
  });

  const result = {
    event: "perplexity.search.completed",
    batchId,
    query,
    answer: response.choices[0].message.content,
    citations: (response as any).citations || [],
    model: response.model,
    tokens: response.usage?.total_tokens,
  };

  // Deliver result via callback
  await fetch(callbackUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  });
}, {
  connection: { host: "localhost", port: 6379 },
  concurrency: 3,  // Stay within rate limits
  limiter: { max: 40, duration: 60000 },  // 40 RPM safety margin
});
```

### Step 3: Scheduled News Monitor
```typescript
// Run via cron: every 6 hours
async function monitorTopics(
  topics: string[],
  webhookUrl: string
) {
  for (const topic of topics) {
    const response = await perplexity.chat.completions.create({
      model: "sonar",
      messages: [{
        role: "system",
        content: "Summarize the latest developments. Be concise. Include only new information.",
      }, {
        role: "user",
        content: `Latest developments about "${topic}" in the past 24 hours`,
      }],
      search_recency_filter: "day",
      max_tokens: 500,
    } as any);

    const answer = response.choices[0].message.content || "";
    const citations = (response as any).citations || [];

    // Only notify if there are actual developments
    if (citations.length > 0 && answer.length > 100) {
      await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event: "perplexity.monitor.update",
          topic,
          summary: answer,
          citations,
          timestamp: new Date().toISOString(),
        }),
      });
    }

    // Rate limit protection
    await new Promise((r) => setTimeout(r, 2000));
  }
}
```

### Step 4: Client-Side SSE Consumer
```typescript
// Browser client consuming the streaming endpoint
function consumeSearchStream(
  query: string,
  onText: (text: string) => void,
  onCitations: (urls: string[]) => void,
  onDone: () => void
) {
  fetch("/api/search/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  }).then(async (response) => {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const event = JSON.parse(line.slice(6));

        if (event.type === "text") onText(event.content);
        if (event.type === "citations") onCitations(event.urls);
        if (event.type === "done") onDone();
      }
    }
  });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Stream stalls | Complex search taking too long | Set per-chunk timeout (10s) |
| 429 in batch | Too many concurrent workers | Reduce concurrency, add rate limiter |
| Empty monitor alerts | Topic too niche | Broaden topic or reduce recency filter |
| Callback fails | Webhook URL down | Retry with exponential backoff |

## Output
- Streaming SSE endpoint for real-time search
- Batch research pipeline with queue-based processing
- Scheduled news monitoring with alerting
- Client-side stream consumer

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [BullMQ Documentation](https://docs.bullmq.io)
- [Server-Sent Events MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

## Next Steps
For deployment setup, see `perplexity-deploy-integration`.
