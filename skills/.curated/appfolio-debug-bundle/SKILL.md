---
name: appfolio-debug-bundle
description: 'Collect AppFolio API debug evidence for support tickets.

  Trigger: "appfolio debug".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.5.0
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

## Instructions

1. Obtain incident approval and define the affected time window, portfolio, and
   safe-read probes; do not collect tenant, lease, payment, or raw log bodies
   merely because they are available.
2. Create the bundle with redacted configuration state, provider status/latency,
   rate-limit headers, and package versions only; keep credentials out of argv.
3. Review every file before sharing, encrypt or use the approved support channel
   for the archive, and delete the local copy according to the incident policy.
4. If evidence requires sensitive records, stop and obtain a separately approved
   minimal export rather than expanding this general-purpose debug bundle.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-appfolio-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

NETRC_FILE="$(mktemp)"
trap 'rm -f "$NETRC_FILE"' EXIT
chmod 600 "$NETRC_FILE"
APPFOLIO_HOST="${APPFOLIO_BASE_URL#https://}"
APPFOLIO_HOST="${APPFOLIO_HOST%%/*}"
printf 'machine %s login %s password %s\n' "$APPFOLIO_HOST" \
  "$APPFOLIO_CLIENT_ID" "$APPFOLIO_CLIENT_SECRET" > "$NETRC_FILE"

probe() {
  endpoint="$1"
  curl -s -o /dev/null -w 'HTTP %{http_code} in %{time_total}s\n' \
    --netrc-file "$NETRC_FILE" "${APPFOLIO_BASE_URL}/${endpoint}?per_page=1" \
    || printf 'UNREACHABLE\n'
}

# Environment check
echo "=== Environment ===" > "$BUNDLE/environment.txt"
echo "Base URL: ${APPFOLIO_BASE_URL:-NOT SET}" >> "$BUNDLE/environment.txt"
echo "Client ID: ${APPFOLIO_CLIENT_ID:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Client Secret: ${APPFOLIO_CLIENT_SECRET:+SET (redacted)}" >> "$BUNDLE/environment.txt"
echo "Node: $(node -v 2>/dev/null || echo 'not installed')" >> "$BUNDLE/environment.txt"
echo "Timestamp: $(date -u)" >> "$BUNDLE/environment.txt"

# API connectivity metadata only — never write API bodies into this bundle.
echo "=== API Health ===" > "$BUNDLE/api-health.txt"
probe properties >> "$BUNDLE/api-health.txt"

# Work orders endpoint probe
echo "=== Work Orders ===" > "$BUNDLE/work-orders.txt"
probe work_orders >> "$BUNDLE/work-orders.txt"

# Tenant endpoint probe
echo "=== Tenants ===" > "$BUNDLE/tenants.txt"
probe tenants >> "$BUNDLE/tenants.txt"

# Log inventory only; raw logs may contain tenant and financial data.
echo "=== Log Inventory ===" > "$BUNDLE/app-logs.txt"
find /var/log/appfolio-sync -maxdepth 1 -type f -printf '%f %s bytes\n' 2>/dev/null \
  || echo "No sync logs found" >> "$BUNDLE/app-logs.txt"

# Rate limit headers
echo "=== Rate Limits ===" > "$BUNDLE/rate-limits.txt"
curl -sI --netrc-file "$NETRC_FILE" \
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

## Output

- A reviewable, redacted bundle of configuration presence, endpoint status and
  latency, rate-limit headers, log inventory, and dependency metadata
- A support handoff receipt that names the incident scope and sensitive-data
  exclusions rather than packaging tenant, payment, or raw application records
- A fail-closed decision when the required evidence cannot be collected safely

## Error Handling

Treat a probe failure as evidence of a failed probe, not permission to capture
larger responses or bypass credential controls. For `401`/`403`, verify the
managed client configuration with the credential owner; for `429`, preserve the
rate headers and pause further probes; for `5xx` or timeout, collect only the
redacted timing/status evidence and check the provider status page. If support
needs a specific tenant or payment record, use a separately approved minimal
export with its own retention and access controls.

## Examples

For a production sync timeout, create a bundle covering the affected time
window and one properties safe-read probe. Confirm it contains status/latency,
rate headers, dependency versions, and log file metadata—but no response body,
credential, tenant, or financial data. Review the archive before uploading it
to the approved encrypted support channel. If review finds a raw payload or
secret, delete the archive, rotate as appropriate, and regenerate a minimized
bundle before escalation.

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
