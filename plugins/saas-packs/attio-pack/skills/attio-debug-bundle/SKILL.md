---
name: attio-debug-bundle
description: |
  Collect Attio integration diagnostic evidence -- API health, scopes,
  object schema, and rate limit status -- for debugging or support tickets.
  Trigger: "attio debug", "attio support bundle", "attio diagnostic",
  "collect attio logs", "attio not working debug".
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Bash(tar:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, attio]
compatible-with: claude-code
---

# Attio Debug Bundle

## Overview

Collect all diagnostic evidence needed to debug Attio API issues or file a support ticket. Checks auth, scopes, object schema, rate limit headers, and endpoint connectivity.

## Prerequisites

- `ATTIO_API_KEY` environment variable set
- `curl` and `jq` available
- Permissions to read project environment

## Instructions

### Step 1: Run the Full Diagnostic Script

```bash
#!/bin/bash
# attio-debug-bundle.sh -- Collects Attio diagnostic evidence
set -euo pipefail

BUNDLE_DIR="attio-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"
SUMMARY="$BUNDLE_DIR/summary.txt"

echo "=== Attio Debug Bundle ===" | tee "$SUMMARY"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$SUMMARY"
echo "" | tee -a "$SUMMARY"

# 1. Check token is set (never log the actual key)
echo "--- Token Status ---" | tee -a "$SUMMARY"
if [ -z "${ATTIO_API_KEY:-}" ]; then
  echo "ATTIO_API_KEY: NOT SET" | tee -a "$SUMMARY"
  echo "Cannot proceed without API key" | tee -a "$SUMMARY"
  exit 1
else
  echo "ATTIO_API_KEY: SET (${#ATTIO_API_KEY} chars, starts with ${ATTIO_API_KEY:0:3}...)" | tee -a "$SUMMARY"
fi

# 2. API connectivity and auth test
echo "" | tee -a "$SUMMARY"
echo "--- API Connectivity ---" | tee -a "$SUMMARY"
HTTP_CODE=$(curl -s -o "$BUNDLE_DIR/objects-response.json" -w "%{http_code}" \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  https://api.attio.com/v2/objects)
echo "GET /v2/objects: HTTP $HTTP_CODE" | tee -a "$SUMMARY"

if [ "$HTTP_CODE" = "200" ]; then
  echo "AUTH: OK" | tee -a "$SUMMARY"
  jq -r '.data[] | "  - " + .api_slug + " (" + .singular_noun + ")"' \
    "$BUNDLE_DIR/objects-response.json" | tee -a "$SUMMARY"
elif [ "$HTTP_CODE" = "401" ]; then
  echo "AUTH: FAILED -- token invalid or revoked" | tee -a "$SUMMARY"
elif [ "$HTTP_CODE" = "403" ]; then
  echo "AUTH: INSUFFICIENT SCOPES" | tee -a "$SUMMARY"
  jq '.message' "$BUNDLE_DIR/objects-response.json" 2>/dev/null | tee -a "$SUMMARY"
fi

# 3. Rate limit headers
echo "" | tee -a "$SUMMARY"
echo "--- Rate Limit Status ---" | tee -a "$SUMMARY"
curl -s -D "$BUNDLE_DIR/headers.txt" -o /dev/null \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  https://api.attio.com/v2/objects
grep -i "x-ratelimit\|retry-after" "$BUNDLE_DIR/headers.txt" 2>/dev/null | tee -a "$SUMMARY" || echo "No rate limit headers found" | tee -a "$SUMMARY"

# 4. List attributes for core objects
echo "" | tee -a "$SUMMARY"
echo "--- Object Schemas ---" | tee -a "$SUMMARY"
for obj in people companies; do
  echo "  $obj attributes:" | tee -a "$SUMMARY"
  curl -s "https://api.attio.com/v2/objects/$obj/attributes" \
    -H "Authorization: Bearer ${ATTIO_API_KEY}" \
    | jq -r '.data[] | "    " + .api_slug + " (" + .type + ", required=" + (.is_required|tostring) + ")"' \
    2>/dev/null | tee -a "$SUMMARY" || echo "    FAILED" | tee -a "$SUMMARY"
done

# 5. List available lists
echo "" | tee -a "$SUMMARY"
echo "--- Lists ---" | tee -a "$SUMMARY"
curl -s https://api.attio.com/v2/lists \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  | jq -r '.data[] | "  - " + .api_slug + " (" + .name + ")"' \
  2>/dev/null | tee -a "$SUMMARY" || echo "  FAILED (may need list_entry:read scope)" | tee -a "$SUMMARY"

# 6. Webhooks
echo "" | tee -a "$SUMMARY"
echo "--- Webhooks ---" | tee -a "$SUMMARY"
curl -s https://api.attio.com/v2/webhooks \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  | jq -r '.data[] | "  - " + .id.webhook_id + " -> " + .target_url' \
  2>/dev/null | tee -a "$SUMMARY" || echo "  FAILED (may need webhook:read-write scope)" | tee -a "$SUMMARY"

# 7. Environment info
echo "" | tee -a "$SUMMARY"
echo "--- Environment ---" | tee -a "$SUMMARY"
echo "Node: $(node --version 2>/dev/null || echo 'not installed')" | tee -a "$SUMMARY"
echo "OS: $(uname -s) $(uname -r)" | tee -a "$SUMMARY"

# 8. Status page
echo "" | tee -a "$SUMMARY"
echo "--- Attio Status ---" | tee -a "$SUMMARY"
curl -s https://status.attio.com/api/v2/status.json \
  | jq -r '.status.description' 2>/dev/null | tee -a "$SUMMARY" || echo "Could not reach status page" | tee -a "$SUMMARY"

# Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

### Step 2: Review Before Sharing

**Always check the bundle for leaked secrets before sharing:**

```bash
tar -tzf attio-debug-*.tar.gz  # List files
tar -xzf attio-debug-*.tar.gz && cat */summary.txt
```

**Safe to share:** HTTP status codes, object slugs, attribute types, rate limit headers, error messages.

**Never share:** Full API key, record IDs with PII, webhook secrets.

### Step 3: Quick Single-Command Diagnostic

For fast triage without a full bundle:

```bash
# One-liner: auth + objects + rate limit check
curl -s -w "\n--- HTTP %{http_code} ---\n" \
  -H "Authorization: Bearer ${ATTIO_API_KEY}" \
  https://api.attio.com/v2/objects | jq '{objects: [.data[].api_slug], count: (.data|length)}'
