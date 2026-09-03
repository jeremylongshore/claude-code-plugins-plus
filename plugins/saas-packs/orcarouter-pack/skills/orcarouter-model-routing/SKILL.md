---
name: orcarouter-model-routing
description: |
  Route requests across models with OrcaRouter's routers and provider-prefixed
  model IDs, and read which concrete model served each request. Use when
  picking a model per task, comparing model quality/cost/latency, or relying on
  the gateway's routing instead of hard-coding model IDs. Triggers: "orcarouter
  routing", "orcarouter model selection", "which model", "adaptive routing",
  "route my request".
  Trigger with "orcarouter-model-routing" keywords like "orcarouter", "gateway", or the skill name.
allowed-tools: Bash(curl:*), Bash(python3:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Kus Wardhanie <kuswardhanietidims-svg@users.noreply.github.com>
tags:
- saas
- orcarouter
- routing
- model-selection
- ai-gateway
compatibility: Designed for Claude Code
---
# OrcaRouter Model Routing

## Overview

Choose how a request gets routed across models. OrcaRouter exposes provider-prefixed model IDs (`openai/gpt-4o-mini`, `anthropic/claude-sonnet-4.6`) plus first-party `orcarouter/*` options: **named routers** (`orcarouter/auto`, `orcarouter/free`) that resolve a model per request, and **fusion panels** (`orcarouter/fusion`, `orcarouter/fusion-flash`, `orcarouter/fusion-mini`) that run a curated panel of frontier models in parallel and return the single strongest answer.

You can also pin a provider-prefixed ID when you need a specific model. This skill covers both patterns.

## Prerequisites

- An OrcaRouter API key (`sk-orca-...`) exported as `ORCAROUTER_API_KEY`
- The OpenAI SDK or cURL (see `orcarouter-install-auth`)
- Familiarity with the `/v1/models` catalog (see `orcarouter-hello-world`)

## Instructions

1. Decide the routing mode: a router/fusion slug (`orcarouter/*`) or a pinned provider-prefixed ID.
2. Send the request and read the `X-Orca-Resolved-Model` response header to see which concrete model served it (present when you call a named `orcarouter/*` router).
3. For pinned routing, use the exact provider/model ID from `/v1/models`.
4. When the pinned model is unavailable, wrap the call in a fallback chain (`extra_body.models` or a client-side chain — see `orcarouter-fallback-reliability`).

## Routing via a Router (cURL)

```bash
curl -si https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "orcarouter/auto",
    "messages": [{"role": "user", "content": "Write a one-line haiku"}],
    "max_tokens": 100
  }' | grep -iE '^x-orca-|content'
```

The `X-Orca-Resolved-Model` header tells you which concrete model the router picked. See [Response Headers](https://docs.orcarouter.ai/routing/response-headers).

## Routing Tiers

| Model ID | What it is | Use when |
| -------- | -------- | -------- |
| `orcarouter/auto` | Auto router (per-account): sizes model strength to request difficulty | You want routing to "just work" without pinning |
| `orcarouter/fusion` | Frontier panel (Claude Opus 4.8 · GPT-5.5 · Gemini 3.1 Pro) + judge | Hardest reasoning and code |
| `orcarouter/fusion-mini` | Lean two-model panel + judge | A cheaper frontier option |
| `orcarouter/fusion-flash` | Budget panel of cheaper models | Cost-sensitive fan-out |
| `orcarouter/free` | Named router over the no-credit `-free` models | CI, smoke tests, dev loop |

Fusion panels bill as the sum of the panel legs plus the judge call (zero markup) — only on requests that fan out. See [Fusion](https://docs.orcarouter.ai/routing/fusion) and [Auto Router](https://docs.orcarouter.ai/routing/auto-router).

## Pinned Routing (Python)

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

# Pin a specific model when the task needs it
r = client.chat.completions.create(
    model="anthropic/claude-sonnet-4.6",
    messages=[{"role": "user", "content": "Explain recursion simply"}],
    max_tokens=200,
)
print(r.choices[0].message.content)
```

## Task-Based Selection

Use the routing option as the lever per task:

| Task shape | Recommended |
| ---------- | ----------- |
| Complex reasoning, long context | Pin `anthropic/claude-sonnet-4.6`/`anthropic/claude-opus-4.7`, or `orcarouter/fusion` |
| General assistant, cost-aware | `orcarouter/auto` |
| High-volume, latency-sensitive | `orcarouter/fusion-flash` or a cheap pinned model |
| Smoke tests, CI, dev loop | `orcarouter/free` |

## Output

A successful routing call returns the completion plus `usage`. When you called a named `orcarouter/*` router, the `X-Orca-Resolved-Model` header records which concrete model served the request — log it for audit. The resolved model can change between calls as the router re-optimizes.

## Examples

```text
$ curl -si https://api.orcarouter.ai/v1/chat/completions ... -d '{"model":"orcarouter/auto",...}' | grep -i x-orca-resolved-model
x-orca-resolved-model: openai/gpt-4o-mini
```

```text
Task: haiku → routed through orcarouter/auto → resolved to openai/gpt-4o-mini
```

More routing patterns (fallback chains, cost ceilings, capability hints): `references/routing-patterns.md`.

## Error Handling

| HTTP | Cause | Fix |
|------|-------|-----|
| 400 | Invalid model ID or routing hint | Check `/v1/models`; use a valid `orcarouter/*` or provider-prefixed ID |
| 404 | Model not currently served | Add a fallback chain or retry |
| 429 | Rate limit or credit constraint | Respect `Retry-After`; use `orcarouter/free` for testing |
| 402 | Insufficient credits for the routed model | Add credits or switch to a cheaper routing tier |

## Enterprise Considerations

- Log the `X-Orca-Resolved-Model` header — the gateway's routing decision is part of the request record
- Set a cost ceiling by choosing a cheaper tier/panel or pinning a known-price model
- Combine a router with a pinned fallback for critical paths (see `orcarouter-fallback-reliability`)

## References

- Routing patterns and fallback examples: `references/routing-patterns.md`
- [Auto Router](https://docs.orcarouter.ai/routing/auto-router) · [Fusion](https://docs.orcarouter.ai/routing/fusion) · [Models](https://docs.orcarouter.ai/getting-started/models) · `/v1/models` catalog at `https://api.orcarouter.ai/v1/models`
