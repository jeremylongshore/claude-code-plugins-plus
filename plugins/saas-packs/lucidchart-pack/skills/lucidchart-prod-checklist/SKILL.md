---
name: lucidchart-prod-checklist
description: |
  Prod Checklist for Lucidchart.
  Trigger: "lucidchart prod checklist".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Production Checklist

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
  try { /* test Lucidchart API call */ return { status: 'healthy' }; }
  catch { return { status: 'degraded' }; }
}
```

## Resources
- [Lucidchart Docs](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-upgrade-migration`.
