---
name: serpapi-security-basics
description: |
  Secure SerpApi API keys and prevent credit abuse.
  Use when storing API keys, implementing backend proxies,
  or auditing SerpApi access patterns.
  Trigger: "serpapi security", "serpapi API key security", "secure serpapi".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Security Basics

## Overview

SerpApi uses a single API key for authentication. The key grants full account access -- there are no scoped keys or OAuth. Protect it like a credit card: never expose in frontend code, always proxy through your backend.

## Instructions

### Step 1: Never Expose API Key in Frontend

```typescript
// BAD: API key in browser-side code
const result = await fetch(`https://serpapi.com/search.json?q=${query}&api_key=YOUR_KEY`);

// GOOD: Proxy through your backend
// Frontend
const result = await fetch(`/api/search?q=${encodeURIComponent(query)}`);

// Backend (api/search.ts)
export async function GET(req: Request) {
  const url = new URL(req.url);
  const q = url.searchParams.get('q');
  const result = await getJson({
    engine: 'google', q,
    api_key: process.env.SERPAPI_API_KEY, // Server-side only
  });
  return Response.json(result.organic_results);
}
```

### Step 2: Secure Storage

```bash
# .gitignore
.env
.env.local

# Use platform secret managers in production
gh secret set SERPAPI_API_KEY       # GitHub Actions
vercel env add SERPAPI_API_KEY      # Vercel
fly secrets set SERPAPI_API_KEY=x   # Fly.io
```

### Step 3: Rate Limit Your Proxy

```typescript
// Prevent abuse of your search proxy endpoint
import rateLimit from 'express-rate-limit';

const searchLimiter = rateLimit({
  windowMs: 60_000,    // 1 minute
  max: 10,             // 10 searches per minute per IP
  message: 'Too many searches, try again later',
});

app.get('/api/search', searchLimiter, searchHandler);
```

### Step 4: Monitor Usage

```bash
# Set up daily usage check
curl -s "https://serpapi.com/account.json?api_key=$SERPAPI_API_KEY" \
  | jq '{used: .this_month_usage, remaining: .plan_searches_left}'

# Alert if usage is unexpectedly high
```

## Security Checklist

- [ ] API key in environment variables only
- [ ] `.env` in `.gitignore`
- [ ] Backend proxy for all search requests
- [ ] Rate limiting on proxy endpoints
- [ ] Usage monitoring and alerts
- [ ] Separate keys for dev/prod (if available)

## Resources

- [SerpApi Dashboard](https://serpapi.com/dashboard)
- [Manage API Key](https://serpapi.com/manage-api-key)

## Next Steps

For production deployment, see `serpapi-prod-checklist`.
