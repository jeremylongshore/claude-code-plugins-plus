---
name: klingai-performance-tuning
description: |
  Optimize Kling AI for speed, quality, and cost efficiency. Use when improving generation times
  or finding optimal settings. Trigger with phrases like 'klingai performance', 'kling ai optimize',
  'faster klingai', 'klingai quality settings'.
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, kling-ai, performance, optimization]

---
# Kling AI Performance Tuning

## Overview

Optimize video generation for your use case by choosing the right model, mode, and parameters. Covers benchmarking, speed vs. quality trade-offs, connection pooling, and caching strategies.

## Speed vs. Quality Matrix

| Config | ~Gen Time | Quality | Credits (5s) | Best For |
|--------|-----------|---------|-------------|----------|
| v2.5-turbo + standard | 30-60s | Good | 10 | Drafts, iteration |
| v2-master + standard | 60-90s | High | 10 | Production previews |
| v2.6 + standard | 60-120s | Highest | 10 | Quality-sensitive |
| v2.6 + professional | 120-300s | Highest+ | 35 | Final output |
| v2.6 + prof + audio | 180-400s | Highest+ | 200 | Full production |

## Benchmarking Tool

```python
import time, requests, json

def benchmark_model(prompt: str, model: str, mode: str = "standard",
                    runs: int = 3) -> dict:
    """Benchmark generation time for a model/mode combination."""
    times = []

    for i in range(runs):
        start = time.monotonic()

        # Submit
        r = requests.post(f"{BASE}/videos/text2video", headers=get_headers(), json={
            "model_name": model, "prompt": prompt, "duration": "5", "mode": mode,
        }).json()
        task_id = r["data"]["task_id"]

        # Poll
        while True:
            time.sleep(10)
            result = requests.get(
                f"{BASE}/videos/text2video/{task_id}", headers=get_headers()
            ).json()
            if result["data"]["task_status"] in ("succeed", "failed"):
                break

        elapsed = time.monotonic() - start
        times.append(elapsed)
        print(f"  Run {i+1}/{runs}: {elapsed:.1f}s ({result['data']['task_status']})")

    return {
        "model": model,
        "mode": mode,
        "avg_sec": round(sum(times) / len(times), 1),
        "min_sec": round(min(times), 1),
        "max_sec": round(max(times), 1),
        "runs": runs,
    }

# Compare models
prompt = "A waterfall in a tropical forest, cinematic"
for model in ["kling-v2-5-turbo", "kling-v2-master", "kling-v2-6"]:
    result = benchmark_model(prompt, model, runs=2)
    print(f"{model}: avg={result['avg_sec']}s, min={result['min_sec']}s")
```

## Connection Pooling

```python
import requests

# Without pooling: new TCP connection per request (slow)
# With pooling: reuse connections (fast)

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=5,     # number of connection pools
    pool_maxsize=10,        # max connections per pool
    max_retries=3,          # auto-retry on connection errors
)
session.mount("https://", adapter)

# Use session instead of requests directly
response = session.post(f"{BASE}/videos/text2video", headers=get_headers(), json=body)
```

## Prompt Optimization

Prompts that generate faster:

| Technique | Why It Helps |
|-----------|-------------|
| Clear single subject | Less complexity to resolve |
| Specify camera angle | Reduces ambiguity |
| Avoid conflicting styles | "realistic anime" confuses the model |
| Keep under 200 words | Shorter prompts process faster |
| Use negative prompts | Removes processing of unwanted elements |

```python
# Slow prompt (vague, conflicting)
slow = "A scene with many things happening, realistic but also artistic"

# Fast prompt (specific, clear)
fast = "A single red fox walking through snow, side view, natural lighting, 4K"
```

## Caching Strategy

```python
import hashlib

class PromptCache:
    """Cache results to avoid regenerating identical videos."""

    def __init__(self):
        self._cache = {}

    def _key(self, prompt: str, model: str, duration: int, mode: str) -> str:
        raw = f"{prompt}|{model}|{duration}|{mode}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, prompt, model, duration, mode):
        key = self._key(prompt, model, duration, mode)
        return self._cache.get(key)

    def set(self, prompt, model, duration, mode, video_url):
        key = self._key(prompt, model, duration, mode)
        self._cache[key] = {
            "url": video_url,
            "cached_at": time.time(),
        }

cache = PromptCache()

def generate_with_cache(prompt, model="kling-v2-master", duration=5, mode="standard"):
    cached = cache.get(prompt, model, duration, mode)
    if cached:
        print(f"Cache hit: {cached['url']}")
        return cached["url"]

    # Generate
    result = client.text_to_video(prompt, model=model, duration=duration, mode=mode)
    url = result["videos"][0]["url"]
    cache.set(prompt, model, duration, mode, url)
    return url
```

## Optimization Checklist

- [ ] Use `kling-v2-5-turbo` for iteration, `v2-6` for final
- [ ] Use `standard` mode until final render
- [ ] Connection pooling via `requests.Session()`
- [ ] Cache identical prompt+param combinations
- [ ] Prompt: specific, single subject, < 200 words
- [ ] Batch submissions paced at 2-3s intervals
- [ ] Use `callback_url` instead of polling
- [ ] Download videos async (don't block on CDN download)

## Resources

- [Model Catalog](https://app.klingai.com/global/dev/document-api/apiReference/model/skillsMap)
- [Developer Portal](https://app.klingai.com/global/dev)
