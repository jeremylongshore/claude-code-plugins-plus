# HubSpot Product Event Sync — Implementation Guide

Full implementation reference: event queue with batching, idempotency key design, 207 error handling with dead-letter queue, property type validation, and contact auto-create. The TypeScript patterns are in `SKILL.md`; this document covers complete runnable implementations, Python equivalents, DLQ patterns, and backfill tooling.

## Complete TypeScript Implementation

The following is a production-ready, self-contained sync pipeline. Wire it to your event stream transport (Kafka consumer, SQS poller, or webhook handler) by calling `queue.push(event)`.

```typescript
import { createHash } from "crypto";
import { createClient, RedisClientType } from "redis";

// ── Types ──────────────────────────────────────────────────────────────────

export interface ProductEvent {
  eventId: string;
  email: string;
  properties: Record<string, string | number | boolean>;
  occurredAt: number; // Unix ms
}

export interface DLQEntry {
  event: ProductEvent;
  error: { message: string; category?: string; status?: number };
  failedAt: string;
  retryCount: number;
  nextRetryAt?: string;
}

interface HubSpot207Error {
  status: string;
  category: string;
  message: string;
  context: { id?: string[] };
}

interface HubSpot207Body {
  status: string;
  results: Array<{ id: string; properties: Record<string, string> }>;
  errors: HubSpot207Error[];
  startedAt: string;
  completedAt: string;
}

// ── Idempotency ────────────────────────────────────────────────────────────

function idempotencyKey(eventId: string, propertyName: string): string {
  return createHash("sha256")
    .update(`${eventId}:${propertyName}`)
    .digest("hex")
    .slice(0, 16);
}

async function isAlreadyProcessed(redis: RedisClientType, key: string): Promise<boolean> {
  return (await redis.get(`hs_sync:${key}`)) !== null;
}

async function markProcessed(redis: RedisClientType, key: string): Promise<void> {
  // 48-hour TTL covers the worst realistic retry window
  await redis.setEx(`hs_sync:${key}`, 172_800, "1");
}

// Build a compound key for the whole event (all properties bundled)
// Use per-property keys when you need property-level deduplication
function eventLevelKey(event: ProductEvent): string {
  return createHash("sha256")
    .update(event.eventId)
    .digest("hex")
    .slice(0, 16);
}

// ── Property type validation ───────────────────────────────────────────────

type HubSpotPropertyType = "string" | "number" | "date" | "datetime" | "bool" | "enumeration";

interface PropertyDefinition {
  name: string;
  type: HubSpotPropertyType;
  fieldType: string;
  label: string;
  groupName: string;
  description?: string;
}

// Cache validated types in-process — property schemas are stable
const propertyTypeCache = new Map<string, HubSpotPropertyType>();

async function ensureProperty(
  token: string,
  objectType: "contacts" | "companies",
  prop: PropertyDefinition,
): Promise<void> {
  const cacheKey = `${objectType}:${prop.name}`;
  if (propertyTypeCache.has(cacheKey)) return;

  const res = await fetch(
    `https://api.hubapi.com/crm/v3/properties/${objectType}/${prop.name}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );

  if (res.status === 200) {
    const existing = await res.json();
    if (existing.type !== prop.type) {
      throw new Error(
        `PROPERTY_TYPE_MISMATCH: ${prop.name} is '${existing.type}' in HubSpot but ` +
        `your schema declares '${prop.type}'. Writing will silently coerce values. ` +
        `Fix: rename property to a new name, or delete and recreate (data loss on existing records). ` +
        `You cannot update a property type in place via the HubSpot API.`,
      );
    }
    propertyTypeCache.set(cacheKey, existing.type);
    return;
  }

  if (res.status !== 404) {
    throw new Error(`Unexpected ${res.status} checking property ${prop.name}: ${await res.text()}`);
  }

  // Create
  const create = await fetch(
    `https://api.hubapi.com/crm/v3/properties/${objectType}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
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

  propertyTypeCache.set(cacheKey, prop.type);
  console.info("Created HubSpot property", { name: prop.name, type: prop.type });
}

// Validate event property values against cached types before batching
function validateEventProperties(
  event: ProductEvent,
  schema: Map<string, HubSpotPropertyType>,
): string[] {
  const errors: string[] = [];
  for (const [key, value] of Object.entries(event.properties)) {
    const expectedType = schema.get(key);
    if (!expectedType) {
      errors.push(`Unknown property: ${key} — not in schema; will cause PROPERTY_DOESNT_EXIST on write`);
      continue;
    }
    if (expectedType === "number" && isNaN(Number(value))) {
      errors.push(`Type mismatch: ${key} expects number but got '${value}'`);
    }
    if (expectedType === "bool" && value !== true && value !== false && value !== "true" && value !== "false") {
      errors.push(`Type mismatch: ${key} expects bool but got '${value}'`);
    }
  }
  return errors;
}

// ── Retry ──────────────────────────────────────────────────────────────────

async function withRetry(
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

    console.warn("HubSpot rate limited or server error", {
      status: res.status,
      attempt,
      delayMs: Math.round(delay),
      dailyRemaining: res.headers.get("X-HubSpot-RateLimit-Daily-Remaining"),
    });

    await new Promise((r) => setTimeout(r, delay));
  }
  throw new Error("unreachable");
}

// ── Dead-letter queue ─────────────────────────────────────────────────────

// Interface — implement against your preferred store (Postgres, Redis, S3)
interface DeadLetterQueue {
  push(entry: DLQEntry): Promise<void>;
  pop(limit: number): Promise<DLQEntry[]>;
  ack(entry: DLQEntry): Promise<void>;
  nack(entry: DLQEntry, nextRetryDelayMs: number): Promise<void>;
}

// Minimal Postgres implementation (pseudocode — fill in your pg client)
class PostgresDLQ implements DeadLetterQueue {
  constructor(private readonly pool: any) {}

  async push(entry: DLQEntry): Promise<void> {
    await this.pool.query(
      `INSERT INTO hubspot_dlq (event_id, email, event_json, error_json, failed_at, retry_count, next_retry_at)
       VALUES ($1, $2, $3, $4, $5, $6, NOW() + interval '1 minute')
       ON CONFLICT (event_id) DO UPDATE
         SET error_json = EXCLUDED.error_json,
             retry_count = hubspot_dlq.retry_count + 1,
             next_retry_at = NOW() + interval '5 minutes'`,
      [
        entry.event.eventId,
        entry.event.email,
        JSON.stringify(entry.event),
        JSON.stringify(entry.error),
        entry.failedAt,
        entry.retryCount,
      ],
    );
  }

  async pop(limit: number): Promise<DLQEntry[]> {
    const { rows } = await this.pool.query(
      `SELECT * FROM hubspot_dlq
       WHERE retry_count < 5 AND next_retry_at < NOW()
       ORDER BY failed_at ASC
       LIMIT $1`,
      [limit],
    );
    return rows.map((r: any) => ({
      event: JSON.parse(r.event_json),
      error: JSON.parse(r.error_json),
      failedAt: r.failed_at,
      retryCount: r.retry_count,
    }));
  }

  async ack(entry: DLQEntry): Promise<void> {
    await this.pool.query(
      "DELETE FROM hubspot_dlq WHERE event_id = $1",
      [entry.event.eventId],
    );
  }

  async nack(entry: DLQEntry, nextRetryDelayMs: number): Promise<void> {
    await this.pool.query(
      `UPDATE hubspot_dlq
       SET retry_count = retry_count + 1,
           next_retry_at = NOW() + ($1 || ' milliseconds')::interval
       WHERE event_id = $2`,
      [nextRetryDelayMs, entry.event.eventId],
    );
  }
}

// ── Sync pipeline ──────────────────────────────────────────────────────────

const BATCH_SIZE = 100;
const FLUSH_INTERVAL_MS = 5_000;

export class HubSpotEventSyncPipeline {
  private queue: ProductEvent[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;
  private schema: Map<string, HubSpotPropertyType> = new Map();

  constructor(
    private readonly token: string,
    private readonly redis: RedisClientType,
    private readonly dlq: DeadLetterQueue,
  ) {}

  // Call at startup with your property definitions
  async initialize(
    objectType: "contacts" | "companies",
    properties: PropertyDefinition[],
  ): Promise<void> {
    for (const prop of properties) {
      await ensureProperty(this.token, objectType, prop);
      this.schema.set(prop.name, prop.type);
    }
    console.info("HubSpot property schema validated", { count: properties.length });
  }

  push(event: ProductEvent): void {
    // Validate before queueing — surface type errors immediately
    const errors = validateEventProperties(event, this.schema);
    if (errors.length > 0) {
      console.error("Event property validation failed — dropping event", {
        eventId: event.eventId,
        errors,
      });
      return;
    }

    this.queue.push(event);

    if (this.queue.length >= BATCH_SIZE) {
      void this.flush();
    } else if (!this.timer) {
      this.timer = setTimeout(() => void this.flush(), FLUSH_INTERVAL_MS);
    }
  }

  async flush(): Promise<void> {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, BATCH_SIZE);

    // Idempotency filter — skip events already processed
    const unprocessed: ProductEvent[] = [];
    for (const event of batch) {
      const key = eventLevelKey(event);
      if (await isAlreadyProcessed(this.redis, key)) {
        console.debug("Skipping already-processed event", { eventId: event.eventId });
        continue;
      }
      unprocessed.push(event);
    }

    if (unprocessed.length > 0) {
      await this.sendBatch(unprocessed);
    }

    // If more events arrived while flushing, flush again immediately
    if (this.queue.length > 0) void this.flush();
  }

  private async sendBatch(events: ProductEvent[]): Promise<void> {
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

  private async handle207(res: Response, events: ProductEvent[]): Promise<void> {
    if (res.status === 200) {
      // All succeeded — mark as processed
      for (const event of events) {
        await markProcessed(this.redis, eventLevelKey(event));
      }
      console.info("HubSpot batch succeeded", { count: events.length });
      return;
    }

    if (res.status === 207) {
      const body: HubSpot207Body = await res.json();
      const successEmails = new Set(
        // For upsert, results contain the created/updated email in properties
        body.results.map((r) => r.properties.email).filter(Boolean),
      );

      // Mark successful contacts as processed
      for (const event of events) {
        if (successEmails.has(event.email)) {
          await markProcessed(this.redis, eventLevelKey(event));
        }
      }

      // Route failures to DLQ
      const failedEmails = new Set(body.errors.flatMap((e) => e.context.id ?? []));
      console.error("HubSpot batch partial failure", {
        total: events.length,
        succeeded: body.results.length,
        failed: body.errors.length,
        errors: body.errors.map((e) => ({ category: e.category, message: e.message })),
      });

      for (const err of body.errors) {
        const failedEmail = err.context.id?.[0];
        const failedEvent = events.find((e) => e.email === failedEmail);
        if (failedEvent) {
          await this.dlq.push({
            event: failedEvent,
            error: { message: err.message, category: err.category },
            failedAt: new Date().toISOString(),
            retryCount: 0,
          });
        }
      }

      return;
    }

    // Non-2xx — all events in batch failed
    const body = await res.text();
    console.error("HubSpot batch entirely failed", { status: res.status, body });

    for (const event of events) {
      await this.dlq.push({
        event,
        error: { message: body, status: res.status },
        failedAt: new Date().toISOString(),
        retryCount: 0,
      });
    }
  }

  private serializeProperties(
    props: Record<string, string | number | boolean>,
  ): Record<string, string> {
    return Object.fromEntries(
      Object.entries(props).map(([k, v]) => [k, String(v)]),
    );
  }
}
```

## DLQ Schema (Postgres)

```sql
CREATE TABLE hubspot_dlq (
  id            BIGSERIAL PRIMARY KEY,
  event_id      TEXT NOT NULL UNIQUE,
  email         TEXT NOT NULL,
  event_json    JSONB NOT NULL,
  error_json    JSONB NOT NULL,
  failed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  retry_count   INT NOT NULL DEFAULT 0,
  next_retry_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '1 minute',
  resolved_at   TIMESTAMPTZ,
  resolution    TEXT -- 'replayed', 'discarded', 'manual'
);

CREATE INDEX idx_hubspot_dlq_next_retry ON hubspot_dlq (next_retry_at)
  WHERE resolved_at IS NULL;

CREATE INDEX idx_hubspot_dlq_email ON hubspot_dlq (email)
  WHERE resolved_at IS NULL;
```

**Replay query:**

```sql
SELECT event_id, email, event_json, retry_count
FROM hubspot_dlq
WHERE resolved_at IS NULL
  AND retry_count < 5
  AND next_retry_at < NOW()
ORDER BY failed_at ASC
LIMIT 500;
```

## Python Implementation

For Python services consuming from Kafka, SQS, or a polling loop:

```python
import hashlib
import json
import time
import threading
from dataclasses import dataclass, field
from typing import Any
import requests

BATCH_SIZE = 100
FLUSH_INTERVAL_SECS = 5
HS_BASE = "https://api.hubapi.com"


@dataclass
class ProductEvent:
    event_id: str
    email: str
    properties: dict[str, str | int | float | bool]
    occurred_at: int  # Unix ms


def idempotency_key(event_id: str) -> str:
    return hashlib.sha256(event_id.encode()).hexdigest()[:16]


def is_already_processed(redis_client, key: str) -> bool:
    return redis_client.get(f"hs_sync:{key}") is not None


def mark_processed(redis_client, key: str) -> None:
    redis_client.setex(f"hs_sync:{key}", 172_800, "1")  # 48h TTL


def with_retry(fn, max_attempts: int = 4, base_delay: float = 1.0):
    for attempt in range(1, max_attempts + 1):
        res = fn()
        if res.status_code not in (429,) and res.status_code < 500:
            return res
        if attempt == max_attempts:
            return res

        retry_after = int(res.headers.get("Retry-After", "0"))
        exp_delay = min(30.0, base_delay * (2 ** attempt))
        import random
        delay = retry_after if retry_after > 0 else random.random() * exp_delay
        time.sleep(delay)

    raise RuntimeError("unreachable")


class HubSpotSyncPipeline:
    def __init__(self, token: str, redis_client, dlq):
        self.token = token
        self.redis = redis_client
        self.dlq = dlq
        self._queue: list[ProductEvent] = []
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def push(self, event: ProductEvent) -> None:
        with self._lock:
            self._queue.append(event)
            if len(self._queue) >= BATCH_SIZE:
                self._flush_locked()
            elif self._timer is None:
                self._timer = threading.Timer(FLUSH_INTERVAL_SECS, self.flush)
                self._timer.daemon = True
                self._timer.start()

    def flush(self) -> None:
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None
        if not self._queue:
            return

        batch = self._queue[:BATCH_SIZE]
        self._queue = self._queue[BATCH_SIZE:]

        # Filter already-processed
        unprocessed = [
            e for e in batch
            if not is_already_processed(self.redis, idempotency_key(e.event_id))
        ]

        if unprocessed:
            self._send_batch(unprocessed)

    def _send_batch(self, events: list[ProductEvent]) -> None:
        inputs = [
            {
                "idProperty": "email",
                "id": e.email,
                "properties": {k: str(v) for k, v in e.properties.items()},
            }
            for e in events
        ]

        res = with_retry(lambda: requests.post(
            f"{HS_BASE}/crm/v3/objects/contacts/batch/upsert",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json={"inputs": inputs},
            timeout=30,
        ))

        self._handle_response(res, events)

    def _handle_response(self, res, events: list[ProductEvent]) -> None:
        if res.status_code == 200:
            for e in events:
                mark_processed(self.redis, idempotency_key(e.event_id))
            return

        if res.status_code == 207:
            body = res.json()
            success_emails = {r["properties"].get("email") for r in body.get("results", [])}

            for e in events:
                if e.email in success_emails:
                    mark_processed(self.redis, idempotency_key(e.event_id))

            for err in body.get("errors", []):
                failed_email = (err.get("context", {}).get("id") or [None])[0]
                failed_event = next((e for e in events if e.email == failed_email), None)
                if failed_event:
                    self.dlq.push({
                        "event": failed_event.__dict__,
                        "error": {"message": err["message"], "category": err["category"]},
                        "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "retry_count": 0,
                    })
            return

        # All failed
        for e in events:
            self.dlq.push({
                "event": e.__dict__,
                "error": {"message": res.text, "status": res.status_code},
                "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "retry_count": 0,
            })
```

## Counter Property Pattern (Increment-Safe)

Counters cannot be made idempotent by simple write deduplication alone — if the same event is processed twice, the increment fires twice. The safe pattern: deduplicate before the read-modify-write, not after.

```typescript
async function safeIncrement(
  token: string,
  email: string,
  propertyName: string,
  delta: number,
  event: ProductEvent,
  redis: RedisClientType,
): Promise<void> {
  const key = `counter:${idempotencyKey(event.eventId, propertyName)}`;

  // Check before the expensive read
  if (await isAlreadyProcessed(redis, key)) {
    console.debug("Counter increment already applied", { eventId: event.eventId, propertyName });
    return;
  }

  // Search for contact by email
  const search = await fetch("https://api.hubapi.com/crm/v3/objects/contacts/search", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      filterGroups: [{ filters: [{ propertyName: "email", operator: "EQ", value: email }] }],
      properties: [propertyName],
      limit: 1,
    }),
  });
  const found = await search.json();

  if (found.total === 0) {
    // Contact does not exist — create with initial value
    await fetch("https://api.hubapi.com/crm/v3/objects/contacts", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ properties: { email, [propertyName]: String(delta) } }),
    });
  } else {
    const contactId = found.results[0].id;
    const current = parseFloat(found.results[0].properties[propertyName] ?? "0");
    const next = current + delta;

    await fetch(`https://api.hubapi.com/crm/v3/objects/contacts/${contactId}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ properties: { [propertyName]: String(next) } }),
    });
  }

  await markProcessed(redis, key);
}
```

**When to use counters vs timestamps:** If you only need to know the last time something happened (`last_active_date`), a `datetime` property is idempotent by nature — writing the same timestamp twice is harmless. If you need cumulative counts (`total_sessions`), you need the counter pattern above. When possible, derive counts in your analytics warehouse and sync only the computed result to HubSpot — this avoids the read-modify-write race entirely.

## Backfill Tooling

When bootstrapping a new sync pipeline, you will need to backfill historical events. Backfill differs from live sync in three ways: the event stream is a finite dataset (not a queue), the contact may not exist yet (always use upsert), and the volume can be much larger than the sustained live rate.

```bash
#!/usr/bin/env bash
# backfill.sh — batch backfill from a JSONL file
# Each line: {"event_id":"...","email":"...","properties":{...},"occurred_at":1234567890000}

