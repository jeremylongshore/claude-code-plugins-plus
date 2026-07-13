---
name: openrouter-pricing-basics
description: 'Understand OpenRouter pricing, calculate costs, and optimize spend.
  Use when budgeting, comparing model costs, or tracking spend. Triggers: ''openrouter
  pricing'', ''openrouter cost'', ''model pricing'', ''openrouter budget'', ''how
  much does openrouter cost''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(curl:*), Bash(jq:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- pricing
- cost-optimization
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Pricing Basics

## Overview

OpenRouter charges per token with separate rates for prompt (input) and completion (output) tokens. Prices are listed per token in the models API (multiply by 1M for per-million rates). Credits are prepaid with a 5.5% processing fee ($0.80 minimum). Free models are available for testing and low-volume use.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- `curl` and `jq` for the model-pricing and credit-balance queries
- Python 3.8+ with the OpenAI SDK plus the `requests` package for the cost-calculation and generation-endpoint snippets
- Prepaid credits for paid models — the public models/pricing endpoint needs no auth, but real completions require credits or a `:free` model

## Instructions

1. Read How Pricing Works: prepaid credits (5.5% fee, $0.80 minimum) are drawn down per request as `(prompt_tokens * prompt_rate) + (completion_tokens * completion_rate)`.
2. Query per-token rates via `GET /api/v1/models` per Query Model Pricing, and place candidate models in the Cost Tiers table (free → premium).
3. Estimate spend before committing: run `estimate_cost()` from Calculate Request Cost with your expected prompt/completion token counts.
4. After sending real traffic, fetch the exact charge with `GET /api/v1/generation?id=` per Track Actual Cost Per Request.
5. Watch the balance via `GET /api/v1/auth/key` per Check Credit Balance, and enable auto-topup for production keys.
6. Cut costs with the `:floor` and `:free` variants per Save Money with Variants, and check Special Pricing for reasoning tokens, image inputs, per-request fees, and BYOK.

## How Pricing Works

1. **Buy credits** at [openrouter.ai/credits](https://openrouter.ai/credits) (5.5% fee, $0.80 minimum)
2. **Each request** deducts `(prompt_tokens * prompt_rate) + (completion_tokens * completion_rate)`
3. **Check balance** via `GET /api/v1/auth/key` or the dashboard
4. **Auto-topup** is available to prevent service interruption

## Query Model Pricing

```bash
# Get pricing for all models
curl -s https://openrouter.ai/api/v1/models | jq '.data[] | select(.id == "anthropic/claude-3.5-sonnet") | {
  id: .id,
  prompt_per_M: ((.pricing.prompt | tonumber) * 1000000),
  completion_per_M: ((.pricing.completion | tonumber) * 1000000),
  context: .context_length
}'
# → { "id": "anthropic/claude-3.5-sonnet", "prompt_per_M": 3, "completion_per_M": 15, "context": 200000 }
```

## Cost Tiers (Representative)

| Tier | Example Model | Prompt/1M | Completion/1M | Use Case |
|------|--------------|-----------|---------------|----------|
| Free | `google/gemma-2-9b-it:free` | $0.00 | $0.00 | Testing, prototyping |
| Budget | `meta-llama/llama-3.1-8b-instruct` | $0.06 | $0.06 | Simple Q&A, classification |
| Mid | `openai/gpt-4o-mini` | $0.15 | $0.60 | General purpose |
| Standard | `anthropic/claude-3.5-sonnet` | $3.00 | $15.00 | Complex reasoning, code |
| Premium | `openai/o1` | $15.00 | $60.00 | Deep reasoning |

## Calculate Request Cost

```python
def estimate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost for a single request."""
    import requests
    models = requests.get("https://openrouter.ai/api/v1/models").json()["data"]
    model = next((m for m in models if m["id"] == model_id), None)
    if not model:
        raise ValueError(f"Model {model_id} not found")

    prompt_rate = float(model["pricing"]["prompt"])       # Cost per token
    completion_rate = float(model["pricing"]["completion"])
    return (prompt_tokens * prompt_rate) + (completion_tokens * completion_rate)

# Example: Claude 3.5 Sonnet, 1000 prompt + 500 completion tokens
cost = estimate_cost("anthropic/claude-3.5-sonnet", 1000, 500)
print(f"Estimated cost: ${cost:.6f}")  # ~$0.0105
```

## Track Actual Cost Per Request

```python
import requests

# Method 1: From response usage (estimate)
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)
# response.usage.prompt_tokens, response.usage.completion_tokens

# Method 2: Query generation endpoint (exact cost from OpenRouter)
gen = requests.get(
    f"https://openrouter.ai/api/v1/generation?id={response.id}",
    headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
).json()
print(f"Exact cost: ${gen['data']['total_cost']}")
print(f"Tokens: {gen['data']['tokens_prompt']} prompt + {gen['data']['tokens_completion']} completion")
```

## Check Credit Balance

```bash
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '{
    credits_used: .data.usage,
    credit_limit: .data.limit,
    remaining: ((.data.limit // 0) - .data.usage),
    is_free_tier: .data.is_free_tier
  }'
```

## Save Money with Variants

```python
# :floor variant picks the cheapest provider for a model
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet:floor",  # Cheapest provider
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)

# :free variant uses free providers (where available)
response = client.chat.completions.create(
    model="google/gemma-2-9b-it:free",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)
```

## Special Pricing

| Item | Pricing |
|------|---------|
| **Reasoning tokens** | Charged as output tokens at completion rate |
| **Image inputs** | Per-image charge listed in `pricing.image` |
| **Per-request fee** | Some models charge a flat fee per request (`pricing.request`) |
| **BYOK** | First 1M requests/month free; then 5% of normal provider cost |
| **Free model limits** | 50 req/day (free users), 1000 req/day (with $10+ credits) |

## Output

- A per-model pricing record from the models API: `prompt_per_M`, `completion_per_M`, `context` (e.g. $3 / $15 per 1M tokens for `anthropic/claude-3.5-sonnet`)
- A pre-request dollar estimate from `estimate_cost()` and the exact post-request figures from the generation endpoint: `total_cost`, `tokens_prompt`, `tokens_completion`
- A credit-balance snapshot from `/api/v1/auth/key`: `credits_used`, `credit_limit`, `remaining`, `is_free_tier`

## Examples

Check remaining credits before a batch job:

```bash
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '{
    credits_used: .data.usage,
    remaining: ((.data.limit // 0) - .data.usage)
  }'
# {"credits_used": 2.34, "remaining": 47.66}
```

Estimating first keeps surprises out: 1,000 prompt + 500 completion tokens on `anthropic/claude-3.5-sonnet` comes to roughly $0.0105 via `estimate_cost()`, and the generation endpoint then confirms the exact charge. More worked examples: `references/examples.md`.

## Error Handling

| HTTP | Cause | Fix |
|------|-------|-----|
| 402 | Insufficient credits | Top up at [openrouter.ai/credits](https://openrouter.ai/credits) or use `:free` model |
| 402 | Key credit limit reached | Increase key limit or use a different key |

## Enterprise Considerations

- Set per-key credit limits via the dashboard or provisioning API to isolate blast radius
- Query `/api/v1/generation?id=` after each request for exact cost auditing
- Use `:floor` variant to automatically pick the cheapest provider
- Route simple tasks to budget models and complex tasks to premium models (see openrouter-model-routing)
- Set `max_tokens` on every request to cap completion cost
- Enable auto-topup to prevent service interruptions in production

## References

- Examples | Errors
- [Pricing](https://openrouter.ai/pricing) | [Credits](https://openrouter.ai/credits) | [Models API](https://openrouter.ai/docs/api/api-reference/models/get-models)
