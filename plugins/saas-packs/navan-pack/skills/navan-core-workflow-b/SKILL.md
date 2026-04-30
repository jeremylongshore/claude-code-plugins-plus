---
name: navan-core-workflow-b
description: 'Manage Navan expense reporting, transaction data, and ERP synchronization.

  Use when building expense pipelines, automating approval workflows, or syncing transactions
  to accounting systems.

  Trigger with "navan expense management", "navan expense workflow", "navan transaction
  sync".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan — Expense Management

## Overview

This skill covers the Navan expense reporting workflow through the REST API. The Expense Transaction API requires separate enablement from Navan support — it is not available by default. Once enabled, you can retrieve transaction data incrementally (the TRANSACTION table is append-only, unlike BOOKING which re-imports weekly). This skill provides patterns for expense data retrieval, approval workflow automation, and synchronization with ERP systems including NetSuite, Sage Intacct, Xero, and QuickBooks.

## Prerequisites

- Navan account with OAuth 2.0 API credentials (see `navan-install-auth`)
- Expense Transaction API enabled by Navan support (submit request via help center)
- For ERP sync: active integration configured in Navan Admin > Integrations
- Environment variables: `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`, `NAVAN_BASE_URL`
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Request Expense API Enablement

The Expense Transaction API is not self-service. To enable it:

1. Navigate to [Navan Help Center](https://app.navan.com/app/helpcenter)
2. Submit a support request for "Expense Transaction API access"
3. Provide your company ID and the OAuth client_id that needs access
4. Navan support will enable the expense endpoints (typically 1-3 business days)
5. Verify access by calling the transaction endpoint after enablement

### Step 2: Authenticate

```typescript
const tokenRes = await fetch(`${process.env.NAVAN_BASE_URL}/ta-auth/oauth/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: process.env.NAVAN_CLIENT_ID!,
    client_secret: process.env.NAVAN_CLIENT_SECRET!,
  }),
});
const { access_token } = await tokenRes.json();
const headers = { Authorization: `Bearer ${access_token}` };
```

### Step 3: Retrieve Expense Transactions

```typescript
// Expense transactions are incremental — use date ranges for efficient pulls
// Note: The bookings endpoint is the primary data endpoint; expense data
// may require separate enablement from Navan support
const txnRes = await fetch(
  `${process.env.NAVAN_BASE_URL}/v1/bookings` +
  `?createdFrom=2026-03-01&createdTo=2026-03-31&page=0&size=50`,
  { headers }
);
const { data: transactions } = await txnRes.json();

transactions.forEach((txn: any) => {
  console.log(`ID: ${txn.transaction_id}`);
  console.log(`  Employee: ${txn.employee_name} (${txn.employee_id})`);
  console.log(`  Amount: ${txn.currency} ${txn.amount}`);
  console.log(`  Category: ${txn.category}`);
  console.log(`  Status: ${txn.approval_status}`);
  console.log(`  Merchant: ${txn.merchant_name}`);
});
```

### Step 4: Build Approval Workflow Logic

```typescript
// Route expenses based on amount thresholds and department policies
interface ApprovalRule {
  maxAmount: number;
  approverLevel: 'manager' | 'director' | 'vp' | 'cfo';
}

const approvalRules: ApprovalRule[] = [
  { maxAmount: 100, approverLevel: 'manager' },
  { maxAmount: 500, approverLevel: 'director' },
  { maxAmount: 5000, approverLevel: 'vp' },
  { maxAmount: Infinity, approverLevel: 'cfo' },
];

function getRequiredApprover(amount: number): string {
  const rule = approvalRules.find(r => amount <= r.maxAmount);
  return rule?.approverLevel ?? 'cfo';
}

