---
name: fondo-deploy-integration
description: |
  Deploy financial dashboards and reporting tools that consume Fondo data
  to Vercel, Fly.io, or internal infrastructure.
  Trigger: "fondo dashboard deploy", "fondo financial dashboard", "deploy finance app".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Deploy Integration

## Overview

Deploy internal financial dashboards that display Fondo-managed data. Pull data from shared providers (Stripe for revenue, Gusto for payroll) and Fondo CSV exports to build custom views for your team.

## Instructions

### Internal Finance Dashboard (Next.js)

```typescript
// app/api/metrics/route.ts — pull from Stripe (same data Fondo uses)
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_API_KEY!);

export async function GET() {
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  const charges = await stripe.charges.list({
    created: { gte: Math.floor(monthStart.getTime() / 1000) },
    limit: 100,
  });

  const mrr = charges.data
    .filter(c => c.status === 'succeeded')
    .reduce((sum, c) => sum + c.amount, 0) / 100;

  return Response.json({
    mrr,
    monthlyBurn: 85000,  // From Fondo reports
    runway: 1200000 / 85000,  // Cash / burn
    updatedAt: new Date().toISOString(),
  });
}
```

### Deploy

```bash
# Vercel (recommended for internal dashboards)
vercel env add STRIPE_API_KEY production
vercel --prod

# Password-protect with Vercel Authentication or middleware
```

## Resources

- [Stripe API](https://stripe.com/docs/api)
- [Vercel Deployment](https://vercel.com/docs)

## Next Steps

For webhook event handling, see `fondo-webhooks-events`.
