---
name: orcarouter-fallback-reliability
description: |
  Make OrcaRouter calls resilient with fallback and retry patterns. Use when a
  primary model is down or rate-limited, when you need an automatic fallback
  chain, or when you are hardening a production LLM path. Triggers:
  "orcarouter fallback", "orcarouter failover", "orcarouter retry",
  "resilience", "reliability", "circuit breaker".
  Trigger with "orcarouter-fallback-reliability" keywords like "orcarouter", "gateway", or the skill name.
allowed-tools: Bash(curl:*), Bash(python3:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Kus Wardhanie <kuswardhanietidims-svg@users.noreply.github.com>
tags:
- saas
- orcarouter
- reliability
- fallback
- failover
- production
compatibility: Designed for Claude Code
---
# OrcaRouter Fallback & Reliability

## Overview

Build resilience into OrcaRouter calls. The gateway supports **server-side fallback chains** via `extra_body.models` + `route: "fallback"` — if the primary model fails (5xx / 429 / network error), the gateway tries the next entry before returning. On top of that you layer client-side retries with backoff for the cases the gateway cannot absorb (auth, a chain that exhausted every entry, budget). This skill covers both layers.

## Prerequisites

- An OrcaRouter API key (`sk-orca-...`) exported as `ORCAROUTER_API_KEY`
- Python 3.8+ / Node.js 18+ with the OpenAI SDK, or cURL + jq
- At least two model IDs you can call (see `orcarouter-model-routing`)

## Instructions

1. Start with a server-side fallback chain (`extra_body.models` + `route: "fallback"`) for upstream failures.
2. Add client-side retries with exponential backoff for 429 and transient 5xx.
3. Fail fast on 4xx (except 408/429) and on gateway policy blocks (`guardrail_blocked` / `firewall_blocked` — these are deterministic, skip-retry).
4. Log the served model from the `X-Orca-Fallback-Model` header to verify the chain.

## Server-Side Fallback Chain

The gateway tries the chain in order. The top-level `model` is the first attempt; when the chain is present the gateway uses it. Max 5 models; same endpoint type recommended (e.g. all chat models). Billing is for the model that actually served.

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

r = client.chat.completions.create(
    model="anthropic/claude-sonnet-4.6",   # primary
    messages=[{"role": "user", "content": "Critical task"}],
    max_tokens=200,
    extra_body={
        "models": [
            "anthropic/claude-sonnet-4.6",
            "openai/gpt-4o-mini",
            "google/gemini-2.5-flash",
        ],
        "route": "fallback",
    },
)
```

The response headers `X-Orca-Fallback-Level` (0 = primary served) and `X-Orca-Fallback-Model` name the model that served the request. See [Model Fallbacks](https://docs.orcarouter.ai/routing/model-fallbacks).

```bash
curl -si https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-sonnet-4.6",
    "messages": [{"role": "user", "content": "Critical task"}],
    "max_tokens": 200,
    "extra_body": {
      "models": ["anthropic/claude-sonnet-4.6", "openai/gpt-4o-mini", "google/gemini-2.5-flash"],
      "route": "fallback"
    }
  }' | grep -iE '^x-orca-fallback|content'
```

## Client-Side Retry with Backoff

On a `429`, read `Retry-After`, wait that long, retry the same request; if a second `429` occurs, double the wait up to 60s. The OpenAI SDKs handle `Retry-After` automatically by default. Custom code is only needed if you disabled SDK retries:

```python
from openai import OpenAI
import os, time

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
    max_retries=0,  # we manage retries ourselves below
)

def call_with_retry(**kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = min(60, 2 ** attempt)  # 1s, 2s, 4s ...
            print(f"retry in {wait}s after: {e}")
            time.sleep(wait)

r = call_with_retry(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)
```

## What Not to Retry

- **4xx (except 408/429)** — retrying a malformed request wastes quota
- **401** — invalid key; fix config and fail fast
- **`guardrail_blocked` / `firewall_blocked` / `firewall_approval_pending`** — deterministic policy blocks marked skip-retry; fix the input or resolve the approval instead (see `orcarouter-agent-security`)
- **Free-tier `429` without `Retry-After`** — the request exceeded the free tier's prompt cap; retrying unchanged fails forever

## Output

A resilient call path returns a completion. When the primary route fails, the gateway (server-side chain) or your client retry loop handles it, and the response headers tell you which model served. Transient 429/5xx become handled delays instead of raised exceptions.

## Examples

```text
# Server-side chain fell back after the primary 5xx'd:
x-orca-fallback-level: 1
x-orca-fallback-model: openai/gpt-4o-mini

# Client retry handled a 429:
retry in 1s after: 429 rate limited
retry in 2s after: 429 rate limited
```

More reliability patterns (circuit breaker, idempotency, timeout budgets): `references/reliability-patterns.md`.

## Error Handling

| HTTP | Cause | Client response |
|------|-------|-----------------|
| 429 | Rate limit | Wait `Retry-After`, retry; then exponential backoff |
| 5xx | Upstream provider failure | Server-side fallback chain handles most; client retry handles the rest |
| 401 | Invalid key | Do not retry — fail fast with a config error |
| 400 | Bad request or policy block | Do not retry; branch on `error.code` for policy blocks |

## Enterprise Considerations

- Do not retry 4xx (except 408/429) — retrying a malformed request wastes quota
- Set a timeout budget per call; total chain latency = sum of attempts
- Log `X-Orca-Fallback-Model` on every hop for audit and cost control
- Combine server-side fallback chains with client retries for the strongest path

## References

- Circuit breaker and timeout patterns: `references/reliability-patterns.md`
- [Model Fallbacks](https://docs.orcarouter.ai/routing/model-fallbacks) · [Rate Limits](https://docs.orcarouter.ai/operations/rate-limits) · [Free Models](https://docs.orcarouter.ai/routing/free-models)
