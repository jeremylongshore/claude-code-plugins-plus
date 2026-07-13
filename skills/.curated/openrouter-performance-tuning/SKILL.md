---
name: openrouter-performance-tuning
description: 'Optimize OpenRouter request latency and throughput. Use when building
  real-time applications, reducing TTFT, or scaling request volume. Triggers: ''openrouter
  performance'', ''openrouter latency'', ''openrouter speed'', ''optimize openrouter
  throughput''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- performance
- latency
- optimization
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Performance Tuning

## Overview

OpenRouter adds minimal overhead (~50-100ms) to direct provider calls. Most latency comes from the upstream model. Key levers: model selection (smaller = faster), streaming (lower TTFT), parallel requests, prompt size reduction, and provider routing to faster infrastructure. This skill covers benchmarking, streaming optimization, concurrent processing, and connection tuning.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with the OpenAI SDK (`openai` package) — the examples use both the sync `OpenAI` client and `AsyncOpenAI` for parallel processing
- Credits on the key if you benchmark paid models like `anthropic/claude-3.5-sonnet`; a `:free` model is enough to validate the benchmark harness itself
- `HTTP-Referer` / `X-Title` header values for your app (set in every client constructor here)

## Instructions

1. Establish a baseline: run `benchmark_model()` from Benchmark Latency against your candidate models (e.g. `openai/gpt-4o-mini` vs `anthropic/claude-3.5-sonnet`) and record p50/p95.
2. Check the results against the Model Speed Tiers table to confirm each candidate sits in the right tier for your latency budget (200-500ms TTFT fastest tier; 5-30s for reasoning models).
3. Switch user-facing paths to `stream_completion()` per Streaming for Lower TTFT and verify `ttft_ms` drops (typically 2-10x).
4. Move batch workloads to `parallel_completions()` per Parallel Request Processing, capping concurrency with `asyncio.Semaphore` (`max_concurrent=5-10`).
5. Apply Connection Optimization — one shared client with `timeout=30.0` and `max_retries=2` instead of a new client per request.
6. Work through the Performance Optimization Checklist (set `max_tokens`, shrink prompts, consider `:nitro` variants and provider routing), then re-run the benchmark to quantify each change.

## Benchmark Latency

```python
import os, time, statistics
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

def benchmark_model(model: str, prompt: str = "Say hello", n: int = 5) -> dict:
    """Benchmark a model's latency over N requests."""
    latencies = []
    for _ in range(n):
        start = time.monotonic()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        latencies.append((time.monotonic() - start) * 1000)

    return {
        "model": model,
        "p50_ms": round(statistics.median(latencies)),
        "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)]),
        "avg_ms": round(statistics.mean(latencies)),
        "min_ms": round(min(latencies)),
        "max_ms": round(max(latencies)),
    }

# Compare fast vs slow models
for model in ["openai/gpt-4o-mini", "anthropic/claude-3-haiku", "anthropic/claude-3.5-sonnet"]:
    result = benchmark_model(model)
    print(f"{result['model']}: p50={result['p50_ms']}ms p95={result['p95_ms']}ms")
```

## Streaming for Lower TTFT

```python
def stream_completion(messages, model="openai/gpt-4o-mini", **kwargs):
    """Stream response for lower time-to-first-token."""
    start = time.monotonic()
    first_token_time = None
    full_content = []

    stream = client.chat.completions.create(
        model=model, messages=messages, stream=True,
        stream_options={"include_usage": True},  # Get token counts at end
        **kwargs,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            if first_token_time is None:
                first_token_time = (time.monotonic() - start) * 1000
            full_content.append(chunk.choices[0].delta.content)

    total_time = (time.monotonic() - start) * 1000
    return {
        "content": "".join(full_content),
        "ttft_ms": round(first_token_time or 0),
        "total_ms": round(total_time),
    }
```

## Parallel Request Processing

