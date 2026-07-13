# Multi-Provider Examples

## Python — Cross-Provider Comparison

```python
import os
import time
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

PROVIDERS = {
    "OpenAI":    "openai/gpt-3.5-turbo",
    "Anthropic": "anthropic/claude-3-haiku",
    "Google":    "google/gemma-2-9b-it:free",
    "Meta":      "meta-llama/llama-3-8b-instruct",
}

def compare_providers(prompt: str) -> list[dict]:
    """Send the same prompt to multiple providers and compare results."""
    results = []

    for provider_name, model in PROVIDERS.items():
        start = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            elapsed = time.perf_counter() - start
            results.append({
                "provider": provider_name,
                "model": model,
                "response": response.choices[0].message.content[:100],
                "tokens": response.usage.total_tokens,
                "latency_ms": round(elapsed * 1000),
                "status": "ok",
            })
        except Exception as e:
            results.append({
                "provider": provider_name,
                "model": model,
                "response": None,
                "tokens": 0,
                "latency_ms": 0,
                "status": f"error: {e}",
            })

    return results

# Compare
results = compare_providers("Explain what an API gateway is in 2 sentences.")
for r in results:
    print(f"[{r['provider']}] {r['latency_ms']}ms, {r['tokens']} tokens — {r['status']}")
    if r['response']:
        print(f"  {r['response'][:80]}...\n")
```

### Expected Output

```
[OpenAI] 450ms, 65 tokens — ok
  An API gateway is a server that acts as a single entry point for API requests...

[Anthropic] 380ms, 58 tokens — ok
  An API gateway serves as an intermediary between clients and backend services...

[Google] 620ms, 71 tokens — ok
  An API gateway is a management tool that sits between a client and collection...

[Meta] 510ms, 63 tokens — ok
  An API gateway is a reverse proxy that routes API calls to the appropriate...
```

## TypeScript — Provider Abstraction Layer

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

type TaskType = "code" | "analysis" | "chat" | "creative";

const PROVIDER_MAP: Record<TaskType, string[]> = {
  code: ["anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo"],
  analysis: ["openai/gpt-4-turbo", "anthropic/claude-3.5-sonnet"],
  chat: ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku"],
  creative: ["anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo"],
};

async function multiProviderChat(
  prompt: string,
  taskType: TaskType
): Promise<{ content: string; model: string; provider: string }> {
  const models = PROVIDER_MAP[taskType];

  for (const model of models) {
    try {
      const res = await client.chat.completions.create({
        model,
        messages: [{ role: "user", content: prompt }],
        max_tokens: 300,
      });
      const provider = model.split("/")[0];
      return {
        content: res.choices[0].message.content || "",
        model,
        provider,
      };
    } catch {
      continue; // try next provider
    }
  }

  throw new Error(`All providers failed for task type: ${taskType}`);
}

// Usage: best provider for each task type
const codeResult = await multiProviderChat("Write a quicksort in Python", "code");
console.log(`Code task handled by: ${codeResult.provider}`);

const chatResult = await multiProviderChat("How are you today?", "chat");
console.log(`Chat task handled by: ${chatResult.provider}`);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
