# Scaling Considerations

## Scaling Considerations

### Connection Pooling

```python
import httpx

# Use connection pooling for high-volume
http_client = httpx.Client(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    http_client=http_client
)
```

### Async for High Throughput

```python
from openai import AsyncOpenAI
import asyncio

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

async def process_batch(prompts: list, max_concurrent: int = 10):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(prompt):
        async with semaphore:
            return await async_client.chat.completions.create(
                model="openai/gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )

    return await asyncio.gather(*[process_one(p) for p in prompts])
```
