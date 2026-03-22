---
name: grammarly-debug-bundle
description: |
  Collect Grammarly debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Grammarly problems.
  Trigger with phrases like "grammarly debug", "grammarly support bundle",
  "collect grammarly logs", "grammarly diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Debug Bundle

## Instructions

### Create Debug Bundle

```bash
#!/bin/bash
BUNDLE="grammarly-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

echo "=== Grammarly Debug ===" | tee "$BUNDLE/summary.txt"

# Credential check
echo "CLIENT_ID: ${GRAMMARLY_CLIENT_ID:+[SET]}" >> "$BUNDLE/summary.txt"
echo "ACCESS_TOKEN: ${GRAMMARLY_ACCESS_TOKEN:+[SET]}" >> "$BUNDLE/summary.txt"

# API test
curl -s -w "\nHTTP %{http_code} in %{time_total}s" \
  -H "Authorization: Bearer $GRAMMARLY_ACCESS_TOKEN" \
  -X POST https://api.grammarly.com/ecosystem/api/v2/scores \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a diagnostic test with enough words to meet the minimum thirty word requirement for the Grammarly writing score API."}' \
  > "$BUNDLE/api-test.json" 2>&1

tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources

- [Grammarly Support](https://developer.grammarly.com/docs/support)

## Next Steps

For rate limits, see `grammarly-rate-limits`.
