# Stream Processing

## Stream Processing

### With Callbacks

```python
from typing import Callable

def stream_with_callbacks(
    prompt: str,
    model: str = "openai/gpt-4-turbo",
    on_chunk: Callable[[str], None] = None,
    on_complete: Callable[[str], None] = None,
    on_error: Callable[[Exception], None] = None
):
    """Stream with callback handlers."""
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
                if on_chunk:
                    on_chunk(content)

        if on_complete:
            on_complete(full_response)

        return full_response

    except Exception as e:
        if on_error:
            on_error(e)
        raise

# Usage
stream_with_callbacks(
    "Hello",
    on_chunk=lambda c: print(c, end=""),
    on_complete=lambda r: print(f"\n\nTotal: {len(r)} chars")
)
```

### Token Counting During Stream

```python
def stream_with_token_count(prompt: str, model: str = "openai/gpt-4-turbo"):
    """Stream and count tokens."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        stream_options={"include_usage": True}  # Request usage info
    )

    full_response = ""
    usage = None

    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            yield content

        # Check for usage in final chunk
        if hasattr(chunk, 'usage') and chunk.usage:
            usage = chunk.usage

    return full_response, usage
```
