---
name: openrouter-upgrade-migration
description: |
  Migrate to OpenRouter from direct provider APIs or upgrade between SDK/model versions. Triggers: 'openrouter migrate', 'openrouter upgrade', 'switch to openrouter', 'migrate from openai to openrouter'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, migration, upgrade]

---
# OpenRouter Upgrade & Migration

## Current State
!`npm list openai 2>/dev/null | head -5`
!`pip show openai 2>/dev/null | head -5`

## Overview

Migrating to OpenRouter from a direct provider API (OpenAI, Anthropic) is minimal: change `base_url` and `api_key`, add two headers. The OpenAI SDK works natively with OpenRouter. This skill covers migrating from direct APIs, switching between models, upgrading SDK versions, and running comparison tests.

## Migration from Direct OpenAI

```python
# BEFORE: Direct OpenAI
from openai import OpenAI
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
)

# AFTER: Via OpenRouter (3 lines changed)
from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",     # ← Changed
    api_key=os.environ["OPENROUTER_API_KEY"],     # ← Changed
    default_headers={                              # ← Added
        "HTTP-Referer": "https://my-app.com",
        "X-Title": "my-app",
    },
)
response = client.chat.completions.create(
    model="openai/gpt-4o",  # ← Add provider prefix
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
)
```

## Migration from Direct Anthropic

```python
# BEFORE: Direct Anthropic SDK
import anthropic
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=200,
    messages=[{"role": "user", "content": "Hello"}],
)
content = response.content[0].text

# AFTER: Via OpenRouter (using OpenAI SDK instead of Anthropic SDK)
from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://my-app.com",
        "X-Title": "my-app",
    },
)
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",  # OpenRouter model ID
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
)
content = response.choices[0].message.content  # OpenAI response format
```

## TypeScript Migration

```typescript
// BEFORE: Direct OpenAI
import OpenAI from "openai";
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// AFTER: Via OpenRouter
const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: {
    "HTTP-Referer": "https://my-app.com",
    "X-Title": "my-app",
  },
});
// Change model from "gpt-4o" to "openai/gpt-4o"
```

## Migration Checklist

```python
MIGRATION_CHECKLIST = {
    "config": [
        "base_url changed to https://openrouter.ai/api/v1",
        "API key changed to OPENROUTER_API_KEY (sk-or-v1-...)",
        "HTTP-Referer and X-Title headers added",
        "Model IDs prefixed with provider/ (e.g., openai/gpt-4o)",
    ],
    "code": [
        "All client initialization updated",
        "Model IDs updated in all routes/configs",
        "Error handling covers OpenRouter-specific codes (402, 408)",
        "Streaming still works with new endpoint",
        "Tool/function calling still works",
    ],
    "testing": [
        "Same prompts produce comparable quality output",
        "Latency within acceptable range (expect +50-100ms)",
        "Token counts match expectations",
        "Cost tracking updated for OpenRouter pricing",
        "Fallback chain tested",
    ],
    "operations": [
        "Credit balance sufficient for expected usage",
        "Per-key credit limits configured",
        "Monitoring updated to track OpenRouter metrics",
        "Alerting on new error codes (402, 408)",
        "Rollback plan documented",
    ],
}
```

## Model ID Migration Map

| Direct Provider | OpenRouter ID |
|----------------|---------------|
| `gpt-4o` | `openai/gpt-4o` |
| `gpt-4o-mini` | `openai/gpt-4o-mini` |
| `o1` | `openai/o1` |
| `claude-3-5-sonnet-20241022` | `anthropic/claude-3.5-sonnet` |
| `claude-3-haiku-20240307` | `anthropic/claude-3-haiku` |
| `gemini-2.0-flash` | `google/gemini-2.0-flash-001` |
| `llama-3.1-8b-instruct` | `meta-llama/llama-3.1-8b-instruct` |

## Comparison Test Script

```python
def compare_migration(prompt: str, old_model: str, new_model: str):
    """Run same prompt through old and new configurations to compare."""
    import time

    # New: OpenRouter
    or_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "migration-test"},
    )

    start = time.monotonic()
    or_response = or_client.chat.completions.create(
        model=new_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200, temperature=0,
    )
    or_latency = (time.monotonic() - start) * 1000

    return {
        "openrouter": {
            "model": or_response.model,
            "content": or_response.choices[0].message.content[:100],
            "tokens": or_response.usage.prompt_tokens + or_response.usage.completion_tokens,
            "latency_ms": round(or_latency),
        },
    }

# Test
result = compare_migration(
    "What is 2+2?",
    old_model="gpt-4o",
    new_model="openai/gpt-4o",
)
print(json.dumps(result, indent=2))
```

## Feature Flag Migration

```python
import os

USE_OPENROUTER = os.environ.get("USE_OPENROUTER", "false").lower() == "true"

def get_llm_client():
    """Feature flag for gradual migration."""
    if USE_OPENROUTER:
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
        )
    else:
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def get_model_id(model: str) -> str:
    """Map model IDs based on current backend."""
    if USE_OPENROUTER and "/" not in model:
        MODEL_MAP = {"gpt-4o": "openai/gpt-4o", "gpt-4o-mini": "openai/gpt-4o-mini"}
        return MODEL_MAP.get(model, f"openai/{model}")
    return model
```

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 401 after migration | Using old API key with new base_url | Update to OpenRouter API key (sk-or-v1-...) |
| `model_not_found` | Missing provider prefix | Add `openai/` or `anthropic/` prefix to model ID |
| Different response format | Switched from Anthropic SDK to OpenAI SDK | Update response parsing: `.choices[0].message.content` |
| Higher latency | OpenRouter proxy overhead | Expected: +50-100ms; use streaming to mask it |

## Enterprise Considerations

- Migration from direct provider to OpenRouter requires only 3 lines of code change
- Use feature flags for gradual migration (10% -> 50% -> 100%)
- Run comparison tests on critical prompts before full migration
- OpenRouter adds ~50-100ms overhead; use streaming to mask perceived latency
- Keep direct provider keys active during migration for quick rollback
- Update monitoring dashboards for OpenRouter-specific metrics (generation_id, provider used)

## References

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Quickstart](https://openrouter.ai/docs/quickstart) | [OpenAI Compatibility](https://openrouter.ai/docs/frameworks)
