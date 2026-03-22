---
name: openevidence-prod-checklist
description: |
  Prod Checklist for OpenEvidence.
  Trigger: "openevidence prod checklist".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Production Checklist

## Pre-Launch
- [ ] Production credentials in secret manager
- [ ] Rate limiting implemented
- [ ] Error handling for all API codes
- [ ] Health check endpoint
- [ ] Monitoring and alerting
- [ ] Rollback procedure documented

## Health Check
```typescript
async function health() {
  try { /* test OpenEvidence API call */ return { status: 'healthy' }; }
  catch { return { status: 'degraded' }; }
}
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-upgrade-migration`.
