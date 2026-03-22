---
name: openrouter-model-routing
description: |
  Implement intelligent model routing to optimize cost, quality, and latency on OpenRouter. Use when building multi-model systems or optimizing spend across task types. Triggers: 'openrouter routing', 'model routing', 'route to model', 'model selection openrouter'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, routing, cost-optimization, model-selection]

---
# OpenRouter Model Routing

## Overview

OpenRouter gives you access to 100+ models through one API. The key to cost efficiency is routing each request to the right model based on task complexity, required capabilities, cost budget, and latency requirements. This skill covers task-based routing, complexity classification, cost-aware selection, and OpenRouter's native routing features.

## Task-Based Router

```python
import os, re
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

# Model tiers by cost and capability
MODELS = {
    "free":    "google/gemma-2-9b-it:free",          # $0/0 — testing only
    "budget":  "meta-llama/llama-3.1-8b-instruct",   # $0.06/$0.06 per 1M
    "mid":     "openai/gpt-4o-mini",                  # $0.15/$0.60 per 1M
    "standard":"anthropic/claude-3.5-sonnet",         # $3/$15 per 1M
    "premium": "openai/o1",                           # $15/$60 per 1M
}

TASK_ROUTING = {
    "classification":  "budget",   # Simple label assignment
    "translation":     "mid",      # Moderate quality needed
    "summarization":   "mid",      # Good quality, cost-effective
    "code_generation": "standard", # Needs high accuracy
    "code_review":     "standard", # Needs reasoning
    "analysis":        "standard", # Complex reasoning
    "creative_writing":"standard", # Quality matters
    "deep_reasoning":  "premium",  # Multi-step logic
    "simple_qa":       "budget",   # Basic questions
    "chat":            "mid",      # General conversation
}

def route_request(task_type: str, messages: list[dict], **kwargs) -> dict:
    """Route to appropriate model based on task type."""
    tier = TASK_ROUTING.get(task_type, "mid")
    model = MODELS[tier]

    response = client.chat.completions.create(
        model=model, messages=messages, **kwargs
    )
    return {
        "content": response.choices[0].message.content,
        "model": response.model,
        "tier": tier,
        "tokens": response.usage.prompt_tokens + response.usage.completion_tokens,
    }
```

## Complexity-Based Auto-Router

```python
def classify_complexity(prompt: str) -> str:
    """Classify prompt complexity to select model tier.

    Simple heuristics -- replace with a trained classifier for production.
    """
    word_count = len(prompt.split())
    has_code = bool(re.search(r'```|def |function |class |import ', prompt))
    has_reasoning = bool(re.search(r'explain|analyze|compare|why|how does|trade.?off', prompt, re.I))
    has_math = bool(re.search(r'calculate|equation|formula|derive|proof', prompt, re.I))

    if has_math or (has_reasoning and has_code):
        return "premium"
    if has_code or has_reasoning or word_count > 500:
        return "standard"
    if word_count > 100:
        return "mid"
    return "budget"

def auto_route(messages: list[dict], **kwargs):
    """Automatically select model based on prompt complexity."""
    user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    tier = classify_complexity(user_msg)
    model = MODELS[tier]

    response = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return response
```

## OpenRouter Native Routing

```python
# Route: "fallback" — try models in order until one succeeds
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
    extra_body={
        "models": [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
        ],
        "route": "fallback",
    },
)

# Provider routing — control which provider serves a model
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
    extra_body={
        "provider": {
            "order": ["Anthropic", "AWS Bedrock"],
            "allow_fallbacks": True,
        },
    },
)

# Model variant: ":floor" picks cheapest provider
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet:floor",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
)
```

## Cost-Aware Router

```python
import requests

def get_model_pricing() -> dict:
    """Fetch current pricing for cost-aware routing."""
    models = requests.get("https://openrouter.ai/api/v1/models").json()["data"]
    return {
        m["id"]: {
            "prompt": float(m["pricing"]["prompt"]) * 1_000_000,
            "completion": float(m["pricing"]["completion"]) * 1_000_000,
            "context": m["context_length"],
        }
        for m in models
    }

def cheapest_model_for_task(pricing: dict, min_context: int = 4096,
                             needs_tools: bool = False) -> str:
    """Find the cheapest model that meets requirements."""
    candidates = [
        (mid, p) for mid, p in pricing.items()
        if p["context"] >= min_context and p["prompt"] > 0  # Exclude free (unreliable)
    ]
    candidates.sort(key=lambda x: x[1]["prompt"] + x[1]["completion"])
    return candidates[0][0] if candidates else "openai/gpt-4o-mini"
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Wrong model selected | Classification too coarse | Add more task categories; test with diverse prompts |
| Model unavailable | Selected model temporarily down | Add fallback chain per tier |
| Cost overrun | Complex tasks routed to premium models | Set `max_tokens` and daily budget caps |
| Quality regression | Budget model can't handle task | Monitor output quality; escalate tier on poor results |

## Enterprise Considerations

- Start with manual task-type routing (explicit labels), then graduate to auto-classification
- Log every routing decision (task type, tier, model, cost) to tune the router over time
- Use OpenRouter's `:floor` variant to automatically get the cheapest provider for any model
- Set `max_tokens` on every request to cap per-request cost regardless of model tier
- A/B test routing rules: send 10% of traffic to a different tier and compare quality metrics
- Combine with fallback chains so each tier has backup models

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Model Routing](https://openrouter.ai/docs/features/model-routing) | [Provider Routing](https://openrouter.ai/docs/features/provider-routing)
