---
name: fondo-security-basics
description: |
  Apply security best practices for Fondo including OAuth token management,
  financial data protection, SOC 2 compliance, and access control.
  Trigger: "fondo security", "fondo data protection", "fondo SOC 2", "fondo access control".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Security Basics

## Overview

Security practices for Fondo financial data: manage OAuth connections, protect exported financial data, control team access, and maintain compliance.

## Instructions

### Step 1: Manage OAuth Connections

| Integration | Token Lifetime | Refresh |
|-------------|---------------|---------|
| Gusto | 90 days | Re-authorize in Dashboard |
| QuickBooks | 100 days | Auto-refresh if accessed within window |
| Plaid (banking) | Indefinite | Revoke/re-connect if compromised |
| Stripe | Indefinite | Revoke in Stripe Dashboard if needed |

### Step 2: Protect Financial Exports

```bash
# When downloading Fondo exports locally:
# 1. Never commit to git
echo "*.csv" >> .gitignore
echo "exports/" >> .gitignore

# 2. Encrypt sensitive exports
gpg -c --cipher-algo AES256 general-ledger-2025.csv

# 3. Delete after use
shred -vfz -n 5 general-ledger-2025.csv
```

### Step 3: Team Access Control

| Role | Access | Who |
|------|--------|-----|
| Owner | Full access, billing, integrations | CEO/founder |
| Admin | View/edit financials, answer questions | CFO/finance lead |
| Viewer | View-only reports | Board members, investors |
| CPA | Full access (Fondo team) | Your assigned CPA |

### Security Checklist

- [ ] OAuth connections reviewed quarterly
- [ ] Financial exports never committed to git
- [ ] Team roles follow least-privilege principle
- [ ] Fondo CPA team has NDA on file
- [ ] Bank connections use Plaid (encrypted, not screen-scraping)
- [ ] Two-factor authentication enabled on Fondo account

## Resources

- [Fondo Security](https://fondo.com)
- [Plaid Security](https://plaid.com/safety/)

## Next Steps

For production readiness, see `fondo-prod-checklist`.
