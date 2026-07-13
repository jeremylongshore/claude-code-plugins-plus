# Cache Invalidation

## Cache Invalidation

### Manual Invalidation

```python
class InvalidatableCache:
    def __init__(self):
        self.cache = {}
        self.tags = {}  # tag -> set of cache keys

    def set(self, key: str, value: str, tags: list = None):
        self.cache[key] = value
        if tags:
            for tag in tags:
                if tag not in self.tags:
                    self.tags[tag] = set()
                self.tags[tag].add(key)

    def get(self, key: str) -> str | None:
        return self.cache.get(key)

    def invalidate_by_tag(self, tag: str):
        if tag in self.tags:
            for key in self.tags[tag]:
                self.cache.pop(key, None)
            del self.tags[tag]

    def invalidate_all(self):
        self.cache.clear()
        self.tags.clear()

# Usage
cache = InvalidatableCache()
cache.set("prompt:123", "response", tags=["user:456", "model:gpt4"])
cache.invalidate_by_tag("user:456")  # Invalidate user's cache
```
