---
name: openrouter-openai-compat
description: |
  Migrate from OpenAI to OpenRouter with minimal code changes. Use when switching to OpenRouter or maintaining dual compatibility. Triggers: 'openrouter openai compatible', 'openrouter drop-in', 'openai to openrouter', 'openrouter migration'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, api, migration, openai]

---
# OpenRouter OpenAI Compatibility

## Overview

OpenRouter implements the OpenAI Chat Completions API specification (`/v1/chat/completions`). Existing OpenAI SDK code works with OpenRouter by changing two values: `base_url` and `api_key`. This gives you access to 400+ models from all providers through the same SDK interface.

## The Two-Line Migration

### Python (Before)
```python
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])  # OpenAI direct
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### Python (After)
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",              # Changed
    api_key=os.environ["OPENROUTER_API_KEY"],              # Changed
    default_headers={
        "HTTP-Referer": "https://your-app.com",            # Added (optional)
        "X-Title": "Your App",                             # Added (optional)
    },
)
response = client.chat.completions.create(
    model="openai/gpt-4o",  # Prefix with provider namespace
    messages=[{"role": "user", "content": "Hello"}],
)
```

### TypeScript (After)
```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: { "HTTP-Referer": "https://your-app.com", "X-Title": "Your App" },
});

const res = await client.chat.completions.create({
  model: "openai/gpt-4o",
  messages: [{ role: "user", content: "Hello" }],
});
```

## Model ID Mapping

| OpenAI Direct | OpenRouter ID |
|---------------|---------------|
| `gpt-4o` | `openai/gpt-4o` |
| `gpt-4o-mini` | `openai/gpt-4o-mini` |
| `gpt-4-turbo` | `openai/gpt-4-turbo` |
| `o1` | `openai/o1` |
| `o1-mini` | `openai/o1-mini` |

You also gain access to non-OpenAI models through the same SDK:
```python
# Same client, any provider
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",  # Anthropic
    messages=[{"role": "user", "content": "Hello"}],
)

response = client.chat.completions.create(
    model="google/gemini-2.0-flash",  # Google
    messages=[{"role": "user", "content": "Hello"}],
)
```

## What Works Identically

| Feature | Status | Notes |
|---------|--------|-------|
| `chat.completions.create` | Fully supported | Main endpoint, all parameters |
| `stream: true` | Fully supported | SSE format identical to OpenAI |
| `tools` / `tool_choice` | Supported | OpenRouter transforms for non-OpenAI providers |
| `response_format: { type: "json_object" }` | Supported | Basic JSON mode |
| `response_format: { type: "json_schema" }` | Supported | Strict schema mode |
| `temperature`, `top_p`, `max_tokens` | Supported | Standard parameters |
| `stop` sequences | Supported | Array of stop strings |
| `n` (multiple completions) | Supported | Multiple choices |

## What Differs

| Feature | Difference | Workaround |
|---------|-----------|------------|
| Model IDs | Prefixed with `provider/` | Update model strings |
| `organization` param | Not used | Remove from client init |
| Embeddings | Limited support | Use direct provider or dedicated embedding service |
| Fine-tuned models | Not directly accessible | Use provider's fine-tuned model ID if hosted |
| `logprobs` | Model-dependent | Check model capabilities via `/api/v1/models` |
| Responses API | Beta support | Use `/api/v1/responses` endpoint |

## OpenRouter-Only Features

These are available through the same SDK but are unique to OpenRouter:

```python
# Model fallbacks (try models in order)
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={
        "models": [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "google/gemini-2.0-flash",
        ],
        "route": "fallback",
    },
)

# Provider preferences
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={
        "provider": {
            "order": ["anthropic"],             # Prefer Anthropic direct
            "allow_fallbacks": True,
            "sort": "price",                    # Cheapest first
        },
    },
)

# Plugins (web search, response healing)
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "What happened today?"}],
    extra_body={
        "plugins": [{"id": "web"}],  # Enable real-time web search
    },
)
```

## Dual-Provider Pattern

```python
import os
from openai import OpenAI

def create_client(provider: str = "openrouter") -> OpenAI:
    if provider == "openai":
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        default_headers={"HTTP-Referer": "https://your-app.com"},
    )

# Switch providers without changing application code
client = create_client(os.environ.get("LLM_PROVIDER", "openrouter"))
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 400 unsupported parameter | Model doesn't support a parameter | Conditionally set params based on model capabilities |
| Different response quality | Non-OpenAI model handles prompt differently | Adjust prompts per model family; test before switching |
| Missing `organization` | OpenRouter ignores org-level auth | Remove `organization` from client init |

## Enterprise Considerations

- Use environment variables to switch between direct OpenAI and OpenRouter without code changes
- Test your full prompt suite across providers before migrating production traffic
- Monitor response quality and latency after migration; some prompts may need tuning
- OpenRouter normalizes the API across providers, but subtle behavioral differences exist between model families
- Use `extra_body` for OpenRouter-specific features (provider preferences, plugins, fallbacks)

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [OpenRouter Quickstart](https://openrouter.ai/docs/quickstart) | [API Parameters](https://openrouter.ai/docs/api/reference/parameters)
