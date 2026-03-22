---
name: canva-debug-bundle
description: |
  Collect Canva Connect API debug evidence for troubleshooting and support.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Canva API problems.
  Trigger with phrases like "canva debug", "canva support bundle",
  "collect canva logs", "canva diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Debug Bundle

## Overview

Collect diagnostic information for Canva Connect API issues. Tests connectivity to `api.canva.com/rest/v1/*`, validates OAuth tokens, checks rate limits, and packages evidence for support tickets.

## Instructions

### Step 1: Connectivity & Auth Check Script

```bash
#!/bin/bash
# canva-debug.sh — Run with: bash canva-debug.sh
set -euo pipefail

TOKEN="${CANVA_ACCESS_TOKEN:-}"
BUNDLE="canva-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

echo "=== Canva Connect API Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$BUNDLE/summary.txt"
echo "" >> "$BUNDLE/summary.txt"

# 1. Check API reachability
echo "--- API Connectivity ---" >> "$BUNDLE/summary.txt"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "https://api.canva.com/rest/v1/users/me")
echo "GET /v1/users/me: HTTP $HTTP_CODE" | tee -a "$BUNDLE/summary.txt"

# 2. Get user identity (if token valid)
if [ "$HTTP_CODE" = "200" ]; then
  curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.canva.com/rest/v1/users/me" | tee "$BUNDLE/user-identity.json" \
    | python3 -m json.tool 2>/dev/null || true
  echo "Token: VALID" >> "$BUNDLE/summary.txt"
else
  echo "Token: INVALID or EXPIRED (HTTP $HTTP_CODE)" >> "$BUNDLE/summary.txt"
fi

# 3. Check response headers for rate limit info
echo "" >> "$BUNDLE/summary.txt"
echo "--- Rate Limit Headers ---" >> "$BUNDLE/summary.txt"
curl -s -D - -o /dev/null -H "Authorization: Bearer $TOKEN" \
  "https://api.canva.com/rest/v1/designs?limit=1" 2>&1 \
  | grep -iE "(x-ratelimit|retry-after|content-type|date)" \
  >> "$BUNDLE/summary.txt" 2>/dev/null || echo "No rate limit headers" >> "$BUNDLE/summary.txt"

# 4. DNS resolution
echo "" >> "$BUNDLE/summary.txt"
echo "--- DNS Resolution ---" >> "$BUNDLE/summary.txt"
nslookup api.canva.com >> "$BUNDLE/summary.txt" 2>&1 || echo "nslookup not available" >> "$BUNDLE/summary.txt"

# 5. TLS check
echo "" >> "$BUNDLE/summary.txt"
echo "--- TLS Handshake ---" >> "$BUNDLE/summary.txt"
curl -sv "https://api.canva.com/rest/v1/users/me" 2>&1 \
  | grep -E "(SSL|TLS|Connected)" >> "$BUNDLE/summary.txt" 2>/dev/null || true

# 6. Environment info
echo "" >> "$BUNDLE/summary.txt"
echo "--- Environment ---" >> "$BUNDLE/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'not found')" >> "$BUNDLE/summary.txt"
echo "OS: $(uname -s -r)" >> "$BUNDLE/summary.txt"
echo "CANVA_CLIENT_ID: ${CANVA_CLIENT_ID:+[SET]}" >> "$BUNDLE/summary.txt"
echo "CANVA_ACCESS_TOKEN: ${CANVA_ACCESS_TOKEN:+[SET]}" >> "$BUNDLE/summary.txt"

# 7. Package bundle
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
echo ""
echo "Bundle created: $BUNDLE.tar.gz"
```

### Step 2: Programmatic Diagnostic

```typescript
// src/canva/diagnostics.ts
interface DiagnosticResult {
  check: string;
  status: 'pass' | 'fail' | 'warn';
  details: string;
  durationMs: number;
}

async function runCanvaDiagnostics(token: string): Promise<DiagnosticResult[]> {
  const results: DiagnosticResult[] = [];

  // Check 1: API reachability
  const start1 = Date.now();
  try {
    const res = await fetch('https://api.canva.com/rest/v1/users/me', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    results.push({
      check: 'API Reachability',
      status: res.ok ? 'pass' : res.status === 401 ? 'fail' : 'warn',
      details: `HTTP ${res.status}`,
      durationMs: Date.now() - start1,
    });
  } catch (e: any) {
    results.push({ check: 'API Reachability', status: 'fail', details: e.message, durationMs: Date.now() - start1 });
  }

  // Check 2: Token validity
  const start2 = Date.now();
  try {
    const res = await fetch('https://api.canva.com/rest/v1/users/me', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      results.push({
        check: 'Token Validity',
        status: 'pass',
        details: `user_id: ${data.team_user.user_id}`,
        durationMs: Date.now() - start2,
      });
    } else {
      results.push({ check: 'Token Validity', status: 'fail', details: `HTTP ${res.status}`, durationMs: Date.now() - start2 });
    }
  } catch (e: any) {
    results.push({ check: 'Token Validity', status: 'fail', details: e.message, durationMs: Date.now() - start2 });
  }

  // Check 3: Design list (tests design:meta:read scope)
  const start3 = Date.now();
  try {
    const res = await fetch('https://api.canva.com/rest/v1/designs?limit=1', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    results.push({
      check: 'Scope: design:meta:read',
      status: res.ok ? 'pass' : res.status === 403 ? 'warn' : 'fail',
      details: res.ok ? 'Scope active' : `HTTP ${res.status} — scope may not be enabled`,
      durationMs: Date.now() - start3,
    });
  } catch (e: any) {
    results.push({ check: 'Scope: design:meta:read', status: 'fail', details: e.message, durationMs: Date.now() - start3 });
  }

  return results;
}

// Print report
const results = await runCanvaDiagnostics(process.env.CANVA_ACCESS_TOKEN!);
for (const r of results) {
  const icon = r.status === 'pass' ? 'OK' : r.status === 'warn' ? 'WARN' : 'FAIL';
  console.log(`[${icon}] ${r.check}: ${r.details} (${r.durationMs}ms)`);
}
```

## Sensitive Data Handling

**ALWAYS REDACT before sharing:**
- Access tokens and refresh tokens
- Client secrets
- User IDs (if privacy-sensitive)

**Safe to include:**
- HTTP status codes and error messages
- Response headers (rate limit info)
- Latency measurements
- SDK/runtime versions

## Error Handling

| Item | Purpose | Included |
|------|---------|----------|
| HTTP status from `/v1/users/me` | Auth validation | Yes |
| Rate limit headers | Throttling diagnosis | Yes |
| DNS resolution | Network path | Yes |
| TLS handshake | Certificate issues | Yes |
| Environment versions | Compatibility | Yes |

## Resources

- [Canva API Requests & Responses](https://www.canva.dev/docs/connect/api-requests-responses/)
- [Canva Changelog](https://www.canva.dev/docs/connect/changelog/)

## Next Steps

For rate limit issues, see `canva-rate-limits`.
