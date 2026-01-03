---
name: openrouter-fallback-config
description: |
  Configure model fallback chains for high availability. Use when building fault-tolerant LLM systems. Trigger with phrases like 'openrouter fallback', 'openrouter backup model', 'openrouter redundancy', 'model failover'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Fallback Configuration

## Overview

This skill demonstrates how to configure and implement model fallback chains that automatically switch to backup models on failure.

## Prerequisites

- OpenRouter integration
- Multiple suitable models identified
- Understanding of your latency/cost requirements

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill demonstrates how to configure and implement model fallback chains that automatically switch to backup models on failure.

## Prerequisites

- OpenRouter integration
- Multiple suitable models identified
- Understanding of your latency/cost requirements

## Basic Fallback Pattern

### Simple Fallback Chain
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

FALLBACK_CHAIN = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "meta-llama/llama-3.1-70b-instruct",
    "mistralai/mistral-large",
]

def chat_with_fallback(prompt: str, **kwargs):
    """Try models in order until one succeeds."""
    last_error = None

    for model in FALLBACK_CHAIN:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
        except Exception as e:
            last_error = e
            print(f"Model {model} failed: {e}")
            continue

    raise last_error or Exception("All fallback models failed")
```

### TypeScript Fallback
```typescript
const FALLBACK_CHAIN = [
  'anthropic/claude-3.5-sonnet',
  'openai/gpt-4-turbo',
  'meta-llama/llama-3.1-70b-instruct',
];

async function chatWithFallback(
  prompt: string,
  options: Partial<OpenAI.Chat.ChatCompletionCreateParams> = {}
): Promise<OpenAI.Chat.ChatCompletion> {
  let lastError: Error | null = null;

  for (const model of FALLBACK_CHAIN) {
    try {
      return await client.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        ...options,
      });
    } catch (error) {
      lastError = error as Error;
      console.error(`Model ${model} failed:`, error);
      continue;
    }
  }

  throw lastError || new Error('All fallback models failed');
}
```

## Smart Fallback Configuration

### Fallback Manager Class
```python
import time
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class ModelConfig:
    id: str
    priority: int = 0
    max_retries: int = 2
    timeout: float = 30.0
    disable_duration: float = 300.0  # 5 minutes

class FallbackManager:
    def __init__(self, models: List[ModelConfig]):
        self.models = sorted(models, key=lambda m: m.priority)
        self.disabled: Dict[str, float] = {}  # model_id -> disable_until

    def is_available(self, model_id: str) -> bool:
        if model_id not in self.disabled:
            return True
        return time.time() > self.disabled[model_id]

    def disable(self, model_id: str, duration: float = 300.0):
        self.disabled[model_id] = time.time() + duration

    def get_available_models(self) -> List[ModelConfig]:
        return [m for m in self.models if self.is_available(m.id)]

    def chat(self, prompt: str, **kwargs):
        available = self.get_available_models()

        if not available:
            # Reset disabled models if all are down
            self.disabled.clear()
            available = self.models

        for model_config in available:
            for attempt in range(model_config.max_retries):
                try:
                    return client.chat.completions.create(
                        model=model_config.id,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=model_config.timeout,
                        **kwargs
                    )
                except Exception as e:
                    if attempt == model_config.max_retries - 1:
                        self.disable(model_config.id, model_config.disable_duration)
                    continue

        raise Exception("All models exhausted")

# Usage
fallback = FallbackManager([
    ModelConfig("anthropic/claude-3.5-sonnet", priority=1),
    ModelConfig("openai/gpt-4-turbo", priority=2),
    ModelConfig("meta-llama/llama-3.1-70b-instruct", priority=3),
])
```

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

## Error-Specific Fallback Logic

### Conditional Fallback
```python
from openai import RateLimitError, APIError, APIConnectionError

