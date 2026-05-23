# Latency Optimization

## Latency Optimization

### Connection Pooling

```python
import httpx
from openai import OpenAI

# Create persistent HTTP client with connection pooling
http_client = httpx.Client(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30.0
    ),
    timeout=httpx.Timeout(60.0, connect=5.0)
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    http_client=http_client
)
```

### Async for Concurrency

```python
from openai import AsyncOpenAI
import asyncio

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

async def batch_process(prompts: list, max_concurrent: int = 10):
    """Process multiple prompts concurrently."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(prompt: str):
        async with semaphore:
            return await async_client.chat.completions.create(
                model="anthropic/claude-3-haiku",  # Fast model
                messages=[{"role": "user", "content": prompt}]
            )

    return await asyncio.gather(*[process_one(p) for p in prompts])
```
