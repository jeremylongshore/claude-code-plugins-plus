---
name: fondo-sdk-patterns
description: |
  Build internal tools that consume Fondo financial data exports with
  typed parsers, QuickBooks integration, and financial modeling patterns.
  Trigger: "fondo data patterns", "fondo integration", "fondo QuickBooks sync".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo SDK Patterns

## Overview

Patterns for consuming Fondo financial data in your internal tools. Since Fondo is a managed platform without a public API, integration happens through CSV exports, QuickBooks Online sync, and payroll provider APIs (Gusto, Rippling).

## Instructions

### Pattern 1: Gusto API for Payroll Data

```typescript
// Gusto API — access payroll data that Fondo also ingests
// https://docs.gusto.com/embedded-payroll/reference

const GUSTO_BASE = 'https://api.gusto-demo.com';  // or api.gusto.com for production

async function getPayrollData(companyId: string, accessToken: string) {
  const res = await fetch(`${GUSTO_BASE}/v1/companies/${companyId}/payrolls`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  const payrolls = await res.json();

  return payrolls.map((p: any) => ({
    period: `${p.pay_period.start_date} to ${p.pay_period.end_date}`,
    grossPay: p.totals.gross_pay,
    taxes: p.totals.employer_taxes,
    netPay: p.totals.net_pay,
    employeeCount: p.employee_compensations.length,
  }));
}
```

### Pattern 2: QuickBooks Online API for GL Data

```typescript
// QuickBooks Online API — mirrors what Fondo syncs
// https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities

const QBO_BASE = 'https://quickbooks.api.intuit.com/v3/company';

async function getTrialBalance(realmId: string, accessToken: string) {
  const res = await fetch(
    `${QBO_BASE}/${realmId}/reports/TrialBalance?start_date=2025-01-01&end_date=2025-03-31`,
    { headers: { 'Authorization': `Bearer ${accessToken}`, 'Accept': 'application/json' } },
  );
  return res.json();
}
```

### Pattern 3: Fondo CSV Export Parser with Zod

```typescript
import { z } from 'zod';

const FondoTransactionSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  description: z.string(),
  amount: z.number(),
  category: z.string(),
  account: z.string(),
  isRnD: z.boolean(),
});

type FondoTransaction = z.infer<typeof FondoTransactionSchema>;
```

## Resources

- [Gusto API](https://docs.gusto.com/)
- [QuickBooks API](https://developer.intuit.com/)
- [Fondo](https://fondo.com)

## Next Steps

Apply patterns in `fondo-core-workflow-a` for monthly close workflows.
