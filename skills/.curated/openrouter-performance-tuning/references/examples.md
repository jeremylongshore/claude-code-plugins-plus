# Performance Tuning Examples

## Python — Latency Measurement

```python
import os
import time
import asyncio
from openai import OpenAI, AsyncOpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def benchmark_model(model: str, prompt: str = "Say hello.", n: int = 5) -> dict:
    """Measure average latency and TTFT for a model."""
    latencies = []

    for _ in range(n):
        start = time.perf_counter()

        # Measure TTFT with streaming
        first_token_time = None
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            stream=True,
        )
        for chunk in stream:
            if first_token_time is None and chunk.choices[0].delta.content:
                first_token_time = time.perf_counter() - start

        total_time = time.perf_counter() - start
        latencies.append({"ttft": first_token_time, "total": total_time})

    avg_ttft = sum(l["ttft"] for l in latencies if l["ttft"]) / len(latencies)
    avg_total = sum(l["total"] for l in latencies) / len(latencies)

    return {
        "model": model,
        "avg_ttft_ms": round(avg_ttft * 1000),
        "avg_total_ms": round(avg_total * 1000),
        "samples": n,
    }

# Compare models
for model in ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku"]:
    result = benchmark_model(model)
    print(f"{result['model']}: TTFT={result['avg_ttft_ms']}ms, Total={result['avg_total_ms']}ms")
```

## Python — Concurrent Requests with asyncio

```python
async def parallel_completions(prompts: list[str], model: str = "openai/gpt-3.5-turbo") -> list[str]:
    """Send multiple requests concurrently for better throughput."""
    async def single_request(prompt: str) -> str:
        response = await async_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        return response.choices[0].message.content

    start = time.perf_counter()
    results = await asyncio.gather(*[single_request(p) for p in prompts])
    elapsed = time.perf_counter() - start

    print(f"Completed {len(prompts)} requests in {elapsed:.1f}s "
          f"({len(prompts)/elapsed:.1f} req/s)")
    return results

# Usage: 10 requests concurrently
prompts = [f"What is the capital of country #{i}?" for i in range(10)]
results = asyncio.run(parallel_completions(prompts))
# Output: Completed 10 requests in 2.3s (4.3 req/s)
```

## TypeScript — Connection Pooling

```typescript
import OpenAI from "openai";

// Create client with optimized settings
const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
  maxRetries: 2,
  timeout: 30_000,
});

async function batchProcess(prompts: string[]): Promise<string[]> {
  const start = performance.now();

  const results = await Promise.all(
    prompts.map((prompt) =>
      client.chat.completions.create({
        model: "openai/gpt-3.5-turbo",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 100,
      })
    )
  );

  const elapsed = (performance.now() - start) / 1000;
  console.log(`${prompts.length} requests in ${elapsed.toFixed(1)}s`);

  return results.map((r) => r.choices[0].message.content || "");
}

const prompts = Array.from({ length: 10 }, (_, i) => `Describe color #${i}`);
batchProcess(prompts);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
