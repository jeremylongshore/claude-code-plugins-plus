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

## Overview

This debug bundle collects diagnostic evidence from Linktree link-in-bio API integrations
for troubleshooting profile rendering, link analytics, and webhook delivery issues. It
captures OAuth token validity, profile metadata retrieval, individual link status checks,
click analytics availability, and webhook endpoint health. The resulting tarball gives
support engineers the data needed to diagnose broken links, missing analytics events,
profile sync failures, and API permission issues without requiring Linktree admin access.

## Prerequisites

- `curl`, `jq`, `tar` installed
- `LINKTREE_API_KEY` set (OAuth bearer token from Linktree developer portal)

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-linktree-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Environment ===" > "$BUNDLE/environment.txt"
echo "API Key: ${LINKTREE_API_KEY:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Node: $(node -v 2>/dev/null || echo 'not installed')" >> "$BUNDLE/environment.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/environment.txt"

# API connectivity — user profile
echo "=== API Health ===" > "$BUNDLE/api-health.txt"
curl -sf -o "$BUNDLE/api-health.txt" -w "HTTP %{http_code} in %{time_total}s\n" \
  -H "Authorization: Bearer ${LINKTREE_API_KEY}" \
  "https://api.linktree.com/v1/user" 2>&1 || echo "UNREACHABLE" > "$BUNDLE/api-health.txt"

# Profile links enumeration
echo "=== Links ===" > "$BUNDLE/links.json"
curl -sf -H "Authorization: Bearer ${LINKTREE_API_KEY}" \
  "https://api.linktree.com/v1/links" \
  >> "$BUNDLE/links.json" 2>&1 || echo '{"error":"FAILED"}' > "$BUNDLE/links.json"

# Link click analytics (last 7 days)
echo "=== Analytics ===" > "$BUNDLE/analytics.json"
curl -sf -H "Authorization: Bearer ${LINKTREE_API_KEY}" \
  "https://api.linktree.com/v1/analytics?period=7d" \
  >> "$BUNDLE/analytics.json" 2>&1 || echo '{"error":"ANALYTICS_FAILED"}' > "$BUNDLE/analytics.json"

# Recent logs
echo "=== Recent Logs ===" > "$BUNDLE/app-logs.txt"
tail -100 /var/log/linktree-sync/*.log >> "$BUNDLE/app-logs.txt" 2>/dev/null || echo "No sync logs found" >> "$BUNDLE/app-logs.txt"

# Rate limit status
echo "=== Rate Limits ===" > "$BUNDLE/rate-limits.txt"
curl -sI -H "Authorization: Bearer ${LINKTREE_API_KEY}" \
  "https://api.linktree.com/v1/user" 2>/dev/null | grep -i "x-rate\|retry-after\|x-ratelimit" >> "$BUNDLE/rate-limits.txt" || echo "No rate limit headers" >> "$BUNDLE/rate-limits.txt"

# Package versions
echo "=== Dependencies ===" > "$BUNDLE/deps.txt"
npm ls 2>/dev/null | grep -i linktree >> "$BUNDLE/deps.txt" || echo "No Linktree npm packages found" >> "$BUNDLE/deps.txt"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-linktree-*.tar.gz
cat debug-linktree-*/environment.txt     # Verify API key is set
cat debug-linktree-*/api-health.txt      # Check HTTP status and latency
jq '.links | length' debug-linktree-*/links.json       # Count active links
jq '.totalClicks' debug-linktree-*/analytics.json      # Verify analytics data
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| 401 Unauthorized | `environment.txt` shows key NOT SET | Generate new API key in Linktree Developer Settings |
| Profile returns but links empty | `links.json` has empty array | Ensure links are published (not draft); check link visibility settings |
| Analytics returns 403 | `analytics.json` shows permission error | Analytics API requires Pro plan or higher; upgrade Linktree subscription |
| Click counts stuck at zero | `analytics.json` shows `totalClicks: 0` | Analytics lag up to 24h; verify links have `tracking` enabled |
| 429 rate limited | `rate-limits.txt` shows retry-after | Linktree allows 100 req/min; implement request queuing with backoff |
| Webhook not firing | App logs show no delivery attempts | Verify webhook URL in Linktree admin; check SSL cert validity on receiving endpoint |

## Automated Health Check

```typescript
async function checkLinktreeHealth(): Promise<{
  status: string;
  latencyMs: number;
  profileOk: boolean;
  linkCount: number;
  analyticsAvailable: boolean;
}> {
  const apiKey = process.env.LINKTREE_API_KEY;
  const headers = { Authorization: `Bearer ${apiKey}` };
  const start = Date.now();

  const profileRes = await fetch("https://api.linktree.com/v1/user", { headers });
  const linksRes = await fetch("https://api.linktree.com/v1/links", { headers });
  const analyticsRes = await fetch("https://api.linktree.com/v1/analytics?period=7d", { headers });

  let linkCount = 0;
  if (linksRes.ok) {
    const data = await linksRes.json();
    linkCount = data.links?.length ?? 0;
  }

  return {
    status: profileRes.ok ? "healthy" : "degraded",
    latencyMs: Date.now() - start,
    profileOk: profileRes.ok,
    linkCount,
    analyticsAvailable: analyticsRes.ok,
  };
}
```

## Resources

- [Linktree Developer Docs](https://linktr.ee/marketplace/developer)
- [Linktree Status Page](https://status.linktr.ee)
- [Linktree API Changelog](https://developers.linktr.ee/changelog)

## Next Steps

See `linktree-rate-limits`.
