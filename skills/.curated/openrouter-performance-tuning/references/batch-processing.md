# Batch Processing

## Batch Processing

### Efficient Batching

```python
async def efficient_batch(
    prompts: list,
    model: str = "anthropic/claude-3-haiku",
    batch_size: int = 10,
    delay_between_batches: float = 0.1
):
    """Process prompts in efficient batches."""
    results = []

    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i + batch_size]

        # Process batch concurrently
        batch_results = await asyncio.gather(*[
            async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": p}],
                max_tokens=500
            )
            for p in batch
        ])

        results.extend(batch_results)

        # Small delay to avoid rate limits
        if i + batch_size < len(prompts):
            await asyncio.sleep(delay_between_batches)

    return results
```
