# Monitoring Costs

## Monitoring Costs

### Per-Request Cost

```python
def get_request_cost(response, model_pricing):
    usage = response.usage
    return calculate_cost(
        model_pricing,
        usage.prompt_tokens,
        usage.completion_tokens
    )

response = client.chat.completions.create(...)
cost = get_request_cost(response, {"prompt": 10, "completion": 30})
print(f"Request cost: ${cost:.6f}")
```

### Dashboard Monitoring

```
openrouter.ai/activity shows:
- Per-request costs
- Daily/weekly/monthly totals
- Model breakdown
- Usage trends
```

### Budget Alerts

```
Set up monitoring:
1. Per-key credit limits
2. Daily spend tracking
3. Alerts when approaching limits
4. Automatic key disable at limit
```
