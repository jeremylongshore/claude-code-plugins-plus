# Upgrade Migration — Runnable Examples

## Python — Migrate from OpenAI Direct to OpenRouter

```python
import os
from openai import OpenAI

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL_MIGRATION_MAP = {
    "gpt-3.5-turbo":  "openai/gpt-3.5-turbo",
    "gpt-4":          "openai/gpt-4",
    "gpt-4-turbo":    "openai/gpt-4-turbo",
    "gpt-4o":         "openai/gpt-4o",
}


def migrate_model_id(old_model: str) -> str:
    if "/" in old_model:
        return old_model  # Already in OpenRouter format
    migrated = MODEL_MIGRATION_MAP.get(old_model)
    if not migrated:
        raise ValueError(f"Unknown model '{old_model}'. Add it to MODEL_MIGRATION_MAP.")
    return migrated


def run_migration_comparison(prompt: str, old_model: str) -> None:
    new_model = migrate_model_id(old_model)
    print(f"Testing: {old_model} -> {new_model}")

    try:
        old_resp = openai_client.chat.completions.create(
            model=old_model, messages=[{"role": "user", "content": prompt}],
            max_tokens=100, temperature=0,
        )
        print(f"[OLD]  {old_resp.choices[0].message.content[:80]}")
    except Exception as e:
        print(f"[OLD]  ERROR: {e}")

    try:
        new_resp = openrouter_client.chat.completions.create(
            model=new_model, messages=[{"role": "user", "content": prompt}],
            max_tokens=100, temperature=0,
        )
        print(f"[NEW]  {new_resp.choices[0].message.content[:80]}")
    except Exception as e:
        print(f"[NEW]  ERROR: {e}")


run_migration_comparison("What is REST API?", "gpt-3.5-turbo")
```

## TypeScript — Feature Flag Migration

```typescript
import OpenAI from "openai";
import crypto from "crypto";

const openrouterClient = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

const openaiClient = new OpenAI({ apiKey: process.env.OPENAI_API_KEY! });

const MIGRATION_PERCENTAGE = parseFloat(process.env.OPENROUTER_MIGRATION_PCT ?? "0");

async function chat(prompt: string, userId: string) {
  const userBucket = parseInt(userId.slice(-2), 16) % 100;
  const useOpenRouter = userBucket < MIGRATION_PERCENTAGE;

  if (useOpenRouter) {
    const res = await openrouterClient.chat.completions.create({
      model: "openai/gpt-3.5-turbo",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 300,
    });
    return { content: res.choices[0].message.content || "", via: "openrouter" };
  } else {
    const res = await openaiClient.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 300,
    });
    return { content: res.choices[0].message.content || "", via: "openai-direct" };
  }
}

// Set OPENROUTER_MIGRATION_PCT=50 to migrate 50% of users
const result = await chat("What is TypeScript?", "user-abc123");
console.log(`Via ${result.via}:`, result.content.slice(0, 80));
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
