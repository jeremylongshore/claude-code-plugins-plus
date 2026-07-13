# Multi-Key Load Balancing

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
