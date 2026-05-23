# Cost-Quality Optimization

## Cost-Quality Optimization

### Adaptive Quality Router

```python
class AdaptiveQualityRouter:
    """Adjust model quality based on request importance."""

    def __init__(self):
        self.quality_levels = {
            "low": ["anthropic/claude-3-haiku", "openai/gpt-3.5-turbo"],
            "medium": ["anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo"],
            "high": ["anthropic/claude-3-opus", "openai/gpt-4"],
        }

    def route(
        self,
        prompt: str,
        importance: str = "medium",
        user_tier: str = "standard"
    ) -> str:
        # Adjust quality based on user tier
        if user_tier == "free":
            importance = "low"
        elif user_tier == "enterprise":
            importance = max(importance, "medium")

        # Get models for quality level
        models = self.quality_levels.get(importance, self.quality_levels["medium"])

        # Select based on task
        task = detect_task_type(prompt)
        if task == "code" and importance != "low":
            return "anthropic/claude-3.5-sonnet"
        if task == "simple":
            return models[0]  # Cheapest

        return models[0]  # First available at quality level

adaptive_router = AdaptiveQualityRouter()
```

### Budget-Aware Routing

```python
class BudgetRouter:
    """Route while respecting budget constraints."""

    def __init__(self, daily_budget: float):
        self.daily_budget = daily_budget
        self.spent_today = 0.0

    def route(self, prompt: str, preferred_model: str = None) -> str:
        remaining = self.daily_budget - self.spent_today
        estimated_cost = self._estimate_cost(prompt, preferred_model)

        # If preferred model fits budget, use it
        if preferred_model and estimated_cost < remaining * 0.1:
            return preferred_model

        # Otherwise, find best model within budget
        models_by_cost = sorted(
            MODEL_PROFILES.values(),
            key=lambda p: p.cost_per_1k
        )

        for profile in models_by_cost:
            cost = self._estimate_cost(prompt, profile.id)
            if cost < remaining * 0.1:  # Don't use more than 10% of remaining
                return profile.id

        # Return cheapest available
        return models_by_cost[0].id

    def _estimate_cost(self, prompt: str, model: str) -> float:
        tokens = len(prompt) // 4 + 500  # Rough estimate
        profile = MODEL_PROFILES.get(model)
        if not profile:
            return 0.01  # Default estimate
        return tokens * profile.cost_per_1k / 1000

    def record_spend(self, cost: float):
        self.spent_today += cost

budget_router = BudgetRouter(daily_budget=50.0)
```
