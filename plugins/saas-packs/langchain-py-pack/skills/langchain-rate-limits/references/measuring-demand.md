# Measuring Demand

Pick `requests_per_second` from data, not vibes. Undersize and you leave throughput on the table; oversize and you 429 under peak.

## What to measure

| Metric | Why | Where to get it |
|---|---|---|
| p50 and p95 RPS | Sizing target — size for p95, not p50 | Callback hit rate over time |
| p50 and p95 input tokens | ITPM binding check (Anthropic) | `response_metadata["token_usage"]["input_tokens"]` |
| p50 and p95 output tokens | OTPM binding check | `response_metadata["token_usage"]["output_tokens"]` |
| Cache hit rate (Anthropic) | Cached-read ITPM separation (P31) | `cache_read_input_tokens` |
| Retry rate | Inflates effective RPS (see backoff-and-retry.md) | Count `on_llm_start` vs logical invocations |
| Wait time at limiter | Detects oversubscribed limit | Instrument `acquire()` duration |

## Quick-and-dirty instrumentation callback

Drop-in for any LangChain chain. Logs one JSON line per call; roll up offline.

```python
from langchain_core.callbacks import BaseCallbackHandler
import time
import json
from uuid import uuid4

class DemandLogger(BaseCallbackHandler):
    def __init__(self, sink=print):
        self.sink = sink
        self._starts = {}  # run_id -> (start_time, model_name)

    def on_llm_start(self, serialized, prompts, run_id=None, **kwargs):
        rid = str(run_id or uuid4())
        self._starts[rid] = (time.time(), serialized.get("name"))

    def on_llm_end(self, response, run_id=None, **kwargs):
        rid = str(run_id or "")
        started, model = self._starts.pop(rid, (time.time(), None))
        usage = {}
        for gen_list in response.generations:
            for gen in gen_list:
                if hasattr(gen.message, "usage_metadata"):
                    usage = gen.message.usage_metadata or {}
                    break
        self.sink(json.dumps({
            "ts": time.time(),
            "model": model,
            "latency_s": round(time.time() - started, 3),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cache_read": usage.get("cache_read_input_tokens", 0),
            "cache_write": usage.get("cache_creation_input_tokens", 0),
        }))

    def on_llm_error(self, error, run_id=None, **kwargs):
        rid = str(run_id or "")
        self._starts.pop(rid, None)
        self.sink(json.dumps({
            "ts": time.time(),
            "error": type(error).__name__,
            "message": str(error)[:200],
        }))
```

Attach once at chain level: `chain.with_config({"callbacks": [DemandLogger()]})`. Collect 24-48 hours of representative traffic before sizing.

## OTEL integration

For teams on OpenTelemetry, use LangChain's built-in OTEL exporter instead of the DIY callback above:

```python
import os
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://otel-collector:4318"
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "false"  # P27 — privacy
```

Emits `gen_ai.request.*` and `gen_ai.response.usage.*` spans per Semantic Conventions. Query RPM from trace count over time, TPM from `usage.input_tokens` sum.

## Roll-up query (pandas)

Assume `DemandLogger` output is in `logs.jsonl`:

```python
import pandas as pd

df = pd.read_json("logs.jsonl", lines=True)
df = df.dropna(subset=["input_tokens"])  # drop error rows
df["ts_min"] = pd.to_datetime(df["ts"], unit="s").dt.floor("1min")

per_min = df.groupby("ts_min").agg(
    rpm=("input_tokens", "count"),
    itpm=("input_tokens", "sum"),
    otpm=("output_tokens", "sum"),
    cache_read=("cache_read", "sum"),
)

print("p50 RPM:", per_min["rpm"].quantile(0.5))
print("p95 RPM:", per_min["rpm"].quantile(0.95))
print("p95 ITPM:", per_min["itpm"].quantile(0.95))
print("p95 OTPM:", per_min["otpm"].quantile(0.95))
print("cache hit rate:", per_min["cache_read"].sum() / per_min["itpm"].sum())
```

Compare the p95 numbers against your tier's RPM / ITPM / OTPM ceilings. The first one that exceeds is your binding constraint — size the limiter for that one.

## Size the limiter on p95, not p50

A p50-sized limiter handles average traffic but queues hard on spikes. A p95-sized limiter handles 95% of minutes without queuing. p99 sizing burns money on unused capacity.

```
target_rps = (tier_rpm * 0.7 / 60)       # use 70% of tier as the SLO
observed_p95_rps = df.rpm.quantile(0.95) / 60

if observed_p95_rps <= target_rps:
    # You have headroom. Set limiter to target_rps.
    requests_per_second = target_rps
else:
    # Traffic exceeds tier. Upgrade tier, or shed load (queue, reject, degrade).
    raise TierExceeded(observed_p95_rps, target_rps)
```

## Load test template

Before production rollout, run a synthetic load test at 1.5x your p95 demand to validate the limiter holds:

```python
import asyncio
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    rate_limiter=redis_limiter,  # production limiter
    max_retries=2,
)

async def hammer(n, rps):
    """Fire n requests at target RPS. Returns (succeeded, rate_limited, latencies)."""
    sem = asyncio.Semaphore(int(rps * 5))  # enough slack for latency
    latencies = []
    errors = 0
    async def one(i):
        nonlocal errors
        t0 = time.time()
        try:
            async with sem:
                await llm.ainvoke(f"Test {i}")
            latencies.append(time.time() - t0)
        except Exception as e:
            errors += 1
    tasks = [asyncio.create_task(one(i)) for i in range(n)]
    await asyncio.gather(*tasks, return_exceptions=True)
    return len(latencies), errors, latencies

succeeded, errored, lat = asyncio.run(hammer(n=600, rps=10))
print(f"ok={succeeded} errors={errored} p50={sorted(lat)[len(lat)//2]:.2f}s")
```

Accept: zero 429s surfaced to caller (limiter absorbed them), p95 latency within SLO, no head-of-line blocking (longest wait < `timeout`).

Reject: any 429 escapes → limiter is too loose, or provider tier is lower than believed. Re-measure.

## Multi-tenant sizing

If your traffic is multi-tenant, the same RPS number across tenants does not imply the same limit. Three strategies:

1. **Per-tenant hard quota** — Each tenant gets a fixed slice (10 RPM each, up to tenant cap). Simple, wastes capacity when tenants are idle.
2. **Per-tenant soft + global hard** — Per-tenant limit prevents noisy neighbors; global limit protects the provider tier. Two-level Redis acquire (see redis-limiter-pattern.md). Best for most SaaS.
3. **Global only with per-tenant accounting** — Single cluster-wide limit, but dashboards break it down by tenant. Fair under low contention; unfair when one tenant hogs.

Measure per-tenant RPM separately before picking. A long-tail distribution (one tenant = 80% of traffic) argues for strategy 2.

## Re-measure on every:

- Product launch (new endpoint, new feature)
- Marketing campaign (traffic spike)
- Provider tier change (more headroom, re-tune)
- Model change (different TPM shape — `gpt-4o` vs `gpt-4o-mini`)
- Prompt redesign (different input token count)
- Caching change (cache hit rate shift)

A limiter set six months ago on a different model is a liability, not a safety net.

## Cross-references

- [Provider Tier Matrix](provider-tier-matrix.md) — which tier's numbers you are sizing against
- [Redis Limiter Pattern](redis-limiter-pattern.md) — what to configure with your measured `requests_per_second`
- [Backoff and Retry](backoff-and-retry.md) — how retries inflate your effective RPS and what to budget
