# Credit-Aware Load Balancing

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
