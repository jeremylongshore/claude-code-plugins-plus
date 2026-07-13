# Known Pitfalls — Runnable Examples

## Python — Startup Model Validation

```python
import os
import sys
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

REQUIRED_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-3.5-turbo",
]

def validate_models_at_startup() -> None:
    try:
        available = {m.id for m in client.models.list().data}
    except Exception as e:
        print(f"[WARN] Could not fetch model list: {e}")
        return

    missing = [m for m in REQUIRED_MODELS if m not in available]
    if missing:
        print(f"[ERROR] Required models unavailable: {missing}")
        sys.exit(1)
    print(f"[OK] All {len(REQUIRED_MODELS)} required models available")

validate_models_at_startup()
```

## Python — Always Set max_tokens (Avoid Cost Surprises)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MAX_TOKENS_BY_TASK = {
    "classification": 20,
    "short_answer": 150,
    "summary": 300,
    "detailed_analysis": 1000,
}

def complete_with_budget(prompt: str, task: str = "short_answer") -> str:
    max_tokens = MAX_TOKENS_BY_TASK.get(task, 300)
    response = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

print(complete_with_budget("Is Python dynamically typed? Answer yes or no.", "classification"))
print(complete_with_budget("What is Python?", "short_answer"))
```

## Python — Safe API Key Management

```python
import os
from pathlib import Path

def load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY environment variable not set.\n"
            "Add it to your shell profile or use a secrets manager."
        )
    if not key.startswith("sk-or-"):
        raise RuntimeError(
            f"Invalid API key format. Expected 'sk-or-...' but got '{key[:8]}...'"
        )
    env_file = Path(".env")
    if env_file.exists() and "OPENROUTER_API_KEY" in env_file.read_text():
        print("[WARN] .env file contains OPENROUTER_API_KEY — ensure .env is in .gitignore")
    return key

api_key = load_api_key()
print(f"API key loaded: {api_key[:8]}...")
```

## TypeScript — Provider-Agnostic Prompt Testing

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

const PRODUCTION_MODEL = "anthropic/claude-3.5-sonnet";

async function testPrompt(prompt: string, expectedPattern: RegExp): Promise<boolean> {
  const res = await client.chat.completions.create({
    model: PRODUCTION_MODEL,
    messages: [{ role: "user", content: prompt }],
    max_tokens: 200,
    temperature: 0,
  });
  const content = res.choices[0].message.content || "";
  const passes = expectedPattern.test(content);
  console.log(`[${passes ? "PASS" : "FAIL"}] Model: ${PRODUCTION_MODEL}`);
  return passes;
}

await testPrompt(
  "Classify as POSITIVE, NEGATIVE, or NEUTRAL: 'I love this product!'",
  /POSITIVE/i
);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
