# Error Handling In Streams

## Error Handling in Streams

### Robust Streaming

```python
from openai import APIError, RateLimitError

def robust_stream(prompt: str, model: str, retries: int = 3):
    """Stream with retry logic."""
    for attempt in range(retries):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            return

        except RateLimitError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

        except APIError as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                raise
```

### Stream Timeout

```python
import asyncio

async def stream_with_timeout(
    prompt: str,
    model: str = "openai/gpt-4-turbo",
    timeout: float = 60.0
):
    """Stream with overall timeout."""
    async def stream_generator():
        stream = await async_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    try:
        parts = []
        async for content in asyncio.wait_for(
            stream_generator().__aiter__().__anext__,
            timeout=timeout
        ):
            parts.append(content)
            yield content
    except asyncio.TimeoutError:
        raise Exception(f"Stream timed out after {timeout}s")
```
