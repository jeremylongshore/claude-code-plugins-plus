---
name: navan-debug-bundle
description: |
  Debug Bundle for Navan.
  Trigger: "navan debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan Debug Bundle

## Debug Script
```bash
#!/bin/bash
BUNDLE="navan-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "NAVAN_API_KEY: ${NAVAN_API_KEY:+SET}" > "$BUNDLE/summary.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/summary.txt"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources
- [Navan Support](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-rate-limits`.
