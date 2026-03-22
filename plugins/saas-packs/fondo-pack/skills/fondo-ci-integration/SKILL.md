---
name: fondo-ci-integration
description: |
  Automate financial reporting workflows that complement Fondo with CI/CD
  pipelines for expense tracking, budget alerts, and financial data validation.
  Trigger: "fondo CI", "fondo automation", "fondo financial alerts".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo CI Integration

## Overview

Automate financial workflows alongside Fondo. While Fondo handles bookkeeping, you can build CI pipelines for budget monitoring, expense alerts, and financial data validation using data from shared providers (Stripe, Gusto).

## Instructions

### Budget Alert Pipeline

```yaml
# .github/workflows/finance-alerts.yml
name: Financial Alerts
on:
  schedule:
    - cron: '0 9 * * MON'  # Weekly Monday 9am

jobs:
  budget-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: node scripts/check-burn-rate.js
        env:
          STRIPE_API_KEY: ${{ secrets.STRIPE_API_KEY }}
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
```

```typescript
// scripts/check-burn-rate.js
// Pull Stripe revenue + known fixed costs to estimate burn
const stripe = require('stripe')(process.env.STRIPE_API_KEY);

async function checkBurnRate() {
  const charges = await stripe.charges.list({ created: { gte: monthStart() }, limit: 100 });
  const revenue = charges.data.reduce((sum, c) => sum + c.amount, 0) / 100;

  const monthlyBurn = 85000;  // Known from Fondo reports
  const netBurn = monthlyBurn - revenue;

  if (netBurn > 100000) {
    await sendSlackAlert(`Burn rate alert: Net burn $${netBurn.toLocaleString()}/month`);
  }
}
```

## Resources

- [Stripe API](https://stripe.com/docs/api)
- [Fondo](https://fondo.com)

## Next Steps

For deployment patterns, see `fondo-deploy-integration`.
