---
name: fondo-prod-checklist
description: |
  Execute Fondo production readiness checklist for year-end tax filing,
  R&D credit claims, and board-ready financial reporting.
  Trigger: "fondo production", "fondo tax filing ready", "fondo year-end checklist".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Production Checklist

## Year-End Tax Filing Readiness

### Integrations
- [ ] All bank accounts connected and syncing
- [ ] Payroll provider connected (all W-2 and 1099 data)
- [ ] Revenue sources connected (Stripe, invoicing)
- [ ] Expense tools connected (Brex, Ramp, Expensify)

### Bookkeeping
- [ ] All 12 months closed and reviewed
- [ ] No outstanding categorization questions in Dashboard
- [ ] Intercompany transactions reconciled
- [ ] Equity events recorded (fundraise, options exercised)
- [ ] Fixed assets and depreciation logged

### R&D Tax Credits
- [ ] R&D employees identified and tagged
- [ ] Qualifying activities documented
- [ ] Contractor R&D hours logged
- [ ] Cloud compute costs allocated to R&D
- [ ] CPA team interview completed

### Tax Filing
- [ ] Federal return (Form 1120) preparation started
- [ ] State returns for registered states identified
- [ ] Form 6765 (R&D credit) included
- [ ] Estimated tax payments reviewed
- [ ] Extension filed if needed (Form 7004 by March 15)

### Board Reporting
- [ ] Annual P&L finalized
- [ ] Balance sheet reviewed
- [ ] Cap table reconciled with equity events
- [ ] Runway projection updated

## Key Deadlines

| Deadline | Filing | Notes |
|----------|--------|-------|
| Jan 31 | W-2 / 1099 issuance | Via payroll provider |
| Mar 15 | S-corp / partnership returns (or extension) | Form 7004 for extension |
| Apr 15 | C-corp return (or extension) | Form 6765 for R&D credit |
| Sep 15 | Extended S-corp / partnership due | After extension |
| Oct 15 | Extended C-corp due | After extension |

## Resources

- [Fondo TaxPass](https://fondo.com/taxpass)
- [IRS Form 1120](https://www.irs.gov/forms-pubs/about-form-1120)

## Next Steps

For version updates, see `fondo-upgrade-migration`.
