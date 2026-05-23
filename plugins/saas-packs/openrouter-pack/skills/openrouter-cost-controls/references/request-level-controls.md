# Request-Level Controls

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
