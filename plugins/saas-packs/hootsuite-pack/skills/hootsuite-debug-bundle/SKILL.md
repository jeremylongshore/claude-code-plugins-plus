---
name: hootsuite-debug-bundle
description: |
  Collect Hootsuite debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Hootsuite problems.
  Trigger with phrases like "hootsuite debug", "hootsuite support bundle",
  "collect hootsuite logs", "hootsuite diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Debug Bundle

## Instructions

### Create Debug Bundle

```bash
#!/bin/bash
BUNDLE="hootsuite-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

echo "=== Hootsuite Debug ===" | tee "$BUNDLE/summary.txt"
echo "Date: $(date -u)" >> "$BUNDLE/summary.txt"

# Credentials check (presence only)
echo "--- Config ---" >> "$BUNDLE/summary.txt"
echo "CLIENT_ID: ${HOOTSUITE_CLIENT_ID:+[SET]}" >> "$BUNDLE/summary.txt"
echo "ACCESS_TOKEN: ${HOOTSUITE_ACCESS_TOKEN:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity
echo "--- API Test ---" >> "$BUNDLE/summary.txt"
curl -s -w "HTTP %{http_code} in %{time_total}s\n" -o "$BUNDLE/me.json" \
  -H "Authorization: Bearer $HOOTSUITE_ACCESS_TOKEN" \
  https://platform.hootsuite.com/v1/me >> "$BUNDLE/summary.txt" 2>&1

# Social profiles
curl -s -o "$BUNDLE/profiles.json" \
  -H "Authorization: Bearer $HOOTSUITE_ACCESS_TOKEN" \
  https://platform.hootsuite.com/v1/socialProfiles 2>/dev/null

tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Output

- API connectivity test results
- Social profile listing
- Token validity check

## Resources

- [Hootsuite Support](https://developer.hootsuite.com)

## Next Steps

For rate limits, see `hootsuite-rate-limits`.
