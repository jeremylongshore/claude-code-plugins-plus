# Batch Concurrency Per Provider

## The P08 Trap

`Runnable.batch(inputs)` and `.abatch(inputs)` in LangChain 1.0 default to `max_concurrency=1`. They loop inputs sequentially with extra bookkeeping — sometimes *slower* than a plain `for` loop.

```python
# WRONG — this is serial plus overhead
results = await chain.abatch(inputs)

# RIGHT — explicit parallelism
results = await chain.abatch(
    inputs,
    config={"max_concurrency": 10},
)
```

LangChain docs: `https://python.langchain.com/docs/how_to/streaming/#batching`.

## Per-Provider Safe Concurrency Table

Baseline values. Always confirm against your account's posted RPM/TPM and then load-test.

| Provider | Tier assumption | Safe `max_concurrency` starting point | Ceiling signal |
|----------|------------------|----------------------------------------|----------------|
| Anthropic (claude-sonnet-4.5 / 4.6) | Tier 2-3 | 10-20 | `429 rate_limit_error` or rising `retry-after` headers |
| OpenAI (gpt-4o / 4o-mini) | Tier 3-4 | 20-50 | `429` + TPM exhaustion in header |
| OpenAI (o1 / reasoning) | Any | 2-5 | Cost + latency, not rate limits |
| Azure OpenAI | PTU | From deployment quota | Quota saturation in metrics |
| Google Gemini 1.5/2.5 | Paid | 10-30 | 429 or quota exceeded |
| Cohere | Production | 20-40 | 429 |
| Local vLLM / TGI | GPU-bound | 100-500 (batch sweet spot ~N=32-64 on A100) | GPU KV-cache OOM |
| Self-hosted Ollama | Consumer GPU | 1-4 | Process queue backpressure |

## Measuring Saturation

1. Sweep `max_concurrency` at 1, 5, 10, 20, 40 against a fixed 200-input workload.
2. Record p50, p95 total latency and total cost.
3. Plot throughput vs concurrency. The curve flattens — pick the knee, not the peak.
4. Subtract 20% headroom for traffic spikes.

```python
import asyncio, time

async def sweep(chain, inputs, levels=(1, 5, 10, 20, 40)):
    for n in levels:
        t0 = time.perf_counter()
        await chain.abatch(inputs, config={"max_concurrency": n})
        dt = time.perf_counter() - t0
        print(f"concurrency={n:3d}  wall={dt:6.2f}s  rps={len(inputs)/dt:5.1f}")
```

## Multi-Worker Semaphore Pattern

`max_concurrency` is per-process. With N gunicorn workers you multiply the effective concurrency by N. Protect the account-wide limit with a shared semaphore (Redis) or a global gateway (LiteLLM proxy, Anthropic Bedrock, Portkey).

```python
# Per-process semaphore guarding cross-request calls inside one worker
sem = asyncio.Semaphore(20)

async def guarded_invoke(chain, input):
    async with sem:
        return await chain.ainvoke(input)
```

For cross-worker limits, prefer a proxy (LiteLLM, Portkey, OpenRouter) that enforces the ceiling centrally. Application-level Redis semaphores add latency and drift out of sync under restart storms.

## Checklist

- [ ] Every `.batch` / `.abatch` call has an explicit `max_concurrency` in `config`.
- [ ] Concurrency is capped below the provider RPM with 20% headroom.
- [ ] Multi-worker deploys use a proxy or Redis semaphore for account-wide limits.
- [ ] Sweep results are recorded in the runbook (update quarterly).
