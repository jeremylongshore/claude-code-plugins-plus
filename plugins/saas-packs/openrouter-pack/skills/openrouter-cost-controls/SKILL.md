---
name: openrouter-cost-controls
description: |
  Implement cost controls for OpenRouter API usage. Use when setting budgets, preventing overspend, or managing per-key limits. Triggers: 'openrouter budget', 'openrouter cost limit', 'openrouter spending', 'control openrouter cost'.
allowed-tools: Read, Write, Edit, Bash, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, openrouter, cost-optimization, budgets]

---
# OpenRouter Cost Controls

## Overview

OpenRouter provides per-key credit limits, a credit balance API, and per-generation cost queries. Combined with client-side budget middleware, you can enforce hard spending caps at the key level and soft caps in your application. This skill covers key-level limits, per-request cost tracking, budget enforcement middleware, and alert systems.

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

- [Examples](${CLAUDE_SKILL_DIR}/references/examples.md) | [Errors](${CLAUDE_SKILL_DIR}/references/errors.md)
- [Credits](https://openrouter.ai/credits) | [Key Provisioning](https://openrouter.ai/docs/guides/overview/auth/provisioning-api-keys)
