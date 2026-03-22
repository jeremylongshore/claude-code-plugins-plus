---
name: fondo-upgrade-migration
description: |
  Migrate to Fondo from other bookkeeping services, switch between Fondo plans,
  or transition accountants while maintaining financial continuity.
  Trigger: "migrate to fondo", "switch to fondo", "fondo migration", "change accountant".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Upgrade & Migration

## Overview

Migrate to Fondo from DIY bookkeeping, other accounting firms, or platforms like Pilot, Bench, or Kruze. Fondo handles the historical data import.

## Migration Scenarios

| From | Complexity | Timeline |
|------|-----------|----------|
| DIY QuickBooks | Low | 1-2 weeks |
| Another bookkeeping firm | Medium | 2-4 weeks |
| Pilot / Bench / Kruze | Medium | 2-3 weeks |
| No prior bookkeeping | High (catch-up) | 4-8 weeks |
| International entity | High | 4-6 weeks |

## Instructions

### Step 1: Prepare Migration Data

Gather from your current provider:
- [ ] QuickBooks Online backup (or GL export as CSV)
- [ ] Bank statements (last 2 years for R&D credit)
- [ ] Payroll records (all W-2 and 1099 data)
- [ ] Prior tax returns (1120, state returns)
- [ ] R&D credit studies (Form 6765 if previously claimed)
- [ ] Cap table and equity event history

### Step 2: Onboard with Fondo

1. Sign up at [fondo.com](https://fondo.com) and select plan
2. Upload historical data via Dashboard > Migration
3. Connect active integrations (bank, payroll, expense)
4. Fondo CPA team reviews and reconciles historical data
5. First month close produces baseline reports

### Step 3: Transition from Previous Accountant

```
Timeline:
  Week 1: Sign Fondo engagement letter, connect integrations
  Week 2: Previous accountant provides data export and handoff notes
  Week 3: Fondo reviews historical data, catches up any gaps
  Week 4: First Fondo-managed month close complete
```

### Plan Upgrades

| Plan | Includes | Best For |
|------|----------|----------|
| Bookkeeping | Monthly close, financial statements | Pre-revenue startups |
| TaxPass | Bookkeeping + tax filing + R&D credits | Most startups |
| Enterprise | Custom, dedicated CPA team | Series B+ |

## Resources

- [Fondo Pricing](https://fondo.com)
- [Fondo TaxPass](https://fondo.com/taxpass)

## Next Steps

For CI integration, see `fondo-ci-integration`.
