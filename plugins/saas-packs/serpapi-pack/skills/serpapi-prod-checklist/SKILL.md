---
name: serpapi-prod-checklist
description: |
  Production readiness checklist for SerpApi integrations.
  Use when deploying search features, validating credit budgets,
  or preparing SerpApi-powered apps for launch.
  Trigger: "serpapi production", "deploy serpapi", "serpapi go-live".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi Production Checklist

## Checklist

### API Key & Authentication
- [ ] API key stored in secret manager (not env files)
- [ ] Backend proxy for all client-side search requests
- [ ] Key not exposed in frontend bundles or logs
- [ ] Usage monitoring configured

### Credit Budget
- [ ] Monthly search volume estimated
- [ ] Plan tier matches expected volume
- [ ] Response caching implemented (LRU or Redis)
- [ ] Archive API used for result retrieval (free)
- [ ] Budget alerts set (e.g., 80% threshold)

### Error Handling
- [ ] Check `search_metadata.status` before using results
- [ ] Handle `error` field in responses
- [ ] Retry on 500/timeout (max 2 retries)
- [ ] Graceful fallback when credits exhausted
- [ ] Log search IDs for debugging (`search_metadata.id`)

### Performance
- [ ] Response caching with appropriate TTL
- [ ] Rate limiting per plan tier (see `serpapi-rate-limits`)
- [ ] Async search for non-critical queries
- [ ] Proxy endpoint rate-limited to prevent abuse

### Health Check

```typescript
app.get('/health', async (req, res) => {
  try {
    const account = await fetch(
      `https://serpapi.com/account.json?api_key=${process.env.SERPAPI_API_KEY}`
    ).then(r => r.json());

    res.json({
      status: account.plan_searches_left > 0 ? 'healthy' : 'degraded',
      serpapi: {
        plan: account.plan_name,
        remaining: account.plan_searches_left,
        used: account.this_month_usage,
      },
    });
  } catch {
    res.status(503).json({ status: 'unhealthy', serpapi: { error: 'unreachable' } });
  }
});
```

## Error Handling

| Alert | Condition | Severity |
|-------|-----------|----------|
| Credits Low | remaining < 10% | P2 |
| Credits Exhausted | remaining = 0 | P1 |
| API Unreachable | Account check fails | P1 |
| High Error Rate | > 5% searches fail | P2 |

## Resources

- [SerpApi Status](https://serpapi.com/status)
- [Account API](https://serpapi.com/account-api)
- [SerpApi Pricing](https://serpapi.com/pricing)

## Next Steps

For version upgrades, see `serpapi-upgrade-migration`.
