---
name: finta-rate-limits
description: |
  Understand Finta usage limits and plan tiers.
  Trigger with phrases like "finta limits", "finta plan limits".
allowed-tools: Read
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Rate Limits

## Plan-Based Limits

Finta is a web application -- limits are based on plan tier, not API rate limits:

| Feature | Free | Pro |
|---------|------|-----|
| Investors in pipeline | Limited | Unlimited |
| Deal rooms | 1 | Unlimited |
| Data rooms | Limited | Unlimited |
| Team members | 1 | Multiple |
| Aurora AI suggestions | Limited | Full access |
| Payment collection | No | Yes (Stripe/ACH) |

## Resources

- [Finta Pricing](https://www.trustfinta.com/pricing)

## Next Steps

For security, see `finta-security-basics`.
