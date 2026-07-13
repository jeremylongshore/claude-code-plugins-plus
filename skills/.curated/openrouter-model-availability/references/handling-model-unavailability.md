# Handling Model Unavailability

## Handling Model Unavailability

### Fallback Chain

```python
class ModelFallback:
    def __init__(self, models: list):
        self.models = models
        self.disabled = set()
        self.disable_until = {}

    def disable_model(self, model: str, duration: float = 300):
        """Temporarily disable a model."""
        self.disabled.add(model)
        self.disable_until[model] = time.time() + duration

    def get_available_models(self) -> list:
        """Get currently available models."""
        now = time.time()
        # Re-enable models past their disable duration
        for model in list(self.disabled):
            if self.disable_until.get(model, 0) < now:
                self.disabled.remove(model)

        return [m for m in self.models if m not in self.disabled]

    def chat(self, prompt: str, **kwargs):
        """Try models in order until one works."""
        available = self.get_available_models()

        if not available:
            raise Exception("All models unavailable")

        for model in available:
            try:
                return client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
            except Exception as e:
                if "unavailable" in str(e).lower():
                    self.disable_model(model)
                    continue
                raise

        raise Exception("All models failed")

# Usage
fallback = ModelFallback([
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct"
])
```

### Model Groups

```python
MODEL_GROUPS = {
    "coding": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "deepseek/deepseek-coder"
    ],
    "fast": [
        "anthropic/claude-3-haiku",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3.1-8b-instruct"
    ],
    "cheap": [
        "meta-llama/llama-3.1-8b-instruct",
        "mistralai/mistral-7b-instruct"
    ]
}

def get_working_model(group: str) -> Optional[str]:
    """Find first working model in group."""
    models = MODEL_GROUPS.get(group, [])

    for model in models:
        health = check_model_health(model, timeout=5.0)
        if health["status"] == "healthy":
            return model

    return None
```
