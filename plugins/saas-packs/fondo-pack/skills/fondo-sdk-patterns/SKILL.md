---
name: fondo-sdk-patterns
description: 'Build internal tools that consume Fondo financial data exports with

  typed parsers, QuickBooks integration, and financial modeling patterns.

  Trigger: "fondo data patterns", "fondo integration", "fondo QuickBooks sync".

  '
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- accounting
- fondo
compatibility: Designed for Claude Code
---
# Fondo SDK Patterns

## Overview
Production-ready patterns for integrating with Fondo tax and accounting data. Fondo is a managed bookkeeping platform that syncs through QuickBooks Online and payroll providers. Integration uses the `FONDO_API_KEY`-authenticated REST endpoints for exports, the QuickBooks Online API for GL data, and structured CSV parsing with Zod validation for bulk imports.

## Singleton Client
```typescript
const FONDO_BASE = 'https://api.fondo.com/v1';
let _client: FondoClient | null = null;
export function getClient(): FondoClient {
  if (!_client) {
    const apiKey = process.env.FONDO_API_KEY;
    if (!apiKey) throw new Error('FONDO_API_KEY must be set — get it from your Fondo dashboard');
    _client = new FondoClient(apiKey);
  }
  return _client;
}
class FondoClient {
  private headers: Record<string, string>;
  constructor(apiKey: string) { this.headers = { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' }; }
  async getTransactions(start: string, end: string): Promise<FondoTransaction[]> {
    const res = await fetch(`${FONDO_BASE}/transactions?start=${start}&end=${end}`, { headers: this.headers });
    if (!res.ok) throw new FondoError(res.status, await res.text()); return res.json();
  }
  async getAccounts(): Promise<FondoAccount[]> {
    const res = await fetch(`${FONDO_BASE}/accounts`, { headers: this.headers });
    if (!res.ok) throw new FondoError(res.status, await res.text()); return res.json();
  }
}
```

## Error Wrapper
```typescript
export class FondoError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'FondoError'; }
}
export async function safeCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    if (err instanceof FondoError && err.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    if (err instanceof FondoError && err.status === 401) throw new FondoError(401, 'Invalid FONDO_API_KEY');
    throw new FondoError(err.status ?? 0, `${operation} failed: ${err.message}`);
  }
}
```

## Request Builder
```typescript
class FondoQuery {
  private params: Record<string, string> = {};
  dateRange(start: string, end: string) { this.params.start = start; this.params.end = end; return this; }
  category(cat: string) { this.params.category = cat; return this; }
  accountId(id: string) { this.params.account_id = id; return this; }
  rndOnly() { this.params.is_rnd = 'true'; return this; }
  limit(n: number) { this.params.limit = String(n); return this; }
  build() { return new URLSearchParams(this.params).toString(); }
}
// Usage: new FondoQuery().dateRange('2025-01-01','2025-03-31').rndOnly().build();
```

## Response Types
```typescript
interface FondoTransaction {
  id: string; date: string; description: string; amount: number;
  category: string; account: string; is_rnd: boolean; vendor: string;
}
interface FondoAccount {
  id: string; name: string; type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense';
  balance: number; currency: string;
}
interface FondoReport {
  id: string; period: string; type: 'trial_balance' | 'profit_loss' | 'balance_sheet';
  generated_at: string; rows: Array<{ account: string; debit: number; credit: number }>;
}
interface FondoRnDCredit {
  tax_year: number; qualifying_expenses: number; credit_amount: number;
  status: 'draft' | 'filed' | 'approved';
}
```

## Testing Utilities
```typescript
export function mockTransaction(overrides: Partial<FondoTransaction> = {}): FondoTransaction {
  return { id: 'txn-001', date: '2025-03-15', description: 'AWS hosting',
    amount: 450.00, category: 'Cloud Infrastructure', account: 'Operating Expenses',
    is_rnd: true, vendor: 'Amazon Web Services', ...overrides };
}
export function mockAccount(overrides: Partial<FondoAccount> = {}): FondoAccount {
  return { id: 'acct-001', name: 'Operating Expenses', type: 'expense',
    balance: 12500.00, currency: 'USD', ...overrides };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| `safeCall` wrapper | All Fondo API calls | Structured error logging with operation context |
| Retry on 429 | Bulk transaction exports | 5s backoff before retry |
| Zod validation | CSV import parsing | Reject malformed rows before DB insert |
| Auth validation | Client init | Fail fast on missing `FONDO_API_KEY` |

## Resources
- [Fondo](https://fondo.com)

## Next Steps
Apply patterns in `fondo-core-workflow-a`.
