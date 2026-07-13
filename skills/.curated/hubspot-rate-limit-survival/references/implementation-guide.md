# HubSpot Rate Limit Survival — Implementation Guide

Python equivalents, Bull/Redis queue architecture, daily quota dashboard metrics, Retry-After parser, and batch chunker patterns. TypeScript token bucket and `hubspotFetch` wrapper live in `SKILL.md`; this document covers language parity, infrastructure wiring, and observability.

## Python: Token Bucket Implementation

Thread-safe token bucket for Python services. Uses `threading.Lock` for the in-process case; swap for `asyncio.Lock` in async services.

```python
import threading
import time
import math

class TokenBucket:
    """
    Thread-safe token bucket for HubSpot API rate limiting.

    capacity:         max tokens (= burst window limit)
    refill_rate_per_s: tokens added per second
    """

    def __init__(self, capacity: float, refill_rate_per_s: float) -> None:
        self._capacity = capacity
        self._refill_rate_per_s = refill_rate_per_s
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate_per_s)
        self._last_refill = now

    def consume(self, count: float = 1.0) -> float:
        """
        Consume `count` tokens.
        Returns seconds to wait before the request may proceed (0.0 = immediate).
        """
        with self._lock:
            self._refill()
            if self._tokens >= count:
                self._tokens -= count
                return 0.0
            deficit = count - self._tokens
            return deficit / self._refill_rate_per_s

    def acquire(self, count: float = 1.0) -> None:
        """Block until `count` tokens are available, then consume them."""
        wait = self.consume(count)
        if wait > 0:
            time.sleep(wait)


# Plan tier factory
def make_bucket_for_plan(plan: str) -> TokenBucket:
    plans = {
        "starter":             TokenBucket(capacity=100,  refill_rate_per_s=10.0),
        "professional":        TokenBucket(capacity=150,  refill_rate_per_s=15.0),   # OAuth
        "ops_hub_enterprise":  TokenBucket(capacity=1000, refill_rate_per_s=100.0),  # 100 req/s
    }
    if plan not in plans:
        raise ValueError(f"Unknown plan tier: {plan!r}. Valid: {list(plans)}")
    return plans[plan]


# Async variant (aiohttp / httpx services)
import asyncio

class AsyncTokenBucket:
    def __init__(self, capacity: float, refill_rate_per_s: float) -> None:
        self._capacity = capacity
        self._refill_rate_per_s = refill_rate_per_s
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, count: float = 1.0) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(
                self._capacity, self._tokens + elapsed * self._refill_rate_per_s
            )
            self._last_refill = now
            if self._tokens >= count:
                self._tokens -= count
                return
            deficit = count - self._tokens
            wait = deficit / self._refill_rate_per_s
            self._tokens = 0.0
        await asyncio.sleep(wait)
```

## Python: Retry-After Parser and hubspot_fetch

