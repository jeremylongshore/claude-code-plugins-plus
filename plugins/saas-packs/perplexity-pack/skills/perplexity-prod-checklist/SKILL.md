---
name: perplexity-prod-checklist
description: |
  Execute Perplexity production deployment checklist for Sonar API integrations.
  Use when deploying Perplexity integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "perplexity production", "deploy perplexity",
  "perplexity go-live", "perplexity launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, deployment]

---
# Perplexity Production Checklist

## Overview
Complete checklist for deploying Perplexity Sonar API integrations to production. Perplexity-specific concerns: every API call performs a live web search (variable latency), citations link to third-party sites (must validate), and costs scale per-request plus per-token.

## Prerequisites
- Staging environment tested
- Production API key generated (separate from dev/staging)
- Monitoring configured
- Cost budget defined

## Production Readiness Checklist

### API Configuration
- [ ] Production `PERPLEXITY_API_KEY` in secret manager (not env file)
- [ ] Key starts with `pplx-` and has credits loaded
- [ ] Separate API keys for dev/staging/prod
- [ ] Base URL is `https://api.perplexity.ai` (not localhost/proxy)
- [ ] Model selection configured: `sonar` for fast, `sonar-pro` for deep

### Code Quality
- [ ] All search calls wrapped in retry with exponential backoff
- [ ] Rate limiting implemented (50 RPM default)
- [ ] Query sanitization strips PII before sending to Perplexity
- [ ] Citations parsed from response (not extracted from text)
- [ ] `max_tokens` set on all requests (prevents runaway costs)
- [ ] Timeouts configured: 15s for sonar, 30s for sonar-pro
- [ ] Error handling covers 401, 402, 429, 500+ status codes
- [ ] No hardcoded API keys in source code

### Performance
- [ ] Result caching implemented for repeated queries
- [ ] Cache TTL appropriate: 30min for news, 4hrs for research, 24hrs for facts
- [ ] Streaming enabled for user-facing search (reduces perceived latency)
- [ ] Request queue prevents burst overload
- [ ] `search_domain_filter` used where appropriate (reduces search time)

### Monitoring
- [ ] Latency tracked per model (sonar ~2s, sonar-pro ~5s, deep-research ~30s)
- [ ] Error rate monitored (alert on >5% failure rate)
- [ ] Token usage tracked for cost projection
- [ ] Citation count per response logged (quality signal)
- [ ] 429 rate limit errors tracked with alert

### Cost Controls
- [ ] Monthly budget cap set on API key
- [ ] Model routing: simple queries to `sonar`, complex to `sonar-pro`
- [ ] `max_tokens` capped per endpoint
- [ ] Cache hit rate monitored (target >30%)
- [ ] Cost per query tracked by model

### Graceful Degradation
```typescript
async function searchWithFallback(query: string) {
  try {
    // Primary: sonar-pro for deep answers
    return await perplexity.chat.completions.create({
      model: "sonar-pro",
      messages: [{ role: "user", content: query }],
      max_tokens: 2048,
    });
  } catch (err: any) {
    if (err.status === 429 || err.status >= 500) {
      // Fallback: sonar for faster, cheaper response
      return await perplexity.chat.completions.create({
        model: "sonar",
        messages: [{ role: "user", content: query }],
        max_tokens: 512,
      });
    }
    throw err;
  }
}
```

### Health Check Endpoint
```typescript
app.get("/health/perplexity", async (req, res) => {
  const start = Date.now();
  try {
    const response = await perplexity.chat.completions.create({
      model: "sonar",
      messages: [{ role: "user", content: "ping" }],
      max_tokens: 5,
    });
    res.json({
      status: "healthy",
      latencyMs: Date.now() - start,
      model: response.model,
    });
  } catch (err: any) {
    res.status(503).json({
      status: "unhealthy",
      error: err.status || err.message,
      latencyMs: Date.now() - start,
    });
  }
});
```

## Alerting Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| API Unreachable | Health check fails 3x | P1 |
| High Error Rate | 429/5xx > 5% over 5min | P2 |
| High Latency | p95 > 15s for sonar | P2 |
| Budget Exceeded | Monthly cost > 80% cap | P2 |
| Auth Failure | Any 401/402 error | P1 |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Variable latency | Web search per request | Set appropriate timeouts per model |
| Broken citations | Source pages changed | Validate citation URLs before displaying |
| Cost overrun | No model routing | Route simple queries to sonar |
| Rate limit spikes | Burst traffic | Queue requests with p-queue |

## Output
- Production-ready Perplexity integration with all checks passing
- Health check endpoint for monitoring
- Graceful degradation from sonar-pro to sonar
- Alerting rules configured

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Model Pricing](https://docs.perplexity.ai/docs/getting-started/pricing)

## Next Steps
For version upgrades, see `perplexity-upgrade-migration`.
