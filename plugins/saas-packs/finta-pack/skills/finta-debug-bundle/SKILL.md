---
name: finta-debug-bundle
description: |
  Collect Finta diagnostic information for support.
  Trigger with phrases like "finta debug", "finta support".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Debug Bundle

## What to Collect

Since Finta is a web app without a public API, collect:
1. **Browser console errors**: F12 > Console tab > screenshot
2. **Network tab**: F12 > Network > filter for failed requests (red)
3. **Account info**: Plan type, connected integrations
4. **Steps to reproduce**: Exact sequence that causes the issue

## Submit to Support

Contact Finta support via the in-app chat or email with:
- Screenshots of the issue
- Browser and OS version
- Connected integrations status

## Next Steps

For rate limits, see `finta-rate-limits`.
