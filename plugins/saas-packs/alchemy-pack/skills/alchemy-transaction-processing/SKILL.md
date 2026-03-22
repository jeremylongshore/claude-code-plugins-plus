---
name: alchemy-transaction-processing
description: |
  Execute Alchemy primary workflow: Transaction Processing.
  Use when syncing expenses from corporate cards into accounting,
  processing payments and tracking settlement status, or reconciling transactions across multiple accounts.
  Trigger with phrases like "alchemy process transaction",
  "create and track transactions with alchemy".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, alchemy]
---

# Alchemy Transaction Processing

## Overview
Create, track, and reconcile financial transactions programmatically.
This is the primary workflow — money moves in, money moves out, everything reconciles.


## Prerequisites
- Completed `alchemy-install-auth` setup

- Understanding of Alchemy core concepts

- Valid API credentials configured

## Instructions

### Step 1: List Recent Transactions
```typescript
const transactions = await client.transactions.list({
  from: '2026-03-01',
  to: '2026-03-22',
  limit: 100,
});
console.log(`${transactions.total} transactions in period`);
console.log(`Total: $${transactions.data.reduce((sum, t) => sum + t.amount, 0) / 100}`);

```

### Step 2: Categorize and Tag
```typescript
for (const txn of transactions.data) {
  const category = categorize(txn.merchant, txn.amount);
  await client.transactions.update(txn.id, {
    category: category.code,
    memo: category.label,
    tags: [category.department],
  });
}

```

### Step 3: Export for Reconciliation
```typescript
const report = await client.reports.generate({
  type: 'transaction_summary',
  period: '2026-03',
  format: 'csv',
  groupBy: 'category',
});
fs.writeFileSync('march-reconciliation.csv', report.data);
console.log('Exported reconciliation report');

```

## Output
- Completed Transaction Processing execution

- Expected results from Alchemy API

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Insufficient Funds | Account balance too low for the requested transaction | Check balance before initiating. Set up low-balance alerts. |
| Duplicate Transaction | Idempotency key already used for a completed transaction | Use unique idempotency keys per transaction. Check existing transactions. |

## Examples

### Complete Workflow
```typescript
const client = new FinanceClient({ apiKey: process.env.API_KEY });

async function syncExpenses(startDate: string) {
  const txns = await client.transactions.list({ from: startDate, status: 'completed' });
  for (const txn of txns.data) {
    await accountingSystem.createExpense({
      amount: txn.amount,
      vendor: txn.merchant.name,
      date: txn.date,
      receipt: txn.receipt_url,
    });
  }
  return txns.total;
}

```

### Common Variations
- **Real-time sync**: Webhook on transaction.completed for instant reconciliation
- **Multi-currency**: Handle exchange rates and conversion fees
- **Receipt matching**: Auto-match receipts to transactions via OCR


## Resources
- [Alchemy Documentation](https://docs.alchemy.com)
- [Alchemy API Reference](https://docs.alchemy.com/api)

## Next Steps
For secondary workflow, see `alchemy-reporting-compliance`.