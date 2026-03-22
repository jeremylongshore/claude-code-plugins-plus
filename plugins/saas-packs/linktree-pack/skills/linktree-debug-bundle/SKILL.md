---
name: linktree-debug-bundle
description: |
  Debug Bundle for Linktree.
  Trigger: "linktree debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, linktree, social]
compatible-with: claude-code
---

# Linktree Debug Bundle

## Debug Script
```bash
#!/bin/bash
BUNDLE="linktree-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "LINKTREE_API_KEY: ${LINKTREE_API_KEY:+SET}" > "$BUNDLE/summary.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/summary.txt"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources
- [Linktree Support](https://linktr.ee/marketplace/developer)

## Next Steps
See `linktree-rate-limits`.
