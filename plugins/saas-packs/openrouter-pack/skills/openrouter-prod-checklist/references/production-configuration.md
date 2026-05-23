# Production Configuration

## Production Configuration

### Recommended Defaults

```python
PRODUCTION_CONFIG = {
    # Timeouts
    "timeout": 60.0,          # Connection timeout
    "max_retries": 3,         # Retry count

    # Token limits
    "max_tokens": 4096,       # Default response limit
    "temperature": 0.7,       # Balanced creativity

    # Headers
    "http_referer": "https://your-app.com",
    "x_title": "Your App Name",

    # Fallback models
    "fallback_models": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "meta-llama/llama-3.1-70b-instruct"
    ]
}
```

### Production Client

```python
class ProductionOpenRouterClient:
    def __init__(self, config: dict = None):
        config = config or PRODUCTION_CONFIG

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            timeout=config.get("timeout", 60.0),
            max_retries=config.get("max_retries", 3),
            default_headers={
                "HTTP-Referer": config.get("http_referer", ""),
                "X-Title": config.get("x_title", ""),
            }
        )
        self.fallback_models = config.get("fallback_models", [])
        self.max_tokens = config.get("max_tokens", 4096)

    def chat(
        self,
        prompt: str,
        model: str = "anthropic/claude-3.5-sonnet",
        **kwargs
    ):
        models_to_try = [model] + [
            m for m in self.fallback_models if m != model
        ]

        last_error = None
        for try_model in models_to_try:
            try:
                return self.client.chat.completions.create(
                    model=try_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    **{k: v for k, v in kwargs.items() if k != "max_tokens"}
                )
            except Exception as e:
                last_error = e
                if "unavailable" in str(e).lower():
                    continue
                raise

        raise last_error or Exception("All models failed")
```
