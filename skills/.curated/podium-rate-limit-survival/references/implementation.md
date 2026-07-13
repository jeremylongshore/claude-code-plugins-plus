# Implementation Reference — podium-rate-limit-survival

Language-portability layer plus counter-store wiring plus the on-call playbook for a 429 cascade in progress.

## Node.js / TypeScript port

The Python `TokenBucket` translates to TypeScript directly. The async semantics map cleanly — `asyncio.Lock` becomes a single-flight promise; `asyncio.sleep` becomes `setTimeout` wrapped in a promise.

```typescript
export class TokenBucket {
  private tokens: number;
  private lastRefill: number;
  private waiters: Array<() => void> = [];

  constructor(
    private readonly ratePerSec: number,
    private readonly capacity: number,
  ) {
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }

  async acquire(n: number = 1): Promise<void> {
    while (true) {
      this.refill();
      if (this.tokens >= n) {
        this.tokens -= n;
        return;
      }
      const deficit = n - this.tokens;
      const waitMs = (deficit / this.ratePerSec) * 1000;
      await new Promise<void>((res) => setTimeout(res, waitMs));
    }
  }

  private refill(): void {
    const now = Date.now();
    const elapsedSec = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.capacity, this.tokens + elapsedSec * this.ratePerSec);
    this.lastRefill = now;
  }
}

export function parseRetryAfter(header: string): number {
  const trimmed = header.trim();
  // Integer seconds
  const asInt = parseInt(trimmed, 10);
  if (!isNaN(asInt) && String(asInt) === trimmed) {
    return Math.max(0, asInt);
  }
  // HTTP-date — RFC 7231
  const parsed = Date.parse(trimmed);
  if (!isNaN(parsed)) {
    return Math.max(0, (parsed - Date.now()) / 1000);
  }
  return 60;   // safe default on malformed
}
```

The Node version does not need an explicit lock — the single-threaded event loop serializes the `refill()` + decrement sequence implicitly. The same is **not** true under Worker Threads; if you fan a single bucket across workers, you must add explicit synchronization (atomics on `SharedArrayBuffer`, or move the bucket to Redis).

## Counter-store integrations

### Redis (preferred)

```python
import redis.asyncio as aioredis
from datetime import datetime, timezone

class RedisQuotaCounter:
    def __init__(self, redis_url: str):
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    def _key(self) -> str:
        return f"podium:quota:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    async def increment(self, n: int = 1) -> int:
        key = self._key()
        new = await self._redis.incr(key, n)
        if new == n:
            # First write of the day — set TTL to UTC midnight + 1h grace
            now = datetime.now(timezone.utc)
            tomorrow_utc_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_utc_midnight = tomorrow_utc_midnight.replace(day=now.day + 1)
            seconds_until = int((tomorrow_utc_midnight - now).total_seconds()) + 3600
            await self._redis.expire(key, seconds_until)
        return new

    async def current(self) -> int:
        return int(await self._redis.get(self._key()) or 0)
```

Redis is the canonical choice — INCR is atomic, key TTLs handle the daily reset automatically, and multiple processes share the same counter without coordination. ElastiCache, Memorystore, Upstash, and self-hosted Redis 6+ all work without modification.

### SQLite (single-process fallback)

```python
import sqlite3
from datetime import datetime, timezone

class SQLiteQuotaCounter:
    def __init__(self, path: str):
        self._path = path
        with sqlite3.connect(path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quota (
                    day TEXT PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 0
                )
            """)

    def _today(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async def increment(self, n: int = 1) -> int:
        day = self._today()
        # SQLite doesn't have async-native bindings; the I/O is fast enough to
        # run in a thread executor for asyncio compatibility.
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._increment_sync, day, n)

    def _increment_sync(self, day: str, n: int) -> int:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "INSERT INTO quota (day, count) VALUES (?, ?) "
                "ON CONFLICT(day) DO UPDATE SET count = count + ?",
                (day, n, n),
            )
            row = conn.execute("SELECT count FROM quota WHERE day = ?", (day,)).fetchone()
            return row[0]
```

SQLite is acceptable for single-process integrations (one webhook handler, one cron driver) where the daily counter does not need to be shared. **Do not** share a SQLite file across processes for this purpose — `INSERT ... ON CONFLICT` is atomic within a connection but the write throughput collapses under concurrent writers. Use Redis instead.

### In-memory (development only)

```python
class MemoryQuotaCounter:
    def __init__(self):
        self._day = None
        self._count = 0

    async def increment(self, n: int = 1) -> int:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._day:
            self._day = today
            self._count = 0
        self._count += n
        return self._count
```

