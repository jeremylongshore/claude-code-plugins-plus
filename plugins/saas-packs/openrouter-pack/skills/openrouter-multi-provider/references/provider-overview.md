# Provider Overview

## Provider Overview

### Available Providers

```
Provider        | Models                           | Strengths
----------------|----------------------------------|------------------
OpenAI          | GPT-4, GPT-4 Turbo, GPT-3.5     | General, Functions
Anthropic       | Claude 3 Opus/Sonnet/Haiku       | Code, Analysis
Meta            | Llama 3.1 (8B, 70B, 405B)       | Open source, Cost
Mistral         | Mistral, Mixtral                 | Speed, Europe
Google          | Gemini Pro 1.5                   | Long context
Cohere          | Command R+                       | RAG, Enterprise
```

### Get All Available Models

```python
import requests

def get_all_models(api_key: str) -> dict:
    """Get all models grouped by provider."""
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    models = response.json()["data"]

    by_provider = {}
    for model in models:
        provider = model["id"].split("/")[0]
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append({
            "id": model["id"],
            "name": model.get("name", model["id"]),
            "context": model.get("context_length", 0),
            "pricing": model.get("pricing", {})
        })

    return by_provider

providers = get_all_models(api_key)
print(f"Providers: {list(providers.keys())}")
```
