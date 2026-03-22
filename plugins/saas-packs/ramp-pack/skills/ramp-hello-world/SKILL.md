---
name: ramp-hello-world
description: |
  Ramp hello world — corporate card and expense management API integration.
  Use when working with Ramp for card management, expenses, or accounting sync.
  Trigger with phrases like "ramp hello world", "ramp-hello-world", "corporate card API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ramp, fintech, expenses, corporate-cards]
compatible-with: claude-code, codex, openclaw
---

# Ramp Hello World

## Overview
List cards, get transactions, and check user details using the Ramp API.

## Prerequisites
- Completed `ramp-install-auth` with valid access token

## Instructions

### Step 1: List Virtual Cards
```python
resp = requests.get(f"{BASE}/cards", headers=headers, params={"page_size": 10})
for card in resp.json()["data"]:
    print(f"Card: {card['display_name']} — Limit: ${card['spending_restrictions']['amount']/100:.2f}")
    print(f"  Status: {card['state']}, Last4: {card['last_four']}")
```

### Step 2: Get Recent Transactions
```python
resp = requests.get(f"{BASE}/transactions", headers=headers, params={
    "start_date": "2026-01-01",
    "page_size": 10,
})
for tx in resp.json()["data"]:
    print(f"${tx['amount']/100:.2f} at {tx['merchant_name']} — {tx['sk_category_name']}")
```

### Step 3: List Users
```python
resp = requests.get(f"{BASE}/users", headers=headers, params={"page_size": 10})
for user in resp.json()["data"]:
    print(f"  {user['first_name']} {user['last_name']} — {user['role']}")
```

## Output
- Cards listed with limits and status
- Recent transactions with merchant details
- Users with role information

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty results | No data in sandbox | Create test cards first |
| `403 Forbidden` | Insufficient permissions | Check API app permissions |
| `400 Bad date format` | Wrong date format | Use ISO 8601: YYYY-MM-DD |

## Resources
- [Ramp API Documentation](https://docs.ramp.com/)
- [Cards and Funds](https://docs.ramp.com/developer-api/v1/cards-and-funds)

## Next Steps
Issue virtual cards: `ramp-core-workflow-a`
