# Caching Strategy Examples

## Python — In-Memory LRU Cache

```python
import os
import hashlib
import json
import time
from functools import lru_cache
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

class ResponseCache:
    """TTL-based response cache for OpenRouter API calls."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache: dict[str, dict] = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _make_key(self, model: str, messages: list, **params) -> str:
        """Generate a deterministic cache key from request parameters."""
        key_data = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": params.get("temperature", 1),
            "max_tokens": params.get("max_tokens"),
        }, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, key: str) -> str | None:
        entry = self.cache.get(key)
        if entry and (time.time() - entry["timestamp"]) < self.ttl:
            self.hits += 1
            return entry["response"]
        if entry:
            del self.cache[key]  # expired
        self.misses += 1
        return None

    def put(self, key: str, response: str):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache, key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest]
        self.cache[key] = {"response": response, "timestamp": time.time()}

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

cache = ResponseCache(max_size=500, ttl_seconds=3600)

def cached_completion(prompt: str, model: str = "openai/gpt-3.5-turbo",
                      max_tokens: int = 300) -> str:
    messages = [{"role": "user", "content": prompt}]
    key = cache._make_key(model, messages, max_tokens=max_tokens)

    cached = cache.get(key)
    if cached:
        print(f"[Cache HIT] key={key[:8]}...")
        return cached

    response = client.chat.completions.create(
        model=model, messages=messages, max_tokens=max_tokens, temperature=0,
    )
    content = response.choices[0].message.content
    cache.put(key, content)
    print(f"[Cache MISS] key={key[:8]}... (stored)")
    return content

# Usage — second call is instant from cache
result1 = cached_completion("What is Python?")   # [Cache MISS]
result2 = cached_completion("What is Python?")   # [Cache HIT]
print(f"Hit rate: {cache.hit_rate:.0%}")          # Hit rate: 50%
```

## TypeScript — Redis-Based Caching

```typescript
import OpenAI from "openai";
import crypto from "crypto";

const client = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});

// Simple in-memory cache (replace with Redis in production)
const cache = new Map<string, { response: string; expiry: number }>();

function cacheKey(model: string, messages: any[], maxTokens: number): string {
  const data = JSON.stringify({ model, messages, maxTokens });
  return crypto.createHash("sha256").update(data).digest("hex").slice(0, 16);
}

async function cachedChat(
  prompt: string,
  model = "openai/gpt-3.5-turbo",
  ttlMs = 3600_000
): Promise<string> {
  const messages = [{ role: "user" as const, content: prompt }];
  const key = cacheKey(model, messages, 300);

  const cached = cache.get(key);
  if (cached && cached.expiry > Date.now()) {
    console.log(`[HIT] ${key.slice(0, 8)}`);
    return cached.response;
  }

  const res = await client.chat.completions.create({
    model,
    messages,
    max_tokens: 300,
    temperature: 0,
  });

  const content = res.choices[0].message.content || "";
  cache.set(key, { response: content, expiry: Date.now() + ttlMs });
  console.log(`[MISS] ${key.slice(0, 8)} stored`);
  return content;
}

// Two identical calls — second one is cached
await cachedChat("Explain caching in one sentence.");
await cachedChat("Explain caching in one sentence.");
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
