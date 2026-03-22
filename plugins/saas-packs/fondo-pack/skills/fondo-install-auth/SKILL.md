---
name: fondo-install-auth
description: |
  Set up Fondo account and configure integrations with Gusto, QuickBooks,
  and bank accounts for automated startup bookkeeping and R&D tax credits.
  Trigger: "setup fondo", "fondo account", "fondo integrations", "connect fondo".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Install & Auth

## Overview

Set up Fondo for automated startup bookkeeping, tax filing, and R&D tax credits. Fondo is a managed platform (not an API-first service) that integrates with payroll providers, banks, and expense tools. Configuration happens through the Fondo dashboard and OAuth connections.

## Prerequisites

- US-incorporated startup (C-corp or LLC)
- Fondo account at [fondo.com](https://fondo.com)
- Active payroll provider (Gusto, Rippling, ADP, etc.)
- Business bank account

## Instructions

### Step 1: Create Fondo Account

1. Sign up at [fondo.com](https://fondo.com)
2. Select your plan: **TaxPass** (bookkeeping + taxes + R&D credits)
3. Complete company profile (EIN, incorporation date, state)

### Step 2: Connect Payroll Provider

| Provider | Connection Type | Data Synced |
|----------|----------------|-------------|
| Gusto | OAuth 2.0 | Payroll runs, employee data, tax filings |
| Rippling | OAuth 2.0 | Payroll, benefits, headcount |
| ADP | API key | Payroll summaries, tax deposits |
| Justworks | OAuth 2.0 | PEO payroll, contractor payments |
| QuickBooks Payroll | OAuth 2.0 | Payroll journal entries |
| Paychex | Manual upload | Pay stubs, tax forms |

Navigate to Fondo Dashboard > Integrations > Connect Payroll and authorize.

### Step 3: Connect Bank Accounts

```
Fondo Dashboard > Integrations > Banking
  → Connect via Plaid (most banks)
  → Or manual CSV upload for unsupported banks
  → Mercury, SVB, Brex, Chase all supported via Plaid
```

### Step 4: Connect Expense Tools

| Tool | What It Provides |
|------|------------------|
| Brex | Corporate card transactions |
| Ramp | Card spend, reimbursements |
| Expensify | Receipt data, categorized expenses |
| Bill.com | AP/AR, vendor payments |
| Stripe | Revenue data, payouts |

### Step 5: Verify Connection

After connecting, verify in Dashboard > Integrations:
- Green check = connected and syncing
- Yellow warning = needs re-authorization
- Red X = connection failed, re-connect needed

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| OAuth expired | Token expiry (90 days typical) | Re-authorize in Dashboard > Integrations |
| Missing transactions | Bank feed lag | Wait 24h or upload CSV manually |
| Duplicate entries | Multiple connections to same account | Remove duplicate connection |
| Sync paused | Provider API change | Contact Fondo support |

## Resources

- [Fondo](https://fondo.com)
- [Fondo R&D Credits FAQ](https://fondo.com/blog/fondo-rd-credits-faq)
- [TaxPass Overview](https://fondo.com/taxpass)

## Next Steps

After setup, proceed to `fondo-hello-world` to verify your first financial sync.
