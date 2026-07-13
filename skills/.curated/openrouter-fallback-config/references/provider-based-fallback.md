# Provider-Based Fallback

## Provider-Based Fallback

### Cross-Provider Resilience

```python
PROVIDERS = {
    "anthropic": [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
    ],
    "openai": [
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
    ],
    "meta": [
        "meta-llama/llama-3.1-70b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
    ],
}

def get_cross_provider_chain(primary_provider: str) -> list:
    """Build chain that switches providers on failure."""
    chain = []

    # Primary provider models first
    chain.extend(PROVIDERS.get(primary_provider, []))

    # Then other providers
    for provider, models in PROVIDERS.items():
        if provider != primary_provider:
            chain.extend(models)

    return chain

def chat_cross_provider(prompt: str, primary_provider: str = "anthropic"):
    chain = get_cross_provider_chain(primary_provider)

    for model in chain:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception:
            continue

    raise Exception("All providers failed")
```
