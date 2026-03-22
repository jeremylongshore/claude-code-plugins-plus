---
name: clay-load-scale
description: |
  Scale Clay enrichment pipelines for high-volume processing (10K-100K+ leads/month).
  Use when planning capacity for large enrichment runs, optimizing batch processing,
  or designing high-volume Clay architectures.
  Trigger with phrases like "clay scale", "clay high volume", "clay large batch",
  "clay capacity planning", "clay 100k leads", "clay bulk enrichment".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, testing, performance, scaling]

---
# Clay Load & Scale

## Overview

Strategies for processing 10K-100K+ leads through Clay monthly. Clay is a hosted platform -- you can't add servers. Scaling focuses on: table partitioning, webhook management, batch submission pacing, credit budgeting at scale, and multi-table architectures.

## Prerequisites

- Clay Growth or Enterprise plan
- Understanding of Clay's credit model (Data Credits + Actions)
- Queue infrastructure for batch processing (Redis, SQS, or BullMQ)
- Monitoring for credit consumption

## Instructions

### Step 1: Capacity Planning

```typescript
// src/clay/capacity-planner.ts
interface CapacityPlan {
  monthlyLeads: number;
  creditsPerLead: number;
  totalCreditsNeeded: number;
  planRequired: string;
  estimatedMonthlyCost: number;
  webhooksNeeded: number;        // Each webhook has 50K lifetime limit
  tablesRecommended: number;
}

function planCapacity(monthlyLeads: number, creditsPerLead = 6): CapacityPlan {
  const totalCredits = monthlyLeads * creditsPerLead;

  // Determine plan
  let plan: string, cost: number;
  if (totalCredits <= 2500) {
    plan = 'Launch ($185/mo)';
    cost = 185;
  } else if (totalCredits <= 6000) {
    plan = 'Growth ($495/mo)';
    cost = 495;
  } else {
    plan = `Enterprise (custom pricing for ${totalCredits} credits/mo)`;
    cost = 495 + Math.ceil((totalCredits - 6000) / 1000) * 50; // Rough estimate
  }

  // With own API keys: 0 data credits, only actions consumed
  console.log(`TIP: With own API keys, you need 0 Data Credits.`);
  console.log(`     Only ${monthlyLeads} Actions needed (Growth plan includes 40K).`);

  return {
    monthlyLeads,
    creditsPerLead,
    totalCreditsNeeded: totalCredits,
    planRequired: plan,
    estimatedMonthlyCost: cost,
    webhooksNeeded: Math.ceil(monthlyLeads / 50_000 * 12), // Annual webhooks needed
    tablesRecommended: Math.ceil(monthlyLeads / 10_000), // ~10K rows per table for manageability
  };
}

// Example
const plan = planCapacity(50_000);
console.log(plan);
// Monthly leads: 50,000
// Credits needed: 300,000 (or 0 with own API keys)
// Webhooks needed: 12/year
// Tables recommended: 5
```

### Step 2: Implement Batch Queue Architecture

```typescript
// src/clay/batch-processor.ts
import { Queue, Worker } from 'bullmq';
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!);

// Create a queue for Clay webhook submissions
const clayQueue = new Queue('clay-enrichment', { connection: redis });

interface EnrichmentJob {
  leads: Record<string, unknown>[];
  webhookUrl: string;
  batchId: string;
  priority: 'high' | 'normal' | 'low';
}

// Submit a batch for processing
async function queueBatch(
  leads: Record<string, unknown>[],
  webhookUrl: string,
  priority: 'high' | 'normal' | 'low' = 'normal',
): Promise<string> {
  const batchId = `batch-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

  // Split into chunks of 100 for manageable processing
  const chunks = [];
  for (let i = 0; i < leads.length; i += 100) {
    chunks.push(leads.slice(i, i + 100));
  }

  for (let i = 0; i < chunks.length; i++) {
    await clayQueue.add(`${batchId}-chunk-${i}`, {
      leads: chunks[i],
      webhookUrl,
      batchId,
      priority,
    }, {
      priority: priority === 'high' ? 1 : priority === 'normal' ? 5 : 10,
      attempts: 3,
      backoff: { type: 'exponential', delay: 5000 },
    });
  }

  console.log(`Queued ${leads.length} leads in ${chunks.length} chunks (batch: ${batchId})`);
  return batchId;
}

