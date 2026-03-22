---
name: brightdata-webhooks-events
description: |
  Implement Bright Data webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Bright Data event notifications securely.
  Trigger with phrases like "brightdata webhook", "brightdata events",
  "brightdata webhook signature", "handle brightdata events", "brightdata notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, data, brightdata]
compatible-with: claude-code
---

# Bright Data Webhooks & Events

## Overview

Handle Bright Data webhook deliveries from the Web Scraper API and Datasets API. When you trigger an async collection, Bright Data sends the results to your webhook URL with the collected data in JSON, NDJSON, or CSV format.

## Prerequisites

- Web Scraper API or Datasets API configured
- HTTPS endpoint accessible from internet
- API token for webhook Authorization header

## Instructions

### Step 1: Configure Webhook URL When Triggering Collection

```typescript
// trigger-with-webhook.ts
const API_TOKEN = process.env.BRIGHTDATA_API_TOKEN!;

async function triggerWithWebhook(datasetId: string, urls: string[]) {
  const params = new URLSearchParams({
    dataset_id: datasetId,
    format: 'json',
    endpoint: 'https://your-app.com/webhooks/brightdata', // Your webhook URL
    uncompressed_webhook: 'true', // Send uncompressed for easier handling
    auth_header: `Bearer ${process.env.BRIGHTDATA_WEBHOOK_SECRET}`, // Auth header sent with delivery
  });

  // Optional: notification URL (lightweight ping when done)
  params.set('notify', 'https://your-app.com/webhooks/brightdata-notify');

  const response = await fetch(
    `https://api.brightdata.com/datasets/v3/trigger?${params}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(urls.map(url => ({ url }))),
    }
  );

  const result = await response.json();
  console.log('Snapshot ID:', result.snapshot_id);
  return result;
}
```

### Step 2: Webhook Endpoint — Receive Data Delivery

```typescript
// api/webhooks/brightdata.ts
import express from 'express';

const app = express();

// Bright Data sends collected data as JSON array
app.post('/webhooks/brightdata',
  express.json({ limit: '50mb' }), // Collections can be large
  async (req, res) => {
    // Validate Authorization header
    const authHeader = req.headers.authorization;
    if (authHeader !== `Bearer ${process.env.BRIGHTDATA_WEBHOOK_SECRET}`) {
      console.error('Invalid webhook authorization');
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const records = req.body; // Array of scraped records
    console.log(`Received ${records.length} records`);

    // Process records
    for (const record of records) {
      console.log(`URL: ${record.url}`);
      console.log(`Title: ${record.title}`);
      console.log(`Data: ${JSON.stringify(record).substring(0, 200)}`);
    }

    // Store results
    await saveToDatabase(records);

    // Return 200 quickly — Bright Data retries on non-2xx
    res.status(200).json({ received: records.length });
  }
);
```

### Step 3: Notification Endpoint (Lightweight)

```typescript
// api/webhooks/brightdata-notify.ts
// Notification is a small JSON with snapshot status — not the full data
app.post('/webhooks/brightdata-notify',
  express.json(),
  async (req, res) => {
    const { snapshot_id, status } = req.body;
    console.log(`Collection ${snapshot_id}: ${status}`);

    if (status === 'ready') {
      // Option A: Data already delivered to endpoint above
      // Option B: Fetch data manually
      const data = await fetch(
        `https://api.brightdata.com/datasets/v3/snapshot/${snapshot_id}?format=json`,
        { headers: { 'Authorization': `Bearer ${process.env.BRIGHTDATA_API_TOKEN}` } }
      );
      const records = await data.json();
      console.log(`Fetched ${records.length} records from snapshot`);
    }

    res.status(200).json({ received: true });
  }
);
```

### Step 4: Idempotency and Deduplication

```typescript
// Bright Data may retry delivery — deduplicate by snapshot_id
const processedSnapshots = new Set<string>();

async function handleDelivery(snapshotId: string, records: any[]) {
  if (processedSnapshots.has(snapshotId)) {
    console.log(`Snapshot ${snapshotId} already processed, skipping`);
    return;
  }

  await saveToDatabase(records);
  processedSnapshots.add(snapshotId);

  // For production, use Redis instead of in-memory Set
  // await redis.set(`bd:snapshot:${snapshotId}`, '1', 'EX', 86400 * 7);
}
```

### Step 5: Test Webhooks Locally

```bash
# Expose local server with ngrok
ngrok http 3000

# Trigger a small collection with your ngrok URL
curl -X POST "https://api.brightdata.com/datasets/v3/trigger?dataset_id=YOUR_ID&format=json&endpoint=https://YOUR.ngrok.io/webhooks/brightdata&auth_header=Bearer%20test_secret" \
  -H "Authorization: Bearer ${BRIGHTDATA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '[{"url": "https://example.com"}]'
```

## Webhook Delivery Configuration

| Parameter | Values | Default |
|-----------|--------|---------|
| `format` | `json`, `ndjson`, `csv`, `jsonl` | `json` |
| `uncompressed_webhook` | `true`, `false` | `false` (gzip) |
| `endpoint` | Your webhook URL | None |
| `auth_header` | Authorization header value | None |
| `notify` | Notification-only URL | None |

## Output

- Webhook endpoint receiving collection results
- Authorization header validation
- Notification endpoint for status updates
- Deduplication by snapshot_id

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| No delivery received | Wrong endpoint URL | Check URL in trigger params |
| 413 Payload Too Large | Large collection | Increase body limit or use streaming |
| Duplicate deliveries | Retry on timeout | Implement snapshot_id deduplication |
| Auth header mismatch | Wrong secret | Check `auth_header` in trigger params |

## Resources

- [Web Scraper API Webhooks](https://docs.brightdata.com/scraping-automation/web-data-apis/web-scraper-api/trigger-a-collection)
- [Datasets API Delivery](https://docs.brightdata.com/scraping-automation/web-data-apis/web-scraper-api/overview)

## Next Steps

For performance optimization, see `brightdata-performance-tuning`.
