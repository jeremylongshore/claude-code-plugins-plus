---
name: podium-core-workflow-b
description: |
  Podium core workflow b — business messaging and communication platform integration.
  Use when working with Podium API for messaging, reviews, or payments.
  Trigger with phrases like "podium core workflow b", "podium-core-workflow-b".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, podium, messaging, reviews, payments]
compatible-with: claude-code, codex, openclaw
---

# Podium Core Workflow B

## Overview
Manage reviews and payments with Podium: request reviews from customers, track review status, and create payment invoices.

## Prerequisites
- Completed `podium-core-workflow-a` (messaging)
- Reviews and Payments features enabled in Podium account

## Instructions

### Step 1: Request a Review
```typescript
// Send a review request to a customer
const { data } = await podium.post(`/locations/${locationId}/review-invitations`, {
  data: {
    attributes: {
      'contact-phone': '+15551234567',
      'customer-name': 'Jane Doe',
    },
  },
});
console.log(`Review invitation sent: ${data.data.id}`);
```

### Step 2: List Reviews
```typescript
const { data } = await podium.get(`/locations/${locationId}/reviews`);
for (const review of data.data) {
  console.log(`  ${review.attributes.rating}/5 — ${review.attributes.body}`);
}
```

### Step 3: Create a Payment Invoice
```typescript
const { data } = await podium.post(`/locations/${locationId}/invoices`, {
  data: {
    attributes: {
      'contact-phone': '+15551234567',
      amount: 5000,  // $50.00 in cents
      description: 'Service invoice #1234',
    },
  },
});
console.log(`Invoice created: ${data.data.id}, amount: $${data.data.attributes.amount / 100}`);
```

## Output
- Review invitations sent to customers
- Review listing with ratings and content
- Payment invoices created and tracked

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422 Invalid amount` | Amount not in cents | Convert dollars to cents (multiply by 100) |
| `403 Payments not enabled` | Feature not active | Enable Payments in Podium account |
| Review invitation failed | Customer opted out | Check contact preferences |

## Resources
- [Podium Developer Portal](https://developer.podium.com/)
- [Podium API Reference](https://docs.podium.com/reference)

## Next Steps
Handle webhook events: `podium-webhooks-events`
