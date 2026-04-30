---
name: fondo-local-dev-loop
description: 'Configure local development workflows that integrate with Fondo for

  financial data, using Fondo exports with QuickBooks or accounting tools.

  Trigger: "fondo dev setup", "fondo export", "fondo QuickBooks", "fondo local data".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- accounting
- fondo
compatibility: Designed for Claude Code
---
# Fondo Local Dev Loop

## Overview
Local development workflow for Fondo startup tax and bookkeeping integration. Provides a fast feedback loop using CSV exports and mock financial data so you can build dashboards, R&D credit calculators, and burn-rate tools without waiting on live Fondo reports. Toggle between mock mode for rapid iteration and real export parsing for production validation.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# FONDO_API_KEY=fondo_xxxxxxxxxxxx
# FONDO_EXPORT_DIR=./exports
# MOCK_MODE=true
npm install express csv-parse dotenv tsx typescript @types/node
npm install -D vitest supertest
mkdir -p exports
```

## Dev Server
```typescript
// src/dev/server.ts
import express from "express";
const app = express();
app.use(express.json());
const MOCK = process.env.MOCK_MODE === "true";
if (MOCK) {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
} else {
  const { mountExportRoutes } = require("./export-parser");
  mountExportRoutes(app, process.env.FONDO_EXPORT_DIR!);
}
app.listen(3002, () => console.log(`Fondo dev server on :3002 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — realistic startup financial data
export function mountMockRoutes(app: any) {
  app.get("/api/transactions", (_req: any, res: any) => res.json([
    { date: "2025-03-01", description: "AWS Infrastructure", amount: -4200, category: "Cloud Hosting", account: "Operating", isRnD: true },
    { date: "2025-03-05", description: "Engineer Salary", amount: -12500, category: "Payroll", account: "Operating", isRnD: true },
    { date: "2025-03-10", description: "Stripe Revenue", amount: 8750, category: "Revenue", account: "Income", isRnD: false },
  ]));
  app.get("/api/reports/pnl", (_req: any, res: any) => res.json({
    period: "2025-Q1", revenue: 26250, expenses: 50100, netIncome: -23850,
  }));
  app.get("/api/reports/rnd-summary", (_req: any, res: any) => res.json({
    totalQualified: 38500, categories: ["Cloud Hosting", "Payroll", "Software Tools"],
  }));
}
```

## Testing Workflow
```bash
npm run dev:mock &                    # Start mock server in background
npm run test                          # Unit tests with vitest
npm run test -- --watch               # Watch mode for rapid iteration
MOCK_MODE=false npm run test:integration  # Test against real Fondo CSV exports
```

## Debug Tips
- Place sample CSVs in `exports/` to test parsing without Fondo dashboard access
- Validate CSV column headers match Fondo's export format (Date, Description, Amount, Category, Account, R&D Qualified)
- Use `--verbose` flag with the parser to log skipped rows and type coercion warnings
- Check for locale-specific number formats (`$1,234.56` vs `1234.56`) in Amount column

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `CSV parse error` | Malformed export file | Re-export from Fondo with UTF-8 encoding |
| `NaN in amount` | Currency symbols in Amount column | Strip `$` and `,` before `parseFloat` |
| `Missing R&D column` | Older export format | Use Fondo's updated report template |
| `ENOENT exports/` | Export directory missing | Run `mkdir -p exports` |
| `Empty dataset` | Date range has no transactions | Widen the date range in Fondo dashboard |

## Resources
- [Fondo Dashboard](https://app.fondo.com)
- [csv-parse docs](https://csv.js.org/parse/)

## Next Steps
See `fondo-debug-bundle`.
