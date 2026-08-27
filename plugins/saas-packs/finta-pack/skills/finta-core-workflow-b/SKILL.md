---
name: finta-core-workflow-b
description: 'Manage ongoing investor relations and updates with Finta.

  Use when sending investor updates, tracking cap table changes,

  or maintaining LP relationships post-close.

  Trigger with phrases like "finta investor updates", "finta LP management",

  "finta post-close", "finta investor relations".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- fundraising-crm
- investor-management
- finta
compatibility: Designed for Claude Code
---
# Finta Core Workflow: Investor Relations

## Overview

Post-fundraise investor management: send periodic updates, share metrics, manage cap table, and maintain relationships for future rounds.

## Prerequisites

- Confirm the update audience, source-of-truth metrics, and internal approval owner.
- Verify that recipients are authorized for the selected content and documents.
- Prepare a redacted draft outside of production mailing lists for review.

## Instructions

### Investor Updates

1. Go to **Updates** > **New Update**
2. Select template (monthly, quarterly, or custom)
3. Finta auto-populates metrics from connected financial tools:
   - MRR/ARR from Stripe
   - Cash and burn rate from Mercury/Brex
   - Runway calculation
4. Add qualitative updates (milestones, challenges, asks)
5. Send to all investors or select groups

### Update Template

```
Subject: [Company] Monthly Update - March 2026

Key Metrics:
- MRR: $X (up Y% MoM)
- ARR: $X
- Burn Rate: $X/month
- Runway: X months
- Headcount: X

Highlights:
- [Achievement 1]
- [Achievement 2]

Challenges:
- [Challenge and plan to address]

Asks:
- Introductions to [specific companies/people]
- Feedback on [specific topic]
```

### Warm Introduction Network

Finta's network feature identifies 2nd-degree connections:

1. Go to **Network** > **Find Introductions**
2. Select target investor
3. Finta shows mutual connections from your team, advisors, and existing investors
4. Request introduction through the platform

### Cap Table Tracking

- Import cap table from Carta, Pulley, or CSV
- Track ownership percentages after each round
- Model dilution for future rounds
- Export for legal and compliance

## Output

Create an approved investor-update record containing the audience segment, source metric date, reviewer, send time, and any open follow-up requests. Keep cap-table exports and recipient-level details in their approved systems, not in local drafts or repository files.

## Error Handling

- Stop a send when the recipient segment, attached document permissions, or source metrics cannot be verified.
- Treat bounced messages, unsubscribe requests, or audience mismatches as a review queue; do not automatically resend to an alternate address.
- If connected metrics are stale or incomplete, label the update as pending and obtain an owner’s decision before sending.
- Revoke access and document the correction if a restricted update or document is shared with the wrong audience.

## Examples

Draft a monthly update with fictional metrics, have the designated reviewer approve the audience, and send it only to a test segment. Verify the activity record and document permissions, then use the same reviewed template for the authorized production segment.

## Resources

- [Finta for Fund Managers](https://www.trustfinta.com/blog/finta-for-fund-managers-venture-capital-crm)

## Next Steps

For troubleshooting, see `finta-common-errors`.
