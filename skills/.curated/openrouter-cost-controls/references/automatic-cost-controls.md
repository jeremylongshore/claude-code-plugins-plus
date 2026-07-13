# Automatic Cost Controls

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