```python
import os
import json
import logging
import requests
from email.utils import parsedate_to_datetime
from datetime import timezone

logger = logging.getLogger(__name__)

HUBSPOT_BASE = "https://api.hubapi.com"


def parse_retry_after_seconds(response: requests.Response) -> float | None:
    """
    Parse Retry-After header per RFC 7231 § 7.1.3.
    Returns seconds to wait, or None if the header is absent.
    """
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None

    # Prefer integer seconds (HubSpot always uses this form)
    try:
        return float(raw)
    except ValueError:
        pass

    # HTTP-date fallback (spec-valid but unusual)
    try:
        target = parsedate_to_datetime(raw)
        now = __import__("datetime").datetime.now(timezone.utc)
        delta = (target - now).total_seconds()
        return max(0.0, delta)
    except Exception:
        return None


_rate_limit_state: dict = {
    "daily_limit": 500_000,
    "daily_remaining": 500_000,
    "window_ms": 10_000,
    "window_max": 100,
    "window_remaining": 100,
}


def _update_rate_limit_state(response: requests.Response) -> None:
    h = response.headers
    if v := h.get("X-HubSpot-RateLimit-Daily"):
        _rate_limit_state["daily_limit"] = int(v)
    if v := h.get("X-HubSpot-RateLimit-Daily-Remaining"):
        _rate_limit_state["daily_remaining"] = int(v)
    if v := h.get("X-HubSpot-RateLimit-Interval-Milliseconds"):
        _rate_limit_state["window_ms"] = int(v)
    if v := h.get("X-HubSpot-RateLimit-Max"):
        _rate_limit_state["window_max"] = int(v)
    if v := h.get("X-HubSpot-RateLimit-Remaining"):
        _rate_limit_state["window_remaining"] = int(v)

    pct = 1 - (_rate_limit_state["daily_remaining"] / _rate_limit_state["daily_limit"])
    logger.info(json.dumps({
        "event": "hubspot_rate_limit_state",
        "daily_remaining": _rate_limit_state["daily_remaining"],
        "daily_limit": _rate_limit_state["daily_limit"],
        "daily_pct_used": round(pct, 4),
        "window_remaining": _rate_limit_state["window_remaining"],
    }))


def hubspot_fetch(
    path: str,
    method: str = "GET",
    payload: dict | None = None,
    bucket: TokenBucket | None = None,
    max_attempts: int = 5,
    base_delay_s: float = 0.5,
) -> dict:
    """
    Make a HubSpot API call with token-bucket gating, Retry-After honoring,
    and exponential-backoff fallback.
    """
    token = os.environ["HUBSPOT_ACCESS_TOKEN"]
    url = f"{HUBSPOT_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, max_attempts + 1):
        if bucket:
            bucket.acquire()

        resp = requests.request(
            method, url, headers=headers,
            data=json.dumps(payload) if payload else None,
        )
        _update_rate_limit_state(resp)

        if resp.ok:
            return resp.json()

        retryable = resp.status_code == 429 or (500 <= resp.status_code < 600)
        if not retryable or attempt == max_attempts:
            resp.raise_for_status()

        retry_after = parse_retry_after_seconds(resp)
        if retry_after is not None:
            delay = retry_after
        else:
            import random
            cap = 60.0
            delay = random.random() * min(cap, base_delay_s * (2 ** attempt))

        logger.warning(json.dumps({
            "event": "hubspot_retry",
            "status": resp.status_code,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "delay_s": round(delay, 2),
            "retry_after_header": resp.headers.get("Retry-After"),
            "path": path,
        }))
        time.sleep(delay)

    raise RuntimeError("unreachable")
```

## Python: Batch Chunker and Batch Read Wrapper

```python
from typing import TypeVar, Iterator

T = TypeVar("T")
BATCH_SIZE = 100  # HubSpot hard limit


def chunk(lst: list[T], size: int = BATCH_SIZE) -> Iterator[list[T]]:
    """Yield successive chunks of at most `size` elements."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def batch_read(
    object_type: str,
    ids: list[str],
    properties: list[str],
    id_property: str = "hs_object_id",
    bucket: TokenBucket | None = None,
) -> dict:
    """
    Read up to len(ids) CRM records using the batch/read endpoint.

    Automatically chunks ids into groups of 100. Each group costs 1 quota unit.
    Returns {"results": [...], "errors": [...]} aggregated across all chunks.
    """
    all_results: list[dict] = []
    all_errors: list[dict] = []

    for batch_ids in chunk(ids):
        payload = {
            "inputs": [{"id": i} for i in batch_ids],
            "properties": properties,
            "idProperty": id_property,
        }
        body = hubspot_fetch(
            f"/crm/v3/objects/{object_type}/batch/read",
            method="POST",
            payload=payload,
            bucket=bucket,
        )
        all_results.extend(body.get("results", []))
        all_errors.extend(body.get("errors", []))

    return {"results": all_results, "errors": all_errors}


def batch_upsert(
    object_type: str,
    inputs: list[dict],   # each: {"idProperty": "email", "id": "...", "properties": {}}
    bucket: TokenBucket | None = None,
) -> dict:
    """
    Upsert records in chunks of 100. Merges results and errors across chunks.
    """
    all_results: list[dict] = []
    all_errors: list[dict] = []

    for batch_inputs in chunk(inputs):
        body = hubspot_fetch(
            f"/crm/v3/objects/{object_type}/batch/upsert",
            method="POST",
            payload={"inputs": batch_inputs},
            bucket=bucket,
        )
        all_results.extend(body.get("results", []))
        all_errors.extend(body.get("errors", []))

    return {"results": all_results, "errors": all_errors}
```

## Bull/Redis Queue Architecture

