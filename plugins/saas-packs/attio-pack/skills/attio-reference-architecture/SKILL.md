---
name: attio-reference-architecture
description: 'Production reference architecture for Attio CRM integrations -- layered

  project structure, sync patterns, webhook processing, and multi-environment setup.

  Trigger: "attio architecture", "attio best practices", "attio project structure",

  "how to organize attio", "attio integration design".

  '
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- crm
- attio
compatibility: Designed for Claude Code
---
# Attio Reference Architecture

## Overview

Production architecture for CRM integrations with the Attio REST API (`https://api.attio.com/v2`). Designed for contact enrichment pipelines, deal tracking across custom lists, bi-directional activity sync with external systems, and workspace isolation for multi-tenant deployments. Key design drivers: webhook-driven data freshness, idempotent upserts via PUT assertions, schema-aware caching, and layered separation between API client, business logic, and infrastructure.

## Architecture Diagram
```
Your App ──→ Service Layer ──→ Cache (Redis) ──→ Attio REST API v2
                  ↓                               /objects/people/records
             Queue (p-queue) ──→ Sync Worker      /lists/{slug}/entries
                  ↓                               /notes, /tasks
             Webhook Handler ←── Attio Events     /webhooks
                  ↓
             External CRM Sync ──→ HubSpot/Salesforce
```

## Service Layer
```typescript
class ContactService {
  constructor(private client: AttioClient, private cache: CacheLayer) {}

  async findByEmail(email: string): Promise<AttioRecord | null> {
    const res = await this.client.post('/objects/people/records/query', { filter: { email_addresses: email }, limit: 1 });
    return res.data[0] || null;
  }

  async upsertPerson(data: { email: string; firstName: string; lastName: string }): Promise<AttioRecord> {
    const res = await this.client.put('/objects/people/records', {
      data: { values: { email_addresses: [data.email], name: [{ first_name: data.firstName, last_name: data.lastName }] } }
    });
    await this.cache.invalidate(`person:${data.email}`);
    return res.data;
  }

  async addToPipeline(recordId: string, listSlug: string, stage: string): Promise<void> {
    await this.client.post(`/lists/${listSlug}/entries`, {
      data: { parent_record_id: recordId, parent_object: 'people', values: { stage: [{ status: stage }] } }
    });
  }
}
```

## Caching Strategy
```typescript
const CACHE_CONFIG = {
  schema:  { ttl: 1800, prefix: 'schema' },   // 30 min — object/attribute definitions change rarely
  records: { ttl: 300,  prefix: 'record' },    // 5 min — webhook-driven invalidation handles freshness
  lists:   { ttl: 120,  prefix: 'list' },      // 2 min — deal pipeline stages need near-real-time
  notes:   { ttl: 60,   prefix: 'note' },      // 1 min — activity feed freshness
};
// Webhook events (record.updated, list-entry.created) flush matching cache keys immediately
```

## Event Pipeline
```typescript
class AttioEventPipeline {
  private queue = new Bull('attio-events', { redis: process.env.REDIS_URL });

  async onWebhook(event: AttioWebhookEvent): Promise<void> {
    await this.queue.add(event.event_type, event, { attempts: 3, backoff: { type: 'exponential', delay: 2000 } });
  }

  async processRecordEvent(event: AttioWebhookEvent): Promise<void> {
    if (event.event_type === 'record.created') await this.syncToExternalCRM(event.record!.id.record_id);
    if (event.event_type === 'record.updated') await this.cache.invalidate(`record:${event.record!.id.record_id}`);
    if (event.event_type === 'record.merged') await this.reconcileMergedRecords(event);
  }

  async processListEntryEvent(event: AttioWebhookEvent): Promise<void> {
    if (event.event_type === 'list-entry.created') await this.triggerPipelineAutomation(event);
  }
}
```

## Data Model
```typescript
interface AttioRecord       { id: { record_id: string; object_id: string }; values: Record<string, AttioValue[]>; created_at: string; }
interface AttioValue        { attribute_type: string; [key: string]: unknown; }
interface AttioWebhookEvent { event_type: string; object?: { api_slug: string }; record?: AttioRecord; list_entry?: { entry_id: string }; }
interface SyncState         { objectSlug: string; lastSyncOffset: number; lastFullSync: string; recordCount: number; }
```

## Scaling Considerations
- Partition sync workers by Attio object type (people, companies, deals) to isolate rate limits
- Use webhook-driven invalidation rather than polling — Attio delivers events within seconds
- Batch record queries with `/records/query` pagination (500 per page) for full sync
- Schema cache (30 min TTL) prevents redundant attribute lookups on every record access
- Rate-limit outbound writes with p-queue to stay within Attio's per-workspace concurrency limits

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Contact upsert | Attio 429 rate limit | p-queue backoff with jitter, per-object circuit breaker |
| Webhook handler | Duplicate event delivery | Idempotency key on record_id + event_type + timestamp |
| Bi-directional sync | Both sides updated same record | Last-write-wins with conflict resolution queue |
| Schema cache | Stale attribute definitions | Webhook-driven invalidation, fallback to fresh fetch |
| External CRM sync | HubSpot API timeout | Queue retry with dead-letter, manual reconciliation flag |

## Resources
- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [Attio Objects and Lists](https://docs.attio.com/docs/objects-and-lists)
- [Attio Webhooks Guide](https://docs.attio.com/rest-api/guides/webhooks)
- [Attio Developer Platform](https://attio.com/platform/developers)

## Next Steps
See `attio-deploy-integration`.
