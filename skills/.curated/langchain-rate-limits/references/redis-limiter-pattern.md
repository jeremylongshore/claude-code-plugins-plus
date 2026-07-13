# Redis-Backed Rate Limiter Pattern

`langchain_core.rate_limiters.InMemoryRateLimiter` is named honestly: **in-process, single-interpreter only** (pain-catalog P29). The instant you deploy more than one worker — and every modern Python deployment does — it stops enforcing the limit you think it is enforcing.

This is the Redis-backed pattern. Two implementations: a portable atomic Lua script (sliding window) and a one-liner using the Redis 6.2+ `CL.THROTTLE` command (GCRA).

## Why not just use `InMemoryRateLimiter` with `workers=1`?

One uvicorn worker on Cloud Run / GKE is a single point of failure and caps you at one CPU. Nobody ships that to production. The moment you scale to 2+ workers, `InMemoryRateLimiter` silently over-spends — N workers × `requests_per_second=10` sends N×10 RPS to the provider.

You cannot fix this by dividing: `requests_per_second=10/N` rounds to zero on small N, and N itself changes every autoscale event.

## Implementation A — Atomic Lua sliding window

Works on any Redis >= 4.0. Script is `EVALSHA`-able — load once, invoke cheaply.

```python
import time
import hashlib
import redis
from langchain_core.rate_limiters import BaseRateLimiter

# Sliding window: count requests in the last `window_s` seconds; reject if >= limit.
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', key, 0, now - window * 1000)
local count = redis.call('ZCARD', key)
if count < limit then
    redis.call('ZADD', key, now, now)
    redis.call('PEXPIRE', key, window * 1000)
    return 1
else
    return 0
end
"""

class RedisRateLimiter(BaseRateLimiter):
    def __init__(
        self,
        client: redis.Redis,
        key: str,
        requests_per_second: float,
        window_s: int = 1,
        check_every_n_seconds: float = 0.1,
    ):
        self._client = client
        self._key = f"ratelimit:{key}"
        self._limit = int(requests_per_second * window_s)
        self._window = window_s
        self._check_every = check_every_n_seconds
        self._script_sha = hashlib.sha1(SLIDING_WINDOW_LUA.encode()).hexdigest()

    def acquire(self, *, blocking: bool = True) -> bool:
        while True:
            now_ms = int(time.time() * 1000)
            try:
                allowed = self._client.evalsha(
                    self._script_sha, 1, self._key,
                    now_ms, self._window, self._limit,
                )
            except redis.exceptions.NoScriptError:
                allowed = self._client.eval(
                    SLIDING_WINDOW_LUA, 1, self._key,
                    now_ms, self._window, self._limit,
                )
            if allowed:
                return True
            if not blocking:
                return False
            time.sleep(self._check_every)

    async def aacquire(self, *, blocking: bool = True) -> bool:
        # For production, use redis.asyncio.Redis and await the eval call.
        # This sync-bridge version is acceptable for low-throughput workers.
        import asyncio
        return await asyncio.to_thread(self.acquire, blocking=blocking)
```

### Why a sorted set, not a counter?

A fixed-window counter (`INCR` + `EXPIRE`) is simpler but allows 2x burst at the window boundary — 10 requests at `t=0.999s` plus 10 more at `t=1.001s` is 20 requests in 2ms. Sliding window via sorted set prevents this by tracking each request timestamp.

### Key design: per-tenant vs global

```python
# Single key — all tenants share the provider budget
limiter = RedisRateLimiter(client, key="anthropic-tier-1", requests_per_second=50/60)

# Per-tenant — each tenant has its own 10-RPM budget
limiter = RedisRateLimiter(client, key=f"anthropic:tenant:{tenant_id}", requests_per_second=10/60)

# Hierarchical — check both, require both to allow
# (Implement by acquiring tenant key first, then global key; release tenant if global fails)
```

Per-tenant keys require a cleanup strategy — dead tenants leave sorted sets in Redis. Either use short TTLs on the keys (2× window) or run a nightly sweep.

