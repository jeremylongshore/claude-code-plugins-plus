# Batch Concurrency Tuning

`chain.batch(inputs)` without `config={"max_concurrency": N}` silently
serializes on multiple providers (pain-catalog P08). This is the tuning guide
— safe ceilings, semaphore patterns, and the sync/async tradeoff.

## The default is 1

```python
# Serial — default max_concurrency is 1 on several provider packages
chain.batch(inputs_1000)   # 1000 sequential calls

# Parallel — 10 in flight at a time
chain.batch(inputs_1000, config={"max_concurrency": 10})

# Async parallel — same semantics, event-loop friendly
await chain.abatch(inputs_1000, config={"max_concurrency": 10})
```

A three-provider benchmark on 100-document summarization at `max_concurrency=1`
vs `10` typically shows 8-9x wall-clock speedup. Past 10, returns diminish
quickly because you hit rate limits.

## Safe ceilings per provider (default tier)

| Provider | RPM | TPM | Safe `max_concurrency` | Notes |
|---|---|---|---|---|
| Anthropic (Build tier) | 50 | 40K input | 5-10 | TPM is the first binding limit for long prompts |
| Anthropic (Scale tier) | 1000 | 400K input | 20-50 | Needs a semaphore once in-flight > 20 |
| OpenAI (Tier 1) | 500 | 30K | 10-20 | Tier grows with monthly spend |
| OpenAI (Tier 3+) | 5000 | 800K | 50+ | Always use a semaphore past 20 |
| Google Gemini (free) | 15 | 1M | 2-5 | RPM is brutal on free tier |
| Google Gemini (paid) | 2000 | 4M | 20-40 | TPM rarely binds |

These are **defaults** — check your organization's actual tier in the provider
console, then multiply by 0.7 to leave headroom for interactive traffic.

## Why you want a semaphore past 20

`max_concurrency=N` caps the in-flight count **per `.batch()` call**. If your
process has two batch pipelines running concurrently (say, a web handler and a
background job), both hit `max_concurrency=20` independently, so the real
in-flight count is 40 — and you trip rate limits.

```python
import asyncio

# Process-wide semaphore — all LangChain calls share it
llm_semaphore = asyncio.Semaphore(20)

async def rate_limited_abatch(chain, inputs):
    async with llm_semaphore:
        return await chain.abatch(inputs, config={"max_concurrency": 20})
```

This is still not enough on its own — the semaphore guards parallelism but not
rate-limit headers. For production, read the `retry-after` header on 429
responses and sleep.

## Reading provider rate-limit headers

LangChain's built-in `max_retries` on `ChatAnthropic` / `ChatOpenAI` already
honors `retry-after` with exponential backoff. The caveat is that six retries
(default for `ChatOpenAI`) means a single logical call can take 60+ seconds of
wall-clock. At scale, lower `max_retries=2` and push resilience to the
fallback layer — see [Fallback Exception List](fallback-exception-list.md).

## Sync `batch` vs async `abatch`

| Axis | `.batch()` | `.abatch()` |
|---|---|---|
| Blocks the event loop | Yes | No |
| Can run inside FastAPI/async LangGraph node | No | Yes |
| Handles `max_concurrency` | Yes (via thread pool) | Yes (via asyncio gather) |
| Integrates with `asyncio.Semaphore` | No | Yes |
| Needed for long-running CLI scripts | OK | OK |

Rule of thumb: if the code is in an `async def`, use `.abatch()`. If it is a
sync CLI tool or a notebook, `.batch()` is fine and saves the asyncio
boilerplate.

## Failure handling: `return_exceptions`

Default `.batch()` aborts on the first failure, losing all N-1 other results.
For idempotent bulk workloads, set `return_exceptions=True`:

```python
results = chain.batch(
    inputs,
    config={"max_concurrency": 10, "return_exceptions": True},
)

successes = [r for r in results if not isinstance(r, Exception)]
failures = [(i, r) for i, r in enumerate(results) if isinstance(r, Exception)]
# retry failures later with their original indices
```

This is the right default for ETL pipelines. It is the **wrong** default for
transactional workflows where partial success is worse than full failure.

## `max_concurrency` and tool-using chains

If your chain includes `bind_tools(...)` and the model makes tool calls,
`max_concurrency=10` means 10 conversations in flight — each of which may
issue multiple tool calls sequentially within its own thread. Total tool
invocations in flight can exceed `max_concurrency` if tools themselves do
their own batching. Instrument tool latency separately.

## Benchmark harness

```python
import time

def bench(n, max_conc):
    t0 = time.perf_counter()
    chain.batch(inputs[:n], config={"max_concurrency": max_conc})
    return time.perf_counter() - t0

for conc in (1, 5, 10, 20, 50):
    print(f"{conc:>3}: {bench(100, conc):.2f}s")
```

Run this once per provider on a representative input. The sweet spot is
usually the first number where the curve flattens — typically 10-20.
