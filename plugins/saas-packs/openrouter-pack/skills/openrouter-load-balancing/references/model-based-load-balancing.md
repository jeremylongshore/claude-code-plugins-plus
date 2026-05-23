# Model-Based Load Balancing

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
