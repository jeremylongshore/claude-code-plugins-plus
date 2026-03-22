---
name: finta-upgrade-migration
description: |
  Handle Finta platform updates and data migration.
  Trigger with phrases like "finta upgrade", "finta migration".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Upgrade & Migration

## Plan Upgrades

Upgrade from Free to Pro at Settings > Billing for unlimited deal rooms, payment collection, and full Aurora AI access.

## Data Export for Migration

1. Export pipeline as CSV from Pipeline > Export
2. Export investor contacts
3. Download deal room documents
4. Save investor update history

## Importing from Other CRMs

Moving from Affinity, Streak, or spreadsheets:
1. Export from existing tool as CSV
2. Map columns to Finta fields (Name, Firm, Email, Stage)
3. Import via Finta CSV import

## Resources

- [Finta Changelog](https://www.trustfinta.com/change-log)

## Next Steps

For CI, see `finta-ci-integration`.
