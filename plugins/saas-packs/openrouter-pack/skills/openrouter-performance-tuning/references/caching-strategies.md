# Caching Strategies

## Caching Strategies

### Response Caching

```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_completion(cache_key: str) -> str:
    """Return cached response for identical requests."""
    # This is called only on cache miss
    # Actual call happens in wrapper
    pass

def fast_cached_chat(
    prompt: str,
    model: str = "anthropic/claude-3-haiku"
) -> str:
    """Chat with caching for repeated queries."""
    cache_key = hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()

    # Check if in cache
    try:
        return cached_completion(cache_key)
    except:
        pass

    # Make request
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    content = response.choices[0].message.content

    # Update cache (hack for lru_cache)
    cached_completion.cache_clear()
    cached_completion.__wrapped__(cache_key)

    return content
```

### Semantic Caching

```python
class SemanticCache:
    """Cache similar queries."""

    def __init__(self, similarity_threshold: float = 0.92):
        self.threshold = similarity_threshold
        self.cache = []  # (embedding, prompt, response)

    def get(self, prompt: str) -> str | None:
        """Get cached response for similar prompt."""
        if not self.cache:
            return None

        prompt_embedding = self._embed(prompt)

        for cached_emb, cached_prompt, cached_response in self.cache:
            similarity = self._cosine_sim(prompt_embedding, cached_emb)
            if similarity >= self.threshold:
                return cached_response

        return None

    def set(self, prompt: str, response: str):
        """Cache a response."""
        embedding = self._embed(prompt)
        self.cache.append((embedding, prompt, response))
        # Limit cache size
        self.cache = self.cache[-500:]

    def _embed(self, text: str) -> list:
        # Simplified - use actual embedding model
        return [ord(c) for c in text[:100]]

    def _cosine_sim(self, a: list, b: list) -> float:
        # Simplified cosine similarity
        import numpy as np
        a, b = np.array(a), np.array(b[:len(a)])
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
```
