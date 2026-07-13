# Linear Performance Tuning -- Implementation Reference

## Overview

Optimize Linear API usage through GraphQL field selection, batching, caching,
and pagination strategies to minimize latency and API call counts.

## Prerequisites

- Linear API key
- Python 3.9+ or Node.js 18+
- Redis or in-memory cache (optional but recommended)

## GraphQL Field Selection

```python
# Bad: over-fetches unnecessary nested data
BLOATED_QUERY = """
query {
  issues {
    nodes {
      id title description body
      history { nodes { updatedAt changes } }
      comments { nodes { body user { name email } } }
      subscribers { nodes { name } }
    }
  }
}
"""

# Good: only request fields you actually use
LEAN_QUERY = """
query IssueList($teamId: String!, $cursor: String) {
  issues(
    filter: { team: { id: { eq: $teamId } } }
    first: 50
    after: $cursor
    orderBy: updatedAt
  ) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      identifier
      title
      state { name type }
      assignee { name }
      priority
      updatedAt
    }
  }
}
"""
```

## Python TTL Cache

```python
import os
import json
import time
import urllib.request

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]


def graphql(query: str, variables: dict = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": LINEAR_API_KEY,
    }
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["data"]


class LinearCache:
    """Simple TTL cache for Linear API responses."""

    def __init__(self, ttl_seconds: int = 60):
        self._store = {}
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def get(self, key: str):
        if key in self._store:
            ts, value = self._store[key]
            if time.time() - ts < self.ttl:
                self.hits += 1
                return value
            del self._store[key]
        self.misses += 1
        return None

    def set(self, key: str, value) -> None:
        self._store[key] = (time.time(), value)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def stats(self) -> dict:
        total = self.hits + self.misses
        rate = self.hits / total if total else 0
        return {"hits": self.hits, "misses": self.misses, "hit_rate": f"{rate:.0%}"}


_cache = LinearCache(ttl_seconds=120)


def get_team_issues(team_id: str, force_refresh: bool = False) -> list:
    cache_key = f"team_issues:{team_id}"
    if not force_refresh:
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

    issues = []
    cursor = None
    while True:
        data = graphql(LEAN_QUERY, {"teamId": team_id, "cursor": cursor})
        page = data["issues"]
        issues.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    _cache.set(cache_key, issues)
    return issues
```

## Batch User Fetching via Aliases

```python
def batch_fetch_users(user_ids: list) -> dict:
    """Fetch multiple users in a single GraphQL query using field aliases."""
    if not user_ids:
        return {}

    aliases = "\n".join(
        f'u{i}: user(id: "{uid}") {{ id name email }}'
        for i, uid in enumerate(user_ids)
    )
    query = f"query BatchUsers {{ {aliases} }}"
    data = graphql(query)
    return {
        user_ids[int(k[1:])]: v
        for k, v in data.items()
    }
```

## Generic Cursor Paginator

```python
def paginate_all(query: str, variables: dict, data_path: str) -> list:
    """Paginate through all results for any Linear list query.

    data_path: dot-separated key path, e.g. 'issues' or 'team.issues'
    """
    results = []
    cursor = None

    while True:
        data = graphql(query, {**variables, "cursor": cursor})

        node = data
        for key in data_path.split("."):
            node = node[key]

        results.extend(node["nodes"])

        if not node["pageInfo"]["hasNextPage"]:
            break
        cursor = node["pageInfo"]["endCursor"]

    return results
```

## Parallel Team Fetching

```python
import asyncio
import concurrent.futures


def fetch_issues_for_team(team_id: str) -> tuple:
    return team_id, get_team_issues(team_id)


def fetch_all_teams_parallel(team_ids: list) -> dict:
    """Fetch issues for multiple teams concurrently."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch_issues_for_team, tid): tid for tid in team_ids}
        results = {}
        for future in concurrent.futures.as_completed(futures):
            tid, issues = future.result()
            results[tid] = issues
    return results
```

## TypeScript DataLoader Pattern

```typescript
import DataLoader from 'dataloader';
import { LinearClient } from '@linear/sdk';

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY });

const issueLoader = new DataLoader<string, any>(
  async (ids: readonly string[]) => {
    const aliases = ids
      .map((id, i) => `i${i}: issue(id: "${id}") { id identifier title state { name } }`)
      .join('\n');
    const data = await client.rawRequest(`query { ${aliases} }`);
    return ids.map((_id, i) => (data as any)[`i${i}`]);
  },
  { maxBatchSize: 50, cache: true }
);

// Usage -- automatically batches concurrent loads
const [issue1, issue2] = await Promise.all([
  issueLoader.load('ISSUE_ID_1'),
  issueLoader.load('ISSUE_ID_2'),
]);
```

## Rate Limit Monitoring

```python
def check_rate_limit_headers(resp_headers: dict) -> dict:
    """Parse Linear rate limit headers from a response."""
    return {
        "limit": int(resp_headers.get("X-RateLimit-Limit", 1500)),
        "remaining": int(resp_headers.get("X-RateLimit-Remaining", 1500)),
        "reset_at": resp_headers.get("X-RateLimit-Reset", ""),
    }
```

## Resources

- [Linear GraphQL API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
- [Linear Pagination](https://developers.linear.app/docs/graphql/working-with-the-graphql-api#pagination)
- [DataLoader](https://github.com/graphql/dataloader)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
