---
name: ramp-core-workflow-b
description: |
  Ramp core workflow b — corporate card and expense management API integration.
  Use when working with Ramp for card management, expenses, or accounting sync.
  Trigger with phrases like "ramp core workflow b", "ramp-core-workflow-b", "corporate card API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ramp, fintech, expenses, corporate-cards]
compatible-with: claude-code, codex, openclaw
---

# Ramp Core Workflow B

## Overview
Manage transactions and expenses: list, categorize, attach receipts, and sync to accounting.

## Prerequisites
- Completed `ramp-core-workflow-a`

## Instructions

### Step 1: List Transactions with Filters
```python
resp = requests.get(f"{BASE}/transactions", headers=headers, params={
    "start_date": "2026-01-01",
    "end_date": "2026-03-22",
    "merchant_name": "Amazon",
    "page_size": 50,
})
transactions = resp.json()["data"]
total = sum(tx["amount"] for tx in transactions)
print(f"Amazon spend: ${total/100:.2f} across {len(transactions)} transactions")
```

### Step 2: Get Transaction Details
```python
tx_id = transactions[0]["id"]
detail = requests.get(f"{BASE}/transactions/{tx_id}", headers=headers)
tx = detail.json()
print(f"Amount: ${tx['amount']/100:.2f}")
print(f"Merchant: {tx['merchant_name']}")
print(f"Category: {tx['sk_category_name']}")
print(f"Card: {tx['card_holder']['first_name']} — last4: {tx['card_last_four']}")
```

### Step 3: Sync to Accounting
```python
# Fetch transactions ready for accounting sync
sync_resp = requests.get(f"{BASE}/accounting/transactions", headers=headers, params={
    "sync_ready": True,
    "page_size": 100,
})
for tx in sync_resp.json()["data"]:
    # Map to your ERP's chart of accounts
    journal_entry = {
        "date": tx["user_transaction_time"],
        "amount": tx["amount"],
        "account": map_category_to_gl(tx["sk_category_name"]),
        "vendor": tx["merchant_name"],
        "external_id": tx["id"],
    }
    sync_to_erp(journal_entry)

# Mark as synced
requests.post(f"{BASE}/accounting/transactions/sync", headers={**headers, "Content-Type": "application/json"}, json={
    "transaction_ids": [tx["id"] for tx in sync_resp.json()["data"]],
})
```

## Output
- Transactions filtered by date, merchant, category
- Detailed transaction data with card holder info
- Accounting sync with GL mapping

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty results | Wrong date range | Check start_date/end_date format |
| Sync conflict | Already synced | Check sync status before re-syncing |
| Missing category | Uncategorized transaction | Use default GL account |

## Resources
- [Ramp API Documentation](https://docs.ramp.com/)
- [Accounting Guide](https://docs.ramp.com/developer-api/v1/guides/accounting)

## Next Steps
Handle events: `ramp-webhooks-events`
