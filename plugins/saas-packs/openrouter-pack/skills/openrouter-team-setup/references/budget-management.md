# Budget Management

## Budget Management

### Per-User Budgets

```python
class BudgetManager:
    def __init__(self):
        self.budgets = {}  # user_id -> budget
        self.spent = {}    # user_id -> amount spent

    def set_budget(self, user_id: str, amount: float):
        self.budgets[user_id] = amount
        if user_id not in self.spent:
            self.spent[user_id] = 0.0

    def can_spend(self, user_id: str, amount: float) -> bool:
        budget = self.budgets.get(user_id, float('inf'))
        spent = self.spent.get(user_id, 0.0)
        return spent + amount <= budget

    def record_spend(self, user_id: str, amount: float):
        self.spent[user_id] = self.spent.get(user_id, 0.0) + amount

    def get_remaining(self, user_id: str) -> float:
        budget = self.budgets.get(user_id, float('inf'))
        spent = self.spent.get(user_id, 0.0)
        return budget - spent

budget_mgr = BudgetManager()
budget_mgr.set_budget("user123", 50.00)  # $50/month

def budget_checked_chat(user_id: str, prompt: str, model: str):
    # Estimate cost
    estimated_cost = 0.01  # Rough estimate

    if not budget_mgr.can_spend(user_id, estimated_cost):
        raise Exception("Budget exceeded")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    # Calculate actual cost
    actual_cost = calculate_cost(response, model)
    budget_mgr.record_spend(user_id, actual_cost)

    return response
```

### Team Budget Dashboard

```python
class TeamBudgetDashboard:
    def __init__(self, team_budget: float):
        self.team_budget = team_budget
        self.user_spending = {}

    def record_usage(
        self,
        user_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ):
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        if user_id not in self.user_spending:
            self.user_spending[user_id] = []

        self.user_spending[user_id].append({
            "timestamp": datetime.now(),
            "model": model,
            "tokens": prompt_tokens + completion_tokens,
            "cost": cost
        })

    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        prices = {
            "anthropic/claude-3.5-sonnet": (0.003, 0.015),
            "anthropic/claude-3-haiku": (0.00025, 0.00125),
            "openai/gpt-4-turbo": (0.01, 0.03),
        }
        prompt_price, completion_price = prices.get(model, (0.01, 0.03))
        return (
            prompt_tokens * prompt_price / 1000 +
            completion_tokens * completion_price / 1000
        )

    def get_dashboard(self) -> dict:
        total_spent = sum(
            sum(u["cost"] for u in usage)
            for usage in self.user_spending.values()
        )

        return {
            "team_budget": self.team_budget,
            "total_spent": total_spent,
            "remaining": self.team_budget - total_spent,
            "utilization": total_spent / self.team_budget * 100,
            "by_user": {
                user: sum(u["cost"] for u in usage)
                for user, usage in self.user_spending.items()
            }
        }
```
