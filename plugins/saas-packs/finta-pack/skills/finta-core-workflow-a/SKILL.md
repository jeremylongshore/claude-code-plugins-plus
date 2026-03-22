---
name: finta-core-workflow-a
description: |
  Manage a fundraise pipeline end-to-end with Finta.
  Use when running a fundraise, tracking investor conversations,
  managing deal rooms, or collecting commitments.
  Trigger with phrases like "finta fundraise", "finta pipeline management",
  "finta investor tracking", "run fundraise with finta".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Core Workflow: Fundraise Pipeline

## Overview

End-to-end fundraise management with Finta: prospect investors, manage outreach, track meetings, handle due diligence, and close commitments.

## Instructions

### Step 1: Investor Prospecting with Aurora AI

Aurora AI analyzes your company profile and recommends investors based on:
- Thesis alignment (sector, stage, geography)
- Historical investment behavior
- Warm introduction availability from your network

Navigate to **Investors** > **Discover** and review AI-ranked suggestions.

### Step 2: Outreach Campaign

1. Select investors to contact
2. Use Finta's AI-assisted email composer for personalized outreach
3. Finta auto-tracks replies and updates pipeline stages

**Stage automation rules:**
- Investor opens email --> "Reaching Out" (stays)
- Investor replies --> auto-advance to "Intro Meeting"
- Meeting scheduled --> confirm via calendar sync

### Step 3: Deal Room Setup

For each active conversation:
1. Create a **Deal Room** with relevant materials
2. Upload: pitch deck, financial model, cap table, team bios
3. Share link with investor
4. Monitor analytics: views, time spent, pages viewed

### Step 4: Due Diligence Management

1. Create a **Data Room** for detailed document sharing
2. Organize by category: legal, financial, technical, team
3. Set permission-based access (view-only, download, etc.)
4. Track which documents investors have reviewed

### Step 5: Close and Collect

1. Move investor to "Term Sheet" stage when term sheet received
2. Review terms in Finta's term sheet comparison view
3. Accept and move to "Closed"
4. Use Stripe/ACH integration to send payment links
5. Collect committed capital directly through Finta

## Fundraise Metrics Dashboard

Track in Finta or export for custom analysis:
- Total pipeline value
- Conversion rate by stage
- Average time in each stage
- Top investor engagement (deal room views)
- Warm intro utilization rate

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Emails not tracking | OAuth disconnected | Reconnect in Settings |
| Deal room views not logging | Browser blocking | Share via direct email |
| Payment link expired | Stripe session timeout | Generate new link |
| Aurora suggestions poor | Incomplete profile | Complete all company fields |

## Resources

- [Finta for Serial Entrepreneurs](https://www.trustfinta.com/blog/finta-for-serial-entrepreneurs-fundraising)
- [Finta Customers](https://www.trustfinta.com/customers)

## Next Steps

For investor relations and updates, see `finta-core-workflow-b`.
