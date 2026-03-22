---
name: finta-common-errors
description: |
  Diagnose and fix common Finta CRM issues with email sync, deal rooms, and pipeline.
  Trigger with phrases like "finta error", "finta not working", "fix finta".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Common Errors

### 1. Email Sync Stopped Working
**Fix**: Go to Settings > Integrations, disconnect and reconnect Gmail/Outlook OAuth.

### 2. Calendar Events Not Logging
**Fix**: Verify correct calendar is selected. Finta only syncs the primary calendar by default.

### 3. Deal Room Link Not Working
**Fix**: Check if the link expired or access was revoked. Generate a new shareable link.

### 4. CSV Import Fails
**Fix**: Download the Finta CSV template and match column headers exactly. Ensure dates use YYYY-MM-DD format.

### 5. Aurora AI Not Providing Suggestions
**Fix**: Complete all company profile fields (sector, stage, location, raise amount). Aurora needs sufficient context.

### 6. Investor Stage Not Auto-Advancing
**Fix**: Check Settings > Automation rules. Verify email sync is active and tracking the correct inbox.

### 7. Payment Collection Failed
**Fix**: Verify Stripe integration is connected. Check that the payment link amount matches the commitment.

## Resources

- [Finta Help](https://www.trustfinta.com)

## Next Steps

For diagnostics, see `finta-debug-bundle`.
