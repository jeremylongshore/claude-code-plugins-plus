# Switching Between Providers

## Switching Between Providers

### Runtime Switching

```python
import os

class LLMClient:
    def __init__(self, provider: str = "openrouter"):
        if provider == "openai":
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            self.model_prefix = ""
        else:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"]
            )
            self.model_prefix = "openai/"

    def chat(self, prompt: str, model: str = "gpt-4-turbo"):
        full_model = f"{self.model_prefix}{model}" if self.model_prefix else model
        return self.client.chat.completions.create(
            model=full_model,
            messages=[{"role": "user", "content": prompt}]
        )

# Usage
client = LLMClient(provider=os.environ.get("LLM_PROVIDER", "openrouter"))
```

### Configuration-Based

```python
# config.py
import os

LLM_CONFIG = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "model_prefix": "",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
        "model_prefix": "openai/",
    },
}

ACTIVE_PROVIDER = os.environ.get("LLM_PROVIDER", "openrouter")
```