INPUT_FILE=$1
BATCH_SIZE=100
HUBSPOT_TOKEN="${HUBSPOT_ACCESS_TOKEN:?required}"
DLQ_FILE="dlq_$(date +%Y%m%d_%H%M%S).jsonl"

line_count=$(wc -l < "$INPUT_FILE")
batch_num=0
failed=0
succeeded=0

while IFS= read -r line; do
  batch[$batch_num]="$line"
  batch_num=$((batch_num + 1))

  if [ $batch_num -ge $BATCH_SIZE ]; then
    # Build payload
    payload=$(printf '%s\n' "${batch[@]}" | jq -s '[.[] | {idProperty: "email", id: .email, properties: (.properties | with_entries(.value |= tostring))}]')
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
      "https://api.hubapi.com/crm/v3/objects/contacts/batch/upsert" \
      -H "Authorization: Bearer $HUBSPOT_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"inputs\": $payload}")

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -1)

    if [ "$http_code" = "200" ]; then
      succeeded=$((succeeded + batch_num))
    elif [ "$http_code" = "207" ]; then
      error_count=$(echo "$body" | jq '.errors | length')
      succeeded=$((succeeded + batch_num - error_count))
      failed=$((failed + error_count))
      echo "$body" | jq '.errors[]' >> "$DLQ_FILE"
    else
      failed=$((failed + batch_num))
      echo "Batch failed: $http_code" >&2
    fi

    # Rate limit: 100 req/10s = 10 req/s; sleep 100ms per batch
    sleep 0.1
    batch=()
    batch_num=0
  fi
