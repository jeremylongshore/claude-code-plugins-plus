---
name: openrouter-fallback-config
description: 'Configure automatic model fallbacks for high availability on OpenRouter.
  Use when building resilient systems that need to survive provider outages. Triggers:
  ''openrouter fallback'', ''model fallback'', ''openrouter failover'', ''openrouter
  backup model''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(curl:*), Bash(jq:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- reliability
- fallback
- high-availability
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Fallback Config

## Overview

OpenRouter supports native model fallbacks: pass multiple model IDs and OpenRouter tries each in order until one succeeds. You can also use `provider.order` to control which provider serves a specific model. This skill covers native fallbacks, provider routing, client-side fallback chains, and timeout configuration.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with the OpenAI SDK (`pip install openai`) for the fallback patterns; `curl` and `jq` for the Testing Fallbacks step
- A ranked list of acceptable models for your workload, matched by capability (tool calling, vision, context length) so a fallback never silently drops a feature you depend on

## Instructions

1. Start with Native Model Fallback (Server-Side): pass a `models` array plus `route: "fallback"` in `extra_body` and let OpenRouter try each model in order.
2. Log `response.model` after every call — it tells you which model actually served the request, which is how you detect that a fallback fired.
3. If you need the *same* model from specific vendors (e.g., Claude via Anthropic direct vs AWS Bedrock), use Provider Fallback with `provider.order` and `allow_fallbacks`.
4. For per-model timeouts and custom error handling, implement the Client-Side Fallback Chain: `resilient_completion()` walks `FALLBACK_CHAIN` (primary → secondary → budget-fallback → last-resort) and raises once every entry fails.
5. Pick chains per feature with Fallback with Capability Matching — `CAPABILITY_CHAINS` keeps tool-calling, vision, long-context, and budget workloads on models that actually support them.
6. Verify the behavior with Testing Fallbacks: send the curl request with an invalid primary model and confirm the response comes back from `openai/gpt-4o-mini`.

## Native Model Fallback (Server-Side)

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

# Pass multiple models -- OpenRouter tries each in order
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",  # Primary (used for param validation)
    messages=[{"role": "user", "content": "Explain recursion"}],
    max_tokens=500,
    extra_body={
        "models": [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "google/gemini-2.0-flash-001",
        ],
        "route": "fallback",  # Try in order until one succeeds
    },
)

# Check which model actually served the request
print(f"Served by: {response.model}")
```

## Provider Fallback (Same Model, Different Providers)

```python
# Route to specific providers in priority order
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
    extra_body={
        "provider": {
            "order": ["Anthropic", "AWS Bedrock", "GCP Vertex"],
            "allow_fallbacks": True,  # Fall to next provider if first fails
        },
    },
)
```

## Client-Side Fallback Chain

```python
import logging
from openai import OpenAI, APIError, APITimeoutError

log = logging.getLogger("openrouter.fallback")

FALLBACK_CHAIN = [
    {"model": "anthropic/claude-3.5-sonnet", "timeout": 30.0, "label": "primary"},
    {"model": "openai/gpt-4o", "timeout": 25.0, "label": "secondary"},
    {"model": "openai/gpt-4o-mini", "timeout": 15.0, "label": "budget-fallback"},
    {"model": "google/gemini-2.0-flash-001", "timeout": 15.0, "label": "last-resort"},
]

def resilient_completion(messages: list[dict], max_tokens: int = 1024, **kwargs):
    """Try each model in the fallback chain until one succeeds."""
    last_error = None

    for config in FALLBACK_CHAIN:
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
                timeout=config["timeout"],
                default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
            )
            response = client.chat.completions.create(
                model=config["model"],
                messages=messages,
                max_tokens=max_tokens,
                **kwargs,
            )
            log.info(f"Served by {config['label']}: {response.model}")
            return response

        except (APIError, APITimeoutError) as e:
            last_error = e
            log.warning(f"{config['label']} failed ({config['model']}): {e}")
            continue

    raise RuntimeError(f"All fallbacks exhausted. Last error: {last_error}")
```

## Fallback with Capability Matching

```python
# Different models support different features. Match capabilities.
CAPABILITY_CHAINS = {
    "tool_calling": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
    ],
    "vision": [
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.0-flash-001",
    ],
    "long_context": [
        "google/gemini-2.0-flash-001",    # 1M context
        "anthropic/claude-3.5-sonnet",     # 200K context
        "openai/gpt-4o",                   # 128K context
    ],
    "budget": [
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.1-8b-instruct",
        "google/gemma-2-9b-it:free",
    ],
}

def capability_fallback(messages, capability="tool_calling", **kwargs):
    """Select fallback chain based on required capability."""
    chain = CAPABILITY_CHAINS.get(capability, CAPABILITY_CHAINS["tool_calling"])
    return resilient_completion(messages, **kwargs)  # Uses FALLBACK_CHAIN
```

## Testing Fallbacks

```bash
# Test with an invalid model to trigger fallback
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "invalid/model-name",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10,
    "models": ["invalid/model-name", "openai/gpt-4o-mini"],
    "route": "fallback"
  }' | jq '{model: .model, content: .choices[0].message.content}'
# Should succeed with openai/gpt-4o-mini
```

## Output

A configured fallback setup produces:

- Chat completions whose `response.model` field reveals the model that actually served each request — the primary when healthy, a chain entry when a fallback fired
- Log lines from `resilient_completion()`: `Served by primary: anthropic/claude-3.5-sonnet` on success, `primary failed (anthropic/claude-3.5-sonnet): ...` warnings per failed hop
- A `RuntimeError("All fallbacks exhausted. Last error: ...")` when every model in `FALLBACK_CHAIN` fails — the signal to alert on
- From the Testing Fallbacks curl: a `{model, content}` JSON showing the request survived an invalid primary model

## Examples

Force a fallback by putting an invalid model first in the `models` array:

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "invalid/model-name", "messages": [{"role": "user", "content": "test"}],
       "max_tokens": 10, "models": ["invalid/model-name", "openai/gpt-4o-mini"], "route": "fallback"}' \
  | jq '{model: .model, content: .choices[0].message.content}'
```

```json
{"model": "openai/gpt-4o-mini", "content": "Test received!"}
```

The `model` field proves the fallback chain worked. More worked examples: `references/examples.md`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| All fallbacks exhausted | Every model in chain failed | Add more diverse providers; alert on full chain failure |
| Slow cascade | Each model timing out sequentially | Reduce per-model timeout to 10-15s |
| Inconsistent responses | Different models have different capabilities | Ensure all fallback models support features your prompt uses |
| Wrong model served | Fallback triggered unexpectedly | Log which model served each request; check primary model health |

## Enterprise Considerations

- Use server-side fallback (`models` + `route: "fallback"`) for simplicity; client-side for fine-grained control
- Set per-model timeouts -- expensive models get longer timeouts, budget fallbacks get shorter
- Log which model served each request to track fallback frequency (indicates primary model issues)
- Test fallback chains regularly by intentionally failing the primary model
- Match fallback models by capability (tool calling, vision, context length) to avoid silent feature degradation
- Use `provider.order` when you need the same model from a different provider (e.g., Claude via Anthropic direct vs AWS Bedrock)

## References

- Examples | Errors
- [Model Routing](https://openrouter.ai/docs/features/model-routing) | [Provider Routing](https://openrouter.ai/docs/features/provider-routing)