For multi-process deployments (multiple API servers, Kubernetes pods, or long-running ETL workers) where the token bucket cannot be shared in-process, route all HubSpot calls through a single Bull queue with per-worker concurrency limits.

### Queue producer (TypeScript)

```typescript
import { Queue } from "bullmq";
import IORedis from "ioredis";

const redis = new IORedis({
  host: process.env.REDIS_HOST ?? "localhost",
  port: parseInt(process.env.REDIS_PORT ?? "6379"),
  maxRetriesPerRequest: null, // required for BullMQ
});

export const hubspotQueue = new Queue("hubspot-api", {
  connection: redis,
  defaultJobOptions: {
    attempts: 5,
    backoff: { type: "exponential", delay: 1000 },
    removeOnComplete: { count: 500 },
    removeOnFail: { count: 2000 },
  },
});

// Helper — add a batch read job and wait for the result
export async function enqueueBatchRead(
  objectType: string,
  ids: string[],
  properties: string[],
  priority: "critical" | "high" | "normal" | "low" = "normal",
): Promise<{ results: unknown[]; errors: unknown[] }> {
  const priorityMap = { critical: 1, high: 10, normal: 20, low: 40 };

  const job = await hubspotQueue.add(
    "batch-read",
    { operation: "batch-read", objectType, payload: { ids, properties }, priority },
    { priority: priorityMap[priority] },
  );

  const result = await job.waitUntilFinished(
    new (await import("bullmq")).QueueEvents("hubspot-api", { connection: redis }),
    30_000, // 30s timeout
  );
  return result;
}
```

### Queue worker (TypeScript)

```typescript
import { Worker, Job } from "bullmq";
import IORedis from "ioredis";
import { acquireToken, assertDailyQuotaAvailable, hubspotFetch } from "../hubspot-client";

const redis = new IORedis({
  host: process.env.REDIS_HOST ?? "localhost",
  maxRetriesPerRequest: null,
});

const worker = new Worker(
  "hubspot-api",
  async (job: Job) => {
    const { operation, objectType, payload, priority } = job.data;

    // Daily quota gate
    assertDailyQuotaAvailable(priority ?? "normal");

    // Token bucket gate (per-worker; not shared across replicas)
    await acquireToken();

    switch (operation) {
      case "batch-read": {
        const chunks = chunk(payload.ids, 100);
        const results: unknown[] = [];
        const errors: unknown[] = [];
        for (const batch of chunks) {
          await acquireToken(); // one slot per batch
          const res = await hubspotFetch(`/crm/v3/objects/${objectType}/batch/read`, {
            method: "POST",
            body: JSON.stringify({
              inputs: batch.map((id: string) => ({ id })),
              properties: payload.properties,
            }),
          });
          const body = await res.json();
          results.push(...(body.results ?? []));
          errors.push(...(body.errors ?? []));
        }
        return { results, errors };
      }
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }
  },
  {
    connection: redis,
    concurrency: 5,        // 5 in-flight requests per worker replica
    limiter: {
      max: 90,             // 90 jobs per duration (10% headroom below the 100/10s limit)
      duration: 10_000,    // per 10 seconds
    },
  },
);

worker.on("active", (job) =>
  console.log(JSON.stringify({ event: "job_active", id: job.id, name: job.name })),
);
worker.on("completed", (job) =>
  console.log(JSON.stringify({ event: "job_completed", id: job.id })),
);
worker.on("failed", (job, err) =>
  console.error(JSON.stringify({ event: "job_failed", id: job?.id, error: err.message })),
);
```

### Celery + Redis (Python queue alternative)

```python
from celery import Celery
import os

app = Celery(
    "hubspot_tasks",
    broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,           # re-queue on worker crash
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # one task at a time per worker — honors rate limit
    task_routes={
        "hubspot_tasks.batch_read": {"queue": "hubspot-high"},
        "hubspot_tasks.batch_sync": {"queue": "hubspot-low"},
    },
)

_bucket = make_bucket_for_plan(os.environ.get("HUBSPOT_PLAN_TIER", "starter"))

@app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=5,
)
def batch_read_task(self, object_type: str, ids: list[str], properties: list[str]) -> dict:
    _bucket.acquire()  # block until token available
    return batch_read(object_type, ids, properties, bucket=None)  # bucket already acquired
```

## Daily Quota Monitor and Dashboard Metrics