done < "$INPUT_FILE"

echo "Backfill complete: $succeeded succeeded, $failed failed. DLQ: $DLQ_FILE"
```

## Monitoring Checklist

Log these signals to detect pipeline problems before they cause data loss:

| Event | Log level | Alert threshold |
|---|---|---|
| Batch sent (N records) | INFO | — |
| Batch partial failure (207) | ERROR | Any 207 with errors |
| Batch total failure (4xx/5xx) | ERROR | Any non-2xx |
| Idempotency key hit (duplicate) | DEBUG | — |
| DLQ depth growing | WARN | DLQ > 1,000 unresolved entries |
| Daily rate limit below 20% | WARN | Throttle non-critical paths |
| Daily rate limit exhausted | CRITICAL | Stop all sync immediately |
| Property type mismatch at startup | CRITICAL | Halt service — do not proceed |
| Queue depth growing beyond 1,000 | WARN | Flush interval may be too long |

```typescript
// Structured log per batch
console.log(JSON.stringify({
  event: "hubspot_batch_complete",
  total: events.length,
  succeeded: successCount,
  failed: failCount,
  dlqDepth: await dlq.count(),
  dailyRemaining: parseInt(res.headers.get("X-HubSpot-RateLimit-Daily-Remaining") ?? "-1", 10),
  ts: new Date().toISOString(),
}));
```
