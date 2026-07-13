# Task-Specific Fallbacks

## Task-Specific Fallbacks

### By Task Type

```python
TASK_FALLBACKS = {
    "coding": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "deepseek/deepseek-coder",
    ],
    "creative": [
        "anthropic/claude-3-opus",
        "openai/gpt-4-turbo",
        "meta-llama/llama-3.1-70b-instruct",
    ],
    "fast": [
        "anthropic/claude-3-haiku",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3.1-8b-instruct",
    ],
    "default": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
    ],
}

def chat_for_task(prompt: str, task_type: str = "default", **kwargs):
    """Use task-appropriate fallback chain."""
    chain = TASK_FALLBACKS.get(task_type, TASK_FALLBACKS["default"])

    for model in chain:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
        except Exception:
            continue

    raise Exception(f"All {task_type} models failed")
```

### By Cost Tier

```python
COST_TIERS = {
    "premium": [
        "anthropic/claude-3-opus",
        "openai/gpt-4",
    ],
    "standard": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
    ],
    "budget": [
        "anthropic/claude-3-haiku",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3.1-8b-instruct",
    ],
}

def chat_with_budget(prompt: str, max_cost_tier: str = "standard", **kwargs):
    """Use models up to specified cost tier."""
    tiers = ["budget", "standard", "premium"]
    max_index = tiers.index(max_cost_tier)

    models = []
    for tier in tiers[:max_index + 1]:
        models.extend(COST_TIERS[tier])

    for model in models:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
        except Exception:
            continue

    raise Exception("All budget-appropriate models failed")
```
