---
name: ramp-core-workflow-a
description: |
  Ramp core workflow a — corporate card and expense management API integration.
  Use when working with Ramp for card management, expenses, or accounting sync.
  Trigger with phrases like "ramp core workflow a", "ramp-core-workflow-a", "corporate card API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ramp, fintech, expenses, corporate-cards]
compatible-with: claude-code, codex, openclaw
---

# Ramp Core Workflow A

## Overview
Issue and manage virtual cards with spending limits, policies, and lifecycle management.

## Prerequisites
- Completed `ramp-hello-world`

## Instructions

### Step 1: Issue a Virtual Card
```python
card = requests.post(f"{BASE}/cards", headers={**headers, "Content-Type": "application/json"}, json={
    "holder_name": "Jane Smith",
    "spending_restrictions": {
        "amount": 50000,        # $500.00 in cents
        "interval": "monthly",  # monthly, yearly, total
    },
    "display_name": "Marketing Software",
    "fulfillment": { "card_type": "virtual" },
})
card.raise_for_status()
card_id = card.json()["id"]
print(f"Virtual card issued: {card_id}")
```

### Step 2: Update Card Limit
```python
requests.patch(f"{BASE}/cards/{card_id}", headers={**headers, "Content-Type": "application/json"}, json={
    "spending_restrictions": {
        "amount": 100000,  # Increase to $1,000
        "interval": "monthly",
    },
})
```

### Step 3: Suspend Card
```python
requests.post(f"{BASE}/cards/{card_id}/suspend", headers=headers)
print(f"Card {card_id} suspended")
```

### Step 4: Terminate Card
```python
requests.post(f"{BASE}/cards/{card_id}/terminate", headers=headers)
print(f"Card {card_id} terminated")
```

## Output
- Virtual card issued with spending limits
- Card limits updated
- Card suspended/terminated

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422 Invalid holder` | User not found | Verify holder is a Ramp user |
| `400 Invalid amount` | Amount not in cents | Multiply dollars by 100 |
| Card already terminated | Cannot modify | Check card state first |

## Resources
- [Virtual Cards API](https://docs.ramp.com/developer-api/v1/virtual-cards)
- [Cards and Funds](https://docs.ramp.com/developer-api/v1/cards-and-funds)

## Next Steps
Transaction management: `ramp-core-workflow-b`
