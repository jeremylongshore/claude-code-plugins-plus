---
name: finta-reference-architecture
description: |
  Reference architecture for fundraising operations with Finta CRM.
  Trigger with phrases like "finta architecture", "finta fundraising stack".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Reference Architecture

## Fundraising Tech Stack

```
┌──────────────────┐     ┌─────────────────┐
│  Finta CRM       │     │  Deal Room      │
│  (Pipeline Mgmt) │────▶│  (Doc Sharing)  │
└────────┬─────────┘     └─────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────────┐
│ Gmail │ │ Calendar  │
│ Sync  │ │ Sync      │
└───────┘ └───────────┘
         │
    ┌────┴────────────┐
    │                 │
┌───▼───┐      ┌─────▼─────┐
│Stripe │      │ Mercury/  │
│(Pmts) │      │ Brex      │
└───────┘      │(Metrics)  │
               └───────────┘
         │
    ┌────▼──────┐
    │  Zapier   │
    │ (Events)  │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │  Slack /  │
    │  Sheets   │
    └───────────┘
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CRM | Finta | Purpose-built for fundraising |
| Email tracking | Gmail/Outlook sync | Automatic, no manual logging |
| Documents | Finta Deal Rooms | View tracking built in |
| Payments | Stripe via Finta | Direct capital collection |
| Reporting | CSV export + Python | Flexible, custom analysis |
| Notifications | Zapier -> Slack | Real-time team updates |

## Resources

- [Finta Website](https://www.trustfinta.com)
- [Finta for Fund Managers](https://www.trustfinta.com/blog/finta-for-fund-managers-venture-capital-crm)

## Next Steps

This completes the Finta skill pack. Start with `finta-install-auth`.
