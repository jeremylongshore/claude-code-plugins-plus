---
name: grammarly-prod-checklist
description: |
description: |
  
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Production Checklist

## Checklist

### Authentication
- [ ] Client credentials in secrets vault
- [ ] Token refresh logic handles expiry
- [ ] Separate credentials for prod vs dev

### API Integration
- [ ] Text chunking for documents > 100K chars
- [ ] Minimum 30 word validation before API calls
- [ ] Rate limit handling with exponential backoff
- [ ] Error responses logged with request IDs

### Quality Gates
- [ ] Writing score thresholds defined per use case
- [ ] AI detection thresholds configured
- [ ] Plagiarism check timeout handling

### Monitoring
- [ ] API response times tracked
- [ ] Error rates alerting
- [ ] Token refresh failures reported

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

For upgrades, see `grammarly-upgrade-migration`.
