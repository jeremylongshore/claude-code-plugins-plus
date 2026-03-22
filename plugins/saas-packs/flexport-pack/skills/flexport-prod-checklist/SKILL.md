---
name: flexport-prod-checklist
description: |
  Execute Flexport production deployment checklist for logistics integrations.
  Use when deploying shipment tracking, booking automation, or supply chain
  integrations to production with proper monitoring and rollback.
  Trigger: "flexport production", "deploy flexport", "flexport go-live checklist".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Production Checklist

## Overview

Pre-deployment and go-live checklist for Flexport logistics integrations covering API configuration, webhook setup, monitoring, and rollback procedures.

## Pre-Deployment

### Authentication & Secrets
- [ ] Production API key stored in secret manager (not env files)
- [ ] Webhook secret configured and verified
- [ ] Key rotation procedure documented
- [ ] No keys in git history (`git log -p | grep -i flexport_api`)

### API Integration
- [ ] All endpoints tested against production API
- [ ] Pagination implemented for list endpoints (`/shipments`, `/products`)
- [ ] Rate limit handling with exponential backoff
- [ ] Retry logic for transient 5xx errors
- [ ] Idempotency keys on POST/PATCH operations
- [ ] `Flexport-Version: 2` header on all requests

### Webhooks
- [ ] HTTPS endpoint with valid TLS certificate
- [ ] `X-Hub-Signature` verification implemented
- [ ] Webhook endpoint responds within 5 seconds
- [ ] Dead letter queue for failed webhook processing
- [ ] Idempotent webhook handlers (replay-safe)

### Data Integrity
- [ ] HS codes validated against customs requirements
- [ ] UN/LOCODE port codes verified
- [ ] Commercial invoice totals cross-checked
- [ ] Product catalog synced with Flexport Product Library

## Monitoring & Alerting

```typescript
// Health check endpoint
app.get('/health', async (req, res) => {
  const start = Date.now();
  try {
    const r = await fetch('https://api.flexport.com/shipments?per=1', {
      headers: {
        'Authorization': `Bearer ${process.env.FLEXPORT_API_KEY}`,
        'Flexport-Version': '2',
      },
    });
    res.json({
      status: r.ok ? 'healthy' : 'degraded',
      flexport: { connected: r.ok, latencyMs: Date.now() - start },
    });
  } catch {
    res.status(503).json({ status: 'unhealthy', flexport: { connected: false } });
  }
});
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| API error rate | > 5% | > 20% |
| p99 latency | > 3000ms | > 10000ms |
| 429 rate limits | > 5/hour | > 20/hour |
| Webhook failures | > 2/hour | > 10/hour |
| Auth failures (401/403) | Any | Any |

## Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/flexport-integration
# Or for non-k8s: revert to last known good image/version
```

## Resources

- [Flexport Status](https://status.flexport.com)
- [Flexport API Reference](https://apidocs.flexport.com/)

## Next Steps

For version upgrades, see `flexport-upgrade-migration`.
