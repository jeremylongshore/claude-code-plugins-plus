---
name: fondo-local-dev-loop
description: |
  Configure local development workflows that integrate with Fondo for
  financial data, using Fondo exports with QuickBooks or accounting tools.
  Trigger: "fondo dev setup", "fondo export", "fondo QuickBooks", "fondo local data".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Local Dev Loop

## Overview

Work with Fondo financial data locally. Fondo exports data as CSV and generates QuickBooks-compatible reports. Use exports for building internal dashboards, financial modeling, or integrating with your own tools.

## Instructions

### Step 1: Export Financial Data from Fondo

```
Dashboard > Reports > Export
  → Select report type: General Ledger, P&L, Balance Sheet
  → Select date range
  → Export as CSV or PDF
```

### Step 2: Parse Fondo CSV Exports

```typescript
// src/fondo/parse-transactions.ts
import { parse } from 'csv-parse/sync';
import { readFileSync } from 'fs';

interface FondoTransaction {
  date: string;
  description: string;
  amount: number;
  category: string;
  account: string;
  isRnD: boolean;
}

function parseFondoExport(csvPath: string): FondoTransaction[] {
  const content = readFileSync(csvPath, 'utf-8');
  const records = parse(content, { columns: true, skip_empty_lines: true });

  return records.map((row: any) => ({
    date: row['Date'],
    description: row['Description'],
    amount: parseFloat(row['Amount'].replace(/[,$]/g, '')),
    category: row['Category'],
    account: row['Account'],
    isRnD: row['R&D Qualified'] === 'Yes',
  }));
}

// Usage
const transactions = parseFondoExport('exports/general-ledger-2025-q1.csv');
const totalRnD = transactions
  .filter(t => t.isRnD)
  .reduce((sum, t) => sum + Math.abs(t.amount), 0);
console.log(`Total R&D spend: $${totalRnD.toLocaleString()}`);
```

### Step 3: Build Burn Rate Dashboard

```typescript
// Calculate monthly burn from Fondo data
function calculateBurnRate(transactions: FondoTransaction[]): Map<string, number> {
  const monthly = new Map<string, number>();
  for (const t of transactions) {
    const month = t.date.substring(0, 7);  // YYYY-MM
    const current = monthly.get(month) || 0;
    monthly.set(month, current + t.amount);
  }
  return monthly;
}

const burn = calculateBurnRate(transactions);
burn.forEach((amount, month) => {
  console.log(`${month}: $${Math.abs(amount).toLocaleString()}`);
});
```

## Resources

- [Fondo Dashboard](https://app.fondo.com)
- [csv-parse](https://csv.js.org/parse/)

## Next Steps

See `fondo-sdk-patterns` for data integration patterns.
