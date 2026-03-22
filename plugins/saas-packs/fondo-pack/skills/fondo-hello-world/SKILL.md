---
name: fondo-hello-world
description: |
  Verify Fondo setup by checking financial data sync, reviewing categorized
  transactions, and confirming R&D tax credit eligibility.
  Trigger: "fondo first sync", "fondo verify", "fondo hello world", "fondo test".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Hello World

## Overview

Verify your Fondo setup is working: check that bank transactions are syncing, payroll data is flowing, and your company qualifies for R&D tax credits.

## Instructions

### Step 1: Verify Bank Transaction Sync

Navigate to Fondo Dashboard > Transactions:
- Confirm recent bank transactions appear (may take 24-48h for initial sync)
- Check that Plaid connection shows "Connected" status
- Verify transaction dates match your bank statement

### Step 2: Review Auto-Categorization

Fondo automatically categorizes transactions:

| Category | Examples | Tax Impact |
|----------|----------|------------|
| Payroll | Gusto payments, contractor 1099s | Deductible, R&D qualified |
| Software | AWS, GitHub, Figma | Deductible, R&D qualified |
| Office | WeWork, office supplies | Deductible |
| Travel | Flights, hotels, meals | Partially deductible |
| Revenue | Stripe payouts, customer payments | Taxable income |
| Transfers | Between own accounts | Not taxable |

Review and correct any miscategorized transactions in Dashboard > Transactions.

### Step 3: Check R&D Tax Credit Eligibility

```
Fondo Dashboard > Tax Credits > R&D Assessment

Eligible if ALL apply:
✓ US-based employees (W-2, not just contractors)
✓ Developing new/improved products, processes, or software
✓ Technical uncertainty exists in the development
✓ Systematic experimentation/iteration to resolve uncertainty

Average startup credit: $21,000/year
Maximum (payroll tax offset): $500,000/year
```

### Step 4: Verify Payroll Data

```
Dashboard > Payroll Integration
  → Confirm employee count matches your payroll provider
  → Verify salary data for R&D credit calculations
  → Check contractor payments are categorized separately
```

## Expected Output

After 48 hours of setup:
- Bank transactions auto-categorized (85%+ accuracy)
- Payroll data synced monthly
- R&D eligibility assessment complete
- Estimated R&D credit amount displayed

## Error Handling

| Issue | Solution |
|-------|----------|
| No transactions appearing | Check Plaid connection status, allow 24-48h |
| Wrong categorization | Manually recategorize, Fondo learns patterns |
| R&D credit shows $0 | Verify W-2 employees doing qualifying work |
| Payroll data missing | Re-authorize payroll provider OAuth |

## Resources

- [R&D Tax Credit Guide](https://fondo.com/blog/how-to-account-research-and-development-tax-credit-us)
- [Fondo TaxPass](https://fondo.com/taxpass)

## Next Steps

For development workflow details, see `fondo-local-dev-loop`.
