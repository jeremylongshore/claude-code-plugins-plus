---
name: appfolio-common-errors
description: |
  Diagnose and fix common AppFolio API integration errors.
  Trigger: "appfolio error".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio common errors | sed 's/\b\(.\)/\u\1/g'

## Error Reference

| Code | Error | Root Cause | Fix |
|------|-------|-----------|-----|
| `401` | Unauthorized | Invalid client_id/secret | Verify credentials from AppFolio |
| `403` | Forbidden | Not an approved partner | Complete Stack partner application |
| `404` | Not Found | Wrong base URL or endpoint | Use `your-company.appfolio.com/api/v1` |
| `422` | Unprocessable Entity | Missing required fields | Check required fields in API docs |
| `429` | Too Many Requests | Rate limit exceeded | Implement backoff; reduce request rate |
| `500` | Internal Server Error | AppFolio server issue | Retry after delay; check status page |

## Diagnostic Script
```bash
#!/bin/bash
echo "=== AppFolio API Diagnostics ==="
echo -n "Connectivity: "
curl -s -o /dev/null -w "%{http_code}" -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" "${APPFOLIO_BASE_URL}/properties"
echo ""
echo -n "Tenants endpoint: "
curl -s -o /dev/null -w "%{http_code}" -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" "${APPFOLIO_BASE_URL}/tenants"
echo ""
echo "=== Done ==="
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
