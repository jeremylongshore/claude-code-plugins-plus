# Redis Caching

## Redis Caching

### Redis Implementation

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

class RedisCache:
    def __init__(self, prefix: str = "openrouter", ttl: int = 3600):
        self.prefix = prefix
        self.ttl = ttl

    def _key(self, model: str, messages: list) -> str:
        content = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        hash_val = hashlib.sha256(content.encode()).hexdigest()
        return f"{self.prefix}:{hash_val}"

    def get(self, model: str, messages: list) -> str | None:
        key = self._key(model, messages)
        value = redis_client.get(key)
        return value.decode() if value else None

    def set(self, model: str, messages: list, value: str):
        key = self._key(model, messages)
        redis_client.setex(key, self.ttl, value)

redis_cache = RedisCache(ttl=3600)

def chat_with_redis(prompt: str, model: str = "openai/gpt-4-turbo") -> str:
    messages = [{"role": "user", "content": prompt}]

    # Check Redis
    cached = redis_cache.get(model, messages)
    if cached:
        return cached

    # Make request
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content

    # Cache in Redis
    redis_cache.set(model, messages, content)
    return content
```

### Async Redis

```python
import aioredis

async_redis = aioredis.from_url("redis://localhost")

async def async_chat_with_redis(
    prompt: str,
    model: str = "openai/gpt-4-turbo"
) -> str:
    messages = [{"role": "user", "content": prompt}]
    key = redis_cache._key(model, messages)

    # Check cache
    cached = await async_redis.get(key)
    if cached:
        return cached.decode()

    # Make request
    response = await async_client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content

    # Cache
    await async_redis.setex(key, 3600, content)
    return content
```
