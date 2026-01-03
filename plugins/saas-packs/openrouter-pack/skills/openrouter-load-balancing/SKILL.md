---
name: openrouter-load-balancing
description: |
  Distribute requests across multiple OpenRouter configurations. Use when scaling or implementing geographic distribution. Trigger with phrases like 'openrouter load balance', 'distribute requests', 'openrouter scaling', 'multi-key openrouter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# OpenRouter Load Balancing

## Overview

This skill teaches load balancing patterns for distributing requests across multiple API keys or configurations.

## Prerequisites

- Multiple OpenRouter API keys
- Understanding of your traffic patterns

## Instructions

Follow these steps to implement this skill:

1. **Verify Prerequisites**: Ensure all prerequisites listed above are met
2. **Review the Implementation**: Study the code examples and patterns below
3. **Adapt to Your Environment**: Modify configuration values for your setup
4. **Test the Integration**: Run the verification steps to confirm functionality
5. **Monitor in Production**: Set up appropriate logging and monitoring

## Overview

This skill teaches load balancing patterns for distributing requests across multiple API keys or configurations.

## Prerequisites

- Multiple OpenRouter API keys
- Understanding of your traffic patterns

## Multi-Key Load Balancing

### Round Robin
```python
from openai import OpenAI
import itertools

class RoundRobinClient:
    def __init__(self, api_keys: list):
        self.clients = [
            OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=key
            )
            for key in api_keys
        ]
        self.cycle = itertools.cycle(range(len(self.clients)))

    def get_client(self) -> OpenAI:
        idx = next(self.cycle)
        return self.clients[idx]

    def chat(self, **kwargs):
        client = self.get_client()
        return client.chat.completions.create(**kwargs)

# Usage
keys = [
    os.environ["OPENROUTER_API_KEY_1"],
    os.environ["OPENROUTER_API_KEY_2"],
    os.environ["OPENROUTER_API_KEY_3"],
]
lb_client = RoundRobinClient(keys)

response = lb_client.chat(
    model="openai/gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Weighted Round Robin
```python
class WeightedClient:
    def __init__(self, api_keys: list, weights: list):
        self.clients = []
        for key, weight in zip(api_keys, weights):
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=key
            )
            # Add client multiple times based on weight
            self.clients.extend([client] * weight)

        self.cycle = itertools.cycle(range(len(self.clients)))

    def get_client(self) -> OpenAI:
        idx = next(self.cycle)
        return self.clients[idx]

# Key 1 gets 3x traffic, Key 2 gets 2x, Key 3 gets 1x
weighted_client = WeightedClient(
    api_keys=[key1, key2, key3],
    weights=[3, 2, 1]
)
```

## Credit-Aware Load Balancing

### Balance-Based Routing
```python
import requests
import time

class CreditAwareBalancer:
    def __init__(self, api_keys: list):
        self.keys = api_keys
        self.balances = {}
        self.last_check = 0
        self.check_interval = 60  # seconds

    def _refresh_balances(self):
        now = time.time()
        if now - self.last_check < self.check_interval:
            return

        for key in self.keys:
            try:
                response = requests.get(
                    "https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=5
                )
                data = response.json()["data"]
                self.balances[key] = data["limit_remaining"]
            except:
                self.balances[key] = 0

        self.last_check = now

    def get_best_key(self) -> str:
        """Get key with highest remaining balance."""
        self._refresh_balances()

        if not self.balances:
            return self.keys[0]

        return max(self.balances, key=self.balances.get)

    def get_client(self) -> OpenAI:
        key = self.get_best_key()
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key
        )

credit_balancer = CreditAwareBalancer(keys)
```

### Threshold-Based Switching
```python
class ThresholdBalancer:
    def __init__(self, api_keys: list, threshold: float = 10.0):
        self.keys = api_keys
        self.threshold = threshold
        self.current_idx = 0
        self.exhausted = set()

    def check_balance(self, key: str) -> float:
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {key}"},
                timeout=5
            )
            return response.json()["data"]["limit_remaining"]
        except:
            return 0

    def get_key(self) -> str:
        # Try current key
        key = self.keys[self.current_idx]

        if key not in self.exhausted:
            balance = self.check_balance(key)
            if balance >= self.threshold:
                return key
            else:
                self.exhausted.add(key)

        # Find next available key
        for idx in range(len(self.keys)):
            if idx == self.current_idx:
                continue
            key = self.keys[idx]
            if key not in self.exhausted:
                balance = self.check_balance(key)
                if balance >= self.threshold:
                    self.current_idx = idx
                    return key
                else:
                    self.exhausted.add(key)

        # All exhausted, reset and use first
        self.exhausted.clear()
        self.current_idx = 0
        return self.keys[0]
```

## Concurrent Request Distribution

### Async Load Balancer
```python
from openai import AsyncOpenAI
import asyncio
from typing import List

