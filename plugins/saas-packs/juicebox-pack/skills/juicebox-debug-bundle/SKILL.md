---
name: juicebox-debug-bundle
description: |
  Collect Juicebox debug evidence.
  Trigger: "juicebox debug", "juicebox support ticket".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Debug Bundle

## Debug Script
```bash
#!/bin/bash
BUNDLE="jb-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"
echo "JUICEBOX_API_KEY: ${JUICEBOX_API_KEY:+SET}" > "$BUNDLE/summary.txt"
curl -s -w "\nHTTP %{http_code}" -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/health >> "$BUNDLE/summary.txt"
curl -s -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/account/quota > "$BUNDLE/quota.json"
tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Key Headers
| Header | Use |
|--------|-----|
| `X-Request-Id` | Support reference |
| `X-RateLimit-Remaining` | Requests left |
| `Retry-After` | Wait time on 429 |

## Resources
- [Juicebox Support](https://docs.juicebox.work/support)

## Next Steps
See `juicebox-rate-limits`.
