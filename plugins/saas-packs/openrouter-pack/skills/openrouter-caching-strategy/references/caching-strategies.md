# Caching Strategies

## Caching Strategies

### Cache by Intent

```python
from enum import Enum

class CachePolicy(Enum):
    NEVER = "never"
    SHORT = "short"    # 5 minutes
    MEDIUM = "medium"  # 1 hour
    LONG = "long"      # 24 hours

POLICY_TTL = {
    CachePolicy.NEVER: 0,
    CachePolicy.SHORT: 300,
    CachePolicy.MEDIUM: 3600,
    CachePolicy.LONG: 86400,
}

def determine_cache_policy(prompt: str) -> CachePolicy:
    """Determine caching policy based on prompt."""
    prompt_lower = prompt.lower()

    # Never cache time-sensitive queries
    if any(word in prompt_lower for word in ["current", "today", "now", "latest"]):
        return CachePolicy.NEVER

    # Long cache for factual/reference queries
    if any(word in prompt_lower for word in ["definition", "explain", "what is"]):
        return CachePolicy.LONG

    # Medium cache for code generation
    if any(word in prompt_lower for word in ["write", "code", "function"]):
        return CachePolicy.MEDIUM

    return CachePolicy.SHORT

def smart_cached_chat(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    policy = determine_cache_policy(prompt)

    if policy == CachePolicy.NEVER:
        # Skip cache entirely
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    # Use cache with policy TTL
    ttl = POLICY_TTL[policy]
    # ... implement with TTL-aware cache
```

### Multi-Level Caching

```python
class MultiLevelCache:
    def __init__(self):
        self.l1 = TTLCache(maxsize=100, ttl=300)    # Fast, small, short
        self.l2 = TTLCache(maxsize=1000, ttl=3600)  # Larger, longer
        # self.l3 = RedisCache(ttl=86400)           # Persistent

    def get(self, model: str, messages: list) -> str | None:
        # Try L1 first
        result = self.l1.get(model, messages)
        if result:
            return result

        # Try L2
        result = self.l2.get(model, messages)
        if result:
            # Promote to L1
            self.l1.set(model, messages, result)
            return result

        return None

    def set(self, model: str, messages: list, value: str, tier: int = 1):
        if tier >= 1:
            self.l1.set(model, messages, value)
        if tier >= 2:
            self.l2.set(model, messages, value)

multi_cache = MultiLevelCache()
```
