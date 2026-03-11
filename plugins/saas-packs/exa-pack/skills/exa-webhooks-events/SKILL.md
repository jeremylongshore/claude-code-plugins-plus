---
name: exa-webhooks-events
description: |
  Implement Exa webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Exa event notifications securely.
  Trigger with phrases like "exa webhook", "exa events",
  "exa webhook signature", "handle exa events", "exa notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Exa Webhooks & Events

## Overview
Build event-driven integrations around Exa neural search. Exa is primarily a synchronous search API at `api.exa.ai`, so this skill covers async patterns for handling search results, building scheduled content monitoring, and creating webhook-style notification flows around Exa search queries.

## Prerequisites
- Exa API key stored in `EXA_API_KEY` environment variable
- Node.js or Python runtime for scheduled jobs
- Queue system (Redis/BullMQ) for async processing
- Familiarity with Exa search and `findSimilar` endpoints

## Event Patterns

| Pattern | Trigger | Use Case |
|---------|---------|----------|
| Content monitor | Scheduled search query | New content alerts |
| Search complete callback | Async search finishes | Pipeline processing |
| Similarity alert | New similar content found | Competitive monitoring |
| Content change detection | Periodic re-search | Update tracking |

## Instructions

### Step 1: Set Up Content Monitoring Service
```typescript
import Exa from "exa-js";
import { Queue, Worker } from "bullmq";

const exa = new Exa(process.env.EXA_API_KEY!);

interface SearchMonitor {
  id: string;
  query: string;
  webhookUrl: string;
  lastResultIds: string[];
  intervalMinutes: number;
}

const monitorQueue = new Queue("exa-monitors");

async function createMonitor(config: Omit<SearchMonitor, "lastResultIds">) {
  await monitorQueue.add("check-search", config, {
    repeat: { every: config.intervalMinutes * 60 * 1000 },
    jobId: config.id,
  });
}
```

### Step 2: Execute Monitored Searches
```typescript
const worker = new Worker("exa-monitors", async (job) => {
  const monitor = job.data as SearchMonitor;

  const results = await exa.searchAndContents(monitor.query, {
    type: "neural",
    numResults: 10,
    text: { maxCharacters: 500 },
    startPublishedDate: getLastCheckDate(monitor.id),
  });

  const newResults = results.results.filter(
    r => !monitor.lastResultIds.includes(r.id)
  );

  if (newResults.length > 0) {
    await sendWebhook(monitor.webhookUrl, {
      event: "exa.new_results",
      monitorId: monitor.id,
      query: monitor.query,
      results: newResults.map(r => ({
        title: r.title,
        url: r.url,
        snippet: r.text?.substring(0, 200),
        publishedDate: r.publishedDate,
        score: r.score,
      })),
    });
  }
});
```

### Step 3: Build Similarity Alert System
```typescript
async function monitorSimilarContent(seedUrl: string, webhookUrl: string) {
  const results = await exa.findSimilarAndContents(seedUrl, {
    numResults: 5,
    text: { maxCharacters: 300 },
    excludeDomains: ["example.com"],
    startPublishedDate: new Date(Date.now() - 86400000).toISOString(),
  });

  if (results.results.length > 0) {
    await sendWebhook(webhookUrl, {
      event: "exa.similar_content_found",
      seedUrl,
      matches: results.results,
    });
  }
}
```

### Step 4: Webhook Delivery with Retry
```typescript
async function sendWebhook(url: string, payload: any, retries = 3) {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (response.ok) return;
    } catch (error) {
      if (attempt === retries - 1) throw error;
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
    }
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited | Too many API calls | Reduce monitor frequency, batch queries |
| Empty results | Query too specific | Broaden search terms or date range |
| Stale content | No date filter | Use `startPublishedDate` for freshness |
| Duplicate alerts | Missing dedup | Track result IDs between runs |

## Examples

### Competitive Intelligence Monitor
```typescript
await createMonitor({
  id: "competitor-watch",
  query: "AI code review tools launch announcement",
  webhookUrl: "https://api.myapp.com/webhooks/exa-alerts",
  intervalMinutes: 60,
});
```

## Resources
- [Exa API Documentation](https://docs.exa.ai)
- [Exa JavaScript SDK](https://github.com/exa-labs/exa-js)

## Next Steps
For deployment setup, see `exa-deploy-integration`.
