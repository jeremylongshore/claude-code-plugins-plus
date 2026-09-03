---
name: orcarouter-install-auth
description: |
  Set up OrcaRouter API key authentication and verify connectivity to the
  gateway. Use when starting a new OrcaRouter integration, configuring
  ORCAROUTER_API_KEY for an agent or app, or checking that a key is valid.
  Triggers: "orcarouter install", "orcarouter api key", "orcarouter auth",
  "set up orcarouter", "configure orcarouter".
  Trigger with "orcarouter-install-auth" keywords like "orcarouter", "gateway", or the skill name.
allowed-tools: Bash(curl:*), Bash(python3:*), Bash(node:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Kus Wardhanie <kuswardhanietidims-svg@users.noreply.github.com>
tags:
- saas
- orcarouter
- api
- authentication
- setup
compatibility: Designed for Claude Code
---
# OrcaRouter Install & Auth

## Overview

Configure the OrcaRouter API key and verify the gateway is reachable before building anything else. OrcaRouter is an OpenAI-compatible AI gateway at `https://api.orcarouter.ai/v1`; keys use the `sk-orca-` prefix. A single key and base URL unlock the models your account can access, so auth is the only setup step. See [Get an API key](https://docs.orcarouter.ai/getting-started/get-api-key).

## Prerequisites

- An OrcaRouter account with an API key (`sk-orca-...`) — create keys in the OrcaRouter console
- `curl` and `jq` for the CLI check, or Python 3.8+ / Node.js 18+ with the OpenAI SDK for the SDK check
- No separate SDK — the OpenAI SDK points at OrcaRouter via `base_url`

## Instructions

1. Export the key: `export ORCAROUTER_API_KEY="sk-orca-..."`.
2. Run the connectivity check below and confirm you get a JSON list of models back (HTTP 200).
3. Point your OpenAI SDK client at `base_url="https://api.orcarouter.ai/v1"` with the same key.
4. Run the minimal chat completion to confirm the full round-trip.

## Connectivity Check (curl)

```bash
curl -s https://api.orcarouter.ai/v1/models \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  | jq '{count: (.data | length), first_three: [.data[0:3][].id]}'
```

A healthy response reports the model count and a few model IDs. Models are provider-prefixed (`openai/gpt-4o-mini`, `anthropic/claude-sonnet-4.6`) plus first-party routers (`orcarouter/fusion`, `orcarouter/auto`, `orcarouter/free`). The list only includes models your account can access. See [Models](https://docs.orcarouter.ai/getting-started/models).

## Python SDK Client

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

# List models
models = client.models.list()
print(f"Available models: {len(models.data)}")

# Minimal completion
r = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Say OK"}],
    max_tokens=200,
)
print(r.choices[0].message.content)
```

## TypeScript SDK Client

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://api.orcarouter.ai/v1",
  apiKey: process.env.ORCAROUTER_API_KEY,
});

const r = await client.chat.completions.create({
  model: "orcarouter/fusion",
  messages: [{ role: "user", content: "Say OK" }],
  max_tokens: 200,
});

console.log(r.choices[0].message.content);
```

## Output

A successful setup round-trip produces:

- A `models.list` response with the gateway's model catalog (the models your account can access)
- A chat completion whose `choices[0].message.content` holds the reply
- Console output from the SDK examples: the reply text plus token usage

## Examples

```text
$ curl -s https://api.orcarouter.ai/v1/models -H "Authorization: Bearer $ORCAROUTER_API_KEY" | jq '{count: (.data | length)}'
{
  "count": 204
}
```

```text
$ python3 hello.py
Say OK
```

The Python and TypeScript blocks above are the canonical setup checks; the connectivity curl is the minimal one-liner.

## Error Handling

| HTTP | Cause | Fix |
|------|-------|-----|
| 401 | Missing or invalid API key | Export `ORCAROUTER_API_KEY` with a valid `sk-orca-...` key |
| 403 | Key restricted (scope/IP/model allowlist) | Use a different model ID or check key settings in the console |
| 429 | Rate limit or credit constraint | Check `Retry-After` header; top up or wait |
| 404 | Wrong base URL or unknown model | Use `https://api.orcarouter.ai/v1`; list models via `/v1/models` |

## References

- Examples and provider-prefixed model IDs: `references/examples.md`
- [Get an API key](https://docs.orcarouter.ai/getting-started/get-api-key) · [OpenAI SDK compatibility](https://docs.orcarouter.ai/compatibility/openai-sdk) · [Models](https://docs.orcarouter.ai/getting-started/models)
