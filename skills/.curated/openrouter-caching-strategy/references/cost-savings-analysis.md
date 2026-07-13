# Cost Savings Analysis

## Cost Savings Analysis

### Cache Hit Tracking

```python
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.saved_tokens = 0
        self.saved_cost = 0.0

    def record_hit(self, tokens: int, cost_per_m: float):
        self.hits += 1
        self.saved_tokens += tokens
        self.saved_cost += tokens * cost_per_m / 1_000_000

    def record_miss(self):
        self.misses += 1

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "total_requests": total,
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "tokens_saved": self.saved_tokens,
            "cost_saved": self.saved_cost
        }

metrics = CacheMetrics()

def tracked_cached_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
    messages = [{"role": "user", "content": prompt}]

    cached = cache.get(model, messages)
    if cached:
        # Estimate tokens saved
        tokens = len(prompt) // 4 + len(cached) // 4
        metrics.record_hit(tokens, 10.0)  # Assuming $10/M
        return cached

    metrics.record_miss()
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    content = response.choices[0].message.content
    cache.set(model, messages, content)
    return content

# Check savings
print(metrics.stats())
```
