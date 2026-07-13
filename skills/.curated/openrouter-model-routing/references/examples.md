# Model Routing Examples

## Python — Task-Based Router

```python
import os
import re
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Routing table: task type -> model
ROUTING_TABLE = {
    "simple":   "google/gemma-2-9b-it:free",
    "chat":     "openai/gpt-3.5-turbo",
    "code":     "anthropic/claude-3.5-sonnet",
    "analysis": "openai/gpt-4-turbo",
    "creative": "anthropic/claude-3.5-sonnet",
}

def classify_task(prompt: str) -> str:
    """Classify a prompt into a task category."""
    prompt_lower = prompt.lower()

    if any(kw in prompt_lower for kw in ["write code", "implement", "function", "debug", "refactor"]):
        return "code"
    if any(kw in prompt_lower for kw in ["analyze", "compare", "evaluate", "review", "assess"]):
        return "analysis"
    if any(kw in prompt_lower for kw in ["write a story", "poem", "creative", "imagine"]):
        return "creative"
    if len(prompt.split()) < 20:
        return "simple"
    return "chat"

def routed_completion(prompt: str, **kwargs) -> str:
    """Route a prompt to the appropriate model based on task type."""
    task = classify_task(prompt)
    model = ROUTING_TABLE[task]

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=kwargs.get("max_tokens", 500),
    )

    print(f"[Router] Task={task} -> Model={model}")
    return response.choices[0].message.content

# Usage
print(routed_completion("What is 2+2?"))
# [Router] Task=simple -> Model=google/gemma-2-9b-it:free

print(routed_completion("Write a Python function to merge two sorted lists."))
# [Router] Task=code -> Model=anthropic/claude-3.5-sonnet

print(routed_completion("Analyze the pros and cons of microservice architecture."))
# [Router] Task=analysis -> Model=openai/gpt-4-turbo
```

## TypeScript — Cost-Aware Router

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

interface RoutingConfig {
  maxCostPerRequest: number; // USD
  preferredModel: string;
  fallbackModel: string;
}

const TIERS: Record<string, RoutingConfig> = {
  free: {
    maxCostPerRequest: 0,
    preferredModel: "google/gemma-2-9b-it:free",
    fallbackModel: "google/gemma-2-9b-it:free",
  },
  standard: {
    maxCostPerRequest: 0.01,
    preferredModel: "openai/gpt-3.5-turbo",
    fallbackModel: "google/gemma-2-9b-it:free",
  },
  premium: {
    maxCostPerRequest: 0.10,
    preferredModel: "openai/gpt-4-turbo",
    fallbackModel: "anthropic/claude-3.5-sonnet",
  },
};

async function routedChat(prompt: string, userTier: string): Promise<string> {
  const config = TIERS[userTier] || TIERS.standard;

  const response = await client.chat.completions.create({
    model: config.preferredModel,
    messages: [{ role: "user", content: prompt }],
    max_tokens: 300,
  });

  console.log(`[${userTier}] Routed to: ${config.preferredModel}`);
  return response.choices[0].message.content || "";
}

// Usage
routedChat("Hello!", "free");     // -> google/gemma-2-9b-it:free
routedChat("Hello!", "standard"); // -> openai/gpt-3.5-turbo
routedChat("Hello!", "premium");  // -> openai/gpt-4-turbo
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