Instrument these metrics to get an operational dashboard. Wire to Datadog, Prometheus, or CloudWatch.

```typescript
// Structured log events — parseable by all major log aggregators
interface QuotaMetricEvent {
  event: "hubspot_quota_tick";
  ts: string;              // ISO-8601
  daily_limit: number;
  daily_remaining: number;
  daily_pct_used: number;  // 0.00–1.00
  daily_pct_remaining: number;
  window_max: number;
  window_remaining: number;
  window_pct_used: number;
  plan_tier: string;
  shutoff_active: boolean;
  shutoff_priority_shed: string | null;  // "low" | "normal" | "high" | null
}

export function emitQuotaMetrics(state: RateLimitState, planTier: string): void {
  const pctUsed = 1 - (state.dailyRemaining / state.dailyLimit);
  const windowPctUsed = 1 - (state.windowRemaining / state.windowMax);

  const shedPriority =
    pctUsed >= 0.99 ? "high" :
    pctUsed >= 0.95 ? "normal" :
    pctUsed >= 0.90 ? "low" :
    pctUsed >= 0.80 ? "low" :
    null;

  const evt: QuotaMetricEvent = {
    event: "hubspot_quota_tick",
    ts: new Date().toISOString(),
    daily_limit: state.dailyLimit,
    daily_remaining: state.dailyRemaining,
    daily_pct_used: parseFloat(pctUsed.toFixed(4)),
    daily_pct_remaining: parseFloat((1 - pctUsed).toFixed(4)),
    window_max: state.windowMax,
    window_remaining: state.windowRemaining,
    window_pct_used: parseFloat(windowPctUsed.toFixed(4)),
    plan_tier: planTier,
    shutoff_active: pctUsed >= 0.80,
    shutoff_priority_shed: shedPriority,
  };

  console.log(JSON.stringify(evt));

  // Prometheus-compatible output (if using prom-client)
  // hubspot_daily_quota_remaining.set(state.dailyRemaining);
  // hubspot_window_remaining.set(state.windowRemaining);
  // hubspot_daily_pct_used.set(pctUsed);
}

// Emit quota metrics every 60 seconds in addition to per-request updates
setInterval(() => {
  emitQuotaMetrics(rateLimitState, activePlanTier);
}, 60_000);
```

**Recommended alerts:**

| Alert | Condition | Severity |
|---|---|---|
| Quota approaching shutoff | `daily_pct_used >= 0.80` | Warning |
| Normal jobs shedding | `daily_pct_used >= 0.90` | Warning |
| High priority jobs shedding | `daily_pct_used >= 0.95` | Critical |
| Daily quota nearly exhausted | `daily_pct_used >= 0.99` | Critical |
| Burst window at zero | `window_remaining == 0` consecutive for 3+ ticks | Warning |
| Retry storm detected | 429 rate > 10% of calls in a 5-minute window | Critical |

## Rate-Limit Dashboard Cron (Python)

A cron-safe script that emits current state and can feed a dashboard or on-call alert. Safe to run every 60 seconds — uses exactly 1 quota unit per run.

```python
#!/usr/bin/env python3
"""
hubspot-quota-monitor.py

Run every 60s via cron or Kubernetes CronJob.
Emits structured JSON to stdout; route to your log aggregator.
Exit code 0 = healthy, 1 = shutoff threshold reached (alerts on non-zero).
"""
import os
import sys
import json
import time
import requests

HUBSPOT_TOKEN = os.environ["HUBSPOT_ACCESS_TOKEN"]
PLAN_DAILY_LIMIT = int(os.environ.get("HUBSPOT_DAILY_LIMIT", "500000"))
WARN_PCT = float(os.environ.get("HUBSPOT_QUOTA_WARN_PCT", "0.80"))
CRITICAL_PCT = float(os.environ.get("HUBSPOT_QUOTA_CRITICAL_PCT", "0.90"))

def probe() -> dict:
    r = requests.get(
        "https://api.hubapi.com/crm/v3/objects/contacts",
        headers={"Authorization": f"Bearer {HUBSPOT_TOKEN}"},
        params={"limit": 1},
        timeout=10,
    )
    r.raise_for_status()
    h = r.headers

    daily_limit     = int(h.get("X-HubSpot-RateLimit-Daily", PLAN_DAILY_LIMIT))
    daily_remaining = int(h.get("X-HubSpot-RateLimit-Daily-Remaining", daily_limit))
    window_ms       = int(h.get("X-HubSpot-RateLimit-Interval-Milliseconds", 10000))
    window_max      = int(h.get("X-HubSpot-RateLimit-Max", 100))
    window_rem      = int(h.get("X-HubSpot-RateLimit-Remaining", window_max))

    pct_used = round(1 - (daily_remaining / daily_limit), 4)

    status = (
        "critical" if pct_used >= CRITICAL_PCT else
        "warn"     if pct_used >= WARN_PCT     else
        "ok"
    )

    return {
        "event": "hubspot_quota_tick",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "daily_limit": daily_limit,
        "daily_remaining": daily_remaining,
        "daily_pct_used": pct_used,
        "window_ms": window_ms,
        "window_max": window_max,
        "window_remaining": window_rem,
        "status": status,
    }

if __name__ == "__main__":
    try:
        state = probe()
        print(json.dumps(state))
        sys.exit(1 if state["status"] == "critical" else 0)
    except Exception as e:
        print(json.dumps({"event": "hubspot_quota_probe_error", "error": str(e)}))
        sys.exit(2)
```

