# Cost Comparison Tool

## Cost Comparison Tool

```python
def compare_model_costs(prompt: str, models: list):
    """Compare costs across models for same prompt."""
    results = []

    for model_id in models:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # Get pricing from models API
        model_info = get_model_info(model_id)
        cost = calculate_cost(
            model_info["pricing"],
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        results.append({
            "model": model_id,
            "cost": cost,
            "tokens": response.usage.total_tokens
        })

    return sorted(results, key=lambda x: x["cost"])

# Usage
models = [
    "anthropic/claude-3-haiku",
    "openai/gpt-3.5-turbo",
    "openai/gpt-4-turbo"
]
comparison = compare_model_costs("Explain recursion", models)
```
