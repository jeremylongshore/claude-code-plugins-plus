---
name: fondo-rate-limits
description: |
  Manage rate limits for Fondo-connected services including Gusto API,
  QuickBooks API, Plaid, and Stripe when building parallel integrations.
  Trigger: "fondo rate limit", "gusto API limits", "QuickBooks throttling".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Rate Limits

## Overview

Fondo itself has no API rate limits (it's a managed service). But if you build parallel integrations to the same providers Fondo uses (Gusto, QuickBooks, Plaid, Stripe), you share rate limits.

## Provider Rate Limits

| Provider | Rate Limit | Scope |
|----------|-----------|-------|
| Gusto API | 50 requests/min | Per access token |
| QuickBooks Online | 500 requests/min, 10 concurrent | Per realm |
| Plaid | 100 requests/min | Per client_id |
| Stripe | 100 reads/sec, 200 writes/sec | Per API key |
| Mercury API | 50 requests/min | Per API key |

## Instructions

### Avoid Conflicting with Fondo Syncs

```typescript
// If you also call Gusto API directly, coordinate with Fondo's sync schedule
// Fondo typically syncs payroll data daily at midnight UTC
// Schedule your own Gusto API calls outside this window

import PQueue from 'p-queue';

const gustoQueue = new PQueue({
  concurrency: 2,
  interval: 60_000,
  intervalCap: 40,  // Stay under 50/min to leave room for Fondo
});
```

## Resources

- [Gusto API Rate Limits](https://docs.gusto.com/)
- [QuickBooks API Limits](https://developer.intuit.com/)
- [Stripe Rate Limits](https://stripe.com/docs/rate-limits)

## Next Steps

For security, see `fondo-security-basics`.
