---
name: appfolio-debug-bundle
description: 'Collect AppFolio API debug evidence for support tickets.

  Trigger: "appfolio debug".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio Debug Bundle

## Overview

This debug bundle collects diagnostic evidence from AppFolio property management API integrations
for support escalation and root cause analysis. It captures API connectivity against the
properties, tenants, and work orders endpoints, authentication status using client credential
pairs, recent error logs from integration pipelines, and SDK version information. The resulting
tarball gives support engineers everything they need to diagnose connectivity failures, auth
rejections, and data sync issues without requiring live access to your environment.

## Prerequisites

- `curl`, `jq`, `tar` installed
- `APPFOLIO_CLIENT_ID` and `APPFOLIO_CLIENT_SECRET` configured (basic auth pair)
- `APPFOLIO_BASE_URL` set to your Stack API base (e.g., `https://yourcompany.appfolio.com/api/v1`)

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-appfolio-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Environment ===" > "$BUNDLE/environment.txt"
echo "Base URL: ${APPFOLIO_BASE_URL:-NOT SET}" >> "$BUNDLE/environment.txt"
echo "Client ID: ${APPFOLIO_CLIENT_ID:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Client Secret: ${APPFOLIO_CLIENT_SECRET:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Node: $(node -v 2>/dev/null || echo 'not installed')" >> "$BUNDLE/environment.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/environment.txt"

# API connectivity — properties endpoint
echo "=== API Health ===" > "$BUNDLE/api-health.txt"
curl -sf -o "$BUNDLE/api-health.txt" -w "HTTP %{http_code} in %{time_total}s\n" \
  -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" \
  "${APPFOLIO_BASE_URL}/properties?per_page=1" 2>&1 || echo "UNREACHABLE" > "$BUNDLE/api-health.txt"

# Work orders endpoint probe
echo "=== Work Orders ===" > "$BUNDLE/work-orders.txt"
curl -sf -w "HTTP %{http_code}\n" \
  -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" \
  "${APPFOLIO_BASE_URL}/work_orders?per_page=1" >> "$BUNDLE/work-orders.txt" 2>&1 || echo "FAILED" >> "$BUNDLE/work-orders.txt"

# Tenant endpoint probe
echo "=== Tenants ===" > "$BUNDLE/tenants.txt"
curl -sf -w "HTTP %{http_code}\n" \
  -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" \
  "${APPFOLIO_BASE_URL}/tenants?per_page=1" >> "$BUNDLE/tenants.txt" 2>&1 || echo "FAILED" >> "$BUNDLE/tenants.txt"

# Recent integration logs
echo "=== Recent Logs ===" > "$BUNDLE/app-logs.txt"
tail -100 /var/log/appfolio-sync/*.log >> "$BUNDLE/app-logs.txt" 2>/dev/null || echo "No sync logs found" >> "$BUNDLE/app-logs.txt"

# Rate limit headers
echo "=== Rate Limits ===" > "$BUNDLE/rate-limits.txt"
curl -sI -u "${APPFOLIO_CLIENT_ID}:${APPFOLIO_CLIENT_SECRET}" \
  "${APPFOLIO_BASE_URL}/properties?per_page=1" 2>/dev/null | grep -i "x-rate\|retry-after\|x-ratelimit" >> "$BUNDLE/rate-limits.txt" || echo "No rate limit headers" >> "$BUNDLE/rate-limits.txt"

# Package versions
echo "=== Dependencies ===" > "$BUNDLE/deps.txt"
npm ls 2>/dev/null | grep -i appfolio >> "$BUNDLE/deps.txt" || echo "No AppFolio npm packages found" >> "$BUNDLE/deps.txt"

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-appfolio-*.tar.gz
cat debug-appfolio-*/environment.txt     # Verify credentials are set
cat debug-appfolio-*/api-health.txt      # Check HTTP status and latency
cat debug-appfolio-*/rate-limits.txt     # Confirm not throttled
jq '.errors' debug-appfolio-*/work-orders.txt 2>/dev/null  # Parse error payloads
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| 401 on all endpoints | `environment.txt` shows client ID/secret NOT SET | Set `APPFOLIO_CLIENT_ID` and `APPFOLIO_CLIENT_SECRET` in env |
| 403 Forbidden on tenants | `tenants.txt` HTTP 403 | Stack API scope missing; request tenant read permission in AppFolio partner portal |
| 429 Too Many Requests | `rate-limits.txt` shows retry-after header | Back off and implement exponential retry; AppFolio allows 120 req/min |
| Timeout on work orders | `api-health.txt` shows time > 30s | Reduce `per_page` parameter; filter by `updated_since` to narrow result set |
| Empty property list | `api-health.txt` returns `[]` | Verify `APPFOLIO_BASE_URL` points to correct portfolio; check property group filters |
| SSL certificate error | `api-health.txt` shows curl SSL error | Update CA bundle: `sudo update-ca-certificates`; check proxy settings |

## Automated Health Check

```typescript
async function checkAppFolioHealth(): Promise<{
  status: string;
  latencyMs: number;
  endpoints: Record<string, number>;
}> {
  const baseUrl = process.env.APPFOLIO_BASE_URL;
  const creds = Buffer.from(
    `${process.env.APPFOLIO_CLIENT_ID}:${process.env.APPFOLIO_CLIENT_SECRET}`
  ).toString("base64");
  const headers = { Authorization: `Basic ${creds}` };
  const endpoints = ["properties", "tenants", "work_orders"];
  const results: Record<string, number> = {};
  const start = Date.now();
  for (const ep of endpoints) {
    const res = await fetch(`${baseUrl}/${ep}?per_page=1`, { headers });
    results[ep] = res.status;
  }
  return {
    status: Object.values(results).every((s) => s === 200) ? "healthy" : "degraded",
    latencyMs: Date.now() - start,
    endpoints: results,
  };
}
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Status](https://status.appfolio.com)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)

## Next Steps

See `appfolio-rate-limits`.
