---
name: mindtickle-prod-checklist
description: |
  Prod Checklist for MindTickle.
  Trigger: "mindtickle prod checklist".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Production Checklist

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
  try { /* test MindTickle API call */ return { status: 'healthy' }; }
  catch { return { status: 'degraded' }; }
}
```

## Resources
- [MindTickle Docs](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-upgrade-migration`.