Acceptable for unit tests and local development. Resets on process restart — completely unsuitable for production.

## On-call playbook — 429 cascade in progress

The committed location is `docs/runbooks/podium-429-cascade.md`. Print this before a burst window if you have not memorized it.

### Symptoms

- Per-minute 429 rate spiking above 1% (steady state should be < 0.1%)
- Daily quota monitor warning or paging
- Customer reports of delayed review-request emails or webchat ack timeouts

### Step 1: Confirm the cascade is real

```bash
# Pull the last 5 minutes of bucket logs
grep '"event":"podium_429"' /var/log/podium-integration.log | tail -100 | jq -r '.path' | sort | uniq -c
```

If one endpoint family dominates the 429 count, the per-family bucket allocation for that family is too high. If 429s are spread evenly, the global bucket is over-allocated.

### Step 2: Engage manual throttle

```bash
# Reduce the offending family's rate to 25% of configured value
redis-cli SET "podium:throttle:reviews" "0.25" EX 7200    # 2-hour throttle
```

The bucket layer reads this key on every refill and applies the multiplier. Throttle expires automatically after 2 hours so you don't forget to release it.

### Step 3: Verify the cascade subsides

```bash
# Watch the 429 rate in real time
tail -F /var/log/podium-integration.log | grep '"event":"podium_429"' | awk '{print strftime("%H:%M:%S"), $0}'
```

The 429 rate should drop to zero within one minute (the bucket flushes its current queue at the new lower rate). If it does not drop, the throttle didn't engage — check that the bucket layer is reading the Redis throttle key correctly.

### Step 4: Check daily quota state

```bash
python3 scripts/quota_monitor.py --redis-url "$PODIUM_RATE_LIMIT_REDIS_URL" --quota 50000
# Note the exit code: 0/1/2/3 = ok/warn/page/throttle
```

If the daily quota is already at throttle (>= 95%), the integration will degrade further over the next hours regardless of per-family throttle. Page leadership and accept partial degradation until UTC midnight.

### Step 5: Postmortem

After the burst window, do not delete the throttle key prematurely — let it expire on its 2-hour TTL. Capture the bucket logs, build a request trace CSV, and run `scripts/bucket_simulator.py` against the trace with the original bucket configuration to confirm the bucket would have prevented the cascade if sized correctly. Update `config/settings.yaml` based on the simulator's recommendations.

## Library packaging notes

This skill ships the library inline in `SKILL.md` and `references/examples.md` rather than as a separate pip package. The rationale: the library is ~250 lines, every integration needs custom amplification factors and quota tuning, and an extracted package would require versioning that adds maintenance overhead without enabling reuse. If the library grows past ~700 lines or three concrete callers depend on identical configuration, promote it to `@intentsolutions/podium-rate-limit` on npm or `intent-podium-rate-limit` on PyPI.

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_token_bucket_paces_correctly` | unit | 100 concurrent acquirers at rate=60/min complete in ~100s |
| `test_token_bucket_burst_capacity` | unit | First `capacity` acquires are instant; subsequent ones pace at the rate |
| `test_parse_retry_after_int_seconds` | unit | `"30"` → 30.0; `"0"` → 0.0; `"-5"` → 0.0 (clamped) |
| `test_parse_retry_after_http_date` | unit | RFC 7231 date strings parse to correct seconds-from-now |
| `test_parse_retry_after_malformed` | unit | Garbage input returns the 60s safe default |
| `test_daily_quota_atomic_increment` | integration | 1000 concurrent `increment(1)` calls produce count = 1000 exactly |
| `test_daily_quota_ttl_on_first_write` | integration | TTL is set on the first INCR of a new UTC day |
| `test_burst_smoother_completes_in_window` | unit | 80 requests at target_window=120s complete in 120s ± 5s |
| `test_burst_smoother_respects_bucket_rate` | unit | When target_window/N < 1/rate, smoother paces at bucket rate (slower) |
| `test_admission_denies_high_cost_when_quota_low` | unit | At 95% quota consumed, an event with cost > 0.05 * 5% denies |
| `test_per_family_allocation_sum_validates` | unit | Config loader raises on sum(rates) > global ceiling |
| `test_redis_outage_falls_back_to_sqlite` | chaos | Killing Redis mid-burst engages SQLite fallback without request failures |
| `test_429_cascade_simulation` | integration | Stubbed 429 server cannot drive the bucket into a retry storm |
