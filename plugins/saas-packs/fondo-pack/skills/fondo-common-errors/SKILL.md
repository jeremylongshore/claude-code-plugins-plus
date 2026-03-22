---
name: fondo-common-errors
description: |
  Diagnose and fix common Fondo issues including integration sync failures,
  categorization errors, and R&D credit qualification problems.
  Trigger: "fondo error", "fondo sync issue", "fondo not syncing", "fondo problem".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Common Errors

## Overview

Quick reference for common Fondo platform issues and their resolutions.

## Integration Sync Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Bank transactions not appearing | Plaid connection expired | Dashboard > Integrations > Re-connect bank |
| Gusto data stale | OAuth token expired (90-day limit) | Re-authorize in Integrations |
| Stripe revenue missing | Webhook not configured | Connect Stripe in Dashboard > Integrations |
| Duplicate transactions | Multiple connections to same bank | Remove duplicate in Integrations |
| Payroll amounts wrong | Mid-period payroll change | Notify Fondo CPA via Dashboard > Messages |

## Categorization Errors

| Error | Fix |
|-------|-----|
| Software expense marked as Office | Recategorize in Transactions, Fondo learns |
| Contractor marked as Vendor | Ensure 1099 classification matches in payroll |
| Inter-company transfer as Revenue | Mark as Transfer in Transactions |
| R&D expense not flagged | Tag employee/activity as R&D in Dashboard |

## R&D Credit Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Credit is $0 | No qualifying W-2 employees | Hire W-2 (not 1099) for R&D work |
| Credit lower than expected | Activities not properly documented | Schedule call with Fondo CPA team |
| Ineligible (>$5M revenue) | Exceeds startup threshold | Credit still available, just not payroll offset |
| Missing contractor hours | Time tracking not connected | Upload contractor time logs manually |

## Escalation

1. Dashboard > Messages > New Message (response within 1 business day)
2. Schedule call with CPA team via Dashboard > Support
3. For urgent tax deadlines: email support@fondo.com

## Resources

- [Fondo Help Center](https://fondo.com/blog)
- [R&D Credits FAQ](https://fondo.com/blog/fondo-rd-credits-faq)

## Next Steps

For diagnostic data collection, see `fondo-debug-bundle`.
