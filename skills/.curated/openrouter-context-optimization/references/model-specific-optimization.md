# Model-Specific Optimization

## Model-Specific Optimization

### Context Windows by Model

```python
CONTEXT_WINDOWS = {
    "anthropic/claude-3-opus": 200000,
    "anthropic/claude-3.5-sonnet": 200000,
    "anthropic/claude-3-haiku": 200000,
    "openai/gpt-4-turbo": 128000,
    "openai/gpt-4": 8192,
    "openai/gpt-4-32k": 32768,
    "openai/gpt-3.5-turbo": 16385,
    "meta-llama/llama-3.1-70b-instruct": 131000,
}

def select_model_for_context(context_tokens: int) -> str:
    """Select cheapest model that fits context."""
    # Sort by cost (approximate)
    model_costs = [
        ("anthropic/claude-3-haiku", 200000, 0.001),
        ("openai/gpt-3.5-turbo", 16385, 0.002),
        ("meta-llama/llama-3.1-70b-instruct", 131000, 0.001),
        ("anthropic/claude-3.5-sonnet", 200000, 0.018),
        ("openai/gpt-4-turbo", 128000, 0.030),
    ]

    for model, max_ctx, cost in model_costs:
        if context_tokens <= max_ctx * 0.9:  # Leave 10% headroom
            return model

    return "anthropic/claude-3.5-sonnet"  # Fallback to large context
```
