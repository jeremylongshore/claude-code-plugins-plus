# Request Optimization

## Request Optimization

### Minimize Token Usage

```python
def optimize_request(
    prompt: str,
    system: str = None,
    max_tokens: int = None
) -> dict:
    """Create optimized request parameters."""
    messages = []

    # Minimal system prompt
    if system:
        messages.append({
            "role": "system",
            "content": system.strip()[:500]  # Limit system prompt
        })

    messages.append({"role": "user", "content": prompt})

    params = {
        "messages": messages,
    }

    # Set max_tokens to limit response
    if max_tokens:
        params["max_tokens"] = max_tokens
    else:
        # Auto-calculate based on expected response
        params["max_tokens"] = min(500, estimate_tokens(prompt))

    return params

def fast_chat(prompt: str, model: str = "anthropic/claude-3-haiku"):
    """Optimized chat for speed."""
    params = optimize_request(prompt, max_tokens=500)

    return client.chat.completions.create(
        model=model,
        **params
    )
```

### Streaming for Perceived Speed

```python
def stream_response(prompt: str, model: str = "anthropic/claude-3-haiku"):
    """Stream response for faster time-to-first-token."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=500
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```
