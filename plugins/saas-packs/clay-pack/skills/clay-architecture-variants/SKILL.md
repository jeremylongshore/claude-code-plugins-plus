---
name: clay-architecture-variants
description: |
  Choose and implement Clay integration architecture for different scales and use cases.
  Use when designing new Clay integrations, comparing direct vs queue-based vs event-driven,
  or planning architecture for Clay-powered data operations.
  Trigger with phrases like "clay architecture", "clay blueprint",
  "how to structure clay", "clay integration design", "clay event-driven".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, migration, scaling]

---
# Clay Architecture Variants

## Overview

Three proven architecture patterns for Clay data enrichment at different scales. Clay is a hosted SaaS -- your architecture decisions focus on how you send data in (webhooks), how you get enriched data out (HTTP API columns, CRM sync, or CSV export), and how you orchestrate the flow.

## Prerequisites

- Clay account with appropriate plan tier
- Clear understanding of data volume and latency requirements
- Infrastructure for chosen architecture tier (if queue-based or event-driven)

## Instructions

### Architecture 1: Direct Integration (Simple)

**Best for:** Small teams, < 1K enrichments/day, ad-hoc usage.

```
┌──────────────┐     webhook     ┌───────────┐
│ Your App     │───────POST─────>│ Clay Table │
│ (or CSV)     │                 │ (enriches) │
└──────────────┘                 └─────┬─────┘
                                       │
                                  CRM action
                                  or CSV export
                                       │
                                       v
                                 ┌───────────┐
                                 │ CRM / DB  │
                                 └───────────┘
```

```typescript
// Direct: send leads synchronously, export results manually
async function directEnrich(leads: Lead[]): Promise<void> {
  for (const lead of leads) {
    await fetch(process.env.CLAY_WEBHOOK_URL!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(lead),
    });
    await new Promise(r => setTimeout(r, 250)); // Rate limit
  }
  console.log(`Sent ${leads.length} leads. Check Clay table for enriched data.`);
  // Enriched data reaches CRM via Clay's native CRM action column
}
```

**Pros:** Zero infrastructure, 5-minute setup, works on all Clay plans.
**Cons:** No retry logic, no programmatic access to enriched data, manual export only.

---

### Architecture 2: Webhook-in, HTTP API-out (Standard)

**Best for:** Growing teams, 1K-10K enrichments/day, CRM integration.

```
┌──────────────┐     webhook     ┌───────────┐   HTTP API col   ┌──────────────┐
│ Your App     │───────POST─────>│ Clay Table │──────POST──────>│ Your Webhook │
│              │                 │ (enriches) │                 │ Handler      │
└──────────────┘                 └───────────┘                 └──────┬───────┘
                                                                      │
                                                                 Process +
                                                                 Route
                                                                      │
                                                          ┌───────────┼───────────┐
                                                          │           │           │
                                                          v           v           v
                                                       ┌─────┐   ┌───────┐   ┌──────┐
                                                       │ CRM │   │Outreach│  │ DB   │
                                                       └─────┘   └───────┘   └──────┘
```

```typescript
// Standard: send leads via webhook, receive enriched data via HTTP API column
// Inbound: Your app -> Clay
async function sendLeads(leads: Lead[]): Promise<void> {
  const batchResult = await clayClient.sendBatch(leads, 200);
  console.log(`Sent: ${batchResult.sent}, Failed: ${batchResult.failed}`);
}

// Outbound: Clay HTTP API column -> Your webhook handler
app.post('/api/clay/enriched', async (req, res) => {
  res.json({ ok: true }); // Respond fast

  const lead = req.body;
  if (lead.icp_score >= 80 && lead.work_email) {
    await pushToCRM(lead);
    await addToOutreachSequence(lead);
  } else if (lead.icp_score >= 50) {
    await addToNurtureCampaign(lead);
  }
});
```

**Pros:** Full automation, programmatic access to enriched data, flexible routing.
**Cons:** Requires Growth plan (HTTP API columns), needs public HTTPS endpoint.

