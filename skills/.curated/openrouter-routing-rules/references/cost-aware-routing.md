# Cost-Aware Routing

## Cost-Aware Routing

### Budget Router

```python
MODEL_COSTS = {
    "anthropic/claude-3-opus": 15.0,      # $/M tokens
    "openai/gpt-4": 30.0,
    "anthropic/claude-3.5-sonnet": 3.0,
    "openai/gpt-4-turbo": 10.0,
    "anthropic/claude-3-haiku": 0.25,
    "openai/gpt-3.5-turbo": 0.5,
    "meta-llama/llama-3.1-8b-instruct": 0.06,
}

class BudgetRouter:
    def __init__(self, budget_per_request: float):
        self.budget = budget_per_request

    def route(self, prompt: str, expected_tokens: int) -> str:
        estimated_cost = {}

        for model, cost_per_m in MODEL_COSTS.items():
            # Cost = tokens * price_per_million / 1_000_000
            request_cost = expected_tokens * cost_per_m / 1_000_000
            if request_cost <= self.budget:
                estimated_cost[model] = request_cost

        if not estimated_cost:
            # Return cheapest if nothing fits budget
            return min(MODEL_COSTS, key=MODEL_COSTS.get)

        # Return best model within budget
        quality_order = [
            "anthropic/claude-3-opus",
            "openai/gpt-4",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4-turbo",
            "anthropic/claude-3-haiku",
            "openai/gpt-3.5-turbo",
            "meta-llama/llama-3.1-8b-instruct",
        ]

        for model in quality_order:
            if model in estimated_cost:
                return model

        return list(estimated_cost.keys())[0]

# $0.01 budget per request
budget_router = BudgetRouter(budget_per_request=0.01)
model = budget_router.route("Hello", expected_tokens=1000)
```
