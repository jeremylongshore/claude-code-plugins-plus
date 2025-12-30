---
name: openrouter-multi-provider
description: |
  Work with multiple providers through OpenRouter. Triggers on "openrouter providers",
  "openrouter multi-model", "compare models openrouter", "openrouter provider selection".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Multi-Provider

## Provider Overview

### Available Providers
```
Provider        | Models                           | Strengths
----------------|----------------------------------|------------------
OpenAI          | GPT-4, GPT-4 Turbo, GPT-3.5     | General, Functions
Anthropic       | Claude 3 Opus/Sonnet/Haiku       | Code, Analysis
Meta            | Llama 3.1 (8B, 70B, 405B)       | Open source, Cost
Mistral         | Mistral, Mixtral                 | Speed, Europe
Google          | Gemini Pro 1.5                   | Long context
Cohere          | Command R+                       | RAG, Enterprise
```

### Get All Available Models
```python
import requests

def get_all_models(api_key: str) -> dict:
    """Get all models grouped by provider."""
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    models = response.json()["data"]

    by_provider = {}
    for model in models:
        provider = model["id"].split("/")[0]
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append({
            "id": model["id"],
            "name": model.get("name", model["id"]),
            "context": model.get("context_length", 0),
            "pricing": model.get("pricing", {})
        })

    return by_provider

providers = get_all_models(api_key)
print(f"Providers: {list(providers.keys())}")
```

## Model Comparison

### Compare Responses
```python
async def compare_models(
    prompt: str,
    models: list,
    **kwargs
) -> dict:
    """Compare responses across models."""
    results = {}

    for model in models:
        start = time.time()
        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

            results[model] = {
                "success": True,
                "content": response.choices[0].message.content,
                "tokens": response.usage.total_tokens,
                "latency_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            results[model] = {
                "success": False,
                "error": str(e),
                "latency_ms": (time.time() - start) * 1000
            }

    return results

# Compare top models
models = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct"
]
comparison = await compare_models("Explain quantum computing", models)
```

### Parallel Comparison
```python
import asyncio

async def parallel_compare(
    prompt: str,
    models: list,
    **kwargs
) -> dict:
    """Run comparisons in parallel."""

    async def query_model(model: str):
        start = time.time()
        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return model, {
                "success": True,
                "content": response.choices[0].message.content,
                "tokens": response.usage.total_tokens,
                "latency_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            return model, {
                "success": False,
                "error": str(e)
            }

    tasks = [query_model(m) for m in models]
    results = await asyncio.gather(*tasks)

    return dict(results)
```

## Provider-Specific Features

### OpenAI Features
```python
def openai_with_json_mode(prompt: str):
    """Use OpenAI JSON mode."""
    return client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

def openai_with_functions(prompt: str, tools: list):
    """Use OpenAI function calling."""
    return client.chat.completions.create(
        model="openai/gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
        tool_choice="auto"
    )
```

### Anthropic Features
```python
def anthropic_long_context(prompt: str, context: str):
    """Use Claude's long context window."""
    # Claude 3 supports 200K tokens
    messages = [
        {"role": "system", "content": f"Context:\n{context}"},
        {"role": "user", "content": prompt}
    ]

    return client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=messages,
        max_tokens=4096
    )
```

### Open Source Models
```python
def use_open_source(prompt: str, prefer_local: bool = False):
    """Use open source models through OpenRouter."""
    models = [
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mixtral-8x7b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
    ]

    model = models[0]

    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```

## Multi-Provider Router

### Best Provider for Task
```python
PROVIDER_STRENGTHS = {
    "anthropic": {
        "strengths": ["code", "analysis", "long_context", "safety"],
        "models": {
            "premium": "anthropic/claude-3-opus",
            "standard": "anthropic/claude-3.5-sonnet",
            "fast": "anthropic/claude-3-haiku"
        }
    },
    "openai": {
        "strengths": ["general", "function_calling", "json", "creative"],
        "models": {
            "premium": "openai/gpt-4",
            "standard": "openai/gpt-4-turbo",
            "fast": "openai/gpt-3.5-turbo"
        }
    },
    "meta-llama": {
        "strengths": ["cost", "open_source", "general"],
        "models": {
            "premium": "meta-llama/llama-3.1-405b-instruct",
            "standard": "meta-llama/llama-3.1-70b-instruct",
            "fast": "meta-llama/llama-3.1-8b-instruct"
        }
    },
    "mistralai": {
        "strengths": ["speed", "european", "efficient"],
        "models": {
            "premium": "mistralai/mistral-large",
            "standard": "mistralai/mixtral-8x7b-instruct",
            "fast": "mistralai/mistral-7b-instruct"
        }
    }
}

def select_provider_for_task(
    task: str,
    quality: str = "standard"
) -> str:
    """Select best provider for task."""
    task_providers = {
        "code": ["anthropic", "openai"],
        "analysis": ["anthropic", "openai"],
        "function_calling": ["openai"],
        "json": ["openai"],
        "creative": ["openai", "anthropic"],
        "long_context": ["anthropic"],
        "cost": ["meta-llama", "mistralai"],
        "general": ["anthropic", "openai", "meta-llama"]
    }

    providers = task_providers.get(task, task_providers["general"])
    best_provider = providers[0]

    return PROVIDER_STRENGTHS[best_provider]["models"][quality]

# Usage
model = select_provider_for_task("code", "standard")
# Returns: "anthropic/claude-3.5-sonnet"
```

