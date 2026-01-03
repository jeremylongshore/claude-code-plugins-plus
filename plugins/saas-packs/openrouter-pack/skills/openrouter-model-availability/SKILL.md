---
name: openrouter-model-availability
description: |
  Check model availability and implement fallback chains. Use when building resilient systems or handling model outages. Trigger with phrases like 'openrouter availability', 'openrouter fallback', 'openrouter model down', 'openrouter health check'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Model Availability

## Overview

This skill covers model health monitoring, availability checking, and implementing automatic fallback chains for production reliability.

## Prerequisites

- OpenRouter integration
- Multiple model options identified

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill covers model health monitoring, availability checking, and implementing automatic fallback chains for production reliability.

## Prerequisites

- OpenRouter integration
- Multiple model options identified

## Checking Model Status

### List All Available Models
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Python Model Checker
```python
import requests

def get_available_models(api_key: str) -> list:
    """Get all currently available models."""
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    response.raise_for_status()
    return response.json()["data"]

def is_model_available(api_key: str, model_id: str) -> bool:
    """Check if specific model is available."""
    models = get_available_models(api_key)
    return any(m["id"] == model_id for m in models)

# Usage
if is_model_available(api_key, "openai/gpt-4-turbo"):
    print("Model is available")
```

### TypeScript Model Checker
```typescript
interface ModelInfo {
  id: string;
  name: string;
  context_length: number;
  pricing: {
    prompt: string;
    completion: string;
  };
}

async function getAvailableModels(apiKey: string): Promise<ModelInfo[]> {
  const response = await fetch('https://openrouter.ai/api/v1/models', {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  const data = await response.json();
  return data.data;
}

async function isModelAvailable(apiKey: string, modelId: string): Promise<boolean> {
  const models = await getAvailableModels(apiKey);
  return models.some((m) => m.id === modelId);
}
```

## Model Health Monitoring

### Health Check Function
```python
import time
from typing import Optional

def check_model_health(
    model_id: str,
    timeout: float = 10.0
) -> dict:
    """Check if model responds correctly."""
    start = time.time()

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=5,
            timeout=timeout
        )

        latency = time.time() - start
        return {
            "model": model_id,
            "status": "healthy",
            "latency_ms": latency * 1000,
            "response": response.choices[0].message.content
        }

    except Exception as e:
        latency = time.time() - start
        return {
            "model": model_id,
            "status": "unhealthy",
            "latency_ms": latency * 1000,
            "error": str(e)
        }

# Check multiple models
models_to_check = [
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-sonnet",
    "meta-llama/llama-3.1-70b-instruct"
]

for model in models_to_check:
    health = check_model_health(model)
    print(f"{model}: {health['status']} ({health['latency_ms']:.0f}ms)")
```

### Continuous Monitoring
```python
import asyncio
from datetime import datetime

class ModelMonitor:
    def __init__(self, models: list, check_interval: int = 60):
        self.models = models
        self.check_interval = check_interval
        self.status_history = {m: [] for m in models}

    async def check_all(self):
        """Check all models once."""
        results = {}
        for model in self.models:
            health = check_model_health(model)
            results[model] = health

            self.status_history[model].append({
                "timestamp": datetime.now().isoformat(),
                "status": health["status"],
                "latency": health.get("latency_ms", 0)
            })

            # Keep last 100 entries
            self.status_history[model] = self.status_history[model][-100:]

        return results

    def get_uptime(self, model: str) -> float:
        """Calculate uptime percentage for model."""
        history = self.status_history.get(model, [])
        if not history:
            return 0.0
        healthy = sum(1 for h in history if h["status"] == "healthy")
        return healthy / len(history) * 100

    async def run(self):
        """Continuous monitoring loop."""
        while True:
            results = await self.check_all()
            print(f"\n[{datetime.now().isoformat()}] Model Status:")
            for model, health in results.items():
                uptime = self.get_uptime(model)
                print(f"  {model}: {health['status']} (uptime: {uptime:.1f}%)")
            await asyncio.sleep(self.check_interval)

# Usage
monitor = ModelMonitor([
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-sonnet"
])
# asyncio.run(monitor.run())
```

## Handling Model Unavailability

### Fallback Chain
```python
class ModelFallback:
    def __init__(self, models: list):
        self.models = models
        self.disabled = set()
        self.disable_until = {}

    def disable_model(self, model: str, duration: float = 300):
        """Temporarily disable a model."""
        self.disabled.add(model)
        self.disable_until[model] = time.time() + duration

    def get_available_models(self) -> list:
        """Get currently available models."""
        now = time.time()
        # Re-enable models past their disable duration
        for model in list(self.disabled):
            if self.disable_until.get(model, 0) < now:
                self.disabled.remove(model)

        return [m for m in self.models if m not in self.disabled]

    def chat(self, prompt: str, **kwargs):
        """Try models in order until one works."""
        available = self.get_available_models()

        if not available:
            raise Exception("All models unavailable")

        for model in available:
            try:
                return client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
            except Exception as e:
                if "unavailable" in str(e).lower():
                    self.disable_model(model)
                    continue
                raise

        raise Exception("All models failed")

# Usage
fallback = ModelFallback([
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct"
])
```

### Model Groups
```python
MODEL_GROUPS = {
    "coding": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "deepseek/deepseek-coder"
    ],
    "fast": [
        "anthropic/claude-3-haiku",
        "openai/gpt-3.5-turbo",
        "meta-llama/llama-3.1-8b-instruct"
    ],
    "cheap": [
        "meta-llama/llama-3.1-8b-instruct",
        "mistralai/mistral-7b-instruct"
    ]
}

def get_working_model(group: str) -> Optional[str]:
    """Find first working model in group."""
    models = MODEL_GROUPS.get(group, [])

    for model in models:
        health = check_model_health(model, timeout=5.0)
        if health["status"] == "healthy":
            return model

    return None
```

## Provider Status

### Check Provider Health
```python
PROVIDERS = {
    "openai": ["openai/gpt-4-turbo", "openai/gpt-3.5-turbo"],
    "anthropic": ["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku"],
    "meta": ["meta-llama/llama-3.1-70b-instruct", "meta-llama/llama-3.1-8b-instruct"],
}

def check_provider_health(provider: str) -> dict:
    """Check health of all models from a provider."""
    models = PROVIDERS.get(provider, [])
    results = {"provider": provider, "models": {}}

    for model in models:
        health = check_model_health(model)
        results["models"][model] = health["status"]

    healthy = sum(1 for s in results["models"].values() if s == "healthy")
    results["healthy_count"] = healthy
    results["total_count"] = len(models)
    results["status"] = "healthy" if healthy == len(models) else "degraded" if healthy > 0 else "down"

    return results
```

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

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)

## Output

Successful execution produces:
- Working OpenRouter integration
- Verified API connectivity
- Example responses demonstrating functionality

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format (must start with `sk-or-`)
2. **429 Rate Limited**: Implement exponential backoff
3. **500 Server Error**: Retry with backoff, check OpenRouter status page
4. **Model Not Found**: Verify model ID includes provider prefix

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
