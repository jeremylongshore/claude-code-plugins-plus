---
name: hubspot-product-event-sync
description: |
  Sync backend product events into HubSpot contact and company custom properties using
  idempotent batched updates — the Segment integration pattern without Segment. Use when
  you need to push server-side behavioral signals (feature usage, session counts, last-seen
  timestamps, trial milestones) into HubSpot CRM properties so sales and marketing can
  act on product data without a CDP in the stack. Trigger with "hubspot product events",
  "sync events to hubspot", "hubspot custom properties", "hubspot event pipeline",
  "hubspot segment alternative", "push usage data to hubspot".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Bash(python3:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code
tags:
  - hubspot
  - product-analytics
  - event-sync
  - integration-engineering
---

# HubSpot Product Event Sync

## Overview

Push backend product events into HubSpot custom contact and company properties — the core pattern of a Segment-style integration, built directly against the HubSpot CRM API without a CDP middleman. This is not a tutorial on HubSpot setup. It is the code your data pipeline runs at 3am when a product launch generates a 10K events/minute storm, when a network hiccup causes the same batch to be retried and your "total sessions" counter doubles, when a property type mismatch silently truncates numbers, and when your contact lookup fails because a new user signed up ten seconds ago and HubSpot doesn't have them yet.

The six production failures this skill prevents:

1. **Non-idempotent updates** — the same event processed twice (retry after network failure) increments a counter twice. "Last seen" survives duplication; "total sessions" does not. Idempotency keys must be event-level, not request-level.
2. **Property type mismatch** — writing a number to a HubSpot `string` property returns HTTP 200 with the value coerced silently. The stored data is wrong; no error surfaces. Validate property types before writing.
3. **Rate-limit burnout from event storms** — a product launch generates 10K events/minute. Naive sync exhausts the 100 req/10s burst budget in under two seconds. A token-bucket queue is non-optional.
4. **Contact not found** — the product event carries an email that HubSpot does not have yet. The batch update silently drops the record. Upsert-by-email or auto-create is the correct path.
5. **Batch partial failure (207 Multi-Status)** — `POST /crm/v3/objects/contacts/batch/update` returns 207 when some records succeed and others fail. Treating 207 as success causes silent data loss at scale. Parse the per-object `errors` array.
6. **Custom event vs custom property confusion** — HubSpot has two different systems: custom behavioral events (Marketing Hub Enterprise, timeline-visible) and custom contact/company properties (available on all tiers, stored as structured data on the record). Using the wrong mechanism for the use case leads to wrong attribution, missing data, or a surprise $3K/month plan upgrade.

## Prerequisites

- Node.js 18+ or Python 3.10+
- HubSpot private app token with scopes: `crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.objects.companies.read`, `crm.objects.companies.write`, `crm.schemas.contacts.read`, `crm.schemas.contacts.write`
- Custom properties already defined in HubSpot (or use the property-create flow in this skill to create them)
- Your backend event stream: Kafka topic, SQS queue, webhook receiver, or polling loop — the sync layer is transport-agnostic
- A dead-letter store for failed records: a Postgres table, Redis sorted set, or S3 prefix — anything you can replay from

## Instructions

Build in this order. Each section neutralizes one production failure mode.

### 1. Decide: custom property or custom behavioral event?

Get this wrong and you build the right pipeline into the wrong HubSpot system. Custom properties and custom behavioral events are entirely separate surfaces.

| Dimension | Custom property | Custom behavioral event |
|---|---|---|
| HubSpot tier | All tiers | Marketing Hub Enterprise only |
| Visible in | Contact/company record sidebar | Record timeline + Behavioral Events report |
| Query in lists | Yes (`contact.hs_last_active_date > 7d ago`) | Limited (via list enrollment criteria) |
| Attribution | No native attribution | Yes (can be tied to campaign attribution) |
| API | `/crm/v3/objects/contacts/batch/update` | `/events/v3/send` |
| Best for | Product data, counts, timestamps, tier flags | Marketing touchpoints, funnel stages, UTM-tagged actions |
| Wrong for | Timeline visibility of behavioral sequences | Querying by property value in segmentation lists |

**Rule of thumb:** if your sales team needs to filter contacts by a product signal (e.g., "show me contacts where last_active_date > 14 days ago"), it goes in a custom property. If your marketing team needs to see a behavioral sequence on the contact timeline, it goes in a custom behavioral event. Most product-to-CRM pipelines use custom properties exclusively.

### 2. Verify and create property definitions

Before writing any data, confirm that the target property exists and has the right type. HubSpot returns 200 even when coercing an incompatible value, so the validation must happen on your side.

```typescript
type HubSpotPropertyType = "string" | "number" | "date" | "datetime" | "bool" | "enumeration";

interface PropertyDefinition {
  name: string;
  type: HubSpotPropertyType;
  fieldType: "text" | "number" | "date" | "booleancheckbox" | "select" | "textarea";
  label: string;
  groupName: string;
  description?: string;
}

async function ensureProperty(
  token: string,
  objectType: "contacts" | "companies",
  prop: PropertyDefinition,
): Promise<void> {
  // Check if it exists first
  const check = await fetch(
    `https://api.hubapi.com/crm/v3/properties/${objectType}/${prop.name}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );

  if (check.status === 200) {
    const existing = await check.json();
    if (existing.type !== prop.type) {
      throw new Error(
        `Property type mismatch: ${prop.name} is ${existing.type} in HubSpot, ` +
        `but your schema declares it as ${prop.type}. ` +
        `Mismatched writes return 200 with silently wrong data. ` +
        `Either rename the property or migrate the type — you cannot update a property type in place.`,
      );
    }
    return; // exists and type matches — nothing to do
  }

  if (check.status !== 404) {
    throw new Error(`Unexpected status ${check.status} checking property ${prop.name}`);
  }

  // Create it
  const create = await fetch(
    `https://api.hubapi.com/crm/v3/properties/${objectType}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: prop.name,
        label: prop.label,
        type: prop.type,
        fieldType: prop.fieldType,
        groupName: prop.groupName,
        description: prop.description ?? "",
      }),
    },
  );

  if (!create.ok) {
    throw new Error(`Failed to create property ${prop.name}: ${await create.text()}`);
  }
}
```

Call `ensureProperty` at service startup, not per-event. Property definitions are stable; checking them on every event wastes rate-limit budget and adds latency.

### 3. Idempotency key design

An idempotency key is the contract that makes retry safe. The key must uniquely identify a specific value written to a specific property for a specific event occurrence. The wrong key design causes either over-deduplication (missing legitimate updates) or under-deduplication (counter inflation on retry).

```typescript
import { createHash } from "crypto";

interface ProductEvent {
  eventId: string;          // UUID from your event stream — unique per occurrence
  email: string;
  properties: Record<string, string | number | boolean>;
  occurredAt: number;       // Unix ms
}

// Idempotency key = hash(eventId + propertyName)
// Scope per-property, not per-event, so you can track exactly which property write was retried
function idempotencyKey(eventId: string, propertyName: string): string {
  return createHash("sha256")
    .update(`${eventId}:${propertyName}`)
    .digest("hex")
    .slice(0, 16); // 16 hex chars = 8 bytes = 64 bits of collision resistance
}

// Store processed keys with TTL to cap memory. Redis SETEX is canonical.
// Postgres alternative: INSERT INTO idempotency_keys (key, processed_at) ON CONFLICT DO NOTHING
async function isAlreadyProcessed(key: string, redis: RedisClient): Promise<boolean> {
  return (await redis.get(`hs_sync:${key}`)) !== null;
}

async function markProcessed(key: string, redis: RedisClient): Promise<void> {
  // 48h TTL — cover the worst realistic retry window
  await redis.setex(`hs_sync:${key}`, 172_800, "1");
}
```

**Counter properties require special handling.** You cannot make "increment by 1" idempotent with a simple deduplication key on the write side, because HubSpot properties are absolute values, not deltas. The only safe pattern is:

1. Read the current value from HubSpot before writing.
2. Compute the new value in your code.
3. Write the absolute new value.
4. Use the idempotency key to skip the entire operation (read + write) if this event was already processed.

```typescript
async function incrementCounter(
  token: string,
  contactId: string,
  propertyName: string,
  delta: number,
  idempotencyKeyValue: string,
  redis: RedisClient,
): Promise<void> {
  if (await isAlreadyProcessed(idempotencyKeyValue, redis)) return;

  // Read current value
  const res = await fetch(
    `https://api.hubapi.com/crm/v3/objects/contacts/${contactId}?properties=${propertyName}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  const contact = await res.json();
  const current = parseFloat(contact.properties[propertyName] ?? "0");
  const next = current + delta;

  // Write absolute value
  await fetch(`https://api.hubapi.com/crm/v3/objects/contacts/${contactId}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ properties: { [propertyName]: String(next) } }),
  });

  await markProcessed(idempotencyKeyValue, redis);
}
```

### 4. Event queue with batching and rate limiting

A token-bucket queue that collects events for up to 5 seconds or until 100 accumulate, then flushes one batch. One batch = one API call. This converts an event storm of 10K events/minute into 100 API calls/minute — well within the 600 calls/minute budget.

```typescript
interface SyncQueue {
  events: ProductEvent[];
  timer: ReturnType<typeof setTimeout> | null;
}

const BATCH_SIZE = 100;      // HubSpot batch/update limit
const FLUSH_INTERVAL_MS = 5_000;

class HubSpotEventSyncQueue {
  private queue: ProductEvent[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;
  private readonly token: string;
  private readonly redis: RedisClient;
  private readonly dlq: DeadLetterQueue;

  constructor(token: string, redis: RedisClient, dlq: DeadLetterQueue) {
    this.token = token;
    this.redis = redis;
    this.dlq = dlq;
  }

  push(event: ProductEvent): void {
    this.queue.push(event);
    if (this.queue.length >= BATCH_SIZE) {
      this.flush(); // flush immediately on full batch
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), FLUSH_INTERVAL_MS);
    }
  }

  async flush(): Promise<void> {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, BATCH_SIZE);
    await this.processBatch(batch);

    // If more remain (queue grew while flushing), flush again immediately
    if (this.queue.length > 0) this.flush();
  }

  private async processBatch(events: ProductEvent[]): Promise<void> {
    // Resolve contacts by email via upsert — auto-creates on miss
    const inputs = events.map((e) => ({
      idProperty: "email",
      id: e.email,
      properties: this.serializeProperties(e.properties),
    }));

    const res = await withRetry(() =>
      fetch("https://api.hubapi.com/crm/v3/objects/contacts/batch/upsert", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ inputs }),
      }),
    );

    await this.handle207(res, events);
  }

  private serializeProperties(
    props: Record<string, string | number | boolean>,
  ): Record<string, string> {
    // HubSpot batch API requires all values as strings
    return Object.fromEntries(
      Object.entries(props).map(([k, v]) => [k, String(v)]),
    );
  }
}
```

### 5. 207 Multi-Status handling with dead-letter queue

This is the most commonly mishandled failure mode. HubSpot returns HTTP 207 when a batch partially succeeds. The response body contains a `results` array (successes) and an `errors` array (failures). Your code must parse both.

```typescript
interface HubSpot207Response {
  status: "COMPLETE" | "PENDING" | "PROCESSING" | "CANCELED";
  results: Array<{ id: string; properties: Record<string, string> }>;
  errors: Array<{
    status: string;
    category: string;
    message: string;
    context: { id?: string[] };
  }>;
  startedAt: string;
  completedAt: string;
}

async function handle207(
  res: Response,
  events: ProductEvent[],
  dlq: DeadLetterQueue,
): Promise<void> {
  // 200 = all succeeded; 207 = partial; 400+ = all failed
  if (res.status === 200) return;

  if (res.status === 207) {
    const body: HubSpot207Response = await res.json();

    // Log successes (optional — useful for counters)
    const successIds = new Set(body.results.map((r) => r.id));

    // Route failures to DLQ with full context for replay
    for (const err of body.errors) {
      const failedId = err.context.id?.[0];
      const failedEvent = events.find((e) => e.email === failedId);
      console.error("HubSpot batch partial failure", {
        error: err.message,
        category: err.category,
        contactId: failedId,
        email: failedEvent?.email,
      });
      if (failedEvent) {
        await dlq.push({
          event: failedEvent,
          error: err,
          failedAt: new Date().toISOString(),
          retryCount: 0,
        });
      }
    }

    return;
  }

  // Non-2xx — entire batch failed
  const body = await res.text();
  console.error("HubSpot batch entirely failed", { status: res.status, body });

  // Route all events to DLQ
  for (const event of events) {
    await dlq.push({ event, error: { message: body, status: res.status }, failedAt: new Date().toISOString(), retryCount: 0 });
  }
}
```

### 6. Auto-create contact on miss

When an event arrives for an email that is not yet in HubSpot, `batch/update` silently drops the record. The correct path is `batch/upsert` (used in section 4 above) which creates the contact if the email is not found. If you are using `batch/update` for other reasons, implement an explicit create-on-miss fallback:

```typescript
async function upsertContactByEmail(
  token: string,
  email: string,
  properties: Record<string, string>,
): Promise<string> {
  // Try to find by email first
  const search = await fetch("https://api.hubapi.com/crm/v3/objects/contacts/search", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      filterGroups: [{
        filters: [{ propertyName: "email", operator: "EQ", value: email }],
      }],
      properties: ["email"],
      limit: 1,
    }),
  });

  const searchResult = await search.json();

  if (searchResult.total > 0) {
    // Exists — update
    const contactId = searchResult.results[0].id;
    await fetch(`https://api.hubapi.com/crm/v3/objects/contacts/${contactId}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ properties }),
    });
    return contactId;
  }

  // Does not exist — create with product properties included
  const create = await fetch("https://api.hubapi.com/crm/v3/objects/contacts", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ properties: { email, ...properties } }),
  });
  const newContact = await create.json();
  return newContact.id;
}
```

**When to use search+create vs upsert:** `batch/upsert` with `idProperty: "email"` is simpler and handles both cases atomically in one API call. Use the search+create pattern only when you need the contact ID back synchronously before writing other properties, or when building a single-contact sync path (not a batch path).

### 7. Rate limit wiring

Wire the retry helper to read `Retry-After` from 429 responses and respect it. Do not implement a fixed delay — the `Retry-After` value is the only one HubSpot guarantees will not extend your suspension.

```typescript
async function withRetry<T>(
  fn: () => Promise<Response>,
  maxAttempts = 4,
  baseDelayMs = 1_000,
): Promise<Response> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const res = await fn();

    if (res.status !== 429 && res.status < 500) return res;
    if (attempt === maxAttempts) return res;

    const retryAfterSec = parseInt(res.headers.get("Retry-After") ?? "0", 10);
    const expDelay = Math.min(30_000, baseDelayMs * 2 ** attempt);
    const jittered = Math.random() * expDelay;
    const delay = retryAfterSec > 0 ? retryAfterSec * 1_000 : jittered;

    console.warn("HubSpot rate limit or server error", {
      status: res.status,
      attempt,
      delayMs: delay,
      dailyRemaining: res.headers.get("X-HubSpot-RateLimit-Daily-Remaining"),
    });

    await new Promise((r) => setTimeout(r, delay));
  }

  throw new Error("unreachable");
}
```

## Error Handling

| HTTP Status | Error | Root Cause | Action |
|---|---|---|---|
| `200 OK` | None | Full success | Proceed |
| `207 Multi-Status` | Per-object `errors` array in body | Partial batch failure — some records failed, some succeeded | Parse `errors` array; route failures to DLQ; do NOT retry the entire batch |
| `400 BAD_REQUEST` | `INVALID_PROPERTY_VALUE` | Value incompatible with property type (number to string, invalid enum option) | Validate property type before write; fix upstream; do not retry as-is |
| `400 BAD_REQUEST` | `PROPERTY_DOESNT_EXIST` | Property name is wrong or was deleted | Verify property name via GET; re-run `ensureProperty` |
| `400 BAD_REQUEST` | `CONTACT_EXISTS` | Create attempted with an email that already exists | Switch to update path; use upsert endpoint |
| `401 UNAUTHORIZED` | `INVALID_AUTHENTICATION` | Token expired or revoked | Refresh or rotate token |
| `403 FORBIDDEN` | `MISSING_SCOPES` | Private app missing `crm.objects.contacts.write` | Portal admin re-grants scope |
| `404 NOT_FOUND` | `OBJECT_NOT_FOUND` | Contact ID not found (on direct ID-based update) | Switch to upsert by email; verify ID |
| `409 CONFLICT` | `DUPLICATE_VALUE` | Duplicate unique property value | Deduplicate before writing; use upsert |
| `429 TOO_MANY_REQUESTS` | `RATE_LIMIT` | Burst or daily quota exhausted | Respect `Retry-After` header; reduce flush frequency; implement token-bucket |
| `5xx SERVER_ERROR` | Various | HubSpot internal error | Retry with exponential backoff and jitter; DLQ after max attempts |

**207 is a success status code — do not treat it as success.** A 207 from `batch/update` or `batch/upsert` means the request completed but individual records inside the batch may have failed. Always inspect `body.errors`.

## Examples

### Bootstrap: define your custom property schema

```typescript
// Run once at service startup
const PRODUCT_PROPERTIES: PropertyDefinition[] = [
  {
    name: "hs_product_last_active_date",
    label: "Last Active Date (Product)",
    type: "datetime",
    fieldType: "date",
    groupName: "product_signals",
    description: "Last timestamp the contact triggered a product event",
  },
  {
    name: "hs_product_total_sessions",
    label: "Total Sessions (Product)",
    type: "number",
    fieldType: "number",
    groupName: "product_signals",
    description: "Lifetime session count from product backend",
  },
  {
    name: "hs_product_current_plan",
    label: "Current Plan (Product)",
    type: "enumeration",
    fieldType: "select",
    groupName: "product_signals",
    description: "Plan tier from billing system",
  },
];

