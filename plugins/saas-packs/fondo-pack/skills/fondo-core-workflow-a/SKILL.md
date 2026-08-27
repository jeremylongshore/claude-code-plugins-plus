---
name: fondo-core-workflow-a
description: 'Execute Fondo primary workflow: monthly bookkeeping close and financial
  reporting.

  Use when managing month-end close, reviewing financial statements,

  or preparing for board meetings and fundraising.

  Trigger: "fondo bookkeeping", "fondo month close", "fondo financial reports".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- accounting
- fondo
compatibility: Designed for Claude Code
---
# Fondo Core Workflow A: Monthly Bookkeeping

## Overview

The primary Fondo workflow: automated monthly bookkeeping close. Fondo's CPA team handles reconciliation, categorization, and financial statement preparation. Your role is to answer questions and review deliverables.

## Prerequisites

- A designated finance owner, close calendar, approved source systems, access controls, and professional-review responsibility.
- Documented retention and correction process; use synthetic data for automation tests.

## Instructions

1. Confirm source completeness and reconciliation state before treating a close as ready for review.
2. Respond to questions through the authorized finance workflow, preserving supporting evidence in approved systems.
3. Review statements and exceptions with the responsible professional; correct discrepancies using the documented process.
4. Publish only approved, access-controlled reports and record the review state.

## Output

Create a close receipt with period, source-completeness result, reviewer, open exceptions, report approval state, and next action. Do not include ledger rows, accounts, payroll, tax data, or credentials.

## Examples

Use a fictional month-end ledger summary to test the review workflow, create one deliberate reconciliation exception, and verify the close remains pending until the finance reviewer resolves it.

## Monthly Close Timeline

| Day | Activity | Who |
|-----|----------|-----|
| 1-5 | Bank and payroll data syncs | Automated |
| 5-10 | Transaction categorization and reconciliation | Fondo CPA team |
| 10-15 | Review questions sent to you | Fondo CPA team |
| 15-20 | You answer categorization questions | You |
| 20-25 | Financial statements prepared | Fondo CPA team |
| 25-30 | Reports delivered to dashboard | Automated |

## Deliverables

### Financial Statements (Monthly)

| Report | Contents | Use Case |
|--------|----------|----------|
| Income Statement (P&L) | Revenue, COGS, operating expenses, net income | Board meetings, fundraising |
| Balance Sheet | Assets, liabilities, equity | Financial health snapshot |
| Cash Flow Statement | Operating, investing, financing activities | Burn rate analysis |
| General Ledger | All transactions with GL codes | Audit trail |
| Accounts Payable Aging | Outstanding vendor bills | Cash management |

### Key Metrics (Auto-Calculated)

```
Dashboard > Financial Overview

Monthly Burn Rate:     $85,000
Runway (months):       14.2
MRR:                   $12,500
Gross Margin:          72%
R&D Spend:             $62,000 (73% of opex)
Headcount Cost:        $58,000
```

## Answering Fondo Questions

```
Dashboard > Messages > Open Items

Common questions:
Q: "What is the $2,500 payment to Acme Corp?"
A: "Software license for our dev tooling" → Category: Software/R&D

Q: "Is the $15,000 transfer to savings an investment?"
A: "No, just parking cash" → Category: Transfer (non-taxable)

Q: "Should contractor payments to John Doe be R&D?"
A: "Yes, he writes code for our product" → R&D qualified
```

## Error Handling

| Issue | Solution |
|-------|----------|
| Late close (past 25th) | Prioritize answering open questions |
| Unexpected expense spike | Review Dashboard > Transactions for anomalies |
| Revenue not matching Stripe | Check Stripe connection in Integrations |
| Missing payroll entry | Verify payroll provider sync status |

## Resources

- Fondo Dashboard
- [Understanding Financial Statements](https://fondo.com/blog)

## Next Steps

For R&D tax credit workflow, see `fondo-core-workflow-b`.
