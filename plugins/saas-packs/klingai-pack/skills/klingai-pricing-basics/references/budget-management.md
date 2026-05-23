# Budget Management

## Budget Management

```python
class BudgetManager:
    """Track and manage video generation budget."""

    def __init__(self, monthly_budget: float):
        self.monthly_budget = monthly_budget
        self.spent = 0.0
        self.generations = []

    def can_afford(self, estimated_cost: float) -> bool:
        """Check if generation is within budget."""
        return (self.spent + estimated_cost) <= self.monthly_budget

    def record_generation(self, cost: float, metadata: dict):
        """Record a generation and its cost."""
        self.spent += cost
        self.generations.append({
            "cost": cost,
            "remaining": self.monthly_budget - self.spent,
            **metadata
        })

    def get_remaining(self) -> float:
        """Get remaining budget."""
        return self.monthly_budget - self.spent

    def get_usage_report(self) -> dict:
        """Generate usage report."""
        return {
            "budget": self.monthly_budget,
            "spent": self.spent,
            "remaining": self.get_remaining(),
            "utilization": (self.spent / self.monthly_budget) * 100,
            "generations": len(self.generations)
        }

# Usage
budget = BudgetManager(monthly_budget=100.0)

if budget.can_afford(5.0):
    # Generate video
    budget.record_generation(5.0, {"prompt": "...", "duration": 10})

print(budget.get_usage_report())
```
