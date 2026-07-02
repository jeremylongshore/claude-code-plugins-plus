---
name: openrouter-model-catalog
description: 'Query, filter, and select from OpenRouter''s 400+ model catalog. Use
  when choosing models, comparing pricing, or checking capabilities. Triggers: ''openrouter
  models'', ''list models'', ''model catalog'', ''compare models'', ''available models''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(curl:*), Bash(jq:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- models
- catalog
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Model Catalog

## Overview

Query the `GET /api/v1/models` endpoint to browse 400+ models, filter by capabilities, compare pricing, and check provider endpoints. No API key required for the models endpoint.

## Prerequisites

- `curl` and `jq` for the command-line catalog queries — `GET /api/v1/models` itself requires no auth
- An OpenRouter API key exported as `OPENROUTER_API_KEY` only for the Special Routers completion example — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with `requests` for filtering, plus the OpenAI SDK for the `openrouter/auto` example (`pip install requests openai`)

## Instructions

1. List the catalog per List All Models: `curl -s https://openrouter.ai/api/v1/models | jq '.data | length'`; add `?supported_parameters=tools` to filter to tool-calling models.
2. Read Model Object Shape to interpret each entry — `pricing.prompt`/`pricing.completion` are per token (multiply by 1M for readable rates), plus `context_length`, `top_provider.max_completion_tokens`, and `architecture.modality`.
3. Filter programmatically per Python: Query and Filter — free models, tool-calling models, cheapest paid models sorted by prompt price, and 128K+ context models.
4. Compare per-provider pricing and quantization for a single model via `GET /api/v1/models/{id}/endpoints` per List Providers for a Model.
5. Pick behavior with a suffix per Model Variants (`:free`, `:nitro`, `:floor`, `:extended`, `:thinking`), or delegate selection entirely to `openrouter/auto` per Special Routers.
6. Sanity-check choices against the Popular Model Quick Reference, but always verify live pricing via `/api/v1/models` — prices change frequently.

## List All Models

```bash
# Full catalog (no auth required)
curl -s https://openrouter.ai/api/v1/models | jq '.data | length'
# → 400+

# Filter to text output models only
curl -s "https://openrouter.ai/api/v1/models?supported_parameters=tools" | jq '.data | length'
```

## Model Object Shape

```json
{
  "id": "anthropic/claude-3.5-sonnet",
  "name": "Claude 3.5 Sonnet",
  "description": "Anthropic's most intelligent model...",
  "context_length": 200000,
  "pricing": {
    "prompt": "0.000003",
    "completion": "0.000015",
    "image": "0.0048",
    "request": "0"
  },
  "top_provider": {
    "context_length": 200000,
    "max_completion_tokens": 8192,
    "is_moderated": false
  },
  "per_request_limits": null,
  "architecture": {
    "modality": "text+image->text",
    "tokenizer": "Claude",
    "instruct_type": null
  }
}
```

Key fields:

- `pricing.prompt` / `pricing.completion` -- cost per token (not per million; multiply by 1M for readable rates)
- `context_length` -- max input tokens
- `top_provider.max_completion_tokens` -- max output tokens
- `architecture.modality` -- `text->text`, `text+image->text`, etc.

## Python: Query and Filter

```python
import requests

models = requests.get("https://openrouter.ai/api/v1/models").json()["data"]

# Find all free models
free_models = [m for m in models if m["pricing"]["prompt"] == "0"]
print(f"Free models: {len(free_models)}")

# Models with tool calling support
# (query with supported_parameters)
tool_models = requests.get(
    "https://openrouter.ai/api/v1/models?supported_parameters=tools"
).json()["data"]
print(f"Tool-calling models: {len(tool_models)}")

# Sort by prompt price (cheapest first, excluding free)
paid = [m for m in models if float(m["pricing"]["prompt"]) > 0]
paid.sort(key=lambda m: float(m["pricing"]["prompt"]))
for m in paid[:10]:
    cost_per_m = float(m["pricing"]["prompt"]) * 1_000_000
    print(f"  ${cost_per_m:.2f}/M tokens — {m['id']} ({m['context_length']//1000}K ctx)")

# Filter by context length (128K+)
large_ctx = [m for m in models if m["context_length"] >= 128_000]
print(f"128K+ context models: {len(large_ctx)}")
```

## List Providers for a Model

```bash
# See all providers and their pricing for a specific model
curl -s "https://openrouter.ai/api/v1/models/anthropic/claude-3.5-sonnet/endpoints" | jq '.data[] | {
  provider: .provider_name,
  price_prompt: .pricing.prompt,
  price_completion: .pricing.completion,
  context_length: .context_length,
  quantization: .quantization
}'
```

## Model Variants

Append a suffix to any model ID for variant behavior:

| Suffix | Effect | Example |
|--------|--------|---------|
| `:free` | Free tier (where available) | `google/gemma-2-9b-it:free` |
| `:nitro` | Sort providers by throughput (faster) | `anthropic/claude-3.5-sonnet:nitro` |
| `:floor` | Sort providers by price (cheapest) | `openai/gpt-4o:floor` |
| `:extended` | Extended context window | `anthropic/claude-3.5-sonnet:extended` |
| `:thinking` | Enable extended reasoning | `anthropic/claude-3.5-sonnet:thinking` |

## Special Routers

| Model ID | Behavior |
|----------|----------|
| `openrouter/auto` | Auto-selects best model for your prompt (powered by NotDiamond) |
| `openrouter/free` | Routes to free models only |

```python
# Let OpenRouter pick the best model
response = client.chat.completions.create(
    model="openrouter/auto",
    messages=[{"role": "user", "content": "Write a SQL query to find duplicate emails"}],
    max_tokens=200,
)
print(f"Auto-selected: {response.model}")  # Shows which model was chosen
```

## Popular Model Quick Reference

| Model ID | Context | Cost (prompt/completion per 1M) |
|----------|---------|--------------------------------|
| `google/gemma-2-9b-it:free` | 8K | Free |
| `meta-llama/llama-3.1-8b-instruct` | 128K | ~$0.06 / $0.06 |
| `anthropic/claude-3-haiku` | 200K | $0.25 / $1.25 |
| `openai/gpt-4o-mini` | 128K | $0.15 / $0.60 |
| `anthropic/claude-3.5-sonnet` | 200K | $3.00 / $15.00 |
| `openai/gpt-4o` | 128K | $2.50 / $10.00 |
| `openai/o1` | 200K | $15.00 / $60.00 |

*Prices change frequently. Always verify via `/api/v1/models`.*

## Output

- Raw catalog JSON: one object per model with `id`, `context_length`, `pricing`, `top_provider`, and `architecture` fields
- Filtered console listings, e.g. counts of free / tool-calling / 128K+ models and cheapest-paid lines like `$0.06/M tokens — meta-llama/llama-3.1-8b-instruct (128K ctx)`
- Per-provider endpoint rows for one model: `provider_name`, prompt/completion pricing, `context_length`, `quantization`
- For `openrouter/auto` requests, `response.model` reveals which model the router actually selected

## Examples

Fetch the catalog once, then slice it three ways with the filters from Python: Query and Filter:

```python
models = requests.get("https://openrouter.ai/api/v1/models").json()["data"]
free = [m for m in models if m["pricing"]["prompt"] == "0"]
large = [m for m in models if m["context_length"] >= 128_000]
print(f"Total: {len(models)}, free: {len(free)}, 128K+: {len(large)}")
# Total: 267, free: 12, 128K+: 45   (counts drift as the catalog changes)
```

The same pass sorted by prompt price surfaces the cheapest paid options — `meta-llama/llama-3-8b-instruct: $0.05/1M prompt tokens` leads the list in the worked run. More worked examples: `references/examples.md`.

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Model ID not found at request time | Model renamed, removed, or typo | Re-query `/api/v1/models`; use exact ID from catalog |
| Stale pricing | Cached catalog data outdated | Refresh catalog hourly; pricing updates dynamically |
| Empty results with filter | No models match the filter criteria | Broaden the filter; check parameter spelling |

## Enterprise Considerations

- Cache the model catalog with 1-hour TTL (model availability changes infrequently)
- Build a model allowlist for your organization to restrict which models teams can use
- Monitor `/api/v1/models` for deprecation notices and new model additions
- Use `supported_parameters` query filter to ensure models support features you need (tools, JSON mode, etc.)
- Compare providers via the endpoints API to find the cheapest or fastest provider for each model

## References

- Examples | Errors
- [Models Docs](https://openrouter.ai/docs/guides/overview/models) | [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models) | [Model Variants](https://openrouter.ai/docs/guides/routing/model-variants/thinking)