```python
import asyncio
from openai import AsyncOpenAI

async def parallel_completions(prompts: list[str], model="openai/gpt-4o-mini",
                                max_concurrent=10, **kwargs):
    """Process multiple prompts concurrently."""
    semaphore = asyncio.Semaphore(max_concurrent)
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
    )

    async def process(prompt):
        async with semaphore:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response.choices[0].message.content

    return await asyncio.gather(*[process(p) for p in prompts])

# 10 requests in parallel instead of sequential
results = asyncio.run(parallel_completions(
    ["Summarize: " + text for text in documents],
    max_concurrent=5,
    max_tokens=200,
))
```

## Performance Optimization Checklist

| Optimization | Impact | Effort |
|-------------|--------|--------|
| Use streaming | TTFT drops 2-10x | Low |
| Use smaller models for simple tasks | 2-5x faster | Low |
| Reduce prompt size | Proportional to reduction | Medium |
| Set `max_tokens` | Caps response time | Low |
| Parallel requests | N requests in ~1 request time | Medium |
| Use `:nitro` variant | Faster inference (where available) | Low |
| Provider routing to fastest | 10-30% latency reduction | Low |
| Connection keep-alive | Saves TCP/TLS handshake | Low |

## Model Speed Tiers

| Speed | Models | Typical TTFT |
|-------|--------|-------------|
| Fastest | `openai/gpt-4o-mini`, `anthropic/claude-3-haiku` | 200-500ms |
| Fast | `openai/gpt-4o`, `google/gemini-2.0-flash-001` | 500ms-1s |
| Standard | `anthropic/claude-3.5-sonnet` | 1-3s |
| Slow | `openai/o1`, reasoning models | 5-30s |

## Connection Optimization

```text
# Reuse client instance (connection pooling)
# BAD: creating new client per request
for prompt in prompts:
    c = OpenAI(base_url="https://openrouter.ai/api/v1", ...)  # New TCP connection each time
    c.chat.completions.create(...)

# GOOD: reuse single client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    timeout=30.0,           # Set appropriate timeout
    max_retries=2,          # Built-in retry with backoff
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)
for prompt in prompts:
    client.chat.completions.create(...)  # Reuses HTTP connection
```

## Output

- A latency benchmark table per model from `benchmark_model()`: `p50_ms`, `p95_ms`, `avg_ms`, `min_ms`, `max_ms` over N sample requests
- Streaming metrics from `stream_completion()`: the full `content` plus `ttft_ms` and `total_ms` for each request
- A list of completions from `parallel_completions()` produced in roughly one request's wall-clock time instead of N sequential round-trips
- A prioritized tuning plan drawn from the Performance Optimization Checklist (lever, expected impact, effort)

## Examples

Benchmark two fastest-tier candidates before committing to one:

```python
for model in ["openai/gpt-4o-mini", "anthropic/claude-3-haiku"]:
    r = benchmark_model(model, n=5)
    print(f"{r['model']}: p50={r['p50_ms']}ms p95={r['p95_ms']}ms avg={r['avg_ms']}ms")
# openai/gpt-4o-mini: p50=430ms p95=610ms avg=455ms
# anthropic/claude-3-haiku: p50=395ms p95=580ms avg=418ms
```

Both land in the fastest tier (200-500ms typical TTFT), so choose on cost or quality — then `stream_completion()` cuts perceived latency further for user-facing paths. More worked examples: `references/examples.md`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| High TTFT (>5s) | Model cold-starting or overloaded | Switch to `:nitro` variant or different provider |
| Timeout errors | max_tokens too high or model too slow | Reduce max_tokens; use streaming; increase timeout |
| Throughput bottleneck | Sequential processing | Use async + semaphore for concurrent requests |
| Inconsistent latency | Provider load varies | Use `provider.order` to pin to fastest provider |

## Enterprise Considerations

- Benchmark models in your infrastructure, not just locally -- network path matters
- Use streaming for all user-facing requests to minimize perceived latency
- Set `max_tokens` on every request to bound response time and cost
- Reuse client instances to benefit from HTTP connection pooling
- Use `asyncio.Semaphore` to control concurrency and avoid overwhelming the API
- Monitor P95 latency, not just average -- tail latencies indicate provider issues
- Consider `:nitro` model variants for latency-critical paths

## References

- Examples | Errors
- [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models) | Streaming
