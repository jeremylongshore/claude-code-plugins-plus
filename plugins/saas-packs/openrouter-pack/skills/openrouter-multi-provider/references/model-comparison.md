# Model Comparison

## Model Comparison

### Compare Responses

```python
async def compare_models(
    prompt: str,
    models: list,
    **kwargs
) -> dict:
    """Compare responses across models."""
    results = {}

    for model in models:
        start = time.time()
        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

            results[model] = {
                "success": True,
                "content": response.choices[0].message.content,
                "tokens": response.usage.total_tokens,
                "latency_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            results[model] = {
                "success": False,
                "error": str(e),
                "latency_ms": (time.time() - start) * 1000
            }

    return results

# Compare top models
models = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct"
]
comparison = await compare_models("Explain quantum computing", models)
```

### Parallel Comparison

```python
import asyncio

async def parallel_compare(
    prompt: str,
    models: list,
    **kwargs
) -> dict:
    """Run comparisons in parallel."""

    async def query_model(model: str):
        start = time.time()
        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return model, {
                "success": True,
                "content": response.choices[0].message.content,
                "tokens": response.usage.total_tokens,
                "latency_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            return model, {
                "success": False,
                "error": str(e)
            }

    tasks = [query_model(m) for m in models]
    results = await asyncio.gather(*tasks)

    return dict(results)
```
