---
name: onenote-prod-checklist
description: |
  Prod Checklist for OneNote.
  Trigger: "onenote prod checklist".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Production Checklist

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
  try { /* test OneNote API call */ return { status: 'healthy' }; }
  catch { return { status: 'degraded' }; }
}
```

## Resources
- [OneNote Docs](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-upgrade-migration`.
