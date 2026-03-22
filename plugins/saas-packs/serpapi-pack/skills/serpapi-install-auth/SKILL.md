---
name: serpapi-install-auth
description: |
  Install SerpApi client and configure API key authentication.
  Use when setting up SerpApi for search result scraping, configuring API keys,
  or initializing the serpapi Python/Node package.
  Trigger: "install serpapi", "setup serpapi", "serpapi auth", "serpapi API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Install & Auth

## Overview

Install the SerpApi client library and configure API key authentication. SerpApi provides structured JSON results from Google, Bing, YouTube, and 15+ search engines. Auth is API-key-based via the `api_key` parameter or `SERPAPI_API_KEY` env var.

## Prerequisites

- SerpApi account at [serpapi.com](https://serpapi.com)
- API key from [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Install Client

```bash
# Python (official)
pip install serpapi

# Node.js (official)
npm install serpapi

# Alternative Python package (legacy but widely used)
pip install google-search-results
```

### Step 2: Configure API Key

```bash
# .env
SERPAPI_API_KEY=your-api-key-here
```

### Step 3: Verify Connection (Python)

```python
import serpapi, os

client = serpapi.Client(api_key=os.environ["SERPAPI_API_KEY"])
result = client.search(engine="google", q="test", num=1)
print(f"Connected! Search ID: {result['search_metadata']['id']}")
```

### Step 4: Verify Connection (Node.js)

```typescript
import { getJson } from 'serpapi';

const result = await getJson({
  engine: 'google', q: 'test', num: 1,
  api_key: process.env.SERPAPI_API_KEY,
});
console.log(`Connected! Search ID: ${result.search_metadata.id}`);
```

### Step 5: Check Account

```bash
curl "https://serpapi.com/account.json?api_key=$SERPAPI_API_KEY" | jq '{
  plan: .plan_name, used: .this_month_usage, remaining: .plan_searches_left
}'
```

## Output

```
Connected! Search ID: 64a1b2c3d4e5f6
{ plan: "Developer", used: 42, remaining: 4958 }
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid API key` | Wrong or missing key | Check serpapi.com/manage-api-key |
| `Your account is disabled` | Exceeded limits | Upgrade or wait for monthly reset |
| `ModuleNotFoundError` | Not installed | `pip install serpapi` |

## Resources

- [SerpApi Dashboard](https://serpapi.com/dashboard)
- [Python Integration](https://serpapi.com/integrations/python)
- [Account API](https://serpapi.com/account-api)

## Next Steps

Proceed to `serpapi-hello-world` for your first search.
