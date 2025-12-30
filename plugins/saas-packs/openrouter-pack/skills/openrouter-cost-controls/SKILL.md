---
name: openrouter-cost-controls
description: |
  Implement budget controls and cost limits for OpenRouter. Use when managing spending or preventing overruns. Trigger with phrases like 'openrouter budget', 'openrouter spending limit', 'cost control', 'openrouter billing alert'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Cost Controls

## Overview

This skill demonstrates implementing cost controls including per-key limits, budget alerts, and automatic cutoffs.

## Prerequisites

- OpenRouter account
- Budget requirements defined

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill demonstrates implementing cost controls including per-key limits, budget alerts, and automatic cutoffs.

## Prerequisites

- OpenRouter account
- Budget requirements defined

## Per-Key Limits

### Setting Key Limits
```
Dashboard: openrouter.ai/keys

For each key, set:
- Credit limit (e.g., $10, $100, $1000)
- Label for identification
```

### Check Key Limit
```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

Response:
```json
{
  "data": {
    "label": "production",
    "limit": 100.0,
    "usage": 45.23,
    "limit_remaining": 54.77
  }
}
```

## Request-Level Controls

### Max Tokens Limit
```python
def cost_controlled_chat(
    prompt: str,
    model: str = "openai/gpt-4-turbo",
    max_tokens: int = 500,  # Limit response length
    max_cost: float = 0.05   # Maximum cost per request
):
    # Estimate if request would exceed cost limit
    estimated_prompt_tokens = len(prompt) // 4
    estimated_total_tokens = estimated_prompt_tokens + max_tokens

    model_prices = {
        "openai/gpt-4-turbo": (10.0, 30.0),      # $/M tokens
        "anthropic/claude-3.5-sonnet": (3.0, 15.0),
        "anthropic/claude-3-haiku": (0.25, 1.25),
    }

    prompt_price, completion_price = model_prices.get(model, (10.0, 30.0))
    estimated_cost = (
        estimated_prompt_tokens * prompt_price / 1_000_000 +
        max_tokens * completion_price / 1_000_000
    )

    if estimated_cost > max_cost:
        raise ValueError(
            f"Estimated cost ${estimated_cost:.4f} exceeds limit ${max_cost}"
        )

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
```

### Model Tier Restrictions
```python
COST_TIERS = {
    "budget": {
        "max_per_request": 0.001,
        "models": [
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-7b-instruct",
        ]
    },
    "standard": {
        "max_per_request": 0.01,
        "models": [
            "anthropic/claude-3-haiku",
            "openai/gpt-3.5-turbo",
        ]
    },
    "premium": {
        "max_per_request": 0.10,
        "models": [
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4-turbo",
        ]
    }
}

def tier_restricted_chat(
    prompt: str,
    tier: str = "standard",
    model: str = None
):
    tier_config = COST_TIERS.get(tier, COST_TIERS["standard"])

    if model is None:
        model = tier_config["models"][0]
    elif model not in tier_config["models"]:
        raise ValueError(
            f"Model {model} not in tier {tier}. "
            f"Available: {tier_config['models']}"
        )

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```

## Budget Tracking

### Real-Time Cost Tracking
```python
import json
from pathlib import Path
from datetime import datetime, date

class CostTracker:
    def __init__(self, storage_path: str = "cost_tracking.json"):
        self.storage_path = Path(storage_path)
        self.data = self._load()

    def _load(self) -> dict:
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return {"daily": {}, "monthly": {}, "requests": []}

    def _save(self):
        self.storage_path.write_text(json.dumps(self.data, indent=2))

    def record(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float
    ):
        today = date.today().isoformat()
        month = today[:7]  # YYYY-MM

        # Daily
        if today not in self.data["daily"]:
            self.data["daily"][today] = 0.0
        self.data["daily"][today] += cost

        # Monthly
        if month not in self.data["monthly"]:
            self.data["monthly"][month] = 0.0
        self.data["monthly"][month] += cost

        # Detailed log
        self.data["requests"].append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost
        })

        # Keep last 1000 requests
        self.data["requests"] = self.data["requests"][-1000:]

        self._save()

    def get_daily_cost(self, date_str: str = None) -> float:
        date_str = date_str or date.today().isoformat()
        return self.data["daily"].get(date_str, 0.0)

    def get_monthly_cost(self, month_str: str = None) -> float:
        month_str = month_str or date.today().isoformat()[:7]
        return self.data["monthly"].get(month_str, 0.0)

