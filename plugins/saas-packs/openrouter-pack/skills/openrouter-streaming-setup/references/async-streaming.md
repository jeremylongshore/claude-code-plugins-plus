# Async Streaming

## Async Streaming

### Python Async Stream

```python
from openai import AsyncOpenAI

async_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

async def async_stream_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
    """Async streaming with yield."""
    stream = await async_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# Usage
async def main():
    async for content in async_stream_chat("Hello"):
        print(content, end="", flush=True)

import asyncio
asyncio.run(main())
```

### Collecting Streamed Response

```python
async def collect_stream(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    """Collect full streamed response."""
    parts = []
    async for chunk in async_stream_chat(prompt, model):
        parts.append(chunk)
    return "".join(parts)
```
