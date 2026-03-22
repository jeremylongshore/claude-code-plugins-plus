---
name: fondo-webhooks-events
description: |
  Implement event-driven financial workflows using webhooks from Fondo-connected
  services: Stripe payment events, Gusto payroll events, and Plaid transactions.
  Trigger: "fondo webhooks", "fondo events", "stripe payroll webhooks", "financial events".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Webhooks & Events

## Overview

Fondo itself does not send webhooks. Instead, build event-driven workflows using webhooks from the same providers Fondo connects to: Stripe (revenue), Gusto (payroll), Plaid (bank transactions), and Mercury (banking).

## Provider Webhooks

| Provider | Key Events | Use Case |
|----------|-----------|----------|
| Stripe | `charge.succeeded`, `invoice.paid` | Revenue tracking, MRR alerts |
| Gusto | `payroll.processed`, `employee.created` | Payroll cost alerts, headcount |
| Plaid | `transactions.sync`, `item.error` | Expense monitoring |
| Mercury | `transaction.created` | Real-time spend tracking |

## Instructions

### Stripe Revenue Webhook

```typescript
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_API_KEY!);

app.post('/webhooks/stripe', express.raw({ type: '*/*' }), (req, res) => {
  const sig = req.headers['stripe-signature'] as string;
  const event = stripe.webhooks.constructEvent(
    req.body, sig, process.env.STRIPE_WEBHOOK_SECRET!
  );

  switch (event.type) {
    case 'charge.succeeded':
      const amount = (event.data.object as Stripe.Charge).amount / 100;
      console.log(`Revenue: $${amount}`);
      // Update internal dashboard
      break;
    case 'invoice.paid':
      // MRR tracking
      break;
  }
  res.sendStatus(200);
});
```

### Gusto Payroll Webhook

```typescript
// Gusto sends webhooks when payroll is processed
app.post('/webhooks/gusto', express.json(), async (req, res) => {
  const { event_type, data } = req.body;

  if (event_type === 'payroll.processed') {
    const totalPayroll = data.totals.gross_pay;
    console.log(`Payroll processed: $${totalPayroll}`);
    // Alert if significantly different from budget
    if (totalPayroll > monthlyPayrollBudget * 1.1) {
      await sendAlert(`Payroll exceeded budget by ${((totalPayroll / monthlyPayrollBudget - 1) * 100).toFixed(0)}%`);
    }
  }
  res.sendStatus(200);
});
```

## Resources

- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Gusto Webhooks](https://docs.gusto.com/)
- [Plaid Webhooks](https://plaid.com/docs/api/webhooks/)

## Next Steps

For performance optimization, see `fondo-performance-tuning`.
