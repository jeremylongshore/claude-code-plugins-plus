# Status Dashboard

## Status Dashboard

### Simple Status Output

```python
def print_status_dashboard():
    """Print formatted status dashboard."""
    print("=" * 60)
    print("OpenRouter Model Status Dashboard")
    print("=" * 60)

    models = get_available_models(api_key)

    # Group by provider
    by_provider = {}
    for model in models:
        provider = model["id"].split("/")[0]
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(model)

    for provider, provider_models in sorted(by_provider.items()):
        print(f"\n{provider.upper()}:")
        for model in provider_models[:5]:  # Show first 5
            ctx = model.get("context_length", "?")
            prompt_price = model.get("pricing", {}).get("prompt", "?")
            print(f"  ✓ {model['id']} (ctx: {ctx}, ${prompt_price}/token)")
        if len(provider_models) > 5:
            print(f"  ... and {len(provider_models) - 5} more")

print_status_dashboard()
```

### Model Comparison Table

```python
def compare_models(model_ids: list):
    """Compare models side by side."""
    models = get_available_models(api_key)
    model_map = {m["id"]: m for m in models}

    print(f"{'Model':<40} {'Context':<10} {'Prompt $/M':<12} {'Completion $/M'}")
    print("-" * 80)

    for model_id in model_ids:
        if model_id in model_map:
            m = model_map[model_id]
            ctx = m.get("context_length", "N/A")
            prompt = float(m["pricing"]["prompt"]) * 1_000_000
            completion = float(m["pricing"]["completion"]) * 1_000_000
            print(f"{model_id:<40} {ctx:<10} ${prompt:<11.2f} ${completion:.2f}")
        else:
            print(f"{model_id:<40} NOT AVAILABLE")

compare_models([
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku"
])
```