def smart_fallback(prompt: str, primary_model: str, fallback_models: list):
    """Fallback based on error type."""
    try:
        return client.chat.completions.create(
            model=primary_model,
            messages=[{"role": "user", "content": prompt}]
        )
    except RateLimitError:
        # Rate limited - try different model immediately
        pass
    except APIConnectionError:
        # Connection issue - retry same model first
        time.sleep(1)
        try:
            return client.chat.completions.create(
                model=primary_model,
                messages=[{"role": "user", "content": prompt}]
            )
        except:
            pass
    except APIError as e:
        if e.status_code == 503:
            # Model unavailable - try fallbacks
            pass
        else:
            raise  # Don't fallback on client errors

    # Try fallbacks
    for model in fallback_models:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception:
            continue

    raise Exception("Primary and all fallbacks failed")
```

## Provider-Based Fallback

### Cross-Provider Resilience
```python
PROVIDERS = {
    "anthropic": [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
    ],
    "openai": [
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
    ],
    "meta": [
        "meta-llama/llama-3.1-70b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
    ],
}

def get_cross_provider_chain(primary_provider: str) -> list:
    """Build chain that switches providers on failure."""
    chain = []

    # Primary provider models first
    chain.extend(PROVIDERS.get(primary_provider, []))

    # Then other providers
    for provider, models in PROVIDERS.items():
        if provider != primary_provider:
            chain.extend(models)

    return chain

def chat_cross_provider(prompt: str, primary_provider: str = "anthropic"):
    chain = get_cross_provider_chain(primary_provider)

    for model in chain:
        try:
            return client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception:
            continue

    raise Exception("All providers failed")
```

## Fallback Health Tracking

### Track Model Health
```python
from collections import defaultdict
from datetime import datetime, timedelta

class HealthTracker:
    def __init__(self, window_minutes: int = 10):
        self.window = timedelta(minutes=window_minutes)
        self.successes = defaultdict(list)
        self.failures = defaultdict(list)

    def record_success(self, model: str):
        now = datetime.now()
        self._cleanup(model, now)
        self.successes[model].append(now)

    def record_failure(self, model: str):
        now = datetime.now()
        self._cleanup(model, now)
        self.failures[model].append(now)

    def _cleanup(self, model: str, now: datetime):
        cutoff = now - self.window
        self.successes[model] = [t for t in self.successes[model] if t > cutoff]
        self.failures[model] = [t for t in self.failures[model] if t > cutoff]

    def get_success_rate(self, model: str) -> float:
        total = len(self.successes[model]) + len(self.failures[model])
        if total == 0:
            return 1.0  # Assume healthy if no data
        return len(self.successes[model]) / total

    def should_skip(self, model: str, threshold: float = 0.3) -> bool:
        return self.get_success_rate(model) < threshold

tracker = HealthTracker()

def health_aware_fallback(prompt: str, models: list):
    # Sort by current health
    sorted_models = sorted(
        models,
        key=lambda m: tracker.get_success_rate(m),
        reverse=True
    )

    for model in sorted_models:
        if tracker.should_skip(model):
            continue

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            tracker.record_success(model)
            return response
        except Exception:
            tracker.record_failure(model)
            continue

    raise Exception("All healthy models failed")
```

## Configuration Examples

### YAML Configuration
```yaml
# fallback-config.yaml
fallback:
  default_chain:
    - anthropic/claude-3.5-sonnet
    - openai/gpt-4-turbo
    - meta-llama/llama-3.1-70b-instruct

  task_chains:
    coding:
      - anthropic/claude-3.5-sonnet
      - deepseek/deepseek-coder
    fast:
      - anthropic/claude-3-haiku
      - openai/gpt-3.5-turbo

  settings:
    max_retries_per_model: 2
    disable_duration_seconds: 300
    health_window_minutes: 10
    skip_threshold: 0.3
```

### Load Configuration
```python
import yaml

def load_fallback_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)

config = load_fallback_config("fallback-config.yaml")
default_chain = config["fallback"]["default_chain"]
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
