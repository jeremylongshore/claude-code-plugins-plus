# Health-Based Routing

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