// Process pending transactions
const pending = transactions.filter(
  (t: any) => t.approval_status === 'pending'
);
for (const txn of pending) {
  const approver = getRequiredApprover(txn.amount);
  console.log(`${txn.transaction_id}: $${txn.amount} -> route to ${approver}`);
}
```

### Step 5: Map Expense Categories to GL Codes

```typescript
// Map Navan expense categories to your chart of accounts
const categoryToGL: Record<string, string> = {
  'airfare': '6200-10',
  'hotel': '6200-20',
  'meals': '6200-30',
  'ground_transport': '6200-40',
  'car_rental': '6200-50',
  'other_travel': '6200-90',
  'office_supplies': '6300-10',
  'software': '6400-10',
};

function mapToGLCode(category: string): string {
  return categoryToGL[category] ?? '6900-00'; // default: miscellaneous
}

transactions.forEach((txn: any) => {
  const gl = mapToGLCode(txn.category);
  console.log(`${txn.transaction_id}: ${txn.category} -> GL ${gl}`);
});
```

### Step 6: ERP Sync Pattern (NetSuite Example)

```typescript
// Build journal entry payload for NetSuite sync
// Navan integrates natively with NetSuite, Sage Intacct, Xero, QuickBooks
const journalEntries = transactions.map((txn: any) => ({
  tranDate: txn.transaction_date,
  subsidiary: txn.cost_center,
  lineItems: [
    {
      account: mapToGLCode(txn.category),
      debit: txn.amount,
      memo: `Navan: ${txn.merchant_name} - ${txn.employee_name}`,
      department: txn.department,
      class: txn.project_code,
    },
    {
      account: '2000-00', // Accounts Payable
      credit: txn.amount,
      memo: `Navan expense reimbursement`,
    },
  ],
}));

console.log(`Prepared ${journalEntries.length} journal entries for NetSuite sync`);
```

## Output

Successful execution produces:
- Expense transaction records with employee, amount, category, and approval status
- Approval routing decisions based on configurable threshold rules
- GL-coded transaction records ready for ERP import
- Journal entry payloads formatted for target accounting system

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| Unauthorized | 401 | Expired or invalid bearer token | Re-authenticate via POST /ta-auth/oauth/token |
| Forbidden | 403 | Expense API not enabled | Contact Navan support to enable Expense Transaction API |
| Bad Request | 400 | Invalid date range or parameters | Verify date format is YYYY-MM-DD |
| Rate Limited | 429 | Too many requests | Implement exponential backoff (start at 1s) |
| Server Error | 500 | Navan platform issue | Retry with backoff; check Navan status page |
| No Data | 200 (empty) | No transactions in date range | Widen date range or verify expense API enablement |

## Examples

**Python — Expense retrieval with category breakdown:**

```python
import requests
import os
from collections import defaultdict

base_url = os.environ.get('NAVAN_BASE_URL', 'https://api.navan.com')
auth = requests.post(f'{base_url}/ta-auth/oauth/token', data={
    'grant_type': 'client_credentials',
    'client_id': os.environ['NAVAN_CLIENT_ID'],
    'client_secret': os.environ['NAVAN_CLIENT_SECRET'],
})
headers = {'Authorization': f'Bearer {auth.json()["access_token"]}'}

resp = requests.get(
    f'{base_url}/v1/bookings',
    params={'createdFrom': '2026-03-01', 'createdTo': '2026-03-31', 'page': 0, 'size': 50},
    headers=headers,
).json()
txns = resp['data']

# Category breakdown
by_category = defaultdict(float)
for t in txns:
    by_category[t['category']] += t['amount']
for cat, total in sorted(by_category.items(), key=lambda x: -x[1]):
    print(f'  {cat}: ${total:,.2f}')
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Support and documentation
- [Navan Integrations](https://navan.com/integrations) — NetSuite, Sage Intacct, Xero, QuickBooks connectors
- [Booking Data Integration](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/booking-data-integration) — Data export configuration

## Next Steps

After setting up expense management, proceed to `navan-data-sync` for incremental sync strategies or `navan-entity-management` for user and department configuration.
