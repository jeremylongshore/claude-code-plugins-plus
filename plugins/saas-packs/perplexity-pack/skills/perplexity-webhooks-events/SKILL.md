---
name: perplexity-webhooks-events
description: |
  Implement Perplexity webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Perplexity event notifications securely.
  Trigger with phrases like "perplexity webhook", "perplexity events",
  "perplexity webhook signature", "handle perplexity events", "perplexity notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Events & Async Patterns

## Overview
Build event-driven architectures around Perplexity's AI search API. Perplexity provides a chat completions API at `api.perplexity.ai` with real-time web search capabilities. Since Perplexity does not offer native webhooks, this skill covers streaming patterns, async search pipelines, and callback-based workflows for integrating Perplexity's grounded search responses into your systems.

## Prerequisites
- Perplexity API key stored in `PERPLEXITY_API_KEY` environment variable
- Understanding of Perplexity models (sonar, sonar-pro, sonar-reasoning)
- Queue system for batch search processing
- Familiarity with OpenAI-compatible API format

## Event Patterns

| Pattern | Trigger | Use Case |
|---------|---------|----------|
| Streaming SSE | Client search request | Real-time search answers |
| Batch research callback | Queue job completes | Research automation pipeline |
| Scheduled search monitor | Cron trigger | News monitoring, trend alerts |
| Citation extraction | Post-processing | Source verification workflow |

## Instructions

### Step 1: Streaming Search Responses
```typescript
app.post("/api/search/stream", async (req, res) => {
  const { query, model } = req.body;

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
  });

  const response = await fetch("https://api.perplexity.ai/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.PERPLEXITY_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: model || "sonar",
      messages: [{ role: "user", content: query }],
      stream: true,
      return_citations: true,
    }),
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    res.write(chunk);
  }

  res.end();
});
```

### Step 2: Batch Research Pipeline
```typescript
import { Queue, Worker } from "bullmq";

const searchQueue = new Queue("perplexity-research");

async function queueResearch(queries: string[], callbackUrl: string) {
  const batchId = crypto.randomUUID();

  for (const query of queries) {
    await searchQueue.add("search", {
      batchId,
      query,
      callbackUrl,
    });
  }

  return batchId;
}

const worker = new Worker("perplexity-research", async (job) => {
  const { query, callbackUrl, batchId } = job.data;

  const response = await fetch("https://api.perplexity.ai/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.PERPLEXITY_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "sonar-pro",
      messages: [{ role: "user", content: query }],
      return_citations: true,
    }),
  });

  const result = await response.json();
  const answer = result.choices[0].message.content;
  const citations = result.citations || [];

  await fetch(callbackUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event: "perplexity.search.completed",
      batchId,
      query,
      answer,
      citations,
      model: result.model,
    }),
  });
});
```

### Step 3: News Monitoring Service
```typescript
async function monitorTopic(topic: string, webhookUrl: string) {
  const response = await fetch("https://api.perplexity.ai/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.PERPLEXITY_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "sonar",
      messages: [{
        role: "user",
        content: `What are the latest developments about ${topic} in the past 24 hours? Include specific sources.`,
      }],
      return_citations: true,
      search_recency_filter: "day",
    }),
  });

  const result = await response.json();

  if (result.choices[0].message.content.length > 100) {
    await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: "perplexity.monitor.update",
        topic,
        summary: result.choices[0].message.content,
        citations: result.citations,
      }),
    });
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited (429) | Too many requests | Add delays between requests, use queue |
| Empty citations | Query too abstract | Make queries more specific and factual |
| Stale results | No recency filter | Use `search_recency_filter` parameter |
| Model unavailable | Capacity limit | Fall back to smaller model variant |

## Examples

### Quick Search with Citations
```bash
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "sonar", "messages": [{"role": "user", "content": "Latest AI developments"}], "return_citations": true}'
```

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Models](https://docs.perplexity.ai/guides/model-cards)

## Next Steps
For deployment setup, see `perplexity-deploy-integration`.
