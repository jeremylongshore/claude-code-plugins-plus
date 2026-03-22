---
name: fondo-debug-bundle
description: |
  Collect diagnostic information for Fondo support including integration status,
  transaction discrepancies, and financial data reconciliation issues.
  Trigger: "fondo debug", "fondo support", "fondo diagnostic", "fondo reconciliation".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, accounting, fondo]
compatible-with: claude-code
---

# Fondo Debug Bundle

## Overview

Collect information needed when contacting Fondo support about sync issues, reconciliation discrepancies, or tax filing problems.

## Diagnostic Checklist

### Integration Status (Dashboard > Integrations)
- [ ] Bank connection status (Connected/Expired/Error)
- [ ] Payroll provider connection status
- [ ] Last successful sync date for each integration
- [ ] Any warning/error messages displayed

### Transaction Reconciliation
- [ ] Date range of missing/wrong transactions
- [ ] Bank statement balance vs Fondo balance for affected month
- [ ] Screenshot of discrepancy (redact account numbers)
- [ ] List of specific transaction IDs affected

### R&D Credit Issues
- [ ] Employee list with R&D classification
- [ ] Qualifying activity descriptions
- [ ] Total R&D payroll amount from payroll provider
- [ ] Fondo's calculated R&D amount

### Tax Filing Issues
- [ ] Filing year and form type (1120, 6765, etc.)
- [ ] EIN and state of incorporation
- [ ] Extension status (filed or not)
- [ ] Deadline date

## When Contacting Support

Include in your message:
1. Company name and Fondo account email
2. Specific issue description with dates
3. What you expected vs what happened
4. Screenshots (with sensitive data redacted)
5. Urgency level (routine / tax deadline / filing error)

## Resources

- [Fondo Support](https://fondo.com)
- Dashboard > Messages > New Message

## Next Steps

For common issue patterns, see `fondo-common-errors`.
