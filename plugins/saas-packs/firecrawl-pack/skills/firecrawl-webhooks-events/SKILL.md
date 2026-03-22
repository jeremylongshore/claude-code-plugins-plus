---
name: firecrawl-webhooks-events
description: |
  Implement Firecrawl webhook event handling for async crawl and batch scrape jobs.
  Use when setting up webhook endpoints, handling crawl.page/crawl.completed events,
  or processing async job results in real-time.
  Trigger with phrases like "firecrawl webhook", "firecrawl events",
  "firecrawl webhook signature", "handle firecrawl events", "firecrawl notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, webhooks]

---
# Firecrawl Webhooks & Events

## Overview
Handle Firecrawl webhooks for real-time notifications on async crawl and batch scrape jobs. Instead of polling `checkCrawlStatus`, configure a webhook URL and Firecrawl will POST events as pages are scraped and jobs complete. Signed with HMAC-SHA256 via `X-Firecrawl-Signature`.

## Webhook Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `crawl.started` | Crawl job begins | Job ID, config |
| `crawl.page` | Individual page scraped | Page markdown, metadata |
| `crawl.completed` | Full crawl finishes | All pages array |
| `crawl.failed` | Crawl job errors | Error message |
| `batch_scrape.completed` | Batch scrape finishes | All scraped pages |

## Instructions

### Step 1: Start Crawl with Webhook
```typescript
import FirecrawlApp from "@mendable/firecrawl-js";

const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY!,
});

// Webhook as string (simple)
const job = await firecrawl.asyncCrawlUrl("https://docs.example.com", {
  limit: 100,
  scrapeOptions: { formats: ["markdown"] },
  webhook: "https://api.yourapp.com/webhooks/firecrawl",
});

console.log(`Crawl started: ${job.id}`);

// Webhook as object (with metadata and event filtering)
const job2 = await firecrawl.asyncCrawlUrl("https://docs.example.com", {
  limit: 100,
  scrapeOptions: { formats: ["markdown"] },
  webhook: {
    url: "https://api.yourapp.com/webhooks/firecrawl",
    events: ["completed", "page"],  // only these events
    metadata: {
      projectId: "my-project",
      triggeredBy: "cron",
    },
  },
});
```

### Step 2: Webhook Handler with Signature Verification
```typescript
import express from "express";
import crypto from "crypto";

const app = express();
app.use(express.json());

function verifySignature(body: string, signature: string): boolean {
  if (!process.env.FIRECRAWL_WEBHOOK_SECRET) return true; // skip if not configured
  const expected = crypto
    .createHmac("sha256", process.env.FIRECRAWL_WEBHOOK_SECRET)
    .update(body)
    .digest("hex");
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

app.post("/webhooks/firecrawl", express.raw({ type: "application/json" }), async (req, res) => {
  const rawBody = req.body.toString();
  const signature = req.headers["x-firecrawl-signature"] as string;

  if (!verifySignature(rawBody, signature)) {
    return res.status(401).json({ error: "Invalid signature" });
  }

  const { type, id, data, metadata } = JSON.parse(rawBody);

  // Respond immediately — process asynchronously
  res.status(200).json({ received: true });

  switch (type) {
    case "crawl.started":
      console.log(`Crawl ${id} started`);
      break;
    case "crawl.page":
      await handlePageScraped(id, data, metadata);
      break;
    case "crawl.completed":
      await handleCrawlComplete(id, data, metadata);
      break;
    case "crawl.failed":
      await handleCrawlFailed(id, data);
      break;
  }
});
```

### Step 3: Process Page Events (Streaming)
```typescript
async function handlePageScraped(jobId: string, data: any[], metadata: any) {
  for (const page of data) {
    const doc = {
      url: page.metadata?.sourceURL,
      title: page.metadata?.title,
      markdown: page.markdown,
      statusCode: page.metadata?.statusCode,
      crawlJobId: jobId,
      projectId: metadata?.projectId,
      indexedAt: new Date(),
    };

    // Index page immediately — don't wait for full crawl
    await documentStore.upsert(doc);
    console.log(`Indexed: ${doc.url} (${doc.markdown?.length || 0} chars)`);
  }
}
```

### Step 4: Handle Crawl Completion
```typescript
async function handleCrawlComplete(jobId: string, data: any[], metadata: any) {
  console.log(`Crawl ${jobId} complete: ${data.length} pages`);

  // Build search index from all crawled pages
  const documents = data
    .filter(page => page.markdown && page.markdown.length > 100)
    .map(page => ({
      id: page.metadata?.sourceURL,
      title: page.metadata?.title || "",
      content: page.markdown,
      url: page.metadata?.sourceURL,
    }));

  await searchIndex.indexBatch(documents);
  console.log(`Indexed ${documents.length} documents for project ${metadata?.projectId}`);
}

async function handleCrawlFailed(jobId: string, data: any) {
  console.error(`Crawl ${jobId} failed:`, data.error);

  await alerting.send({
    severity: "high",
    message: `Firecrawl crawl job ${jobId} failed`,
    error: data.error,
    partialResults: data.partialResults?.length || 0,
  });
}
```

### Step 5: Polling as Webhook Fallback
```typescript
// Fall back to polling if webhook delivery fails
async function pollWithFallback(jobId: string, timeoutMs = 600000) {
  const deadline = Date.now() + timeoutMs;
  let interval = 2000;

  while (Date.now() < deadline) {
    const status = await firecrawl.checkCrawlStatus(jobId);

    if (status.status === "completed") {
      return status.data;
    }
    if (status.status === "failed") {
      throw new Error(`Crawl failed: ${status.error}`);
    }

    console.log(`Polling: ${status.completed}/${status.total} pages`);
    await new Promise(r => setTimeout(r, interval));
    interval = Math.min(interval * 1.5, 30000);
  }

  throw new Error(`Crawl timed out after ${timeoutMs}ms`);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not received | URL not publicly accessible | Use ngrok for local dev, verify HTTPS |
| Signature mismatch | Wrong secret or body encoding | Use raw body for HMAC, not parsed JSON |
| Duplicate events | Firecrawl retry on non-2xx | Make handler idempotent (dedup by job ID) |
| Webhook timeout | Processing takes too long | Return 200 immediately, process async |
| Lost events | 3 failed retries | Implement polling fallback |

## Examples

### Local Development with ngrok
```bash
set -euo pipefail
# Start ngrok tunnel for local webhook testing
ngrok http 3000
# Use the ngrok URL as your webhook endpoint
# https://abc123.ngrok.io/webhooks/firecrawl
```

## Resources
- [Firecrawl Webhooks](https://docs.firecrawl.dev/webhooks/overview)
- [Webhook Event Types](https://docs.firecrawl.dev/webhooks/events)
- [Crawl Endpoint](https://docs.firecrawl.dev/features/crawl)

## Next Steps
For deployment setup, see `firecrawl-deploy-integration`.
