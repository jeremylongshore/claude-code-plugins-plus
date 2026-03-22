---
name: openrouter-hello-world
description: |
  Send your first OpenRouter API request and understand the response. Use when learning OpenRouter, testing setup, or verifying connectivity. Triggers: 'openrouter hello world', 'openrouter first request', 'test openrouter', 'openrouter quickstart'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, api, quickstart]

---
# OpenRouter Hello World

## Overview

Send a minimal chat completion request through OpenRouter, understand the response format, try different models, and verify the full round-trip works. All requests go to the single endpoint `POST https://openrouter.ai/api/v1/chat/completions`.

## Minimal Request (cURL)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-2-9b-it:free",
    "messages": [{"role": "user", "content": "Say hello in three languages"}],
    "max_tokens": 100
  }' | jq .
```

## Response Format

```json
{
  "id": "gen-abc123xyz",
  "model": "google/gemma-2-9b-it:free",
  "object": "chat.completion",
  "created": 1711234567,
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! Bonjour! Hola!"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  }
}
```

Key fields:
- `id` (`gen-...`) -- use this to query generation stats via `GET /api/v1/generation?id=gen-abc123xyz`
- `model` -- confirms which model actually served the request
- `usage` -- token counts for cost calculation
- `finish_reason` -- `stop` (complete), `length` (hit max_tokens), `tool_calls` (function call)

## Python Example

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://your-app.com", "X-Title": "My App"},
)

# Basic completion
response = client.chat.completions.create(
    model="google/gemma-2-9b-it:free",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is OpenRouter in one sentence?"},
    ],
    max_tokens=100,
)

print(response.choices[0].message.content)
print(f"Model: {response.model}")
print(f"Tokens: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion")
```

## TypeScript Example

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: { "HTTP-Referer": "https://your-app.com", "X-Title": "My App" },
});

const res = await client.chat.completions.create({
  model: "google/gemma-2-9b-it:free",
  messages: [{ role: "user", content: "What is OpenRouter in one sentence?" }],
  max_tokens: 100,
});

console.log(res.choices[0].message.content);
console.log(`Model: ${res.model} | Tokens: ${res.usage?.total_tokens}`);
```

## Try Different Models

```python
# Swap model ID to access any of 400+ models
models_to_try = [
    "google/gemma-2-9b-it:free",         # Free tier
    "meta-llama/llama-3.1-8b-instruct",  # Open-source
    "anthropic/claude-3.5-sonnet",        # Anthropic
    "openai/gpt-4o",                      # OpenAI
    "openrouter/auto",                    # Auto-router (picks best model)
]

for model_id in models_to_try:
    try:
        r = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
        )
        print(f"{model_id}: {r.choices[0].message.content}")
    except Exception as e:
        print(f"{model_id}: {e}")
```

## Check Generation Cost

```bash
# After a request, query the generation endpoint for cost details
curl -s "https://openrouter.ai/api/v1/generation?id=gen-abc123xyz" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '{
    model: .data.model,
    tokens_prompt: .data.tokens_prompt,
    tokens_completion: .data.tokens_completion,
    total_cost: .data.total_cost
  }'
```

## Error Handling

| HTTP | Cause | Fix |
|------|-------|-----|
| 401 | Invalid or missing API key | Verify `sk-or-v1-...` key is exported |
| 402 | Insufficient credits for paid model | Add credits or use a `:free` model |
| 404 | Wrong base URL or invalid model ID | Use `https://openrouter.ai/api/v1`; check model ID at `/api/v1/models` |
| 400 | Malformed JSON or missing `messages` | Ensure `messages` array has objects with `role` and `content` |

## Enterprise Considerations

- Always set `max_tokens` to prevent unbounded completions
- Use `HTTP-Referer` and `X-Title` headers for usage attribution in dashboards
- Query `/api/v1/generation?id=` for async cost auditing
- Test with free models first, then switch to paid models for production

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart) | [API Reference](https://openrouter.ai/docs/api/reference/overview)
