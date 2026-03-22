---
name: onenote-debug-bundle
description: |
  Debug Bundle for OneNote.
  Trigger: "onenote debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, onenote, microsoft]
compatible-with: claude-code
---

# OneNote Debug Bundle

## Debug Script
```bash
#!/bin/bash
BUNDLE="onenote-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "MICROSOFT_GRAPH_TOKEN: ${MICROSOFT_GRAPH_TOKEN:+SET}" > "$BUNDLE/summary.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/summary.txt"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources
- [OneNote Support](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)

## Next Steps
See `onenote-rate-limits`.
