---
name: fondo-debug-bundle
description: 'Collect diagnostic information for Fondo support including integration
  status,

  transaction discrepancies, and financial data reconciliation issues.

  Trigger: "fondo debug", "fondo support", "fondo diagnostic", "fondo reconciliation".

  '
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- accounting
- fondo
compatibility: Designed for Claude Code
---
# Fondo Debug Bundle

## Overview

Collect Fondo API connectivity status, filing compliance state, integration health, and accounting sync diagnostics into a single archive for Fondo support tickets. This bundle helps troubleshoot bank connection failures, reconciliation discrepancies, R&D credit calculation issues, and tax filing errors.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-fondo-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Fondo Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "FONDO_API_KEY: ${FONDO_API_KEY:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${FONDO_API_KEY}" \
  https://api.fondo.com/v1/compliance/status 2>/dev/null || echo "000")
echo "API Status: HTTP $HTTP" >> "$BUNDLE/summary.txt"

# Compliance and filing status
curl -s -H "Authorization: Bearer ${FONDO_API_KEY}" \
  "https://api.fondo.com/v1/compliance/status" \
  > "$BUNDLE/compliance-status.json" 2>&1 || true

# Integration health (bank, payroll connections)
curl -s -H "Authorization: Bearer ${FONDO_API_KEY}" \
  "https://api.fondo.com/v1/integrations" \
  > "$BUNDLE/integrations.json" 2>&1 || true

# Recent filings and rate limits
curl -s -H "Authorization: Bearer ${FONDO_API_KEY}" \
  "https://api.fondo.com/v1/filings?limit=5" > "$BUNDLE/recent-filings.json" 2>&1 || true
curl -s -D "$BUNDLE/rate-headers.txt" -o /dev/null \
  -H "Authorization: Bearer ${FONDO_API_KEY}" \
  https://api.fondo.com/v1/compliance/status 2>/dev/null || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-fondo-*.tar.gz
cat debug-fondo-*/summary.txt                      # Auth + connectivity
jq '.integrations[] | {name, status}' debug-fondo-*/integrations.json  # Bank/payroll health
jq '.[] | {type, status, due_date}' debug-fondo-*/recent-filings.json  # Filing deadlines
grep -i "ratelimit\|retry" debug-fondo-*/rate-headers.txt
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| API returns 401 | `summary.txt` shows HTTP 401 | Regenerate API key in Fondo dashboard > Settings > API |
| Bank connection expired | `integrations.json` shows disconnected status | Re-authenticate bank via Fondo dashboard > Integrations |
| Filing shows overdue | `recent-filings.json` has past due_date | Contact Fondo support immediately; file extension if deadline approaching |
| R&D credit mismatch | `compliance-status.json` shows calculation warnings | Verify employee R&D classifications; reconcile payroll provider totals |
| Transaction sync gap | `integrations.json` shows stale last_sync date | Disconnect and reconnect the bank integration; check for institution outages |

## Automated Health Check

```typescript
async function checkFondo(): Promise<void> {
  const key = process.env.FONDO_API_KEY;
  if (!key) { console.error("[FAIL] FONDO_API_KEY not set"); return; }

  const res = await fetch("https://api.fondo.com/v1/compliance/status", {
    headers: { Authorization: `Bearer ${key}` },
  });
  console.log(`[${res.ok ? "OK" : "FAIL"}] API: HTTP ${res.status}`);

  if (res.ok) {
    const data = await res.json();
    console.log(`[INFO] Compliance status: ${data.status ?? "unknown"}`);
  }
  const remaining = res.headers.get("x-ratelimit-remaining");
  if (remaining) console.log(`[INFO] Rate limit remaining: ${remaining}`);
}
checkFondo();
```

## Resources

- [Fondo Status](https://status.fondo.com)

## Next Steps

See `fondo-common-errors`.
