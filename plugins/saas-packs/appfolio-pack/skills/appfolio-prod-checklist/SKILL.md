---
name: appfolio-prod-checklist
description: |
  Production readiness checklist for AppFolio integrations.
  Trigger: "appfolio production checklist".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio prod checklist | sed 's/\b\(.\)/\u\1/g'

## Pre-Launch Checklist
- [ ] API credentials stored in secret manager
- [ ] Rate limiting configured
- [ ] Error handling with retry logic
- [ ] Monitoring and alerting configured
- [ ] Data validation on all API responses
- [ ] Tenant PII handling CCPA compliant
- [ ] Backup strategy for synced data

## Validation Script
```bash
#!/bin/bash
echo "=== AppFolio Production Readiness ==="
echo -n "[$(curl -s -o /dev/null -w "%{http_code}" -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" "${APPFOLIO_BASE_URL}/properties" | grep -q 200 && echo PASS || echo FAIL)] API Connectivity"
echo ""
echo -n "[$([ -n "$APPFOLIO_CLIENT_SECRET" ] && echo PASS || echo FAIL)] Credentials Set"
echo ""
echo "=== Done ==="
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
