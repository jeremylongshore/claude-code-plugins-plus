# Cost Dashboard

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
