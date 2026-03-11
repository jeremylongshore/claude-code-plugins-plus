---
name: customerio-cost-tuning
description: |
  Optimize Customer.io costs and usage.
  Use when reducing expenses, optimizing usage,
  or right-sizing your Customer.io plan.
  Trigger with phrases like "customer.io cost", "reduce customer.io spend",
  "customer.io billing", "customer.io pricing".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Cost Tuning

## Overview
Optimize Customer.io costs by managing profiles, reducing unnecessary operations, implementing event sampling, and right-sizing your usage.

## Prerequisites
- Access to Customer.io billing dashboard
- Understanding of pricing model (profiles, emails, SMS)
- API access for usage analysis

## Instructions

### Step 1: Audit Profiles
Run profile audits to identify inactive users (30/90+ days), profiles without email, and suppressed users. Remove or archive profiles that aren't receiving value.

### Step 2: Suppress and Delete Inactive Users
Use dry-run mode first to preview impact. Suppress users who haven't engaged, and fully delete profiles to remove from billing.

### Step 3: Implement Event Deduplication
Use LRU cache to deduplicate identical events within a time window. Configure skip lists for low-value events and sampling rates for high-volume events.

### Step 4: Optimize Email Costs
Skip marketing emails for users inactive 6+ months. Consolidate notification emails with batching windows. Suppress after 3+ bounces.

### Step 5: Build Usage Monitoring
Track profile growth, event volume by type, email delivery metrics, and estimated costs. Set up alerts for unexpected usage spikes.

### Step 6: Execute Monthly Cost Review
Follow the checklist: clean profiles, optimize events, manage email lists, and review plan vs actual usage.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Cost Savings Estimates
| Optimization | Typical Savings |
|--------------|-----------------|
| Profile cleanup | 10-30% |
| Event deduplication | 5-15% |
| Email list hygiene | 5-10% |
| Sampling high-volume events | 10-20% |
| Annual billing | 10-20% |

## Error Handling
| Issue | Solution |
|-------|----------|
| Accidental deletion | Customer.io has 30-day recovery |
| Over-suppression | Track suppression reasons |
| Usage spike | Set up usage alerts |

## Resources
- [Customer.io Pricing](https://customer.io/pricing/)
- [Profile Management API](https://customer.io/docs/api/track/#operation/destroy)

## Next Steps
After cost optimization, proceed to `customerio-reference-architecture` for architecture patterns.
