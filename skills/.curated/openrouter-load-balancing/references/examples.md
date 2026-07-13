# Load Balancing Examples

## Python — Multi-Key Round-Robin Load Balancer

```python
import os
import threading
from openai import OpenAI

class KeyPool:
    """Round-robin API key pool for distributing requests."""

    def __init__(self, keys: list[str]):
        if not keys:
            raise ValueError("At least one API key is required")
        self.keys = keys
        self._index = 0
        self._lock = threading.Lock()
        self._stats = {k[:12]: {"requests": 0, "errors": 0} for k in keys}

    def next_key(self) -> str:
        with self._lock:
            key = self.keys[self._index % len(self.keys)]
            self._index += 1
            self._stats[key[:12]]["requests"] += 1
            return key

    def report_error(self, key: str):
        with self._lock:
            self._stats[key[:12]]["errors"] += 1

    def get_stats(self) -> dict:
        with self._lock:
            return dict(self._stats)

# Initialize with multiple keys
keys = [
    os.environ.get("OPENROUTER_KEY_1", os.environ["OPENROUTER_API_KEY"]),
    os.environ.get("OPENROUTER_KEY_2", os.environ["OPENROUTER_API_KEY"]),
]
pool = KeyPool(keys)

def balanced_completion(prompt: str, model: str = "openai/gpt-3.5-turbo") -> str:
    """Make a completion request with load-balanced API keys."""
    key = pool.next_key()
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.choices[0].message.content
    except Exception as e:
        pool.report_error(key)
        raise

# Usage
for i in range(6):
    result = balanced_completion(f"Request {i}: Hello!")
    print(f"[{i}] {result[:50]}...")

print("\nLoad distribution:", pool.get_stats())
# Load distribution: {'sk-or-v1-abc': {'requests': 3, 'errors': 0},
#                     'sk-or-v1-def': {'requests': 3, 'errors': 0}}
```

## TypeScript — Health-Aware Load Balancer

```typescript
import OpenAI from "openai";

interface Endpoint {
  key: string;
  healthy: boolean;
  errorCount: number;
  lastError: number;
  requestCount: number;
}

class LoadBalancer {
  private endpoints: Endpoint[];
  private index = 0;

  constructor(keys: string[]) {
    this.endpoints = keys.map((key) => ({
      key,
      healthy: true,
      errorCount: 0,
      lastError: 0,
      requestCount: 0,
    }));
  }

  getNext(): Endpoint {
    const healthy = this.endpoints.filter((e) => e.healthy);
    if (healthy.length === 0) {
      // Reset all endpoints if none are healthy (circuit breaker reset)
      this.endpoints.forEach((e) => { e.healthy = true; e.errorCount = 0; });
      console.log("[LB] All endpoints reset");
      return this.endpoints[0];
    }
    const ep = healthy[this.index % healthy.length];
    this.index++;
    ep.requestCount++;
    return ep;
  }

  markError(ep: Endpoint) {
    ep.errorCount++;
    if (ep.errorCount >= 3) {
      ep.healthy = false;
      ep.lastError = Date.now();
      console.log(`[LB] Endpoint ${ep.key.slice(0, 12)} marked unhealthy`);
    }
  }

  markSuccess(ep: Endpoint) {
    ep.errorCount = 0;
    ep.healthy = true;
  }
}

const lb = new LoadBalancer([
  process.env.OPENROUTER_KEY_1!,
  process.env.OPENROUTER_KEY_2!,
]);

async function balancedChat(prompt: string): Promise<string> {
  const ep = lb.getNext();
  const client = new OpenAI({
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: ep.key,
  });

  try {
    const res = await client.chat.completions.create({
      model: "openai/gpt-3.5-turbo",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 100,
    });
    lb.markSuccess(ep);
    return res.choices[0].message.content || "";
  } catch (err) {
    lb.markError(ep);
    throw err;
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