---

### Architecture 3: Queue-Based Pipeline (Scale)

**Best for:** Enterprise, 10K+ enrichments/day, multiple data sources.

```
┌───────────┐
│ Web Forms │──┐
└───────────┘  │     ┌───────────┐     webhook     ┌───────────┐
               ├────>│ Job Queue │───────POST─────>│ Clay Table │
┌───────────┐  │     │ (BullMQ)  │                 │ (enriches) │
│ CRM Events│──┘     └───────────┘                 └─────┬─────┘
└───────────┘              │                              │
                      DLQ on fail                   HTTP API col
┌───────────┐              │                              │
│ CSV Import│──────────────┘                              v
└───────────┘                                   ┌──────────────┐
                                                │ Your Handler │
                                                │ (w/ circuit  │
                                                │  breaker)    │
                                                └──────┬───────┘
                                                       │
                                            ┌──────────┼──────────┐
                                            │          │          │
                                            v          v          v
                                         ┌─────┐  ┌───────┐  ┌──────┐
                                         │ CRM │  │Outreach│  │ DWH  │
                                         └─────┘  └───────┘  └──────┘
```

```typescript
// Scale: queue-based with DLQ, circuit breaker, and multi-source intake
import { Queue, Worker } from 'bullmq';

const enrichQueue = new Queue('clay-enrichment');

// Multiple sources feed the queue
async function onWebFormSubmit(lead: Lead) {
  await enrichQueue.add('web-form', { ...lead, source: 'web-form' });
}

async function onCRMEvent(lead: Lead) {
  await enrichQueue.add('crm-event', { ...lead, source: 'crm-event' });
}

async function onCSVImport(leads: Lead[]) {
  for (const lead of leads) {
    await enrichQueue.add('csv-import', { ...lead, source: 'csv-import' });
  }
}

// Worker sends to Clay with rate limiting and circuit breaker
const worker = new Worker('clay-enrichment', async (job) => {
  const { allowed, reason } = circuitBreaker.canProcess(6);
  if (!allowed) throw new Error(`Circuit open: ${reason}`);

  const res = await fetch(process.env.CLAY_WEBHOOK_URL!, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(job.data),
  });

  if (!res.ok) throw new Error(`Clay webhook failed: ${res.status}`);
  circuitBreaker.recordSuccess(6);
}, {
  concurrency: 1,
  limiter: { max: 5, duration: 1000 }, // 5 per second max
});
```

**Pros:** Handles any volume, automatic retries, DLQ for failures, multi-source.
**Cons:** Requires queue infrastructure (Redis), more complex to operate.

## Decision Matrix

| Factor | Direct | Webhook + HTTP API | Queue-Based |
|--------|--------|-------------------|-------------|
| Volume | < 1K/day | 1K-10K/day | 10K+/day |
| Plan required | Any | Growth+ | Growth+ |
| Infrastructure | None | HTTPS endpoint | Redis + HTTPS endpoint |
| Retry logic | Manual | In-app | Automatic (BullMQ) |
| Data access | CSV export only | Real-time callback | Real-time callback |
| CRM sync | Clay native action | HTTP API column | HTTP API column |
| Complexity | Low | Medium | High |
| Time to implement | Hours | Days | 1-2 weeks |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Need real-time enriched data | Using Direct (CSV only) | Upgrade to Webhook + HTTP API |
| Queue backing up | Webhook rate limiting | Reduce concurrency, add delay |
| HTTP API column timeout | Callback endpoint slow | Respond 200 immediately, process async |
| Credits exhausted mid-pipeline | No budget control | Add circuit breaker with credit limit |

## Resources

- [Clay University -- HTTP API Integration](https://university.clay.com/docs/http-api-integration-overview)
- [Clay University -- Using Clay as an API](https://www.clay.com/university/guide/using-clay-as-an-api)
- [BullMQ Documentation](https://docs.bullmq.io/)

## Next Steps

For common pitfalls to avoid, see `clay-known-pitfalls`.