## Implementation B — Redis GCRA (`CL.THROTTLE`)

Redis 6.2+ with the `redis-cell` module (bundled in Redis Enterprise, available as a plugin elsewhere). GCRA (Generic Cell Rate Algorithm) is the algorithm DynamoDB and Stripe use. One command, no Lua.

```python
# CL.THROTTLE key max_burst count_per_period period [quantity]
result = client.execute_command(
    "CL.THROTTLE", "anthropic:tier-1",
    50,   # max burst (bucket depth)
    50,   # count per period
    60,   # period in seconds → 50 requests per 60 seconds = Anthropic tier-1 RPM
    1,    # quantity to consume
)
# result = [allowed, total_limit, remaining, retry_after_s, reset_after_s]
allowed = result[0] == 0
retry_after_s = result[3]
```

GCRA is strictly better than sliding window for steady-state workloads (smoother, no window boundary issues) but requires the extra module. For pure open-source Redis, stick with Lua.

## Wiring into LangChain 1.0

```python
from langchain_anthropic import ChatAnthropic

client = redis.Redis.from_url("redis://redis.internal:6379/0")
limiter = RedisRateLimiter(
    client,
    key="anthropic:prod",
    requests_per_second=40 / 60,  # 40 RPM for tier 1, leave 10 RPM headroom
)

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    rate_limiter=limiter,
    max_retries=2,
    timeout=30,
)
```

`rate_limiter=` is a first-class parameter on `BaseChatModel` in LangChain 1.0 — the model calls `limiter.acquire()` before each request. You do not need to wrap the chain yourself.

## Sliding window vs fixed window vs GCRA

| Property | Fixed window | Sliding window (Lua) | GCRA (`CL.THROTTLE`) |
|---|---|---|---|
| Redis version | >= 2.6 | >= 4.0 (EVAL) | >= 6.2 + redis-cell |
| Boundary burst risk | Yes (2x limit possible) | No | No |
| Storage per key | 1 counter | N timestamps (where N=limit) | 2 floats |
| Latency | ~0.2ms | ~0.5ms | ~0.2ms |
| Fairness under contention | Poor | Fair | Fair |

For LangChain production: **GCRA if you have redis-cell, sliding-window Lua otherwise**. Do not use fixed-window — the boundary burst is exactly what gets you 429'd.

## Integration with a per-worker semaphore

Redis limits cluster RPM. `asyncio.Semaphore(20)` limits in-flight concurrency per worker. Use both:

```python
# Cluster: 40 RPM across all workers (Redis enforces)
# Worker:  20 requests in flight at once (semaphore enforces)
sem = asyncio.Semaphore(20)

async def bounded_invoke(inp):
    async with sem:
        return await llm.ainvoke(inp)
```

Semaphore prevents a single slow worker from queueing hundreds of pending acquires against the Redis limiter (which would still succeed in principle but creates head-of-line blocking on the event loop).

## Failure modes to test

1. **Redis unavailable** — `acquire()` raises `redis.ConnectionError`. Decide: fail-closed (block all LLM calls, shed load) or fail-open (bypass limit, log loudly). For provider-safety, fail-closed.
2. **Clock skew between workers** — Lua uses `redis.call('TIME')` server-side to avoid client clock drift. Our script uses client time (`now_ms = time.time()`); replace with `redis.call('TIME')` inside the Lua if workers are >1s out of sync.
3. **Limit too tight** — `blocking=True` with a tight limit causes every request to wait. Instrument `acquire()` wait time and alert if p95 > 500ms.
4. **`NoScriptError` on Redis restart** — handled in our `acquire()` with the `EVAL` fallback. Script loading on first failure costs one extra round-trip.

## Cross-references

- [Provider Tier Matrix](provider-tier-matrix.md) — which RPM / TPM to set
- [Backoff and Retry](backoff-and-retry.md) — what happens when 429s slip through anyway
- [Measuring Demand](measuring-demand.md) — how to size `requests_per_second` before picking a number