tracker = CostTracker()

def tracked_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    cost = calculate_cost(model, response.usage)
    tracker.record(
        model=model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        cost=cost
    )

    return response

def calculate_cost(model: str, usage) -> float:
    prices = {
        "openai/gpt-4-turbo": (10.0, 30.0),
        "anthropic/claude-3.5-sonnet": (3.0, 15.0),
        "anthropic/claude-3-haiku": (0.25, 1.25),
        "openai/gpt-3.5-turbo": (0.5, 1.5),
    }
    prompt_price, completion_price = prices.get(model, (10.0, 30.0))
    return (
        usage.prompt_tokens * prompt_price / 1_000_000 +
        usage.completion_tokens * completion_price / 1_000_000
    )
```

## Budget Alerts

### Alert System
```python
class BudgetAlertSystem:
    def __init__(self, daily_limit: float, monthly_limit: float):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.alert_thresholds = [0.5, 0.75, 0.9, 1.0]  # 50%, 75%, 90%, 100%
        self.alerts_sent = set()

    def check_and_alert(self, tracker: CostTracker):
        daily = tracker.get_daily_cost()
        monthly = tracker.get_monthly_cost()

        alerts = []

        # Daily alerts
        for threshold in self.alert_thresholds:
            if daily >= self.daily_limit * threshold:
                alert_key = f"daily_{threshold}_{date.today().isoformat()}"
                if alert_key not in self.alerts_sent:
                    alerts.append({
                        "type": "daily",
                        "threshold": threshold,
                        "current": daily,
                        "limit": self.daily_limit
                    })
                    self.alerts_sent.add(alert_key)

        # Monthly alerts
        month = date.today().isoformat()[:7]
        for threshold in self.alert_thresholds:
            if monthly >= self.monthly_limit * threshold:
                alert_key = f"monthly_{threshold}_{month}"
                if alert_key not in self.alerts_sent:
                    alerts.append({
                        "type": "monthly",
                        "threshold": threshold,
                        "current": monthly,
                        "limit": self.monthly_limit
                    })
                    self.alerts_sent.add(alert_key)

        return alerts

    def send_alert(self, alert: dict):
        # Implement your alerting (Slack, email, etc.)
        pct = alert["threshold"] * 100
        print(f"ALERT: {alert['type']} budget at {pct}% "
              f"(${alert['current']:.2f} / ${alert['limit']:.2f})")

alerts = BudgetAlertSystem(daily_limit=50.0, monthly_limit=500.0)
```

### Slack Alert Integration
```python
import requests

def send_slack_alert(webhook_url: str, message: str, level: str = "warning"):
    color = {
        "info": "#36a64f",
        "warning": "#ff9800",
        "critical": "#f44336"
    }.get(level, "#ff9800")

    payload = {
        "attachments": [{
            "color": color,
            "text": message,
            "footer": "OpenRouter Cost Monitor"
        }]
    }

    requests.post(webhook_url, json=payload)

# Usage in alert system
def send_alert(self, alert: dict):
    pct = alert["threshold"] * 100
    level = "critical" if alert["threshold"] >= 0.9 else "warning"

    message = (
        f"*{alert['type'].title()} Budget Alert*\n"
        f"Usage: ${alert['current']:.2f} / ${alert['limit']:.2f} ({pct:.0f}%)"
    )

    send_slack_alert(
        os.environ["SLACK_WEBHOOK_URL"],
        message,
        level
    )
