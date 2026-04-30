---
name: onenote-cost-tuning
description: 'Optimize costs and API usage for OneNote Graph API integrations with
  caching and batching strategies.

  Use when reducing API call volume, planning capacity, or evaluating OneNote integration
  costs.

  Trigger with "onenote costs", "onenote api usage", "onenote optimization", "graph
  api billing onenote".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote Cost Tuning

## Overview

OneNote Graph API calls have no per-request cost — they are included in every Microsoft 365 E3/E5/Business license. However, rate limits create an effective ceiling that functions like a cost constraint: 600 requests per user per 60 seconds and 10,000 requests per app per 10 minutes at the tenant level. Exceeding these limits returns 429 errors with Retry-After headers, degrading user experience the same way budget overruns degrade service. This skill covers the practical optimization strategies that keep you well under those ceilings: metadata caching, JSON batch requests, delta sync, payload minimization with `$select`/`$expand`, and content deduplication. A naive integration that polls every user's notebooks every minute burns through the tenant limit in under 10 minutes. An optimized one handles thousands of users within the same budget.

## Prerequisites

- Microsoft 365 license (E3/E5/Business) — OneNote API is included, no additional billing
- Azure AD app registration with delegated permissions
- Python: `pip install msgraph-sdk azure-identity` or Node: `npm install @microsoft/microsoft-graph-client @azure/identity`
- Understanding of HTTP caching headers (ETag, If-None-Match)

## Instructions

### Licensing Model and True Cost

| Component | Cost |
|-----------|------|
| OneNote API calls | Included in M365 license (no per-call charge) |
| Rate limit: per user | 600 requests / 60 seconds |
| Rate limit: per tenant | 10,000 requests / 10 minutes |
| Retry-After penalty | Blocked for N seconds (header value) |
| Graph metered billing | Optional; extends limits for high-volume apps |

**The real cost is operational:** every 429 response adds latency, retry logic consumes compute, and throttled users see failures. Optimization is about reliability, not billing.

### Strategy 1: Cache Metadata Aggressively

Notebook and section metadata changes rarely (names, IDs, hierarchy). Cache it locally and refresh on a schedule, not per-request:

```typescript
interface CachedMetadata {
  notebooks: any[];
  sections: Map<string, any[]>;  // notebookId -> sections
  fetchedAt: number;
  ttlMs: number;
}

class MetadataCache {
  private cache: CachedMetadata = {
    notebooks: [],
    sections: new Map(),
    fetchedAt: 0,
    ttlMs: 15 * 60 * 1000,  // 15 minutes — notebooks/sections rarely change
  };

  isStale(): boolean {
    return Date.now() - this.cache.fetchedAt > this.cache.ttlMs;
  }

  async getNotebooks(client: any): Promise<any[]> {
    if (!this.isStale() && this.cache.notebooks.length > 0) {
      return this.cache.notebooks;  // 0 API calls
    }
    const response = await client.api("/me/onenote/notebooks")
      .select("id,displayName,lastModifiedDateTime")
      .get();
    this.cache.notebooks = response.value;
    this.cache.fetchedAt = Date.now();
    return this.cache.notebooks;  // 1 API call
  }

  async getSections(client: any, notebookId: string): Promise<any[]> {
    if (!this.isStale() && this.cache.sections.has(notebookId)) {
      return this.cache.sections.get(notebookId)!;
    }
    const response = await client
      .api(`/me/onenote/notebooks/${notebookId}/sections`)
      .select("id,displayName")
      .get();
    this.cache.sections.set(notebookId, response.value);
    return response.value;
  }

  invalidate(): void {
    this.cache.fetchedAt = 0;
  }
}
```

**Savings:** A typical app listing notebooks 100 times/hour drops from 100 calls to 4 calls (one refresh per 15-minute TTL window).

### Strategy 2: JSON Batch Requests

The `$batch` endpoint combines up to 20 requests into a single HTTP call, reducing call count by up to 20x:

