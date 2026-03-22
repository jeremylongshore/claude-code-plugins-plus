---
name: openevidence-debug-bundle
description: |
  Debug Bundle for OpenEvidence.
  Trigger: "openevidence debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Debug Bundle

## Debug Script
```bash
#!/bin/bash
BUNDLE="openevidence-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "OPENEVIDENCE_API_KEY: ${OPENEVIDENCE_API_KEY:+SET}" > "$BUNDLE/summary.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/summary.txt"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources
- [OpenEvidence Support](https://www.openevidence.com)

## Next Steps
See `openevidence-rate-limits`.
