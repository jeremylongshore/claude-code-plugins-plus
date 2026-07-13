---
name: hootsuite-debug-bundle
description: 'Collect Hootsuite debug evidence for support tickets and troubleshooting.

  Use when encountering persistent issues, preparing support tickets,

  or collecting diagnostic information for Hootsuite problems.

  Trigger with phrases like "hootsuite debug", "hootsuite support bundle",

  "collect hootsuite logs", "hootsuite diagnostic".

  '
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- hootsuite
- social-media
compatibility: Designed for Claude Code
---
# Hootsuite Debug Bundle

## Overview

Collect Hootsuite API connectivity status, social profile health, scheduled post state, and OAuth token validity into a single diagnostic archive. This bundle helps troubleshoot failed post scheduling, disconnected social accounts, media upload errors, and API authentication problems.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-hootsuite-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Hootsuite Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "HOOTSUITE_API_KEY: ${HOOTSUITE_API_KEY:+[SET]}" >> "$BUNDLE/summary.txt"
echo "HOOTSUITE_ACCESS_TOKEN: ${HOOTSUITE_ACCESS_TOKEN:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity — user profile endpoint
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${HOOTSUITE_ACCESS_TOKEN}" \
  https://platform.hootsuite.com/v1/me 2>/dev/null || echo "000")
echo "API Status: HTTP $HTTP" >> "$BUNDLE/summary.txt"

# User profile and social profiles
curl -s -H "Authorization: Bearer ${HOOTSUITE_ACCESS_TOKEN}" \
  https://platform.hootsuite.com/v1/me > "$BUNDLE/me.json" 2>&1 || true
curl -s -H "Authorization: Bearer ${HOOTSUITE_ACCESS_TOKEN}" \
  https://platform.hootsuite.com/v1/socialProfiles > "$BUNDLE/profiles.json" 2>&1 || true

# Scheduled posts and rate limit headers
curl -s -D "$BUNDLE/rate-headers.txt" -H "Authorization: Bearer ${HOOTSUITE_ACCESS_TOKEN}" \
  "https://platform.hootsuite.com/v1/messages?limit=10&state=SCHEDULED" > "$BUNDLE/scheduled-posts.json" 2>&1 || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-hootsuite-*.tar.gz
cat debug-hootsuite-*/summary.txt                  # Auth + connectivity
jq '.data[] | {id, type, socialNetworkId}' debug-hootsuite-*/profiles.json  # Connected accounts
jq '.data[] | {id, state, scheduledSendTime}' debug-hootsuite-*/scheduled-posts.json
grep -i "ratelimit\|retry" debug-hootsuite-*/rate-headers.txt
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| API returns 401 | `summary.txt` shows HTTP 401 | OAuth token expired; re-authorize via Hootsuite app OAuth flow |
| Social profile disconnected | `profiles.json` shows missing or error-state profile | Re-connect the social account in Hootsuite dashboard > Social Accounts |
| Scheduled post failed | `scheduled-posts.json` shows FAILED state | Check media URLs are accessible; verify profile has posting permissions |
| Rate limited (429) | `rate-headers.txt` shows Retry-After | Reduce scheduling frequency; batch post creation requests |
| Missing profiles | `profiles.json` returns fewer accounts than expected | Check team permissions; verify plan supports connected account count |

## Automated Health Check

```typescript
async function checkHootsuite(): Promise<void> {
  const token = process.env.HOOTSUITE_ACCESS_TOKEN;
  if (!token) { console.error("[FAIL] HOOTSUITE_ACCESS_TOKEN not set"); return; }

  const res = await fetch("https://platform.hootsuite.com/v1/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  console.log(`[${res.ok ? "OK" : "FAIL"}] API: HTTP ${res.status}`);

  if (res.ok) {
    const profiles = await fetch("https://platform.hootsuite.com/v1/socialProfiles", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await profiles.json();
    console.log(`[INFO] Connected profiles: ${data.data?.length ?? 0}`);
  }
}
checkHootsuite();
```

## Resources

- [Hootsuite Status](https://status.hootsuite.com)

## Next Steps

See `hootsuite-common-errors`.
