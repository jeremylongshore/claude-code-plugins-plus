---
name: oraclecloud-debug-bundle
description: |
  Debug Bundle for Oracle Cloud.
  Trigger: "oraclecloud debug bundle".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Debug Bundle

## Debug Script
```bash
#!/bin/bash
BUNDLE="oraclecloud-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "OCI_CONFIG_FILE: ${OCI_CONFIG_FILE:+SET}" > "$BUNDLE/summary.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/summary.txt"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources
- [Oracle Cloud Support](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-rate-limits`.
