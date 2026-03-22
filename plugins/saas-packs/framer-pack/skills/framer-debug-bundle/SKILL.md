---
name: framer-debug-bundle
description: |
  Collect Framer debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Framer problems.
  Trigger with phrases like "framer debug", "framer support bundle",
  "collect framer logs", "framer diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Debug Bundle

## Overview

Collect diagnostic information for Framer plugin or Server API issues including package versions, API connectivity, and configuration.

## Instructions

### Step 1: Create Debug Bundle

```bash
#!/bin/bash
BUNDLE="framer-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

echo "=== Framer Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Date: $(date -u)" >> "$BUNDLE/summary.txt"

# Runtime
echo "--- Runtime ---" >> "$BUNDLE/summary.txt"
node --version >> "$BUNDLE/summary.txt" 2>&1
npm --version >> "$BUNDLE/summary.txt" 2>&1

# Packages
echo "--- Packages ---" >> "$BUNDLE/summary.txt"
npm list framer-plugin framer-api framer 2>/dev/null >> "$BUNDLE/summary.txt"

# Credentials (presence only)
echo "--- Config ---" >> "$BUNDLE/summary.txt"
echo "FRAMER_API_KEY: ${FRAMER_API_KEY:+[SET]}" >> "$BUNDLE/summary.txt"
echo "FRAMER_SITE_ID: ${FRAMER_SITE_ID:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity
echo "--- API Test ---" >> "$BUNDLE/summary.txt"
curl -s -o /dev/null -w "Framer API: HTTP %{http_code}\n" https://api.framer.com/health >> "$BUNDLE/summary.txt" 2>&1

# Vite config
cp vite.config.ts "$BUNDLE/" 2>/dev/null
cp tsconfig.json "$BUNDLE/" 2>/dev/null
cp package.json "$BUNDLE/" 2>/dev/null

# Bundle
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Output

- `summary.txt` with runtime, packages, connectivity
- Configuration files (non-sensitive)
- Compressed archive for support

## Resources

- [Framer Support](https://www.framer.com/support/)
- [Framer Changelog](https://www.framer.com/developers/changelog)

## Next Steps

For rate limit issues, see `framer-rate-limits`.
