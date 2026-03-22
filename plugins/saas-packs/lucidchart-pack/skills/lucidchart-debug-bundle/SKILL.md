---
name: lucidchart-debug-bundle
description: |
  Debug Bundle for Lucidchart.
  Trigger: "lucidchart debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, lucidchart, diagramming]
compatible-with: claude-code
---

# Lucidchart Debug Bundle

## Debug Script
```bash
#!/bin/bash
BUNDLE="lucidchart-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "LUCID_API_KEY: ${LUCID_API_KEY:+SET}" > "$BUNDLE/summary.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/summary.txt"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources
- [Lucidchart Support](https://developer.lucid.co/reference/overview)

## Next Steps
See `lucidchart-rate-limits`.
