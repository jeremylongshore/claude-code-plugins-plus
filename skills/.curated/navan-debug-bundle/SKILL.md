---
name: navan-debug-bundle
description: "Use when collecting diagnostic data from a Navan API integration \u2014\
  \ OAuth token inspection, API response capture, connectivity testing, and request/response\
  \ logging.\nTrigger with \"navan debug bundle\" or \"debug navan api\".\n"
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Bash(tar:*), Bash(mkdir:*), Bash(date:*),
  Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Debug Bundle

## Overview

Collect diagnostic data from Navan REST API integrations into a structured, shareable debug bundle. Navan has no SDK — all debugging uses raw HTTP requests against their OAuth 2.0 REST endpoints.

## Prerequisites

- Navan API credentials: `client_id` and `client_secret` from Admin > Travel admin > Settings > Integrations
- `curl` and `jq` installed locally
- Credentials are viewable **only once** at creation — store them in a secret manager immediately
- No sandbox environment exists; all API calls hit production

## Instructions

### Step 1 — Create Bundle Directory

```bash
BUNDLE_DIR="navan-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"/{auth,api,connectivity,env}
echo "Bundle initialized: $BUNDLE_DIR"
```

### Step 2 — Capture Environment State

```bash
cat > "$BUNDLE_DIR/env/config.txt" <<ENVEOF
Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
NAVAN_CLIENT_ID: ${NAVAN_CLIENT_ID:+SET (not empty)}${NAVAN_CLIENT_ID:-UNSET}
NAVAN_CLIENT_SECRET: ${NAVAN_CLIENT_SECRET:+SET (not empty)}${NAVAN_CLIENT_SECRET:-UNSET}
NAVAN_TOKEN_URL: ${NAVAN_TOKEN_URL:-https://api.navan.com/ta-auth/oauth/token}
curl version: $(curl --version | head -1)
jq version: $(jq --version 2>/dev/null || echo "not installed")
ENVEOF
```

### Step 3 — Test OAuth Token Acquisition

```bash
curl -s -w "\n---HTTP_CODE:%{http_code}---\n" \
  -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | tee "$BUNDLE_DIR/auth/token-response.json" \
  | jq '{has_token: (.access_token != null), error: .error}'
```

If the token response returns HTTP 401, the credentials are invalid or expired. If HTTP 403, the API integration may not be enabled for your organization.

### Step 4 — Probe API Endpoints

Test each core endpoint and capture full response headers:

```bash
TOKEN=$(jq -r '.access_token' "$BUNDLE_DIR/auth/token-response.json")

# Test the primary bookings endpoint
ENDPOINT="v1/bookings"
curl -s -D "$BUNDLE_DIR/api/bookings-headers.txt" \
  -w "\n---HTTP_CODE:%{http_code}---\n" \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/${ENDPOINT}?page=0&size=1" \
  > "$BUNDLE_DIR/api/bookings-body.json" 2>&1
echo "bookings: $(grep 'HTTP_CODE' "$BUNDLE_DIR/api/bookings-body.json")"
```

### Step 5 — Connectivity and DNS Tests

```bash
curl -s -o /dev/null -w "connect_time: %{time_connect}\nttfb: %{time_starttransfer}\ntotal: %{time_total}\nhttp_code: %{http_code}\n" \
  "https://api.navan.com/ta-auth/oauth/token" \
  > "$BUNDLE_DIR/connectivity/timing.txt"

nslookup api.navan.com > "$BUNDLE_DIR/connectivity/dns.txt" 2>&1
```

### Step 6 — Sanitize and Package

Strip any raw credentials before sharing:

```bash
# Remove raw secrets from bundle files
find "$BUNDLE_DIR" -type f -exec sed -i \
  -e "s/$NAVAN_CLIENT_SECRET/[REDACTED]/g" \
  -e "s/$NAVAN_CLIENT_ID/[CLIENT_ID_REDACTED]/g" {} +

tar -czf "${BUNDLE_DIR}.tar.gz" "$BUNDLE_DIR"
echo "Debug bundle ready: ${BUNDLE_DIR}.tar.gz ($(du -h "${BUNDLE_DIR}.tar.gz" | cut -f1))"
```

## Output

A compressed tarball containing:

| File | Contents |
|------|----------|
| `auth/token-response.json` | OAuth response (token redacted) |
| `api/*-headers.txt` | HTTP response headers per endpoint |
| `api/*-body.json` | API response bodies |
| `connectivity/timing.txt` | Connection timing metrics |
| `connectivity/dns.txt` | DNS resolution results |
| `env/config.txt` | Environment variable state |

## Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 401 | Invalid or expired credentials | Regenerate credentials in Admin > Integrations |
| 403 | API not enabled for organization | Contact Navan admin to enable API access |
| 429 | Rate limit exceeded | Wait and retry; check `Retry-After` header |
| 500 | Navan server error | Retry after 60s; check Navan status |
| `ECONNREFUSED` | Cannot reach Navan | Check DNS, firewall, and proxy settings |

## Examples

Parse a specific error from the bundle:

```bash
# Extract error details from a failed endpoint
jq '.error, .message, .status' "$BUNDLE_DIR/api/bookings-body.json"

# Check if token is expired
jq '.expires_at' "$BUNDLE_DIR/auth/token-response.json"

# Review response times
cat "$BUNDLE_DIR/connectivity/timing.txt"
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Support documentation and troubleshooting
- [Navan Security](https://navan.com/security) — SOC 2 Type II, ISO 27001 compliance details
- [Navan Integrations](https://navan.com/integrations) — Available third-party connectors

## Next Steps

- Use `navan-incident-runbook` if the debug bundle reveals a production incident
- Use `navan-rate-limits` if 429 errors appear in the bundle
- Use `navan-common-errors` for guidance on specific HTTP error codes
