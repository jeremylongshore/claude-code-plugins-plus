---
name: serpapi-debug-bundle
description: |
  Collect SerpApi debug diagnostics: account status, recent searches, and error logs.
  Use when troubleshooting SerpApi issues, checking credit usage,
  or preparing support tickets.
  Trigger: "serpapi debug", "serpapi diagnostic", "serpapi support".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Debug Bundle

## Overview

Collect diagnostic data for SerpApi issues using the Account API and Searches Archive API. SerpApi stores all search results for retrieval without additional credit charges.

## Instructions

### Step 1: Collect Diagnostics

```bash
#!/bin/bash
BUNDLE="serpapi-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
KEY="${SERPAPI_API_KEY:?Set SERPAPI_API_KEY}"

# Account status
curl -s "https://serpapi.com/account.json?api_key=$KEY" \
  | jq '{plan: .plan_name, used: .this_month_usage, remaining: .plan_searches_left, rate_limit: .searches_per_month}' \
  > "$BUNDLE/account.json"

# Recent searches (last 10)
curl -s "https://serpapi.com/searches.json?api_key=$KEY" \
  | jq '.[0:10] | .[] | {id: .id, status: .status, engine: .search_parameters.engine, query: .search_parameters.q, created: .created_at}' \
  > "$BUNDLE/recent-searches.json"

# Test search
curl -s "https://serpapi.com/search.json?q=test&engine=google&num=1&api_key=$KEY" \
  | jq '.search_metadata' > "$BUNDLE/test-search.json"

# Environment
echo "Node: $(node --version 2>/dev/null || echo N/A)" > "$BUNDLE/env.txt"
echo "Python: $(python3 --version 2>/dev/null || echo N/A)" >> "$BUNDLE/env.txt"
pip show serpapi 2>/dev/null >> "$BUNDLE/env.txt" || true
npm list serpapi 2>/dev/null >> "$BUNDLE/env.txt" || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

### Step 2: Retrieve Failed Search Details

```python
# Use the Searches Archive API to get details of any past search
import serpapi, os

client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])

# Get a specific search by ID (no credit charge)
result = client.search(engine="google", search_id="YOUR_SEARCH_ID")
print(f"Status: {result['search_metadata']['status']}")
if "error" in result:
    print(f"Error: {result['error']}")
```

## Error Handling

| Finding | Likely Issue | Action |
|---------|-------------|--------|
| `remaining: 0` | Credits exhausted | Upgrade plan or wait for monthly reset |
| Test search fails | API key issue | Re-check key at serpapi.com |
| Recent searches show errors | Bad parameters | Check engine-specific param requirements |

## Resources

- [Account API](https://serpapi.com/account-api)
- [Searches Archive](https://serpapi.com/search-archive-api)

## Next Steps

For rate limit issues, see `serpapi-rate-limits`.
