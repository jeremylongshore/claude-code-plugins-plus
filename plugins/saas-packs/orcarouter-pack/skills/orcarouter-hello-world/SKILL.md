---
name: orcarouter-hello-world
description: |
  Send your first OrcaRouter chat completion and understand the response
  format. Use when learning OrcaRouter, testing gateway connectivity, or
  verifying a model works. Triggers: "orcarouter hello world", "orcarouter
  first request", "test orcarouter", "orcarouter quickstart".
  Trigger with "orcarouter-hello-world" keywords like "orcarouter", "gateway", or the skill name.
allowed-tools: Bash(curl:*), Bash(python3:*), Bash(node:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Kus Wardhanie <kuswardhanietidims-svg@users.noreply.github.com>
tags:
- saas
- orcarouter
- api
- quickstart
- hello-world
compatibility: Designed for Claude Code
---
# OrcaRouter Hello World

## Overview

Send a minimal chat completion through OrcaRouter's OpenAI-compatible gateway and read the response format. All requests hit the single endpoint `POST https://api.orcarouter.ai/v1/chat/completions`. Model IDs are provider-prefixed (`openai/gpt-4o-mini`, `anthropic/claude-sonnet-4.6`) or first-party routers (`orcarouter/fusion`, `orcarouter/auto`, `orcarouter/free`) — see [Models](https://docs.orcarouter.ai/getting-started/models).

## Prerequisites

- An OrcaRouter API key (`sk-orca-...`) exported as `ORCAROUTER_API_KEY` — see `orcarouter-install-auth`
- `curl` and `jq`, or Python 3.8+ / Node.js 18+ with the OpenAI SDK
- Credits for paid models, or `orcarouter/free` for no-credit testing

## Instructions

1. Export the key: `export ORCAROUTER_API_KEY="sk-orca-..."`.
2. Send the minimal cURL request below and confirm `choices[0].message.content` comes back.
3. Read the Response Format section to identify the key fields (`id`, `model`, `usage`, `finish_reason`).
4. Repeat from your app language with the Python or TypeScript example.
5. Swap model IDs per Try Different Models to confirm multi-model access works with the same code.

## Minimal Request (cURL)

```bash
curl -s https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "orcarouter/fusion",
    "messages": [{"role": "user", "content": "Say OK"}],
    "max_tokens": 200
  }' | jq .
```

## Response Format

```json
{
  "id": "gen-1788050260-PWmZqEcZ7klxZ7l0I8YY",
  "object": "chat.completion",
  "created": 1788050260,
  "model": "orcarouter/fusion",
  "choices": [{
    "index": 0,
    "message": { "role": "assistant", "content": "OK" },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 69,
    "completion_tokens": 34,
    "total_tokens": 103
  }
}
```

Key fields:

- `id` (`gen-...`) — the request ID; every response also carries an `X-Orca-Request-Id` header for cost lookups
- `model` — the model identifier from your request
- `usage` — token counts (reasoning models add `completion_tokens_details.reasoning_tokens`)
- `finish_reason` — `stop` (complete), `length` (hit `max_tokens`), `tool_calls` (function call), `content_filter`

### Seeing which concrete model served a routed request

When you call a first-party router such as `orcarouter/auto` or `orcarouter/fusion`, the concrete model the router resolved to is reported in the `X-Orca-Resolved-Model` response header (with `X-Orca-Router` naming the router). Read it with `-i`/`-v` in cURL or `.headers` in the SDKs. See [Response Headers](https://docs.orcarouter.ai/routing/response-headers).

## Python Example

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

r = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "What is OrcaRouter in one sentence?"}],
    max_tokens=200,
)

print(r.choices[0].message.content)
print(f"Model: {r.model}")
print(f"Tokens: {r.usage.prompt_tokens} prompt + {r.usage.completion_tokens} completion")
```

## TypeScript Example

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://api.orcarouter.ai/v1",
  apiKey: process.env.ORCAROUTER_API_KEY,
});

const r = await client.chat.completions.create({
  model: "orcarouter/fusion",
  messages: [{ role: "user", content: "What is OrcaRouter in one sentence?" }],
  max_tokens: 200,
});

console.log(r.choices[0].message.content);
console.log(`Model: ${r.model} | Tokens: ${r.usage?.total_tokens}`);
```

## Try Different Models

```python
models_to_try = [
    "orcarouter/fusion",         # Frontier panel + judge
    "orcarouter/fusion-flash",   # Budget panel
    "orcarouter/fusion-mini",    # Lean two-model panel
    "orcarouter/free",           # No-credit router over free models
    "orcarouter/auto",           # Auto router, sizes the model per request
    "anthropic/claude-sonnet-4.6",  # Provider-qualified model ID
]

for model_id in models_to_try:
    try:
        r = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
        )
        print(f"{model_id} -> {r.model}: {r.choices[0].message.content}")
    except Exception as e:
        print(f"{model_id}: {e}")
```

## Output

A successful round-trip produces:

- A chat completion JSON with `choices[0].message.content`, a `gen-...` request `id`, the model identifier, and `usage` token counts
- Console output from the SDK examples: the reply text, the model name, and token counts

## Examples

```text
$ curl -s https://api.orcarouter.ai/v1/chat/completions ... | jq .choices[0].message.content
"OK"
```

```text
OrcaRouter is an AI gateway that routes requests across many models behind one OpenAI-compatible endpoint.
Model: orcarouter/fusion
Tokens: 69 prompt + 34 completion
```

More worked examples (cURL with full expected response, SDK variants): `references/examples.md`.

## Error Handling

| HTTP | Cause | Fix |
|------|-------|-----|
| 401 | Invalid or missing API key | Verify `sk-orca-...` key is exported |
| 404 | Wrong base URL or invalid model ID | Use `https://api.orcarouter.ai/v1`; check IDs via `/v1/models` |
| 400 | Malformed JSON, missing `messages`, or a policy block | Ensure `messages` is valid; branch on `error.code` for policy blocks |
| 429 | Rate limit or credit constraint | Check `Retry-After`; top up or wait |

## Enterprise Considerations

- Always set `max_tokens` to prevent unbounded completions
- Read the `X-Orca-Resolved-Model` header to log which concrete model served a routed request
- For per-request cost, send `X-OrcaRouter-Include-Cost: true` and read `usage.cost_usd`, or look the request up with `GET /v1/generation` — see `orcarouter-cost-observability`
- Test with `orcarouter/free` first, then switch to production models

## References

- Examples and routing behavior notes: `references/examples.md`
- [OrcaRouter quickstart](https://docs.orcarouter.ai/getting-started/quickstart) · [Models](https://docs.orcarouter.ai/getting-started/models) · [Response Headers](https://docs.orcarouter.ai/routing/response-headers)
