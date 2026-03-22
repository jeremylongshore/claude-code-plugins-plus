---
name: juicebox-prod-checklist
description: |
  Execute Juicebox production checklist.
  Trigger: "juicebox production", "deploy juicebox".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Production Checklist

## Checklist
- [ ] Production API key in secret manager
- [ ] Rate limiting per plan tier
- [ ] Error handling (401, 403, 429, 500)
- [ ] Candidate data encrypted at rest
- [ ] GDPR/CCPA retention policy
- [ ] Health check tests connectivity
- [ ] Quota usage monitoring
- [ ] Outreach templates compliance-reviewed

## Health Check
```typescript
async function health() {
  try {
    await client.search({ query: 'test', limit: 1 });
    return { status: 'healthy' };
  } catch { return { status: 'degraded' }; }
}
```

## Resources
- [Status](https://status.juicebox.ai)

## Next Steps
See `juicebox-upgrade-migration`.
