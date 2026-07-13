---
name: openrouter-cost-controls
description: 'Implement cost controls for OpenRouter API usage. Use when setting budgets,
  preventing overspend, or managing per-key limits. Triggers: ''openrouter budget'',
  ''openrouter cost limit'', ''openrouter spending'', ''control openrouter cost''.

  '
allowed-tools: Read, Write, Edit, Grep, Bash(python3:*), Bash(node:*), Bash(curl:*), Bash(jq:*), Bash(bc:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- openrouter
- cost-optimization
- budgets
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# OpenRouter Cost Controls

## Overview

OpenRouter provides per-key credit limits, a credit balance API, and per-generation cost queries. Combined with client-side budget middleware, you can enforce hard spending caps at the key level and soft caps in your application. This skill covers key-level limits, per-request cost tracking, budget enforcement middleware, and alert systems.

## Prerequisites

- An OpenRouter API key (`sk-or-v1-...`) exported as `OPENROUTER_API_KEY` — see the `openrouter-install-auth` skill for setup
- Python 3.8+ with the OpenAI SDK and `requests`; Node.js 18+ for the TypeScript per-request cost logger in the references
- `curl`, `jq`, and `bc` for the balance check and the Budget Alert Script
- An OpenRouter management key exported as `OPENROUTER_MGMT_KEY` if you provision per-key credit limits via `POST /api/v1/keys`

## Instructions

1. Query `GET /api/v1/auth/key` per Check Credit Balance to see credits used, the key's limit, remaining balance, free-tier status, and rate limit.
2. Provision scoped keys per Per-Key Credit Limits — `POST /api/v1/keys` with a dollar `limit` (e.g. $50 for `backend-prod`) using the management key, then list keys to review usage against limits per service.
3. Deploy the `BudgetEnforcer` from Budget Enforcement Middleware: `check_budget()` rejects any request whose pre-flight estimate exceeds the per-request or daily cap, and `record_cost()` books the exact spend from `GET /api/v1/generation?id=`.
4. Cut unit cost with Cost-Saving Model Variants: `:floor` picks the cheapest provider, `:free` costs nothing where available, and the task-based `ROUTING` table sends classification to gpt-4o-mini and simple Q&A to Llama 3.1 8B.
5. Schedule the Budget Alert Script (cron) so a balance drop below the threshold fires an alert to Slack or PagerDuty.
6. Set `max_tokens` on every request and enable auto-topup per Enterprise Considerations to cap completion cost without risking an outage.

## Check Credit Balance

```bash
# Current balance and limits
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '{
    credits_used: .data.usage,
    credit_limit: .data.limit,
    remaining: ((.data.limit // 0) - .data.usage),
    is_free_tier: .data.is_free_tier,
    rate_limit: .data.rate_limit
  }'
```

## Per-Key Credit Limits

```python
import os, requests

MGMT_KEY = os.environ["OPENROUTER_MGMT_KEY"]  # Management key

# Create a key with a $50 credit limit
resp = requests.post(
    "https://openrouter.ai/api/v1/keys",
    headers={"Authorization": f"Bearer {MGMT_KEY}"},
    json={"name": "backend-prod", "limit": 50.0},
)
new_key = resp.json()["data"]["key"]  # sk-or-v1-...

# List all keys with their limits and usage
keys = requests.get(
    "https://openrouter.ai/api/v1/keys",
    headers={"Authorization": f"Bearer {MGMT_KEY}"},
).json()
for k in keys.get("data", []):
    print(f"{k['name']}: ${k.get('usage', 0):.4f} / ${k.get('limit', 'unlimited')}")
```

## Budget Enforcement Middleware

```python
import os, time, requests
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={"HTTP-Referer": "https://my-app.com", "X-Title": "my-app"},
)

class BudgetEnforcer:
    """Client-side budget enforcement with server-side cost verification."""

    def __init__(self, daily_limit: float = 10.0, per_request_limit: float = 0.50):
        self.daily_limit = daily_limit
        self.per_request_limit = per_request_limit
        self._daily_spend = 0.0
        self._day = time.strftime("%Y-%m-%d")

    def _reset_if_new_day(self):
        today = time.strftime("%Y-%m-%d")
        if today != self._day:
            self._daily_spend = 0.0
            self._day = today

    def estimate_cost(self, model: str, prompt_tokens: int, max_tokens: int) -> float:
        """Pre-flight cost estimate using cached pricing."""
        # Representative rates (fetch from /models in production)
        RATES = {
            "anthropic/claude-3.5-sonnet": (3.0, 15.0),    # per 1M tokens
            "openai/gpt-4o": (2.50, 10.0),
            "openai/gpt-4o-mini": (0.15, 0.60),
            "meta-llama/llama-3.1-8b-instruct": (0.06, 0.06),
        }
        prompt_rate, comp_rate = RATES.get(model, (3.0, 15.0))
        return (prompt_tokens * prompt_rate / 1_000_000) + (max_tokens * comp_rate / 1_000_000)

    def check_budget(self, model: str, prompt_tokens: int, max_tokens: int):
        """Raise if request would exceed budget."""
        self._reset_if_new_day()
        estimated = self.estimate_cost(model, prompt_tokens, max_tokens)

        if estimated > self.per_request_limit:
            raise ValueError(
                f"Request estimated at ${estimated:.4f} exceeds per-request limit ${self.per_request_limit}"
            )
        if self._daily_spend + estimated > self.daily_limit:
            raise ValueError(
                f"Daily spend ${self._daily_spend:.4f} + request ${estimated:.4f} "
                f"exceeds daily limit ${self.daily_limit}"
            )

    def record_cost(self, generation_id: str):
        """Record actual cost from generation endpoint."""
        try:
            gen = requests.get(
                f"https://openrouter.ai/api/v1/generation?id={generation_id}",
                headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
                timeout=5,
            ).json()
            cost = float(gen.get("data", {}).get("total_cost", 0))
            self._daily_spend += cost
            return cost
        except Exception:
            return 0.0

budget = BudgetEnforcer(daily_limit=25.0, per_request_limit=1.0)
```

## Cost-Saving Model Variants

```python
# :floor variant -- cheapest provider for a model
response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet:floor",  # Cheapest provider
    messages=[{"role": "user", "content": "Summarize this..."}],
    max_tokens=500,
)

# :free variant -- free providers (where available)
response = client.chat.completions.create(
    model="google/gemma-2-9b-it:free",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100,
)

# Route simple tasks to cheap models
ROUTING = {
    "classification": "openai/gpt-4o-mini",      # $0.15/$0.60 per 1M
    "summarization": "anthropic/claude-3-haiku",  # $0.25/$1.25 per 1M
    "code_generation": "anthropic/claude-3.5-sonnet",  # $3/$15 per 1M
    "simple_qa": "meta-llama/llama-3.1-8b-instruct",  # $0.06/$0.06 per 1M
}
```

## Budget Alert Script

```bash
#!/bin/bash
# Alert when credits drop below threshold
THRESHOLD=5.0

REMAINING=$(curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | \
  jq '((.data.limit // 0) - .data.usage)')

if (( $(echo "$REMAINING < $THRESHOLD" | bc -l) )); then
  echo "ALERT: OpenRouter credits low: \$$REMAINING remaining"
  # Send to Slack, PagerDuty, etc.
fi
```

## Output

- A credit-balance JSON summary: `credits_used`, `credit_limit`, `remaining`, `is_free_tier`, and `rate_limit` for the active key
- Newly provisioned API keys with hard dollar limits, plus a per-key `usage / limit` listing from the management API
- `ValueError` rejections from the middleware when a request would exceed the per-request or daily budget, and a running daily-spend total booked from actual generation costs
- Alert lines such as `ALERT: OpenRouter credits low: $4.87 remaining` whenever the balance crosses the configured threshold

## Examples

Check what's left on a key before turning on traffic:

```bash
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '{used: .data.usage, limit: .data.limit, remaining: (.data.limit - .data.usage)}'
```

Expected output:

```json
{"used": 3.42, "limit": 50, "remaining": 46.58}
```

More worked examples, including thread-safe budget middleware and a TypeScript cost logger: `references/examples.md`.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 402 Payment Required | Credits exhausted | Top up at openrouter.ai/credits or use `:free` model |
| 402 Key limit reached | Per-key credit limit hit | Increase key limit or create new key |
| Budget middleware rejects | Client-side limit exceeded | Increase limit or optimize prompt tokens |
| Stale pricing data | Cached rates outdated | Refresh from `/api/v1/models` daily |

## Enterprise Considerations

- Set per-key credit limits via management API to isolate blast radius per service/team
- Query `/api/v1/generation?id=` after each request for exact cost auditing
- Use `:floor` variant to automatically pick the cheapest provider for a model
- Route simple tasks to budget models ($0.06/1M) and reserve premium models for complex tasks
- Set `max_tokens` on every request to cap completion cost
- Enable auto-topup in the dashboard to prevent production service interruptions

## References

- Examples | Errors
- [Credits](https://openrouter.ai/credits) | [Key Provisioning](https://openrouter.ai/docs/guides/overview/auth/provisioning-api-keys)
