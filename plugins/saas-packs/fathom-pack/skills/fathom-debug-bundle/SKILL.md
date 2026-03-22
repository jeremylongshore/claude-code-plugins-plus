---
name: fathom-debug-bundle
description: |
  Collect Fathom API diagnostics for support cases.
  Trigger with phrases like "fathom debug", "fathom diagnostics".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Debug Bundle

```bash
#!/bin/bash
BUNDLE="fathom-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

echo "API Key: ${FATHOM_API_KEY:+[SET]}" > "$BUNDLE/summary.txt"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Api-Key: ${FATHOM_API_KEY}" \
  https://api.fathom.ai/external/v1/meetings?limit=1)
echo "API Status: $HTTP" >> "$BUNDLE/summary.txt"

curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/meetings?limit=3" \
  | jq '.meetings[] | {id, title, created_at}' > "$BUNDLE/recent-meetings.json" 2>&1

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Next Steps

For rate limits, see `fathom-rate-limits`.
