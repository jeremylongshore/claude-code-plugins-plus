# Batch Processing With Rate Limits

## Batch Processing with Rate Limits

### Controlled Batch Processing

```python
import asyncio
from typing import List

async def process_batch(
    prompts: List[str],
    model: str,
    requests_per_minute: int = 60
):
    """Process prompts with rate limiting."""
    delay = 60.0 / requests_per_minute
    results = []

    for i, prompt in enumerate(prompts):
        if i > 0:
            await asyncio.sleep(delay)

        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            results.append({
                "prompt": prompt,
                "response": response.choices[0].message.content,
                "success": True
            })
        except RateLimitError:
            # Extra wait on rate limit
            await asyncio.sleep(delay * 5)
            results.append({
                "prompt": prompt,
                "response": None,
                "success": False,
                "error": "rate_limited"
            })

    return results
```

### Concurrent with Semaphore

```python
async def process_batch_concurrent(
    prompts: List[str],
    model: str,
    max_concurrent: int = 5
):
    """Process with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(prompt: str):
        async with semaphore:
            try:
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return {"prompt": prompt, "response": response, "success": True}
            except RateLimitError:
                await asyncio.sleep(5)
                return {"prompt": prompt, "response": None, "success": False}

    return await asyncio.gather(*[process_one(p) for p in prompts])
```
