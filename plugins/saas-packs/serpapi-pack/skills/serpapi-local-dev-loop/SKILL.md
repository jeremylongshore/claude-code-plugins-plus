---
name: serpapi-local-dev-loop
description: |
  Configure SerpApi local development with cached responses and test fixtures.
  Use when building search integrations, avoiding API calls during development,
  or setting up reproducible test data from SerpApi.
  Trigger: "serpapi dev setup", "serpapi local", "test serpapi locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Local Dev Loop

## Overview

Set up local development for SerpApi with response caching, fixture recording, and offline testing. SerpApi charges per search, so caching results locally is critical for cost-effective development.

## Instructions

### Step 1: Record Real Responses as Fixtures

```python
import serpapi, json, os, hashlib

def record_fixture(params: dict, fixtures_dir="tests/fixtures"):
    """Run a real search and save the response as a fixture file."""
    os.makedirs(fixtures_dir, exist_ok=True)
    client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])
    result = client.search(**params)

    # Deterministic filename from params
    key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]
    path = os.path.join(fixtures_dir, f"{params['engine']}_{key}.json")

    with open(path, "w") as f:
        json.dump(dict(result), f, indent=2)
    print(f"Recorded: {path}")

# Record fixtures for common queries
record_fixture({"engine": "google", "q": "python tutorial", "num": 5})
record_fixture({"engine": "youtube", "search_query": "react hooks"})
record_fixture({"engine": "bing", "q": "machine learning"})
```

### Step 2: Mock Client for Testing

```python
import json, os

class MockSerpApiClient:
    def __init__(self, fixtures_dir="tests/fixtures"):
        self.fixtures_dir = fixtures_dir

    def search(self, **params):
        key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]
        path = os.path.join(self.fixtures_dir, f"{params['engine']}_{key}.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        raise FileNotFoundError(f"No fixture for {params}. Run record_fixture() first.")
```

### Step 3: Vitest Mocking (Node.js)

```typescript
// tests/serpapi.test.ts
import { describe, it, expect, vi } from 'vitest';
import { readFileSync } from 'fs';

vi.mock('serpapi', () => ({
  getJson: vi.fn(async (params) => {
    const fixture = JSON.parse(
      readFileSync(`tests/fixtures/google_sample.json`, 'utf-8')
    );
    return fixture;
  }),
}));

describe('Search Service', () => {
  it('parses organic results', async () => {
    const { getJson } = await import('serpapi');
    const result = await getJson({ engine: 'google', q: 'test' });
    expect(result.organic_results).toBeDefined();
    expect(result.organic_results[0]).toHaveProperty('title');
    expect(result.organic_results[0]).toHaveProperty('link');
  });
});
```

### Step 4: Environment Separation

```bash
# .env.development (uses real API, low num for cost)
SERPAPI_API_KEY=real-key-here
SERPAPI_DEFAULT_NUM=3

# .env.test (uses fixtures, no API calls)
SERPAPI_API_KEY=not-needed
SERPAPI_USE_FIXTURES=true
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError` fixture | Missing fixture | Run `record_fixture()` with real API key |
| Stale fixtures | Search results changed | Re-record periodically |
| `Invalid API key` in dev | Env not loaded | Check `.env.development` loading |

## Resources

- [SerpApi Playground](https://serpapi.com/playground)
- [Vitest Mocking](https://vitest.dev/guide/mocking.html)

## Next Steps

Proceed to `serpapi-sdk-patterns` for production patterns.
