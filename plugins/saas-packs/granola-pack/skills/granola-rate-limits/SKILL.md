---
name: granola-rate-limits
description: |
  Understand Granola plan limits, usage quotas, and API rate limiting.
  Use when hitting meeting limits, choosing between plans,
  or managing Enterprise API rate limits.
  Trigger: "granola limits", "granola quota", "granola plan",
  "granola usage", "granola restrictions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, monitoring, plans]

---
# Granola Rate Limits & Plan Quotas

## Overview
Granola has three plan tiers with different feature access and limits. There are no per-meeting minute caps or monthly meeting count limits on paid plans. Limits primarily apply to the free tier and the Enterprise API.

## Plan Comparison (Current as of March 2026)

### Basic (Free) — $0
| Feature | Limit |
|---------|-------|
| Meetings | 25 lifetime (not monthly) |
| Meeting history | Visible for 14 days only |
| Enhance Notes | Included |
| Templates | Built-in only |
| Granola Chat | Included |
| People & Companies | Included |
| Integrations | None |
| API access | None |

> The free plan is essentially a trial — 25 meetings total, ever. After that, you must upgrade.

### Business — $14/user/month
| Feature | Availability |
|---------|-------------|
| Meetings | Unlimited |
| Meeting history | Unlimited retention |
| Templates | Built-in + custom |
| Granola Chat | Included |
| People & Companies | Included |
| Slack integration | Native |
| Notion integration | Native |
| CRM (HubSpot, Attio, Affinity) | Native |
| Zapier | Full access |
| MCP (AI agent integration) | Included |
| Team shared folders | Included |
| Admin controls | Basic |
| AI training opt-out (org-wide) | Included |
| Priority support | Included |
| Public API access | Included |

### Enterprise — $35+/user/month
| Feature | Availability |
|---------|-------------|
| Everything in Business | Included |
| SSO (Okta, Google Workspace) | Included |
| SCIM provisioning | Included |
| AI training opt-out (enforced) | Default on |
| Usage analytics dashboard | Included |
| Enterprise API (full) | Included |
| Custom data retention policies | Configurable |
| SOC 2 Type 2 compliance report | Available |
| Dedicated account manager | Included |
| Volume discounts | Negotiable |

## API Rate Limits

### Enterprise API
- Rate limits are applied **per workspace** (not per user)
- When exceeded: HTTP `429 Too Many Requests` response
- Retry behavior: respect the `Retry-After` header
- No published rate numbers — contact Granola for workspace-specific limits

### Zapier Integration
- Zapier task limits are governed by your **Zapier plan**, not Granola
- Granola does not throttle outbound Zapier triggers
- For high-volume workspaces, add delay steps between Zap actions to avoid overwhelming downstream apps

## Usage Monitoring

### Check Usage in Granola
1. Click your avatar (bottom-left) > **Settings**
2. Navigate to **Account** or **Subscription**
3. View: current plan, meeting count, team seats, connected integrations

### Free Plan Usage Tracking
```
Meetings Used: 18 / 25 lifetime
History Visible: Last 14 days
Upgrade Required: After 25 meetings
```

### API Usage (Enterprise)
Monitor API usage through response headers:
```bash
# Check rate limit headers in API response
curl -s -I "https://api.granola.ai/v0/notes" \
  -H "Authorization: Bearer $GRANOLA_API_KEY" \
  | grep -i "rate-limit\|retry-after"
```

## What Happens at Limits

| Limit Hit | Behavior | Resolution |
|-----------|----------|------------|
| Free plan 25 meetings | New recordings blocked | Upgrade to Business ($14/mo) |
| Free plan 14-day history | Older notes hidden (not deleted) | Upgrade to restore access |
| API rate limit (429) | Requests rejected | Wait for `Retry-After` period, reduce request frequency |
| Zapier task limit | Zaps paused | Upgrade Zapier plan or reduce trigger frequency |
| Workspace seat limit | Can't add users | Purchase additional seats or remove inactive users |

## Plan Selection Guide

| Scenario | Recommended Plan |
|----------|-----------------|
| Trying Granola (< 25 meetings) | Basic (Free) |
| Individual user, needs integrations | Business ($14/mo) |
| Team of 2-10, shared folders + CRM | Business ($14/user/mo) |
| 10+ users, SSO/SCIM required | Enterprise ($35+/user/mo) |
| Regulated industry (SOC 2, GDPR) | Enterprise |
| API access for custom workflows | Business (basic) or Enterprise (full) |

## Billing Details
- **Annual billing:** Save 10-15% vs monthly
- **Prorated upgrades:** Upgrade mid-cycle, pay difference
- **Seat management:** Add/remove seats in Settings > Team
- **No per-minute charges:** Granola does not charge by meeting duration or transcription minutes

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| "Meeting limit reached" | Free plan exhausted (25 lifetime) | Upgrade to Business |
| "Subscription expired" | Payment method failed | Update payment in Settings > Billing |
| API 429 response | Rate limit exceeded | Implement exponential backoff, reduce request frequency |
| "Feature not available" | Feature requires higher plan | Check plan comparison above and upgrade |

## Resources
- [Granola Pricing](https://www.granola.ai/pricing)
- [Pricing Blog (ROI Calculator)](https://www.granola.ai/blog/granola-pricing-plans-features-roi)
- [Enterprise API Docs](https://docs.granola.ai/help-center/sharing/integrations/enterprise-api)
- [API Changelog](https://docs.granola.ai/api-reference/changelog)

## Next Steps
Proceed to `granola-security-basics` for security and compliance configuration.
