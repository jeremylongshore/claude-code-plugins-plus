---
name: serpapi-common-errors
description: |
  Diagnose and fix SerpApi errors: invalid keys, exhausted credits, blocked searches.
  Use when SerpApi returns errors, empty results, or unexpected status codes.
  Trigger: "serpapi error", "fix serpapi", "serpapi not working", "serpapi empty results".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Common Errors

## Overview

Quick reference for SerpApi errors. Check `search_metadata.status` first -- it will be `Success` or `Error`. Error details are in `search_metadata.error` or `error` at the top level.

## Error Reference

### Invalid API Key
```json
{ "error": "Invalid API key. Your API key should be here: https://serpapi.com/manage-api-key" }
```
**Fix:** Verify key at serpapi.com/manage-api-key. Check env var is loaded.

### Account Disabled / Searches Exhausted
```json
{ "error": "Your searches for the month have run out. You can upgrade your plan at https://serpapi.com/pricing" }
```
**Fix:** Check usage: `curl "https://serpapi.com/account.json?api_key=$SERPAPI_API_KEY"`. Upgrade plan or wait for monthly reset.

### Missing Required Parameter
```json
{ "error": "Missing parameter: q. Please provide a search query." }
```
**Fix:** Each engine has different query params. Google/Bing use `q`, YouTube uses `search_query`.

### Google CAPTCHA / Blocked
```json
{ "search_metadata": { "status": "Error" }, "error": "Google hasn't returned any results for this query." }
```
**Fix:** SerpApi handles CAPTCHAs automatically, but unusual queries or very high volume may trigger blocks. Try different `location` or wait.

### Empty Organic Results (Not an Error)

```python
result = client.search(engine="google", q="xyzzy123nonexistent")
if not result.get("organic_results"):
    # Not an error -- query just has no results
    # Check for answer_box, knowledge_graph, etc.
    print("No organic results, checking other components...")
    print(f"Answer box: {result.get('answer_box')}")
    print(f"Related searches: {result.get('related_searches')}")
```

## Quick Diagnostic

```bash
# 1. Check API key and account status
curl -s "https://serpapi.com/account.json?api_key=$SERPAPI_API_KEY" | jq '{
  plan: .plan_name, used: .this_month_usage, remaining: .plan_searches_left
}'

# 2. Test basic search
curl -s "https://serpapi.com/search.json?q=test&engine=google&api_key=$SERPAPI_API_KEY" \
  | jq '.search_metadata.status'

# 3. Check search archive (last 10 searches)
curl -s "https://serpapi.com/searches.json?api_key=$SERPAPI_API_KEY" \
  | jq '.[0:3] | .[] | {id: .id, status: .status, query: .search_parameters.q}'
```

## Error Handling

| Error | Retryable | Action |
|-------|-----------|--------|
| Invalid API key | No | Fix key |
| Searches exhausted | No | Upgrade plan |
| CAPTCHA/blocked | Sometimes | Change location, wait |
| Timeout | Yes | Retry with backoff |
| Missing parameter | No | Fix request params |
| 500 server error | Yes | Retry 2-3 times |

## Resources

- [SerpApi Status](https://serpapi.com/status)
- [Account API](https://serpapi.com/account-api)
- [Playground](https://serpapi.com/playground) (test queries interactively)

## Next Steps

For comprehensive debugging, see `serpapi-debug-bundle`.
