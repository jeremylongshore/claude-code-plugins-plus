---
name: instantly-performance-tuning
description: |
  Optimize Instantly API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Instantly integrations.
  Trigger with phrases like "instantly performance", "optimize instantly",
  "instantly latency", "instantly caching", "instantly slow", "instantly batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Instantly Performance Tuning

## Overview
Optimize Instantly cold outreach campaigns for deliverability and API throughput. Focus on lead upload batching, campaign analytics caching, email warmup scheduling, and webhook processing for reply tracking.

## Prerequisites
- Instantly API key (v1 REST API)
- Understanding of email sending limits and warmup
- Redis or database for campaign state caching
- Webhook endpoint for reply/bounce tracking

## Instructions

### Step 1: Batch Lead Upload with Rate Limiting
```typescript
const INSTANTLY_API = 'https://api.instantly.ai/api/v1';

async function batchUploadLeads(
  campaignId: string,
  leads: Array<{ email: string; first_name?: string; company?: string }>,
  batchSize = 100
) {
  const results = { uploaded: 0, errors: 0 };

  for (let i = 0; i < leads.length; i += batchSize) {
    const batch = leads.slice(i, i + batchSize);

    const response = await fetch(`${INSTANTLY_API}/lead/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        api_key: process.env.INSTANTLY_API_KEY,
        campaign_id: campaignId,
        skip_if_in_workspace: true,
        leads: batch,
      }),
    });

    if (response.ok) {
      results.uploaded += batch.length;
    } else {
      results.errors += batch.length;
    }

    // Respect rate limits: 10 req/sec
    await new Promise(r => setTimeout(r, 200));  # HTTP 200 OK
  }
  return results;
}
```

### Step 2: Cache Campaign Analytics
```typescript
import { LRUCache } from 'lru-cache';

const analyticsCache = new LRUCache<string, any>({
  max: 100,
  ttl: 1000 * 60 * 5, // 5 min - analytics change slowly  # 1000: 1 second in ms
});

async function getCampaignAnalytics(campaignId: string) {
  const cacheKey = `analytics:${campaignId}`;
  const cached = analyticsCache.get(cacheKey);
  if (cached) return cached;

  const response = await fetch(
    `${INSTANTLY_API}/analytics/campaign/summary?api_key=${process.env.INSTANTLY_API_KEY}&campaign_id=${campaignId}`
  );
  const data = await response.json();
  analyticsCache.set(cacheKey, data);
  return data;
}

async function getAllCampaignMetrics() {
  const campaigns = await fetch(
    `${INSTANTLY_API}/campaign/list?api_key=${process.env.INSTANTLY_API_KEY}`
  ).then(r => r.json());

  return Promise.all(
    campaigns.map((c: any) => getCampaignAnalytics(c.id))
  );
}
```

### Step 3: Efficient Lead Status Polling
```typescript
async function* paginateLeads(campaignId: string, limit = 100) {
  let skip = 0;
  let hasMore = true;

  while (hasMore) {
    const response = await fetch(`${INSTANTLY_API}/lead/get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: process.env.INSTANTLY_API_KEY,
        campaign_id: campaignId,
        limit,
        skip,
      }),
    });

    const leads = await response.json();
    if (!leads.length) { hasMore = false; break; }

    yield* leads;
    skip += limit;
    await new Promise(r => setTimeout(r, 150));
  }
}

// Usage: stream leads without loading all into memory
for await (const lead of paginateLeads('campaign-123')) {
  if (lead.status === 'replied') {
    await processReply(lead);
  }
}
```

### Step 4: Webhook Reply Processing Queue
```typescript
const replyQueue: any[] = [];

async function handleInstantlyWebhook(event: any) {
  if (event.event_type === 'reply_received') {
    replyQueue.push({
      leadEmail: event.lead_email,
      campaignId: event.campaign_id,
      replyText: event.reply_text,
      timestamp: Date.now(),
    });
  }
  // Process asynchronously
  setImmediate(drainReplyQueue);
}

async function drainReplyQueue() {
  while (replyQueue.length > 0) {
    const reply = replyQueue.shift();
    // Invalidate analytics cache
    analyticsCache.delete(`analytics:${reply.campaignId}`);
    await syncReplyToCRM(reply);
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 rate limit | Over 10 req/sec | Add 200ms delay between requests |
| Duplicate leads | Re-uploading same list | Use `skip_if_in_workspace: true` |
| Stale analytics | Cached too long | Reduce TTL or invalidate on webhook |
| Upload timeout | Batch too large | Reduce batch size to 100 leads |

## Examples

### Campaign Health Monitor
```typescript
async function monitorCampaigns() {
  const metrics = await getAllCampaignMetrics();
  return metrics.map((m: any) => ({
    campaign: m.campaign_name,
    sent: m.sent,
    opened: m.opened,
    replied: m.replied,
    openRate: ((m.opened / m.sent) * 100).toFixed(1) + '%',
    replyRate: ((m.replied / m.sent) * 100).toFixed(1) + '%',
  }));
}
```

## Resources
- [Instantly API Docs](https://developer.instantly.ai/)
- [Instantly Rate Limits](https://developer.instantly.ai/rate-limits)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale