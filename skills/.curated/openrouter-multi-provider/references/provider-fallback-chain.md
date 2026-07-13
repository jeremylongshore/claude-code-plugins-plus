# Provider Fallback Chain

## Provider Fallback Chain

### Cross-Provider Resilience

```python
class MultiProviderClient:
    """Client with cross-provider fallback."""

    def __init__(self):
        self.provider_chains = {
            "premium": [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4-turbo",
                "meta-llama/llama-3.1-70b-instruct"
            ],
            "fast": [
                "anthropic/claude-3-haiku",
                "openai/gpt-3.5-turbo",
                "mistralai/mistral-7b-instruct"
            ],
            "cheap": [
                "meta-llama/llama-3.1-8b-instruct",
                "mistralai/mistral-7b-instruct",
                "anthropic/claude-3-haiku"
            ]
        }

        self.disabled_providers = set()

    def disable_provider(self, provider: str, duration: float = 300):
        """Temporarily disable a provider."""
        self.disabled_providers.add(provider)
        # In practice, track expiration time

    def get_chain(self, tier: str) -> list:
        """Get available models in chain."""
        chain = self.provider_chains.get(tier, self.provider_chains["premium"])
        return [
            m for m in chain
            if m.split("/")[0] not in self.disabled_providers
        ]

    def chat(
        self,
        prompt: str,
        tier: str = "premium",
        **kwargs
    ):
        chain = self.get_chain(tier)

        for model in chain:
            try:
                return client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
            except Exception as e:
                provider = model.split("/")[0]
                if "unavailable" in str(e).lower():
                    self.disable_provider(provider)
                continue

        raise Exception("All providers failed")

multi_client = MultiProviderClient()
```
