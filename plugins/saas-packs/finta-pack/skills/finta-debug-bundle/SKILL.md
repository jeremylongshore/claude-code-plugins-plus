---
name: finta-debug-bundle
description: |
  Collect Finta diagnostic information for support.
  Trigger with phrases like "finta debug", "finta support".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Debug Bundle

## Overview

Collect Finta API connectivity status, fundraising round data, investor pipeline health, and integration state into a single diagnostic archive. This bundle helps troubleshoot CRM sync failures, missing investor records, round update errors, and authentication problems. Attach the output to Finta support tickets for faster resolution of fundraising workflow issues.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-finta-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Finta Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "FINTA_API_KEY: ${FINTA_API_KEY:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${FINTA_API_KEY}" \
  https://api.finta.io/v1/rounds 2>/dev/null || echo "000")
echo "API Status: HTTP $HTTP" >> "$BUNDLE/summary.txt"

# Fundraising rounds summary
curl -s -H "Authorization: Bearer ${FINTA_API_KEY}" \
  "https://api.finta.io/v1/rounds" \
  > "$BUNDLE/rounds.json" 2>&1 || true

# Investor records (limited)
curl -s -H "Authorization: Bearer ${FINTA_API_KEY}" \
  "https://api.finta.io/v1/investors?limit=10" \
  > "$BUNDLE/investors-sample.json" 2>&1 || true

# Connected integrations status
curl -s -H "Authorization: Bearer ${FINTA_API_KEY}" \
  "https://api.finta.io/v1/integrations" \
  > "$BUNDLE/integrations.json" 2>&1 || true

# Rate limit headers
curl -s -D "$BUNDLE/rate-headers.txt" -o /dev/null \
  -H "Authorization: Bearer ${FINTA_API_KEY}" \
  https://api.finta.io/v1/rounds 2>/dev/null || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-finta-*.tar.gz
cat debug-finta-*/summary.txt                  # Auth + connectivity overview
jq '.[] | {id, name, status}' debug-finta-*/rounds.json  # Active rounds
jq 'length' debug-finta-*/investors-sample.json          # Investor count check
grep -i "ratelimit\|retry" debug-finta-*/rate-headers.txt
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| API returns 401 | `summary.txt` shows HTTP 401 | Regenerate API key in Finta Settings > API Keys |
| Rounds list empty | `rounds.json` returns empty array | Verify rounds exist in Finta dashboard; check workspace permissions |
| Investor sync missing | `investors-sample.json` has fewer records than expected | Check CRM integration in `integrations.json`; re-authorize connection |
| Integration disconnected | `integrations.json` shows error status | Re-authenticate the integration from Finta Settings > Integrations |
| Rate limited (429) | `rate-headers.txt` shows Retry-After | Reduce polling frequency; batch investor lookups |

## Automated Health Check

```typescript
async function checkFinta(): Promise<void> {
  const key = process.env.FINTA_API_KEY;
  if (!key) { console.error("[FAIL] FINTA_API_KEY not set"); return; }

  const res = await fetch("https://api.finta.io/v1/rounds", {
    headers: { Authorization: `Bearer ${key}` },
  });
  console.log(`[${res.ok ? "OK" : "FAIL"}] API: HTTP ${res.status}`);

  if (res.ok) {
    const data = await res.json();
    console.log(`[INFO] Active rounds: ${Array.isArray(data) ? data.length : 0}`);
  }
}
checkFinta();
```

## Resources

- [Finta Status](https://status.finta.io)

## Next Steps

See `finta-common-errors` for fundraising CRM sync and investor pipeline troubleshooting patterns.