## Provider Fallback Chain

### Cross-Provider Resilience
```python
class MultiProviderClient:
    """Client with cross-provider fallback."""

    def __init__(self):
        self.provider_chains = {
            "premium": [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4-turbo",
                "meta-llama/llama-3.1-70b-instruct"
            ],
            "fast": [
                "anthropic/claude-3-haiku",
                "openai/gpt-3.5-turbo",
                "mistralai/mistral-7b-instruct"
            ],
            "cheap": [
                "meta-llama/llama-3.1-8b-instruct",
                "mistralai/mistral-7b-instruct",
                "anthropic/claude-3-haiku"
            ]
        }

        self.disabled_providers = set()

    def disable_provider(self, provider: str, duration: float = 300):
        """Temporarily disable a provider."""
        self.disabled_providers.add(provider)
        # In practice, track expiration time

    def get_chain(self, tier: str) -> list:
        """Get available models in chain."""
        chain = self.provider_chains.get(tier, self.provider_chains["premium"])
        return [
            m for m in chain
            if m.split("/")[0] not in self.disabled_providers
        ]

    def chat(
        self,
        prompt: str,
        tier: str = "premium",
        **kwargs
    ):
        chain = self.get_chain(tier)

        for model in chain:
            try:
                return client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                )
            except Exception as e:
                provider = model.split("/")[0]
                if "unavailable" in str(e).lower():
                    self.disable_provider(provider)
                continue

        raise Exception("All providers failed")

multi_client = MultiProviderClient()
```

## Cost Optimization Across Providers

### Provider Cost Comparison
```python
PROVIDER_PRICING = {
    "anthropic/claude-3-opus": {"prompt": 15.0, "completion": 75.0},
    "anthropic/claude-3.5-sonnet": {"prompt": 3.0, "completion": 15.0},
    "anthropic/claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
    "openai/gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
    "openai/gpt-4": {"prompt": 30.0, "completion": 60.0},
    "openai/gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
    "meta-llama/llama-3.1-70b-instruct": {"prompt": 0.52, "completion": 0.75},
    "meta-llama/llama-3.1-8b-instruct": {"prompt": 0.06, "completion": 0.06},
}

def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> float:
    """Estimate cost for request."""
    pricing = PROVIDER_PRICING.get(model, {"prompt": 10.0, "completion": 30.0})
    return (
        prompt_tokens * pricing["prompt"] / 1_000_000 +
        completion_tokens * pricing["completion"] / 1_000_000
    )

def find_cheapest_model(
    required_quality: str,
    required_context: int
) -> str:
    """Find cheapest model meeting requirements."""
    candidates = []

    for model, pricing in PROVIDER_PRICING.items():
        # Check context (would need to look up actual limits)
        avg_cost = (pricing["prompt"] + pricing["completion"]) / 2
        candidates.append((model, avg_cost))

    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]
```

## Provider Health Monitoring

### Track Provider Status
```python
class ProviderHealthMonitor:
    """Monitor health across providers."""

    def __init__(self):
        self.status = {}
        self.latencies = {}

    def record_success(self, model: str, latency_ms: float):
        provider = model.split("/")[0]

        if provider not in self.status:
            self.status[provider] = {"success": 0, "failure": 0}
            self.latencies[provider] = []

        self.status[provider]["success"] += 1
        self.latencies[provider].append(latency_ms)
        self.latencies[provider] = self.latencies[provider][-100:]

    def record_failure(self, model: str):
        provider = model.split("/")[0]
        if provider not in self.status:
            self.status[provider] = {"success": 0, "failure": 0}
        self.status[provider]["failure"] += 1

    def get_health_report(self) -> dict:
        """Get health report for all providers."""
        report = {}
        for provider, stats in self.status.items():
            total = stats["success"] + stats["failure"]
            latencies = self.latencies.get(provider, [])

            report[provider] = {
                "success_rate": stats["success"] / total if total else 0,
                "total_requests": total,
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0
            }
        return report

monitor = ProviderHealthMonitor()
```
