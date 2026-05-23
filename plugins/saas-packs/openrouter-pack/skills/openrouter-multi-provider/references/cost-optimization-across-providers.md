# Cost Optimization Across Providers

## Cost Optimization Across Providers

### Provider Cost Comparison

```python
PROVIDER_PRICING = {
    "anthropic/claude-3-opus": {"prompt": 15.0, "completion": 75.0},
    "anthropic/claude-3.5-sonnet": {"prompt": 3.0, "completion": 15.0},
    "anthropic/claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
    "openai/gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
    "openai/gpt-4": {"prompt": 30.0, "completion": 60.0},
    "openai/gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
    "meta-llama/llama-3.1-70b-instruct": {"prompt": 0.52, "completion": 0.75},
    "meta-llama/llama-3.1-8b-instruct": {"prompt": 0.06, "completion": 0.06},
}

def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> float:
    """Estimate cost for request."""
    pricing = PROVIDER_PRICING.get(model, {"prompt": 10.0, "completion": 30.0})
    return (
        prompt_tokens * pricing["prompt"] / 1_000_000 +
        completion_tokens * pricing["completion"] / 1_000_000
    )

def find_cheapest_model(
    required_quality: str,
    required_context: int
) -> str:
    """Find cheapest model meeting requirements."""
    candidates = []

    for model, pricing in PROVIDER_PRICING.items():
        # Check context (would need to look up actual limits)
        avg_cost = (pricing["prompt"] + pricing["completion"]) / 2
        candidates.append((model, avg_cost))

    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]
```
