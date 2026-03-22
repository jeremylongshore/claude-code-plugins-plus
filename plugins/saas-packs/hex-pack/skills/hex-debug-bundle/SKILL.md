---
name: hex-debug-bundle
description: |
  Collect Hex debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Hex problems.
  Trigger with phrases like "hex debug", "hex support bundle",
  "collect hex logs", "hex diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex Debug Bundle

## Instructions

```bash
#!/bin/bash
BUNDLE="hex-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "=== Hex Debug ===" | tee "$BUNDLE/summary.txt"
echo "HEX_API_TOKEN: ${HEX_API_TOKEN:+[SET]}" >> "$BUNDLE/summary.txt"

# API test
curl -s -w "\nHTTP %{http_code}" -H "Authorization: Bearer $HEX_API_TOKEN" \
  https://app.hex.tech/api/v1/projects > "$BUNDLE/projects.json" 2>&1

tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources

- [Hex Support](https://learn.hex.tech/docs)
