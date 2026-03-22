---
name: appfolio-debug-bundle
description: |
  Collect AppFolio API debug evidence for support tickets.
  Trigger: "appfolio debug".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio debug bundle | sed 's/\b\(.\)/\u\1/g'

## Diagnostic Script
```bash
#!/bin/bash
echo "=== AppFolio Debug Bundle $(date -Iseconds) ==="
echo "Base URL: ${APPFOLIO_BASE_URL:-NOT SET}"
echo "Client ID: ${APPFOLIO_CLIENT_ID:+SET (redacted)}"
echo -n "API Health: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" "${APPFOLIO_BASE_URL}/properties")
echo "$HTTP_CODE"
echo -n "Response Time: "
curl -s -o /dev/null -w "%{time_total}s" -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" "${APPFOLIO_BASE_URL}/properties"
echo ""
echo "=== Done ==="
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
