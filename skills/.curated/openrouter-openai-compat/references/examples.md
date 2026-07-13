# OpenAI Compatibility Examples

## Python — Drop-In Replacement

```python
import os
from openai import OpenAI

# BEFORE: Direct OpenAI
# client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
# model = "gpt-3.5-turbo"

# AFTER: OpenRouter (2 lines changed)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",           # Changed
    api_key=os.environ["OPENROUTER_API_KEY"],           # Changed
    default_headers={
        "HTTP-Referer": "https://your-app.com",        # Optional: for analytics
        "X-Title": "Your App Name",                     # Optional: for analytics
    },
)
model = "openai/gpt-3.5-turbo"                          # Changed: add provider prefix

# Everything below is IDENTICAL to OpenAI SDK usage
response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
    max_tokens=100,
    temperature=0.7,
)

print(response.choices[0].message.content)
print(f"Model: {response.model}")
print(f"Tokens: {response.usage.total_tokens}")
```

## TypeScript — Switching Between OpenAI and OpenRouter

```typescript
import OpenAI from "openai";

function createClient(provider: "openai" | "openrouter"): OpenAI {
  if (provider === "openai") {
    return new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  }
  return new OpenAI({
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY,
  });
}

function modelId(base: string, provider: "openai" | "openrouter"): string {
  // OpenRouter requires provider prefix; OpenAI does not
  if (provider === "openrouter" && !base.includes("/")) {
    return `openai/${base}`;
  }
  return base;
}

// Identical code works with both providers
async function chat(prompt: string, provider: "openai" | "openrouter" = "openrouter") {
  const client = createClient(provider);
  const model = modelId("gpt-3.5-turbo", provider);

  const res = await client.chat.completions.create({
    model,
    messages: [{ role: "user", content: prompt }],
    max_tokens: 100,
  });

  return res.choices[0].message.content;
}

// Use OpenRouter (accesses 100+ models)
const result = await chat("Hello!", "openrouter");
console.log(result);

// Or use OpenAI directly (same code path)
// const result = await chat("Hello!", "openai");
```

## Python — Access Non-OpenAI Models with Same SDK

```python
# The key benefit: use the OpenAI SDK to access ANY provider

# Anthropic Claude
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello from Claude via OpenAI SDK!"}],
    max_tokens=100,
)
print(f"Claude says: {response.choices[0].message.content}")

# Google Gemini
response = client.chat.completions.create(
    model="google/gemini-pro",
    messages=[{"role": "user", "content": "Hello from Gemini via OpenAI SDK!"}],
    max_tokens=100,
)
print(f"Gemini says: {response.choices[0].message.content}")

# Meta Llama (free)
response = client.chat.completions.create(
    model="meta-llama/llama-3-8b-instruct",
    messages=[{"role": "user", "content": "Hello from Llama via OpenAI SDK!"}],
    max_tokens=100,
)
print(f"Llama says: {response.choices[0].message.content}")
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
