---
name: fondo-reference-architecture
description: 'Reference architecture for startup financial operations using Fondo
  as the

  bookkeeping backbone with complementary tools for banking, payroll, and reporting.

  Trigger: "fondo architecture", "startup finance stack", "fondo integration architecture".

  '
allowed-tools: Read, Write, Edit
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- accounting
- fondo
compatibility: Designed for Claude Code
---
# Fondo Reference Architecture

## Overview

Reference architecture for a startup's financial operations with Fondo at the center, connecting payroll, banking, payments, and internal reporting.

## Prerequisites

- A data-flow inventory, authorized business purpose, system owners, access/retention policy, and professional-review boundary.
- Separate scoped identities for data sources, processing, storage, reporting, and support, plus synthetic integration fixtures.

## Instructions

1. Enforce field allowlists, access checks, encryption, and retention requirements at every financial-data boundary.
2. Keep financial/tax conclusions under the designated finance professional’s review; integrations may prepare evidence but not replace that review.
3. Use idempotent queues, redacted telemetry, staged promotion, and a correction/rollback path for each downstream consumer.

## Output

Maintain an architecture record describing sources, trust boundaries, approved destinations, access/retention controls, owners, professional-review points, and recovery mechanisms. Do not include finance data or secrets.

## Error Handling

- Quarantine unknown fields, unapproved destinations, and reconciliation mismatches for finance review.
- Disable unsafe consumers and preserve only redacted evidence during recovery.
- Restore the prior mapping/configuration before replaying any financial workflow.

## Examples

Route a fictional aggregate expense event through an approved staging pipeline, deny an unapproved reporting consumer, and verify a duplicate event is suppressed. Record only the opaque event ID and aggregate outcome.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Data Sources                         │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Mercury │  Gusto   │  Stripe  │  Brex    │  AWS/GCP    │
│  Banking │  Payroll │  Revenue │  Expense │  Cloud      │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              Plaid / OAuth Connections                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│                   FONDO PLATFORM                         │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐        │
│  │ Monthly  │  │ Tax      │  │ R&D Tax Credit │        │
│  │ Close    │  │ Filing   │  │ Study (6765)   │        │
│  └──────────┘  └──────────┘  └────────────────┘        │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                     Outputs                              │
├──────────┬──────────┬──────────┬────────────────────────┤
│  P&L     │  Balance │  Cash    │  R&D Credit            │
│  Report  │  Sheet   │  Flow    │  Certificate           │
├──────────┴──────────┴──────────┴────────────────────────┤
│              Internal Dashboard (optional)                │
│  Revenue metrics │ Burn rate │ Runway │ Board deck       │
└─────────────────────────────────────────────────────────┘
```

## Recommended Stack

| Category | Tool | Why |
|----------|------|-----|
| Banking | Mercury or SVB | Startup-friendly, API access, Plaid compatible |
| Payroll | Gusto | Best startup payroll, Fondo integration |
| Revenue | Stripe | Standard payments, clean webhooks |
| Expenses | Brex or Ramp | Auto-receipt capture, categorization |
| Bookkeeping | Fondo | Automated, CPA-managed |
| Tax Filing | Fondo (TaxPass) | Bundled with bookkeeping |
| R&D Credits | Fondo | Integrated with bookkeeping data |
| Cap Table | Carta or Pulley | Equity management |
| Board Reporting | Fondo exports + internal dashboard | Custom metrics |

## Data Flow

1. Transactions flow from banks/cards/payroll into Fondo via Plaid/OAuth
2. Fondo CPA team categorizes and reconciles monthly
3. Financial statements generated and delivered to Dashboard
4. R&D credit study prepared annually from same data
5. Tax returns filed using reconciled data

## Resources

- [Fondo](https://fondo.com)
- [Mercury](https://mercury.com)
- [Gusto](https://gusto.com)

## Next Steps

Start with `fondo-install-auth` to set up your Fondo account.
