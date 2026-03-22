---
name: fathom-prod-checklist
description: |
  Production readiness checklist for Fathom API integrations.
  Trigger with phrases like "fathom production", "fathom go-live", "fathom checklist".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Production Checklist

- [ ] API key stored in secrets manager
- [ ] Rate limiting implemented (60 req/min)
- [ ] Error handling for 401, 404, 429
- [ ] Webhook endpoint configured and tested
- [ ] Meeting data PII handling documented
- [ ] Transcript processing handles empty/missing data
- [ ] Monitoring for failed API calls
- [ ] Backup webhook URL configured
- [ ] OAuth app registered (if building public integration)

## Next Steps

For upgrades, see `fathom-upgrade-migration`.
