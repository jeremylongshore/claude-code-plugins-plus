# Checking Model Status

## Checking Model Status

### List All Available Models

```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Python Model Checker

```python
import requests

def get_available_models(api_key: str) -> list:
    """Get all currently available models."""
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    response.raise_for_status()
    return response.json()["data"]

def is_model_available(api_key: str, model_id: str) -> bool:
    """Check if specific model is available."""
    models = get_available_models(api_key)
    return any(m["id"] == model_id for m in models)

# Usage
if is_model_available(api_key, "openai/gpt-4-turbo"):
    print("Model is available")
```

### TypeScript Model Checker

```typescript
interface ModelInfo {
  id: string;
  name: string;
  context_length: number;
  pricing: {
    prompt: string;
    completion: string;
  };
}

async function getAvailableModels(apiKey: string): Promise<ModelInfo[]> {
  const response = await fetch('https://openrouter.ai/api/v1/models', {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  const data = await response.json();
  return data.data;
}

async function isModelAvailable(apiKey: string, modelId: string): Promise<boolean> {
  const models = await getAvailableModels(apiKey);
  return models.some((m) => m.id === modelId);
}
```