for (const prop of PRODUCT_PROPERTIES) {
  await ensureProperty(token, "contacts", prop);
}
```

### Sync a single product event

```typescript
const event: ProductEvent = {
  eventId: "evt_01HZ9...",
  email: "alice@acme.com",
  properties: {
    hs_product_last_active_date: Date.now(),
    hs_product_total_sessions: 47,
    hs_product_current_plan: "pro",
  },
  occurredAt: Date.now(),
};

queue.push(event);
```

### Replay DLQ events

```bash
# Example: replay from a Postgres DLQ table
psql $DATABASE_URL -c "
  SELECT id, event_json FROM hubspot_dlq
  WHERE retry_count < 3
    AND next_retry_at < NOW()
  LIMIT 500
" --csv | python3 scripts/replay-dlq.py
```

### Verify a batch write worked

```bash
# Check the contact after a sync
curl -s \
  "https://api.hubapi.com/crm/v3/objects/contacts/search" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": "alice@acme.com"}]}],
    "properties": ["email", "hs_product_last_active_date", "hs_product_total_sessions", "hs_product_current_plan"]
  }' | jq '.results[0].properties'
```

### Check rate limit headroom before a bulk backfill

```bash
curl -si \
  "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i "x-hubspot-ratelimit"
```

## Output

- Property schema verified and created at startup — no runtime 400s from missing or type-mismatched properties
- Event queue that batches 100 events or flushes every 5 seconds, whichever comes first
- Idempotency keys stored in Redis with 48-hour TTL — safe to retry any event up to two days after first attempt
- 207 Multi-Status parsed per-object — failures routed to DLQ, successes counted and logged
- Dead-letter queue with retry count, error context, and replay path
- Upsert-by-email on all batch writes — contacts auto-created on first event; no silent drops
- Rate-limit retry with `Retry-After` header respected; exponential backoff with full jitter
- Structured log output per batch: events sent, succeeded, failed, daily rate-limit remaining

## Resources

- [HubSpot Batch Update Contacts](https://developers.hubspot.com/docs/guides/api/crm/objects/contacts#batch-update-contacts)
- [HubSpot Batch Upsert Contacts](https://developers.hubspot.com/docs/guides/api/crm/objects/contacts#upsert-contacts)
- [HubSpot Custom Properties Guide](https://developers.hubspot.com/docs/guides/api/crm/properties)
- [HubSpot Custom Behavioral Events](https://developers.hubspot.com/docs/guides/api/analytics/events/custom-behavioral-events)
- [HubSpot Timeline Events](https://developers.hubspot.com/docs/guides/api/crm/extensions/timeline-events)
- [Rate Limits Reference](https://developers.hubspot.com/docs/guides/apps/api-usage/usage-details)
- [API_REFERENCE.md](references/API_REFERENCE.md) — batch endpoint shapes, 207 response format, property type enumeration, custom event vs property decision matrix
- [implementation-guide.md](references/implementation-guide.md) — event queue with batching, idempotency key design, 207 handling with DLQ, property type validation, contact auto-create pattern
