# Reference Architecture — Runnable Examples

## Python — Service Layer with Cache-Aside

```python
import os
import hashlib
import json
import time
from openai import OpenAI, RateLimitError

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


class ResponseCache:
    def __init__(self, ttl: int = 3600):
        self._store: dict[str, dict] = {}
        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def _key(self, model: str, messages: list) -> str:
        data = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get(self, model: str, messages: list) -> str | None:
        key = self._key(model, messages)
        entry = self._store.get(key)
        if entry and time.time() - entry["ts"] < self.ttl:
            self.hits += 1
            return entry["value"]
        self.misses += 1
        return None

    def set(self, model: str, messages: list, value: str) -> None:
        key = self._key(model, messages)
        self._store[key] = {"value": value, "ts": time.time()}


class AIService:
    def __init__(self):
        self.cache = ResponseCache(ttl=3600)
        self.default_model = "openai/gpt-3.5-turbo"
        self.fallback_model = "google/gemma-2-9b-it:free"
        self.request_count = 0
        self.total_tokens = 0

    def complete(self, prompt: str, model: str | None = None, use_cache: bool = True) -> str:
        model = model or self.default_model
        messages = [{"role": "user", "content": prompt}]

        if use_cache:
            cached = self.cache.get(model, messages)
            if cached:
                return cached

        for attempt_model in [model, self.fallback_model]:
            try:
                resp = client.chat.completions.create(
                    model=attempt_model, messages=messages, max_tokens=500,
                )
                content = resp.choices[0].message.content or ""
                self.request_count += 1
                self.total_tokens += resp.usage.total_tokens
                if use_cache:
                    self.cache.set(model, messages, content)
                return content
            except RateLimitError:
                if attempt_model != self.fallback_model:
                    print(f"[WARN] Rate limited on {attempt_model}, falling back to {self.fallback_model}")
                else:
                    raise

        return ""


service = AIService()
print(service.complete("What is Python?"))
print(service.complete("What is Python?"))  # cache hit
print(f"Stats: {service.request_count} requests, {service.cache.hits} cache hits, {service.total_tokens} tokens")
```

## TypeScript — Express API Gateway

```typescript
import express, { Request, Response } from "express";
import OpenAI from "openai";

const app = express();
app.use(express.json());

const openrouter = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
  maxRetries: 3,
  timeout: 30_000,
});

function validateRequest(req: Request, res: Response, next: Function) {
  const { prompt, model } = req.body;
  if (!prompt || typeof prompt !== "string") {
    return res.status(400).json({ error: "prompt is required and must be a string" });
  }
  if (prompt.length > 10_000) {
    return res.status(400).json({ error: "prompt too long (max 10000 chars)" });
  }
  if (model && !model.includes("/")) {
    return res.status(400).json({ error: "model must include provider prefix" });
  }
  next();
}

app.post("/api/complete", validateRequest, async (req: Request, res: Response) => {
  const { prompt, model = "openai/gpt-3.5-turbo", maxTokens = 500 } = req.body;
  try {
    const start = performance.now();
    const completion = await openrouter.chat.completions.create({
      model, messages: [{ role: "user", content: prompt }], max_tokens: maxTokens,
    });
    res.json({
      content: completion.choices[0].message.content,
      model: completion.model,
      usage: completion.usage,
      latencyMs: Math.round(performance.now() - start),
    });
  } catch (err: any) {
    const status = err.status ?? 500;
    res.status(status >= 400 && status < 600 ? status : 500).json({ error: err.message });
  }
});

app.get("/health", async (_req, res) => {
  try {
    await openrouter.chat.completions.create({
      model: "openai/gpt-3.5-turbo",
      messages: [{ role: "user", content: "1" }],
      max_tokens: 1,
    });
    res.json({ status: "ok" });
  } catch {
    res.status(503).json({ status: "degraded" });
  }
});

app.listen(3000, () => console.log("AI Gateway running on :3000"));
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
