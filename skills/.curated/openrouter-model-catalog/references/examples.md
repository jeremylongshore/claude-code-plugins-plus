# Model Catalog Examples

## cURL — Fetch All Models

```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '.data | length'
# Output: 250+ (number of available models)

# List model IDs with pricing
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '.data[] | {id, context_length, prompt_price: .pricing.prompt, completion_price: .pricing.completion}' \
  | head -40
```

## Python — Query and Filter Models

```python
import os
import requests
from dataclasses import dataclass

@dataclass
class ModelInfo:
    id: str
    context_length: int
    prompt_price: float  # per token
    completion_price: float  # per token

def fetch_models(api_key: str) -> list[ModelInfo]:
    """Fetch all available models from OpenRouter."""
    resp = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    resp.raise_for_status()
    return [
        ModelInfo(
            id=m["id"],
            context_length=m.get("context_length", 0),
            prompt_price=float(m.get("pricing", {}).get("prompt", "0")),
            completion_price=float(m.get("pricing", {}).get("completion", "0")),
        )
        for m in resp.json()["data"]
    ]

def filter_free_models(models: list[ModelInfo]) -> list[ModelInfo]:
    """Return models with zero cost."""
    return [m for m in models if m.prompt_price == 0 and m.completion_price == 0]

def filter_large_context(models: list[ModelInfo], min_ctx: int = 100_000) -> list[ModelInfo]:
    """Return models with context windows >= min_ctx."""
    return [m for m in models if m.context_length >= min_ctx]

def cheapest_models(models: list[ModelInfo], top_n: int = 10) -> list[ModelInfo]:
    """Return the N cheapest paid models by prompt price."""
    paid = [m for m in models if m.prompt_price > 0]
    return sorted(paid, key=lambda m: m.prompt_price)[:top_n]

# Usage
api_key = os.environ["OPENROUTER_API_KEY"]
models = fetch_models(api_key)

print(f"Total models: {len(models)}")
print(f"Free models: {len(filter_free_models(models))}")
print(f"128K+ context: {len(filter_large_context(models))}")

for m in cheapest_models(models, 5):
    cost_per_1m = m.prompt_price * 1_000_000
    print(f"  {m.id}: ${cost_per_1m:.2f}/1M prompt tokens, ctx={m.context_length}")
```

### Expected Output

```
Total models: 267
Free models: 12
128K+ context: 45
  mistralai/mistral-7b-instruct:free: $0.00/1M prompt tokens, ctx=32768
  meta-llama/llama-3-8b-instruct: $0.05/1M prompt tokens, ctx=8192
  google/gemma-2-9b-it: $0.08/1M prompt tokens, ctx=8192
  ...
```

## TypeScript — Search Models by Provider

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

async function listModelsByProvider(provider: string) {
  const response = await fetch("https://openrouter.ai/api/v1/models", {
    headers: { Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}` },
  });
  const { data } = (await response.json()) as { data: any[] };

  const filtered = data
    .filter((m) => m.id.startsWith(`${provider}/`))
    .map((m) => ({
      id: m.id,
      context: m.context_length,
      promptCost: `$${(parseFloat(m.pricing?.prompt || "0") * 1e6).toFixed(2)}/1M`,
    }));

  console.table(filtered);
}

// List all Anthropic models
listModelsByProvider("anthropic");
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