## Testing Rate-Limit Logic Without Burning Production Quota

Test token-bucket and retry behavior using a local mock server instead of hitting the HubSpot API.

```typescript
// vitest / jest test: verify token bucket blocks correctly
import { describe, it, expect, vi } from "vitest";
import { TokenBucket } from "../hubspot-client";

describe("TokenBucket", () => {
  it("returns 0 wait when tokens are available", () => {
    const bucket = new TokenBucket(100, 10 / 10_000);
    expect(bucket.consume(1)).toBe(0);
  });

  it("returns positive wait when bucket is empty", () => {
    const bucket = new TokenBucket(1, 10 / 10_000);
    bucket.consume(1); // drain
    const wait = bucket.consume(1);
    expect(wait).toBeGreaterThan(0);
  });

  it("does not exceed capacity on refill", () => {
    const bucket = new TokenBucket(100, 10 / 10_000);
    bucket.consume(50); // drain half
    // Simulate 10s elapsed — would add 100 tokens but cap at capacity
    vi.setSystemTime(Date.now() + 10_000);
    expect(bucket.available).toBeLessThanOrEqual(100);
    vi.useRealTimers();
  });
});

// Mock server for 429 retry testing (msw)
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

let callCount = 0;

const mockServer = setupServer(
  http.get("https://api.hubapi.com/crm/v3/objects/contacts", () => {
    callCount++;
    if (callCount <= 2) {
      return new HttpResponse(
        JSON.stringify({ status: "error", errorType: "RATE_LIMIT" }),
        {
          status: 429,
          headers: { "Retry-After": "1", "X-HubSpot-RateLimit-Daily-Remaining": "499000" },
        },
      );
    }
    return HttpResponse.json({ results: [], total: 0 });
  }),
);

describe("hubspotFetch retry behavior", () => {
  beforeAll(() => mockServer.listen());
  afterAll(() => mockServer.close());
  beforeEach(() => { callCount = 0; });

  it("retries on 429 and succeeds on third attempt", async () => {
    const res = await hubspotFetch("/crm/v3/objects/contacts?limit=1");
    const body = await res.json();
    expect(body.results).toEqual([]);
    expect(callCount).toBe(3);
  });
});
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `HUBSPOT_ACCESS_TOKEN` | yes | — | Private app token or OAuth access token |
| `HUBSPOT_PLAN_TIER` | no | `starter` | `starter`, `professional`, or `ops_hub_enterprise` |
| `HUBSPOT_DAILY_LIMIT` | no | `500000` | Override if portal has API add-on (1,000,000) |
| `HUBSPOT_QUOTA_WARN_PCT` | no | `0.80` | Fraction consumed before warning alert |
| `HUBSPOT_QUOTA_CRITICAL_PCT` | no | `0.90` | Fraction consumed before critical alert / shutoff |
| `REDIS_HOST` | no (queue only) | `localhost` | Redis host for Bull queue |
| `REDIS_PORT` | no (queue only) | `6379` | Redis port |
| `REDIS_URL` | no (Celery only) | `redis://localhost:6379/0` | Redis connection URL for Celery broker/backend |