class AsyncLoadBalancer:
    def __init__(self, api_keys: list):
        self.clients = [
            AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=key
            )
            for key in api_keys
        ]
        self.current = 0
        self.lock = asyncio.Lock()

    async def get_client(self) -> AsyncOpenAI:
        async with self.lock:
            client = self.clients[self.current]
            self.current = (self.current + 1) % len(self.clients)
            return client

    async def batch_requests(
        self,
        prompts: List[str],
        model: str,
        **kwargs
    ):
        """Distribute batch requests across clients."""
        tasks = []

        for prompt in prompts:
            client = await self.get_client()
            task = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

async_balancer = AsyncLoadBalancer(keys)

# Process 100 prompts across all keys
prompts = ["Question " + str(i) for i in range(100)]
results = await async_balancer.batch_requests(prompts, "openai/gpt-4-turbo")
```

### Semaphore-Based Concurrency
```python
class ConcurrencyLimitedBalancer:
    def __init__(self, api_keys: list, concurrent_per_key: int = 5):
        self.keys = api_keys
        self.semaphores = {
            key: asyncio.Semaphore(concurrent_per_key)
            for key in api_keys
        }
        self.clients = {
            key: AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=key
            )
            for key in api_keys
        }

    async def get_available_key(self) -> str:
        """Get key with available capacity."""
        while True:
            for key in self.keys:
                if not self.semaphores[key].locked():
                    return key
            await asyncio.sleep(0.01)

    async def chat(self, **kwargs):
        key = await self.get_available_key()

        async with self.semaphores[key]:
            return await self.clients[key].chat.completions.create(**kwargs)

limited_balancer = ConcurrencyLimitedBalancer(keys, concurrent_per_key=10)
```

## Model-Based Load Balancing

### Route by Model
```python
class ModelBalancer:
    def __init__(self, model_key_map: dict):
        """
        model_key_map = {
            "anthropic/*": [key1, key2],
            "openai/*": [key3],
            "*": [key4, key5]  # Default
        }
        """
        self.model_key_map = model_key_map
        self.balancers = {
            pattern: RoundRobinClient(keys)
            for pattern, keys in model_key_map.items()
        }

    def _match_pattern(self, model: str) -> str:
        for pattern in self.model_key_map:
            if pattern == "*":
                continue
            if pattern.endswith("/*"):
                prefix = pattern[:-2]
                if model.startswith(prefix):
                    return pattern
            elif pattern == model:
                return pattern
        return "*"

    def chat(self, model: str, **kwargs):
        pattern = self._match_pattern(model)
        balancer = self.balancers.get(pattern, self.balancers["*"])
        return balancer.chat(model=model, **kwargs)

model_balancer = ModelBalancer({
    "anthropic/*": [key1, key2],  # Anthropic models
    "openai/*": [key3, key4],     # OpenAI models
    "*": [key5]                   # Everything else
})
```

## Health-Based Routing

### Health-Aware Balancer
```python
class HealthyBalancer:
    def __init__(self, api_keys: list):
        self.keys = api_keys
        self.health = {key: True for key in api_keys}
        self.error_counts = {key: 0 for key in api_keys}
        self.max_errors = 3
        self.recovery_time = 60
        self.recovery_timestamps = {}

    def mark_unhealthy(self, key: str):
        self.error_counts[key] += 1
        if self.error_counts[key] >= self.max_errors:
            self.health[key] = False
            self.recovery_timestamps[key] = time.time() + self.recovery_time

    def mark_healthy(self, key: str):
        self.error_counts[key] = 0
        self.health[key] = True

    def get_healthy_key(self) -> str:
        now = time.time()

        # Check for recovered keys
        for key in self.keys:
            if not self.health[key]:
                if now > self.recovery_timestamps.get(key, 0):
                    self.health[key] = True
                    self.error_counts[key] = 0

        # Return first healthy key
        for key in self.keys:
            if self.health[key]:
                return key

        # All unhealthy, return first
        return self.keys[0]

    def chat(self, **kwargs):
        key = self.get_healthy_key()
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key
        )

        try:
            response = client.chat.completions.create(**kwargs)
            self.mark_healthy(key)
            return response
        except Exception as e:
            self.mark_unhealthy(key)
            raise

healthy_balancer = HealthyBalancer(keys)
```

## Monitoring Load Distribution

### Request Tracking
```python
from collections import Counter
from datetime import datetime

class LoadMonitor:
    def __init__(self, balancer):
        self.balancer = balancer
        self.request_counts = Counter()
        self.latencies = {}
        self.errors = Counter()

    def record_request(self, key: str, latency: float, success: bool):
        self.request_counts[key] += 1
        if key not in self.latencies:
            self.latencies[key] = []
        self.latencies[key].append(latency)

        if not success:
            self.errors[key] += 1

    def stats(self) -> dict:
        return {
            "distribution": dict(self.request_counts),
            "avg_latency": {
                key: sum(lats) / len(lats)
                for key, lats in self.latencies.items()
            },
            "error_rate": {
                key: self.errors[key] / self.request_counts[key]
                for key in self.request_counts
            }
        }

monitor = LoadMonitor(lb_client)
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
