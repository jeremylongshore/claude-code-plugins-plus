---
name: openrouter-multi-provider
description: |
  Use multiple AI providers (OpenAI, Anthropic, Google, Meta) through OpenRouter's unified API. Use when comparing providers, building cross-provider workflows, or maximizing availability. Triggers: 'openrouter providers', 'multi provider', 'openrouter openai anthropic', 'compare models openrouter'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, multi-provider, comparison]

---
# OpenRouter Multi-Provider

## Overview

OpenRouter's unified API lets you access models from OpenAI, Anthropic, Google, Meta, Mistral, and others with a single API key and endpoint. Model IDs use `provider/model-name` format. The same OpenAI SDK code works for any provider by simply changing the model ID. This skill covers provider comparison, cross-provider routing, feature normalization, and BYOK (Bring Your Own Key).

## Provider Landscape

```bash
# List all providers and their model counts
curl -s https://openrouter.ai/api/v1/models | jq '
  [.data[].id | split("/")[0]] |
  group_by(.) | map({provider: .[0], models: length}) |
  sort_by(-.models)'
```

## Cross-Provider Comparison

```python
import os, time, json
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

def compare_models(prompt: str, models: list[str], max_tokens: int = 500) -> list[dict]:
    """Run the same prompt across multiple models and compare results."""
    results = []
    for model in models:
        start = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0,
            )
            latency = (time.monotonic() - start) * 1000
            results.append({
                "model": model,
                "served_by": response.model,
                "content": response.choices[0].message.content[:200] + "...",
                "tokens": response.usage.prompt_tokens + response.usage.completion_tokens,
                "latency_ms": round(latency, 1),
                "status": "ok",
            })
        except Exception as e:
            results.append({"model": model, "status": "error", "error": str(e)})

    return results

# Compare top-tier models on the same task
results = compare_models(
    "Explain the CAP theorem in distributed systems",
    models=[
        "anthropic/claude-3.5-sonnet",   # Anthropic
        "openai/gpt-4o",                 # OpenAI
        "google/gemini-2.0-flash-001",   # Google
        "meta-llama/llama-3.1-70b-instruct",  # Meta (open-source)
    ],
)
for r in results:
    print(f"{r['model']}: {r.get('latency_ms', 'N/A')}ms, {r.get('tokens', 'N/A')} tokens")
```

## Provider Strength Matrix

| Provider | Best For | Example Models | Price Range |
|----------|----------|---------------|-------------|
| Anthropic | Analysis, safety, long context | `claude-3.5-sonnet`, `claude-3-haiku` | $0.25-$15/1M |
| OpenAI | Code generation, tool calling | `gpt-4o`, `gpt-4o-mini`, `o1` | $0.15-$60/1M |
| Google | Multimodal, huge context (1M) | `gemini-2.0-flash-001`, `gemini-pro` | $0.075-$7/1M |
| Meta | Budget tasks, self-hosting | `llama-3.1-8b-instruct`, `llama-3.1-70b-instruct` | $0.06-$0.90/1M |
| Mistral | European data residency, code | `mistral-large`, `mixtral-8x7b` | $0.24-$8/1M |

## Provider-Specific Routing

```python
# Force specific provider for a model
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
    extra_body={
        "provider": {
            "order": ["Anthropic"],        # Direct to Anthropic
            "allow_fallbacks": False,       # Don't fall back to other providers
        },
    },
)

# Cross-provider fallback: if Anthropic is down, try via AWS Bedrock
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
```

## BYOK (Bring Your Own Key)

```python
# Use your own provider API key through OpenRouter
# Configure BYOK in the OpenRouter dashboard:
# Settings > Integrations > Add Provider Key

# Benefits:
# - First 1M requests/month free via OpenRouter
# - After that, 5% of normal provider cost (vs full OpenRouter markup)
# - Data flows directly to provider under your account
# - Useful for high-volume production workloads

# With BYOK configured, requests automatically use your provider key
response = client.chat.completions.create(
    model="openai/gpt-4o",  # Uses YOUR OpenAI key, routed through OpenRouter
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
)
```

## Feature Normalization

```python
def normalized_completion(messages, model, **kwargs):
    """Handle provider-specific feature differences."""
    # JSON mode: OpenAI native, others via system prompt
    if kwargs.pop("json_mode", False):
        if model.startswith("openai/"):
            kwargs["response_format"] = {"type": "json_object"}
        else:
            # Add JSON instruction to system prompt for non-OpenAI models
            messages = [{"role": "system", "content": "Respond in valid JSON only."}] + [
                m for m in messages if m["role"] != "system"
            ] + [m for m in messages if m["role"] == "system"]

    return client.chat.completions.create(model=model, messages=messages, **kwargs)
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Feature not supported | Provider lacks capability (e.g., tools on Llama) | Check model capabilities via `/models`; use fallback |
| Different response quality | Providers trained differently | Test critical prompts per model; adjust system prompts |
| Provider outage | Single provider down | Use `provider.order` with fallbacks across providers |
| BYOK auth failure | Provider key expired or invalid | Update provider key in OpenRouter dashboard |

## Enterprise Considerations

- OpenRouter normalizes the API, but models differ in output quality, feature support, and data policies
- Use `provider.order` + `allow_fallbacks: true` for cross-provider resilience
- Test the same prompts across providers during evaluation; don't assume equal quality
- BYOK eliminates OpenRouter margin for high-volume workloads (5% vs standard markup)
- Route regulated data only to approved providers using `allow_fallbacks: false`
- Monitor which provider actually serves each request (`response.model`) for attribution

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Supported Providers](https://openrouter.ai/models) | [Provider Routing](https://openrouter.ai/docs/features/provider-routing)
