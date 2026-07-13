---
name: openrouter-hello-world
description: 'Send your first OpenRouter API request and understand the response.
  Use when learning OpenRouter, testing setup, or verifying connectivity. Triggers:
  ''openrouter hello world'', ''openrouter first request'', ''test openrouter'', ''openrouter
  quickstart''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*), Bash(python3:*), Bash(node:*), Bash(jq:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- api
- quickstart
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Hello World

## Overview

Send a minimal chat completion request through OpenRouter, understand the response format, try different models, and verify the full round-trip works. All requests go to the single endpoint `POST https://openrouter.ai/api/v1/chat/completions`.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- `curl` and `jq` for the command-line request, or Python 3.8+ / Node.js 18+ with the OpenAI SDK (`pip install openai` / `npm install openai`)
- A free-tier model works for every step here (no credits required for `:free` models)

## Instructions

1. Export your key: `export OPENROUTER_API_KEY="sk-or-v1-..."`.
2. Send the minimal cURL request below and confirm you get a `choices[0].message.content` back.
3. Read the Response Format section to identify the four key fields (`id`, `model`, `usage`, `finish_reason`).
4. Repeat the same request from your app language using the Python or TypeScript example.
5. Swap model IDs per Try Different Models to confirm multi-model access works with the same code.
6. Query `GET /api/v1/generation?id=gen-...` per Check Generation Cost to verify cost tracking on the request you just sent.

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

## Output

A successful round-trip produces:

- A chat completion JSON with `choices[0].message.content` holding the model's reply, a `gen-...` request `id`, the `model` that actually served the request, and `usage` token counts
- Console output from the Python/TypeScript examples: the reply text plus model name and prompt/completion token counts
- A cost record from the generation endpoint: `tokens_prompt`, `tokens_completion`, and `total_cost` for the request

## Examples

End-to-end run with the minimal cURL request:

```text
$ curl -s https://openrouter.ai/api/v1/chat/completions ... | jq .choices[0].message.content
"Hello! Bonjour! Hola!"
```

The Python and TypeScript sections above are the same request in SDK form; expected console output:

```text
OpenRouter is a unified API gateway that routes requests to 400+ LLMs.
Model: google/gemma-2-9b-it:free
Tokens: 21 prompt + 17 completion
```

More worked examples (cURL with full expected response, SDK variants): `references/examples.md`.

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

- Examples | Errors
- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart) | [API Reference](https://openrouter.ai/docs/api/reference/overview)