```

## Programmatic Health Check

```typescript
interface AttioDiagnostic {
  auth: "ok" | "failed" | "insufficient_scopes";
  objects: string[];
  lists: string[];
  latencyMs: number;
  rateLimitRemaining?: number;
}

async function diagnoseAttio(): Promise<AttioDiagnostic> {
  const start = Date.now();
  try {
    const res = await fetch("https://api.attio.com/v2/objects", {
      headers: { Authorization: `Bearer ${process.env.ATTIO_API_KEY}` },
    });

    const latencyMs = Date.now() - start;

    if (res.status === 401) return { auth: "failed", objects: [], lists: [], latencyMs };
    if (res.status === 403) return { auth: "insufficient_scopes", objects: [], lists: [], latencyMs };

    const data = await res.json();
    return {
      auth: "ok",
      objects: data.data.map((o: any) => o.api_slug),
      lists: [], // fetch separately if needed
      latencyMs,
      rateLimitRemaining: parseInt(res.headers.get("x-ratelimit-remaining") || "0"),
    };
  } catch {
    return { auth: "failed", objects: [], lists: [], latencyMs: Date.now() - start };
  }
}
```

## Error Handling

| Diagnostic result | Meaning | Action |
|-------------------|---------|--------|
| HTTP 200, objects listed | Auth and connectivity OK | Issue is in your code or data |
| HTTP 401 | Token invalid | Regenerate in Attio dashboard |
| HTTP 403 | Missing scopes | Add scopes to token |
| HTTP 429 | Rate limited right now | Wait for `Retry-After`, see `attio-rate-limits` |
| Connection error | Network/firewall issue | Check DNS, proxy, firewall rules |

## Resources

- [Attio REST API Overview](https://docs.attio.com/rest-api/overview)
- [Attio Status Page](https://status.attio.com)
- [Attio Help Center](https://attio.com/help)

## Next Steps

For rate limit issues, see `attio-rate-limits`. For error codes, see `attio-common-errors`.