```

## Automatic Cost Controls

### Hard Limit Enforcement
```python
class HardLimitEnforcer:
    def __init__(
        self,
        tracker: CostTracker,
        daily_limit: float,
        monthly_limit: float
    ):
        self.tracker = tracker
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit

    def can_proceed(self) -> tuple[bool, str]:
        daily = self.tracker.get_daily_cost()
        if daily >= self.daily_limit:
            return False, f"Daily limit ${self.daily_limit} reached"

        monthly = self.tracker.get_monthly_cost()
        if monthly >= self.monthly_limit:
            return False, f"Monthly limit ${self.monthly_limit} reached"

        return True, ""

    def remaining_daily(self) -> float:
        return max(0, self.daily_limit - self.tracker.get_daily_cost())

    def remaining_monthly(self) -> float:
        return max(0, self.monthly_limit - self.tracker.get_monthly_cost())

enforcer = HardLimitEnforcer(tracker, daily_limit=50.0, monthly_limit=500.0)

def limited_chat(prompt: str, model: str):
    can_proceed, reason = enforcer.can_proceed()
    if not can_proceed:
        raise Exception(f"Budget limit reached: {reason}")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    # Track the cost
    cost = calculate_cost(model, response.usage)
    tracker.record(model, response.usage.prompt_tokens,
                   response.usage.completion_tokens, cost)

    return response
```

### Automatic Model Downgrade
```python
def auto_downgrade_chat(
    prompt: str,
    preferred_model: str = "anthropic/claude-3.5-sonnet",
    budget_remaining: float = None
):
    """Automatically downgrade model if budget is low."""
    if budget_remaining is None:
        budget_remaining = enforcer.remaining_daily()

    # Model cost estimates per 1K tokens
    model_costs = {
        "anthropic/claude-3-opus": 0.075,
        "anthropic/claude-3.5-sonnet": 0.018,
        "openai/gpt-4-turbo": 0.030,
        "anthropic/claude-3-haiku": 0.001,
        "openai/gpt-3.5-turbo": 0.002,
    }

    # Estimate cost for request
    estimated_tokens = len(prompt) // 4 + 500
    estimated_cost = estimated_tokens * model_costs.get(preferred_model, 0.030) / 1000

    # Downgrade if needed
    if estimated_cost > budget_remaining * 0.1:  # Don't use more than 10% of remaining
        # Find cheaper model
        cheaper_models = [
            m for m, c in model_costs.items()
            if c < model_costs[preferred_model]
        ]
        if cheaper_models:
            preferred_model = min(cheaper_models, key=lambda m: model_costs[m])
            print(f"Downgraded to {preferred_model} due to budget constraints")

    return client.chat.completions.create(
        model=preferred_model,
        messages=[{"role": "user", "content": prompt}]
    )
```

## Cost Dashboard

### Generate Cost Report
```python
def generate_cost_report(tracker: CostTracker) -> dict:
    """Generate comprehensive cost report."""
    today = date.today()
    this_month = today.isoformat()[:7]
    last_month = (today.replace(day=1) - timedelta(days=1)).isoformat()[:7]

    # Aggregate by model
    model_costs = {}
    for req in tracker.data["requests"]:
        model = req["model"]
        if model not in model_costs:
            model_costs[model] = {"requests": 0, "cost": 0, "tokens": 0}
        model_costs[model]["requests"] += 1
        model_costs[model]["cost"] += req["cost"]
        model_costs[model]["tokens"] += req["prompt_tokens"] + req["completion_tokens"]

    return {
        "summary": {
            "today": tracker.get_daily_cost(),
            "this_month": tracker.get_monthly_cost(this_month),
            "last_month": tracker.get_monthly_cost(last_month),
        },
        "by_model": model_costs,
        "limits": {
            "daily_remaining": enforcer.remaining_daily(),
            "monthly_remaining": enforcer.remaining_monthly(),
        },
        "daily_trend": [
            {"date": d, "cost": c}
            for d, c in sorted(tracker.data["daily"].items())[-30:]
        ]
    }
```

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