```python
import httpx

async def batch_get_sections(access_token: str, notebook_ids: list[str]) -> dict:
    """Fetch sections for multiple notebooks in a single HTTP call."""
    requests = []
    for i, nb_id in enumerate(notebook_ids[:20]):  # Max 20 per batch
        requests.append({
            "id": str(i),
            "method": "GET",
            "url": f"/me/onenote/notebooks/{nb_id}/sections?$select=id,displayName",
        })

    async with httpx.AsyncClient() as http:
        response = await http.post(
            "https://graph.microsoft.com/v1.0/$batch",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"requests": requests},
        )
        batch_result = response.json()

    # Map responses back to notebook IDs
    result = {}
    for resp in batch_result["responses"]:
        idx = int(resp["id"])
        nb_id = notebook_ids[idx]
        if resp["status"] == 200:
            result[nb_id] = resp["body"]["value"]
        else:
            result[nb_id] = []  # Handle individual failures gracefully
    return result
```

**Savings:** Fetching sections for 20 notebooks: 20 calls becomes 1 call. For 100 notebooks, 100 calls becomes 5 calls.

### Strategy 3: Delta Sync Instead of Full Sync

Delta queries return only changes since your last sync, replacing full-list operations that grow linearly with data size:

```typescript
class DeltaSyncer {
  private deltaLinks: Map<string, string> = new Map();

  async syncPages(client: any, sectionId: string): Promise<{
    added: any[];
    modified: any[];
    deleted: string[];
  }> {
    const deltaLink = this.deltaLinks.get(sectionId);
    const url = deltaLink || `/me/onenote/sections/${sectionId}/pages/delta`;

    const response = await client.api(url).get();
    const result = { added: [] as any[], modified: [] as any[], deleted: [] as string[] };

    for (const page of response.value || []) {
      if (page["@removed"]) {
        result.deleted.push(page.id);
      } else if (deltaLink) {
        result.modified.push(page);
      } else {
        result.added.push(page);
      }
    }

    // Store the delta link for next sync
    if (response["@odata.deltaLink"]) {
      this.deltaLinks.set(sectionId, response["@odata.deltaLink"]);
    }

    return result;
  }
}
```

**Savings:** A section with 500 pages that changes 3 pages/hour: full sync = 500+ items per response, delta sync = 3 items. Call count may be same (1), but payload size drops 99%.

### Strategy 4: Payload Minimization with $select and $expand

Every field you do not request is bandwidth you save and parsing you skip:

```bash
# BAD: Returns all fields including content URLs, permissions, links (2-5 KB per page)
GET /me/onenote/sections/{id}/pages

# GOOD: Returns only what you need (200-300 bytes per page)
GET /me/onenote/sections/{id}/pages?$select=id,title,createdDateTime,lastModifiedDateTime&$top=50&$orderby=lastModifiedDateTime desc
```

Use `$expand` to eliminate follow-up calls:

```bash
# Without $expand: 1 call for notebooks + N calls for sections = N+1 calls
GET /me/onenote/notebooks
GET /me/onenote/notebooks/{id1}/sections
GET /me/onenote/notebooks/{id2}/sections

# With $expand: 1 call total
GET /me/onenote/notebooks?$expand=sections($select=id,displayName)&$select=id,displayName
```

### Strategy 5: Content Deduplication

Hash page content before writing to avoid duplicate POST calls:

```python
import hashlib

def content_hash(html_body: str) -> str:
    """Generate a stable hash of page content for dedup."""
    return hashlib.sha256(html_body.encode("utf-8")).hexdigest()

class DeduplicatedWriter:
    def __init__(self):
        self.written_hashes: dict[str, str] = {}  # hash -> page_id

    async def write_page(self, client, section_id: str, title: str, html_body: str):
        h = content_hash(html_body)
        if h in self.written_hashes:
            return self.written_hashes[h]  # Skip duplicate write

        full_html = (
            f"<html><head><title>{title}</title></head>"
            f"<body>{html_body}</body></html>"
        )
        page = await client.me.onenote.sections.by_onenote_section_id(
            section_id
        ).pages.post(content=full_html.encode())
        self.written_hashes[h] = page.id
        return page.id
```

