---
name: fondo-core-workflow-b
description: |
  Execute Fondo R&D tax credit workflow: qualify activities, calculate credits,
  file Form 6765, and claim payroll tax offset for startups.
  Trigger: "fondo R&D credit", "fondo tax credit", "fondo Form 6765", "startup tax credit".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Core Workflow B: R&D Tax Credits

## Overview

Claim R&D tax credits through Fondo. Startups with US W-2 employees doing qualifying R&D can offset up to $500,000/year in payroll taxes (FICA). Fondo's CPA team prepares the Form 6765 study.

## R&D Credit Calculation

```
Qualifying R&D Expenses:
  W-2 wages for R&D employees:        $480,000
  Contractor payments (65%):           $78,000
  Cloud compute (AWS/GCP):             $36,000
  Software tools for R&D:              $12,000
                                       --------
  Total Qualified Research Expenses:   $606,000

Credit Rate (Alternative Simplified):  ~6-8%
Estimated R&D Credit:                  ~$42,000
```

## Qualifying Activities

| Qualifies | Does NOT Qualify |
|-----------|-----------------|
| Developing new software features | Routine maintenance/bug fixes |
| Improving existing algorithms | Marketing or sales activities |
| Building internal tools | Purchasing off-the-shelf software |
| API integrations requiring experimentation | Simple data entry or configuration |
| Machine learning model development | General management |
| Infrastructure automation | Accounting or legal work |

## Timeline

| Month | Activity |
|-------|----------|
| Jan-Feb | Fondo collects prior year R&D data from payroll and expenses |
| Mar | CPA team interviews founders about qualifying activities |
| Apr | R&D credit study prepared, Form 6765 drafted |
| Apr 15 | Filed with corporate tax return (or extension) |
| May-Jun | IRS processes credit, payroll tax offset begins |

## Payroll Tax Offset (Startups)

```
Eligibility for payroll tax offset (Section 41(h)):
  ✓ Less than $5M gross receipts in current year
  ✓ No gross receipts in any year before the 5-year period ending in current year
  ✓ Filed as election on Form 6765

Offset: Up to $250,000 per year against employer FICA (6.2%)
        Up to $250,000 per year against Medicare (1.45%)
        Total: Up to $500,000/year in payroll tax savings
```

## Error Handling

| Issue | Solution |
|-------|----------|
| Credit lower than expected | Review qualifying activity classifications with CPA |
| Missing contractor data | Upload 1099 forms to Fondo dashboard |
| Late filing | File extension (Form 7004) before April 15 |
| IRS audit of R&D claim | Fondo provides audit defense documentation |

## Resources

- [Fondo R&D Credits](https://fondo.com/tax-credits)
- [IRS Form 6765](https://www.irs.gov/forms-pubs/about-form-6765)
- [R&D Credit FAQ](https://fondo.com/blog/fondo-rd-credits-faq)

## Next Steps

For troubleshooting, see `fondo-common-errors`.
