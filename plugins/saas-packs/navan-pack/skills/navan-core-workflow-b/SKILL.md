---
name: navan-core-workflow-b
description: |
  Execute Navan secondary workflow: Expense Management.
  Trigger: "navan expense management", "secondary navan workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan — Expense Management

## Overview
Secondary workflow complementing the primary workflow.

## Instructions

### Step 1: Submit Expense
```typescript
const expense = await client.expenses.create({
  employee_id: 'emp_123',
  category: 'meals',
  amount: 45.50,
  currency: 'USD',
  merchant: 'Restaurant ABC',
  date: '2026-03-15',
  receipt_url: 'https://storage.example.com/receipts/abc.jpg',
  trip_id: 'trip_456',  // Link to trip
  notes: 'Client dinner'
});
console.log(`Expense: ${expense.id} | Status: ${expense.status}`);
```

### Step 2: Get Expense Reports
```typescript
const report = await client.reports.expenses({
  department: 'engineering',
  period: 'last_month',
  group_by: 'category'
});
report.categories.forEach(c =>
  console.log(`${c.name}: $${c.total} (${c.count} expenses)`)
);
console.log(`Total: $${report.total}`);
```

### Step 3: Policy Compliance Check
```typescript
const compliance = await client.policy.check({
  department: 'engineering',
  period: 'last_quarter'
});
console.log(`In-policy: ${compliance.in_policy_pct}%`);
console.log(`Out-of-policy: ${compliance.violations.length} violations`);
compliance.violations.forEach(v =>
  console.log(`  ${v.employee}: ${v.reason} ($${v.amount})`)
);
```

## Resources
- [Navan Docs](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-common-errors`.
