# Concurrent Request Distribution

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
