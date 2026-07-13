# Fallback Config Examples

## cURL — Native OpenRouter Fallback

```bash
# Use the "models" array (plural) for automatic fallback
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "models": [
      "anthropic/claude-3.5-sonnet",
      "openai/gpt-4-turbo",
      "google/gemini-pro"
    ],
    "route": "fallback",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }' | jq '{model: .model, content: .choices[0].message.content}'

# OpenRouter tries models in order; response shows which model was used
```

## Python — Client-Side Fallback with Retry

```python
import os
import time
from openai import OpenAI, APIError, APITimeoutError

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

FALLBACK_CHAIN = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "openai/gpt-3.5-turbo",
    "google/gemma-2-9b-it:free",
]

def chat_with_fallback(messages: list, max_tokens: int = 500) -> dict:
    """Try each model in the fallback chain until one succeeds."""
    last_error = None

    for model in FALLBACK_CHAIN:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                timeout=15,  # fail fast per model
            )
            return {
                "content": response.choices[0].message.content,
                "model_used": response.model,
                "fallback_depth": FALLBACK_CHAIN.index(model),
            }
        except (APIError, APITimeoutError) as e:
            print(f"[Fallback] {model} failed: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All fallback models failed. Last error: {last_error}")

# Usage
result = chat_with_fallback([{"role": "user", "content": "Hello!"}])
print(f"Response from {result['model_used']} (depth={result['fallback_depth']})")
print(result["content"])
```

## TypeScript — Fallback with Health Tracking

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

interface ModelHealth {
  consecutiveFailures: number;
  lastFailure: number;
  cooldownMs: number;
}

const health = new Map<string, ModelHealth>();
const FALLBACK_CHAIN = [
  "anthropic/claude-3.5-sonnet",
  "openai/gpt-4-turbo",
  "openai/gpt-3.5-turbo",
];

function isHealthy(model: string): boolean {
  const h = health.get(model);
  if (!h || h.consecutiveFailures === 0) return true;
  return Date.now() - h.lastFailure > h.cooldownMs;
}

function markFailed(model: string) {
  const h = health.get(model) || { consecutiveFailures: 0, lastFailure: 0, cooldownMs: 5000 };
  h.consecutiveFailures++;
  h.lastFailure = Date.now();
  h.cooldownMs = Math.min(h.cooldownMs * 2, 60000); // exponential cooldown
  health.set(model, h);
}

function markSuccess(model: string) {
  health.set(model, { consecutiveFailures: 0, lastFailure: 0, cooldownMs: 5000 });
}

async function chatWithFallback(prompt: string): Promise<string> {
  for (const model of FALLBACK_CHAIN) {
    if (!isHealthy(model)) {
      console.log(`[Skip] ${model} in cooldown`);
      continue;
    }
    try {
      const res = await client.chat.completions.create({
        model,
        messages: [{ role: "user", content: prompt }],
        max_tokens: 300,
      });
      markSuccess(model);
      console.log(`[OK] ${model}`);
      return res.choices[0].message.content || "";
    } catch {
      markFailed(model);
      console.log(`[Fail] ${model}`);
    }
  }
  throw new Error("All models exhausted");
}

chatWithFallback("What is machine learning?");
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