// Worker processes queued batches
const worker = new Worker<EnrichmentJob>('clay-enrichment', async (job) => {
  const { leads, webhookUrl } = job.data;
  let sent = 0, failed = 0;

  for (const lead of leads) {
    try {
      const res = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lead),
      });

      if (res.status === 429) {
        const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
        console.log(`Rate limited. Waiting ${retryAfter}s...`);
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        // Retry this lead
        const retry = await fetch(webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(lead),
        });
        if (retry.ok) sent++; else failed++;
      } else if (res.ok) {
        sent++;
      } else {
        failed++;
      }
    } catch {
      failed++;
    }

    // Pace submissions: 200ms between rows
    await new Promise(r => setTimeout(r, 200));
  }

  return { sent, failed, total: leads.length };
}, { connection: redis, concurrency: 1 });
```

### Step 3: Multi-Table Strategy

For large volumes, split data across multiple Clay tables:

```yaml
# Large-volume table strategy
tables:
  outbound-leads-tech:
    focus: "Technology companies"
    filter: "industry IN ('Software', 'SaaS', 'Technology')"
    enrichment: Full waterfall + Claygent
    volume: ~5K rows/month

  outbound-leads-finance:
    focus: "Financial services companies"
    filter: "industry IN ('Financial Services', 'Banking', 'Insurance')"
    enrichment: Full waterfall (no Claygent — regulated data)
    volume: ~3K rows/month

  inbound-leads:
    focus: "Website form submissions"
    source: Webhook from web forms
    enrichment: Company lookup + email verification only
    volume: ~2K rows/month
    auto_delete: true  # Stream-through: enrich, push to CRM, delete

  event-attendees:
    focus: "Conference/webinar registrants"
    source: CSV import
    enrichment: Full waterfall + AI personalization
    volume: ~1K rows/month (batch after events)
```

### Step 4: Webhook Rotation for High Volume

```typescript
// src/clay/webhook-rotation.ts
class WebhookRotator {
  private webhooks: { url: string; count: number; maxCount: number }[];
  private currentIndex = 0;

  constructor(webhookUrls: string[], maxPerWebhook = 45_000) {
    this.webhooks = webhookUrls.map(url => ({
      url,
      count: 0,
      maxCount: maxPerWebhook, // Leave 5K buffer under 50K limit
    }));
  }

  getNextWebhook(): string {
    // Find a webhook with remaining capacity
    for (let i = 0; i < this.webhooks.length; i++) {
      const idx = (this.currentIndex + i) % this.webhooks.length;
      if (this.webhooks[idx].count < this.webhooks[idx].maxCount) {
        this.currentIndex = idx;
        return this.webhooks[idx].url;
      }
    }
    throw new Error('All webhooks exhausted! Create new webhooks in Clay.');
  }

  recordSubmission() {
    this.webhooks[this.currentIndex].count++;
  }

  getStatus() {
    return this.webhooks.map((w, i) => ({
      index: i,
      remaining: w.maxCount - w.count,
      percentUsed: ((w.count / w.maxCount) * 100).toFixed(1),
    }));
  }
}

// Usage: rotate across multiple webhooks for the same table
const rotator = new WebhookRotator([
  process.env.CLAY_WEBHOOK_URL_1!,
  process.env.CLAY_WEBHOOK_URL_2!,
  process.env.CLAY_WEBHOOK_URL_3!,
]);
```

### Step 5: Auto-Delete for Stream-Through Processing

For high-volume use cases where Clay enriches and pushes data onward, enable auto-delete to keep tables lean:

In Clay UI: **Table Settings > Auto-delete**

When enabled, Clay enriches incoming webhook data, sends results via HTTP API column to your destination, then deletes the rows. This keeps Clay functioning as a streaming enrichment service rather than a database.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Processing stuck at 400/hr | Explorer plan throttle | Upgrade to Growth (no throttle) |
| Webhook exhausted (50K) | High volume | Rotate to new webhook, implement rotator |
| Queue backing up | Webhook rate limiting | Reduce concurrency, increase delay |
| Table too large to manage | 10K+ rows | Split into multiple focused tables |
| Credit overrun | Uncontrolled batch size | Add budget check before queueing |

## Resources

- [Clay Plans & Billing](https://university.clay.com/docs/plans-and-billing)
- [Clay University -- Using Clay as an API](https://www.clay.com/university/guide/using-clay-as-an-api)
- [BullMQ Documentation](https://docs.bullmq.io/)

## Next Steps

For reliability patterns, see `clay-reliability-patterns`.
