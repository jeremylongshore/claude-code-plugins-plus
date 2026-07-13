# In-Memory Caching

## In-Memory Caching

### Simple LRU Cache

```python
from functools import lru_cache
import hashlib

def hash_request(messages: tuple, model: str) -> str:
    """Create hash key for cache lookup."""
    content = f"{model}:{str(messages)}"
    return hashlib.sha256(content.encode()).hexdigest()

@lru_cache(maxsize=1000)
def cached_chat(cache_key: str, model: str, messages_tuple: tuple) -> str:
    """Cached chat completion."""
    messages = [{"role": m[0], "content": m[1]} for m in messages_tuple]

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content

def chat_with_cache(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    """Use cache for identical requests."""
    messages = (("user", prompt),)
    cache_key = hash_request(messages, model)
    return cached_chat(cache_key, model, messages)
```

### TTL Cache

```python
import time
from collections import OrderedDict

class TTLCache:
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        self.maxsize = maxsize
        self.ttl = ttl  # seconds
        self.cache = OrderedDict()

    def _hash(self, model: str, messages: list) -> str:
        content = f"{model}:{messages}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, model: str, messages: list) -> str | None:
        key = self._hash(model, messages)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.cache.move_to_end(key)
                return value
            else:
                del self.cache[key]
        return None

    def set(self, model: str, messages: list, value: str):
        key = self._hash(model, messages)
        self.cache[key] = (value, time.time())
        self.cache.move_to_end(key)

        while len(self.cache) > self.maxsize:
            self.cache.popitem(last=False)

cache = TTLCache(maxsize=1000, ttl=3600)

def chat_with_ttl_cache(
    prompt: str,
    model: str = "openai/gpt-4-turbo"
) -> str:
    messages = [{"role": "user", "content": prompt}]

    # Check cache
    cached = cache.get(model, messages)
    if cached:
        return cached

    # Make request
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content

    # Cache result
    cache.set(model, messages, content)
    return content
```
