# Response Length Control

## Response Length Control

### Optimal max_tokens

```python
def calculate_optimal_max_tokens(
    prompt_tokens: int,
    model: str,
    expected_response: str = "medium"
) -> int:
    """Calculate optimal max_tokens setting."""
    context_limit = CONTEXT_WINDOWS.get(model, 128000)
    available = context_limit - prompt_tokens

    response_sizes = {
        "short": 100,
        "medium": 500,
        "long": 2000,
        "very_long": 4000
    }

    desired = response_sizes.get(expected_response, 500)
    return min(desired, available - 100)

def chat_with_optimal_tokens(
    prompt: str,
    model: str,
    expected_length: str = "medium"
):
    prompt_tokens = estimate_tokens(prompt)
    max_tokens = calculate_optimal_max_tokens(
        prompt_tokens, model, expected_length
    )

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
```
