---
name: glean-debug-bundle
description: |
  Collect Glean diagnostic information for support including datasource config, indexing status, and search quality metrics.
  Trigger: "glean debug", "glean support", "glean diagnostic".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Debug Bundle

## Diagnostic Script

```bash
#!/bin/bash
BUNDLE="glean-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

echo "=== Glean Debug Bundle ===" | tee "$BUNDLE/summary.txt"

# Datasource config
curl -s -X POST "https://$GLEAN_DOMAIN/api/index/v1/getdatasourceconfig" \
  -H "Authorization: Bearer $GLEAN_INDEXING_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"datasource":"'$GLEAN_DATASOURCE'"}' > "$BUNDLE/datasource-config.json"

# Test search
curl -s -X POST "https://$GLEAN_DOMAIN/api/client/v1/search" \
  -H "Authorization: Bearer $GLEAN_CLIENT_TOKEN" \
  -H "X-Glean-Auth-Type: BEARER" \
  -H "Content-Type: application/json" \
  -d '{"query":"test","pageSize":1}' > "$BUNDLE/search-test.json"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
