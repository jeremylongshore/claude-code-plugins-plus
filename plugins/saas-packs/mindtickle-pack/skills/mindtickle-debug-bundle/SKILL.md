---
name: mindtickle-debug-bundle
description: |
  Debug Bundle for MindTickle.
  Trigger: "mindtickle debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Debug Bundle

## Debug Script
```bash
#!/bin/bash
BUNDLE="mindtickle-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "MINDTICKLE_API_KEY: ${MINDTICKLE_API_KEY:+SET}" > "$BUNDLE/summary.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/summary.txt"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources
- [MindTickle Support](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-rate-limits`.
