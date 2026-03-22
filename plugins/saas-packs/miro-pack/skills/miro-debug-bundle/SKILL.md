---
name: miro-debug-bundle
description: |
  Collect Miro REST API v2 diagnostic evidence for support tickets.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Miro integration problems.
  Trigger with phrases like "miro debug", "miro support bundle",
  "collect miro logs", "miro diagnostic", "miro support ticket".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, debugging, diagnostics]
compatible-with: claude-code
---

# Miro Debug Bundle

## Overview

Collect all diagnostic information needed to troubleshoot Miro REST API v2 integration issues and file effective support tickets.

## Prerequisites

- Access token (even expired ones are useful for diagnostics)
- `curl` and `jq` available
- Application logs accessible

## Instructions

### Step 1: Create the Debug Bundle Script

```bash
#!/bin/bash
# miro-debug-bundle.sh — Collect Miro API diagnostics
set -euo pipefail

BUNDLE_DIR="miro-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Miro Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info

```bash
# Runtime environment
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -srm)" >> "$BUNDLE_DIR/summary.txt"

# SDK version
echo "--- SDK Version ---" >> "$BUNDLE_DIR/summary.txt"
npm list @mirohq/miro-api 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "@mirohq/miro-api: not found" >> "$BUNDLE_DIR/summary.txt"

# Token presence (never log the actual token)
echo "--- Token Status ---" >> "$BUNDLE_DIR/summary.txt"
echo "MIRO_ACCESS_TOKEN: ${MIRO_ACCESS_TOKEN:+SET (length: ${#MIRO_ACCESS_TOKEN})}" >> "$BUNDLE_DIR/summary.txt"
echo "MIRO_CLIENT_ID: ${MIRO_CLIENT_ID:+SET}" >> "$BUNDLE_DIR/summary.txt"
echo "MIRO_REFRESH_TOKEN: ${MIRO_REFRESH_TOKEN:+SET}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: API Connectivity Tests

```bash
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"

# DNS resolution
echo -n "DNS resolve api.miro.com: " >> "$BUNDLE_DIR/summary.txt"
nslookup api.miro.com 2>/dev/null | grep "Address" | tail -1 >> "$BUNDLE_DIR/summary.txt" || echo "FAILED" >> "$BUNDLE_DIR/summary.txt"

# HTTPS connectivity (no auth needed)
echo -n "HTTPS to api.miro.com: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" https://api.miro.com 2>&1 >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Authenticated API test
echo -n "GET /v2/boards: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o "$BUNDLE_DIR/boards-response.json" -w "%{http_code} (%{time_total}s)" \
  -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN:-none}" \
  "https://api.miro.com/v2/boards?limit=1" 2>&1 >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Rate limit status from response headers
echo "--- Rate Limit Status ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -D "$BUNDLE_DIR/response-headers.txt" -o /dev/null \
  -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN:-none}" \
  "https://api.miro.com/v2/boards?limit=1" 2>/dev/null
grep -i "x-ratelimit\|retry-after" "$BUNDLE_DIR/response-headers.txt" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "No rate limit headers found" >> "$BUNDLE_DIR/summary.txt"

# Token info (scopes, user_id, team_id)
echo "--- Token Info ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -H "Authorization: Bearer ${MIRO_ACCESS_TOKEN:-none}" \
  "https://api.miro.com/v1/oauth-token" 2>/dev/null | \
  jq '{scopes, team_id: .team.id, user_id: .user.id}' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "Token introspection failed" >> "$BUNDLE_DIR/summary.txt"

# Miro platform status
echo "--- Miro Platform Status ---" >> "$BUNDLE_DIR/summary.txt"
curl -s "https://status.miro.com/api/v2/status.json" 2>/dev/null | \
  jq '.status' >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "Status page unreachable" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Capture Recent Errors (Redacted)

```bash
echo "--- Recent Application Errors ---" >> "$BUNDLE_DIR/summary.txt"

# Search for Miro-related errors in common log locations
for logpath in \
  "$(npm prefix 2>/dev/null)/logs" \
  "$HOME/.npm/_logs" \
  "/var/log/app" \
  "./logs"; do
  if [ -d "$logpath" ]; then
    grep -ri "miro\|api\.miro\.com" "$logpath"/*.log 2>/dev/null | \
      tail -30 | \
      sed 's/Bearer [A-Za-z0-9._-]*/Bearer [REDACTED]/g' \
      >> "$BUNDLE_DIR/error-logs.txt" 2>/dev/null
  fi
done

# Redact .env file
if [ -f .env ]; then
  echo "--- Config (redacted) ---" > "$BUNDLE_DIR/config-redacted.txt"
  sed 's/=.*/=[REDACTED]/' .env >> "$BUNDLE_DIR/config-redacted.txt"
fi
```

### Step 5: Package the Bundle

```bash
# Remove raw response bodies that might contain sensitive data
rm -f "$BUNDLE_DIR/boards-response.json" "$BUNDLE_DIR/response-headers.txt"

tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"

echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review contents before sharing with Miro support."
```

## Sensitive Data Handling

**ALWAYS redact before sharing:**
- Access tokens and refresh tokens
- Client secrets
- User email addresses and names
- Board content that may contain proprietary information

**Safe to include:**
- HTTP status codes and error messages
- Rate limit header values
- SDK and Node.js versions
- Token scopes (not the token itself)
- Request IDs (`X-Request-Id` header)

## One-Liner Diagnostics

```bash
# Quick API health check
curl -sw "\n%{http_code}" -H "Authorization: Bearer $MIRO_ACCESS_TOKEN" https://api.miro.com/v2/boards?limit=1 | tail -1

# Current rate limit status
curl -sI -H "Authorization: Bearer $MIRO_ACCESS_TOKEN" https://api.miro.com/v2/boards?limit=1 2>/dev/null | grep -i ratelimit

# Token scopes
curl -s -H "Authorization: Bearer $MIRO_ACCESS_TOKEN" https://api.miro.com/v1/oauth-token | jq '.scopes'
```

## Error Handling

| Diagnostic | What It Reveals | If It Fails |
|-----------|----------------|-------------|
| DNS lookup | Network/firewall issues | Check DNS config, VPN |
| HTTPS check | TLS/proxy issues | Check corporate proxy settings |
| Auth test | Token validity | Refresh or re-authorize |
| Rate limit headers | Credit consumption | Implement backoff |
| Token introspection | Scope configuration | Re-check app settings |

## Resources

- [Miro Status Page](https://status.miro.com)
- [Miro Developer Support](https://developers.miro.com/docs/getting-help)
- [OAuth Token Endpoint](https://developers.miro.com/docs/getting-started-with-oauth)

## Next Steps

For rate limit issues specifically, see `miro-rate-limits`.
