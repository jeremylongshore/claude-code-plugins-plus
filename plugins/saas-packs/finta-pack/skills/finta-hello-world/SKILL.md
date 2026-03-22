---
name: finta-hello-world
description: |
  Set up your first fundraise pipeline in Finta with investors and deal stages.
  Use when starting a new fundraise, importing investor lists,
  or learning Finta's pipeline management features.
  Trigger with phrases like "finta hello world", "finta first pipeline",
  "start fundraise in finta", "finta quick start".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Hello World

## Overview

Create your first fundraise pipeline in Finta: add target investors, configure deal stages, and use Aurora AI for investor prospecting.

## Prerequisites

- Completed `finta-install-auth` setup
- Basic company information entered

## Instructions

### Step 1: Create a New Fundraise

1. Click **New Fundraise** in the dashboard
2. Enter details: round name, target amount, equity type (SAFE, Priced, Convertible Note)
3. Set timeline and target close date

### Step 2: Add Target Investors

**Manual Entry:**
- Click **Add Investor** in pipeline view
- Enter: investor name, firm, email, check size range, thesis tags

**CSV Import:**
```csv
Name,Firm,Email,Check Size,Stage,Notes
Jane Smith,Sequoia Capital,jane@sequoia.com,"$500K-$2M",Researching,Met at TechCrunch
Bob Jones,a16z,bob@a16z.com,"$1M-$5M",Reaching Out,Intro from advisor
```

**Aurora AI Prospecting:**
1. Go to **Investors** > **Discover**
2. Aurora ranks investors by thesis fit, check size match, and warm intro availability
3. Add promising matches to your pipeline with one click

### Step 3: Track Pipeline Progress

Finta automatically moves investors through stages based on:
- **Email replies**: Investor responds --> auto-advance to next stage
- **Calendar meetings**: Meeting scheduled --> advance to Intro Meeting
- **Manual updates**: Drag-and-drop in pipeline Kanban view

### Step 4: Set Up Deal Room

1. Navigate to **Deal Rooms** > **Create Deal Room**
2. Upload fundraising materials: pitch deck, financials, cap table
3. Generate shareable link with view tracking
4. Monitor who viewed what and for how long

### Step 5: Send Investor Update

1. Go to **Updates** > **New Update**
2. Select metrics to include: MRR, ARR, burn rate, runway
3. Finta auto-populates from connected financial data
4. Send to all investors or select groups

## Output

- Active fundraise pipeline with investors in stages
- Deal room with shared materials and analytics
- Email/calendar sync tracking communications automatically

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Investors not advancing | Auto-rules disabled | Check Settings > Automation |
| Deal room link broken | Expired share | Regenerate link |
| Metrics not populating | No financial integration | Connect Stripe/Mercury/Brex |
| Aurora suggestions irrelevant | Insufficient company data | Complete company profile |

## Resources

- [Finta for Founders](https://www.trustfinta.com/founders)
- [Finta for Fund Managers](https://www.trustfinta.com/blog/finta-for-fund-managers-venture-capital-crm)

## Next Steps

Proceed to `finta-local-dev-loop` for workflow automation setup.
