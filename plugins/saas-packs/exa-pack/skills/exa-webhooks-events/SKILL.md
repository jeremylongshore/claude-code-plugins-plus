---
name: exa-webhooks-events
description: |
  Build event-driven integrations with Exa using scheduled monitors and content alerts.
  Use when building content monitoring, competitive intelligence pipelines,
  or scheduled search automation with Exa.
  Trigger with phrases like "exa monitor", "exa content alerts",
  "exa scheduled search", "exa event-driven", "exa notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, webhooks, monitoring, automation]

---
# Exa Webhooks & Events

## Overview
Build event-driven integrations around Exa neural search. Exa is a synchronous search API (no native webhooks), so this skill covers building async patterns: scheduled content monitoring with `searchAndContents`, similarity alerts with `findSimilarAndContents`, new content detection using date filters, and webhook-style notification delivery.

## Prerequisites
- `exa-js` installed and `EXA_API_KEY` configured
- Queue system (BullMQ/Redis) or cron scheduler
- Webhook endpoint for notifications

## Event Patterns

| Pattern | Mechanism | Use Case |
|---------|-----------|----------|
| Content monitor | Scheduled `searchAndContents` with `startPublishedDate` | New article alerts |
| Similarity alert | Periodic `findSimilarAndContents` + diff | Competitive monitoring |
| Content change | Re-search + compare result sets | Update tracking |
| Research digest | Scheduled `answer` + email/Slack | Daily briefings |

## Instructions

### Step 1: Content Monitor Service
```typescript
import Exa from "exa-js";
import { Queue, Worker } from "bullmq";

const exa = new Exa(process.env.EXA_API_KEY!);

interface SearchMonitor {
  id: string;
  query: string;
  webhookUrl: string;
  lastResultUrls: Set<string>;
  intervalMinutes: number;
  searchType: "auto" | "neural" | "keyword";
}

const monitorQueue = new Queue("exa-monitors", {
  connection: { host: "localhost", port: 6379 },
});

async function createMonitor(config: Omit<SearchMonitor, "lastResultUrls">) {
  await monitorQueue.add("check-search", config, {
    repeat: { every: config.intervalMinutes * 60 * 1000 },
    jobId: config.id,
  });
  console.log(`Monitor created: ${config.id} (every ${config.intervalMinutes} min)`);
}
```

### Step 2: Execute Monitored Searches
```typescript
const worker = new Worker("exa-monitors", async (job) => {
  const monitor = job.data;

  // Search for new content published since last check
  const results = await exa.searchAndContents(monitor.query, {
    type: monitor.searchType || "auto",
    numResults: 10,
    text: { maxCharacters: 500 },
    highlights: { maxCharacters: 300, query: monitor.query },
    // Only find content published in the monitoring window
    startPublishedDate: getLastCheckDate(monitor.id),
  });

  // Filter to genuinely new results
  const newResults = results.results.filter(
    r => !monitor.lastResultUrls?.has(r.url)
  );

  if (newResults.length > 0) {
    await sendWebhook(monitor.webhookUrl, {
      event: "exa.new_results",
      monitorId: monitor.id,
      query: monitor.query,
      timestamp: new Date().toISOString(),
      results: newResults.map(r => ({
        title: r.title,
        url: r.url,
        snippet: r.text?.substring(0, 200),
        highlights: r.highlights,
        publishedDate: r.publishedDate,
        score: r.score,
      })),
    });

    // Update tracked URLs
    await updateLastResultUrls(monitor.id, newResults.map(r => r.url));
  }
}, { connection: { host: "localhost", port: 6379 } });
```

### Step 3: Similarity Alert System
```typescript
async function monitorSimilarContent(
  seedUrl: string,
  webhookUrl: string,
  checkIntervalHours = 24
) {
  const results = await exa.findSimilarAndContents(seedUrl, {
    numResults: 5,
    text: { maxCharacters: 300 },
    excludeSourceDomain: true,
    // Only find content from the last check period
    startPublishedDate: new Date(
      Date.now() - checkIntervalHours * 60 * 60 * 1000
    ).toISOString(),
  });

  if (results.results.length > 0) {
    await sendWebhook(webhookUrl, {
      event: "exa.similar_content_found",
      seedUrl,
      matchCount: results.results.length,
      matches: results.results.map(r => ({
        title: r.title,
        url: r.url,
        snippet: r.text?.substring(0, 200),
        score: r.score,
      })),
    });
  }

  return results.results.length;
}
```

### Step 4: Webhook Delivery with Retry
```typescript
async function sendWebhook(url: string, payload: any, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Exa-Event": payload.event,
        },
        body: JSON.stringify(payload),
      });
      if (response.ok) return;
      console.warn(`Webhook ${response.status}: ${url}`);
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
    }
    await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
  }
}
```

### Step 5: Daily Research Digest
```typescript
async function generateDailyDigest(
  topics: string[],
  webhookUrl: string
) {
  const digest = [];

  for (const topic of topics) {
    const results = await exa.searchAndContents(topic, {
      type: "neural",
      numResults: 3,
      summary: { query: `Latest developments in: ${topic}` },
      startPublishedDate: new Date(
        Date.now() - 24 * 60 * 60 * 1000
      ).toISOString(),
    });

    digest.push({
      topic,
      articles: results.results.map(r => ({
        title: r.title,
        url: r.url,
        summary: r.summary,
      })),
    });
  }

  await sendWebhook(webhookUrl, {
    event: "exa.daily_digest",
    date: new Date().toISOString().split("T")[0],
    topics: digest,
  });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limited monitors | Too many concurrent checks | Stagger monitor intervals |
| Empty results | Date filter too narrow | Widen to 48-hour windows |
| Duplicate alerts | Missing URL dedup | Track result URLs between runs |
| Webhook delivery fails | Endpoint down | Retry with exponential backoff |

## Examples

### Create a Competitive Intelligence Monitor
```typescript
await createMonitor({
  id: "competitor-watch",
  query: "AI code review tools launch announcement",
  webhookUrl: "https://api.myapp.com/webhooks/exa-alerts",
  intervalMinutes: 60,
  searchType: "neural",
});
```

## Resources
- [Exa Search Reference](https://docs.exa.ai/reference/search)
- [Exa Find Similar](https://docs.exa.ai/reference/find-similar-links)
- [BullMQ Documentation](https://docs.bullmq.io/)

## Next Steps
For deployment setup, see `exa-deploy-integration`.
