---
name: salesloft-sdk-patterns
description: |
  Apply production-ready SalesLoft API patterns for TypeScript and Python.
  Use when building SalesLoft integrations, implementing pagination,
  or wrapping the REST API v2 with typed clients.
  Trigger: "salesloft SDK patterns", "salesloft best practices", "salesloft client wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, sales, outreach, salesloft]
compatible-with: claude-code
---

# SalesLoft SDK Patterns

## Overview

Production-ready patterns for the SalesLoft REST API v2. There is no official TypeScript/Python SDK -- build a typed wrapper around `https://api.salesloft.com/v2/` with automatic pagination, retry, and error normalization.

## Prerequisites

- Completed `salesloft-install-auth` setup
- `axios` or `node-fetch` installed
- Familiarity with async/await and generics

## Instructions

### Step 1: Typed API Client Singleton

```typescript
// src/salesloft/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

interface SalesloftPaging {
  per_page: number;
  current_page: number;
  total_pages: number;
  total_count: number;
}

interface SalesloftListResponse<T> {
  data: T[];
  metadata: { paging: SalesloftPaging };
}

interface SalesloftSingleResponse<T> {
  data: T;
}

let instance: AxiosInstance | null = null;

export function getSalesloftClient(): AxiosInstance {
  if (!instance) {
    instance = axios.create({
      baseURL: process.env.SALESLOFT_BASE_URL || 'https://api.salesloft.com/v2',
      headers: { Authorization: `Bearer ${process.env.SALESLOFT_API_KEY}` },
      timeout: 30_000,
    });
    // Add response interceptor for rate-limit headers
    instance.interceptors.response.use(undefined, handleRateLimitError);
  }
  return instance;
}
```

### Step 2: Automatic Pagination Iterator

```typescript
// SalesLoft paginates with page/per_page params, max 100 per page
async function* paginate<T>(
  endpoint: string,
  params: Record<string, any> = {},
): AsyncGenerator<T> {
  const client = getSalesloftClient();
  let page = 1;
  let totalPages = 1;

  do {
    const { data: response } = await client.get<SalesloftListResponse<T>>(
      endpoint, { params: { ...params, per_page: 100, page } }
    );
    for (const item of response.data) yield item;
    totalPages = response.metadata.paging.total_pages;
    page++;
  } while (page <= totalPages);
}

// Usage: iterate all people
for await (const person of paginate<Person>('/people.json')) {
  console.log(person.display_name);
}
```

### Step 3: Error Handling with Rate-Limit Awareness

```typescript
// SalesLoft uses cost-based rate limiting: 600 cost/min
// High-page requests (page > 100) cost 3-30 points instead of 1
async function handleRateLimitError(error: AxiosError) {
  if (error.response?.status === 429) {
    const retryAfter = parseInt(
      error.response.headers['retry-after'] || '60', 10
    );
    console.warn(`Rate limited. Waiting ${retryAfter}s...`);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return getSalesloftClient().request(error.config!);
  }
  throw error;
}

class SalesloftApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public retryable: boolean,
  ) {
    super(message);
    this.name = 'SalesloftApiError';
  }
}
```

### Step 4: Python Equivalent

```python
import os, time, requests
from typing import Iterator, Any

class SalesloftClient:
    BASE_URL = "https://api.salesloft.com/v2"

    def __init__(self, api_key: str | None = None):
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {api_key or os.environ['SALESLOFT_API_KEY']}"

    def get(self, endpoint: str, **params) -> dict:
        resp = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params)
        if resp.status_code == 429:
            time.sleep(int(resp.headers.get("Retry-After", 60)))
            return self.get(endpoint, **params)
        resp.raise_for_status()
        return resp.json()

    def paginate(self, endpoint: str, **params) -> Iterator[dict]:
        page = 1
        while True:
            result = self.get(endpoint, page=page, per_page=100, **params)
            yield from result["data"]
            if page >= result["metadata"]["paging"]["total_pages"]:
                break
            page += 1
```

## Output

- Type-safe client singleton with rate-limit retry
- Automatic pagination that handles all pages
- Error normalization for consistent handling
- Python and TypeScript implementations

## Error Handling

| Status | Meaning | Retryable | Cost |
|--------|---------|-----------|------|
| `401` | Invalid/expired token | No (refresh token) | 0 |
| `404` | Resource not found | No | 1 |
| `422` | Validation error | No (fix payload) | 1 |
| `429` | Rate limited | Yes (wait `Retry-After`) | 0 |
| `5xx` | Server error | Yes (backoff) | 1 |

## Resources

- [SalesLoft API Basics](https://developers.salesloft.com/docs/platform/api-basics/)
- [Rate Limits](https://developers.salesloft.com/docs/platform/api-basics/rate-limits/)
- [People Endpoint](https://developers.salesloft.com/docs/api/people-index/)

## Next Steps

Apply patterns in `salesloft-core-workflow-a` for real-world usage.
