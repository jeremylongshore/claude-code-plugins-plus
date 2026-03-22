---
name: serpapi-webhooks-events
description: |
  Implement SerpApi async search callbacks and scheduled search monitoring.
  Use when setting up search monitoring, SERP tracking pipelines,
  or async search result retrieval.
  Trigger: "serpapi webhooks", "serpapi monitoring", "serpapi scheduled search", "serpapi async".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Webhooks & Events

## Overview

SerpApi does not have traditional webhooks, but supports async searches and the Searches Archive API. Build SERP monitoring by combining scheduled searches with change detection. Common use case: track keyword rankings over time.

## Instructions

### Step 1: Async Search with Polling

```python
import serpapi, os, time

client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

# Submit async search (returns immediately)
result = client.search(engine="google", q="your keyword", async_search=True)
search_id = result["search_metadata"]["id"]
print(f"Submitted: {search_id}")

# Poll for completion
while True:
    archived = client.search(engine="google", search_id=search_id)
    status = archived["search_metadata"]["status"]
    if status == "Success":
        break
    elif status == "Error":
        raise Exception(f"Search failed: {archived.get('error')}")
    time.sleep(2)

print(f"Results: {len(archived.get('organic_results', []))}")
```

### Step 2: SERP Monitoring Pipeline

```python
import json, hashlib
from datetime import datetime

class SerpMonitor:
    def __init__(self, client, db):
        self.client = client
        self.db = db

    def track_keyword(self, keyword: str, domain: str):
        """Track a domain's ranking position for a keyword."""
        result = self.client.search(engine="google", q=keyword, num=100)
        organic = result.get("organic_results", [])

        position = None
        for r in organic:
            if domain in r.get("link", ""):
                position = r["position"]
                break

        self.db.insert({
            "keyword": keyword,
            "domain": domain,
            "position": position,  # None if not in top 100
            "total_results": result.get("search_information", {}).get("total_results"),
            "checked_at": datetime.utcnow().isoformat(),
            "search_id": result["search_metadata"]["id"],
        })

        return position

    def detect_changes(self, keyword: str, domain: str):
        """Compare current vs previous ranking."""
        current = self.track_keyword(keyword, domain)
        previous = self.db.get_previous_position(keyword, domain)

        if previous and current:
            change = previous - current  # Positive = improved
            if abs(change) >= 3:
                self.notify(f"Ranking change for '{keyword}': {previous} -> {current} ({'+' if change > 0 else ''}{change})")
```

### Step 3: Scheduled Monitoring (Cron)

```typescript
// Run daily keyword tracking
import cron from 'node-cron';
import { getJson } from 'serpapi';

const keywords = ['react framework', 'next.js tutorial', 'typescript guide'];
const targetDomain = 'yoursite.com';

cron.schedule('0 8 * * *', async () => { // Daily at 8 AM
  for (const keyword of keywords) {
    const result = await getJson({
      engine: 'google', q: keyword, num: 100,
      api_key: process.env.SERPAPI_API_KEY,
    });

    const position = result.organic_results?.findIndex(
      (r: any) => r.link?.includes(targetDomain)
    );

    console.log(`${keyword}: Position ${position >= 0 ? position + 1 : 'Not found'}`);
    // Save to database, send alerts on changes
  }
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Async search never completes | Server issue | Timeout after 60s, retry |
| Position tracking uses many credits | 100 results per search | Run daily not hourly |
| Ranking fluctuates | Normal SERP volatility | Track 7-day moving average |

## Resources

- [Async Search](https://serpapi.com/search-api#api-parameters-serpapi-parameters-async)
- [Searches Archive](https://serpapi.com/search-archive-api)

## Next Steps

For performance optimization, see `serpapi-performance-tuning`.