### Cost Modeling Template

Estimate your API call budget per user per day:

| Operation | Calls/occurrence | Frequency/user/day | Daily calls |
|-----------|:---:|:---:|:---:|
| List notebooks | 1 | 4 (cached 15min) | 4 |
| List sections | 1 (batched) | 4 | 4 |
| List pages (delta) | 1 | 24 (hourly) | 24 |
| Read page content | 1 | 10 | 10 |
| Create/update page | 1 | 5 | 5 |
| **Total per user** | | | **47** |
| **100 users / tenant** | | | **4,700** |
| **Tenant limit (10min)** | | | **10,000** |

At 100 users, you are using 47% of the 10-minute tenant budget — safe headroom. At 250+ users, consider Graph metered billing or reduce polling frequency.

### Monitoring Dashboard Metrics

Track these metrics to detect optimization drift:

```python
import time
from collections import defaultdict

class ApiMetrics:
    def __init__(self):
        self.calls_per_user: dict[str, int] = defaultdict(int)
        self.throttle_count = 0
        self.total_latency_ms = 0.0
        self.call_count = 0

    def record_call(self, user_id: str, latency_ms: float, status: int):
        self.calls_per_user[user_id] += 1
        self.total_latency_ms += latency_ms
        self.call_count += 1
        if status == 429:
            self.throttle_count += 1

    def report(self) -> dict:
        return {
            "total_calls": self.call_count,
            "avg_latency_ms": self.total_latency_ms / max(self.call_count, 1),
            "throttle_rate": self.throttle_count / max(self.call_count, 1),
            "top_users": sorted(
                self.calls_per_user.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }
```

**Alert thresholds:**
- Throttle rate > 1%: investigate hotspot user or batch consolidation
- Avg latency > 2000ms: Graph service degradation or oversized payloads
- Single user > 300 calls/hour: likely missing cache or polling too frequently

## Output

After applying this skill, your OneNote integration will have: metadata caching reducing repetitive calls by 95%, batch requests combining up to 20 calls into 1, delta sync for incremental page updates, minimized payloads via `$select`/`$expand`, content deduplication preventing duplicate writes, and a monitoring framework to detect optimization regression.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `429 Too Many Requests` | Exceeded 600/min (user) or 10K/10min (tenant) | Read `Retry-After` header; back off for that many seconds; check for missing cache |
| `507 Insufficient Storage` | Per-section page limit exceeded | Archive old pages or split across sections |
| Batch response with mixed status codes | Some requests in batch succeeded, others failed | Process each batch response individually; retry only failed items |
| Delta link expired | Too long between delta syncs | Fall back to full sync, then resume delta |
| `504 Gateway Timeout` on large `$expand` | Too many nested resources | Reduce `$top` count or remove `$expand` and make separate calls |

## Examples

**Quick audit of current API usage:**

```bash
# Check rate limit headers in any Graph response
curl -sI -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/me/onenote/notebooks" | \
  grep -i "ratelimit\|retry-after\|x-ms"
```

**Batch request via curl:**

```bash
curl -X POST "https://graph.microsoft.com/v1.0/\$batch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"id": "1", "method": "GET", "url": "/me/onenote/notebooks?$select=id,displayName"},
      {"id": "2", "method": "GET", "url": "/me/onenote/sections?$select=id,displayName&$top=50"}
    ]
  }'
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Get Content](https://learn.microsoft.com/en-us/graph/onenote-get-content)
- [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Graph API Reference](https://learn.microsoft.com/en-us/graph/api/overview)

## Next Steps

- Apply `onenote-rate-limits` for detailed Retry-After handling and queue-based throttling
- Use `onenote-performance-tuning` for response time optimization
- See `onenote-prod-checklist` for full production readiness review
