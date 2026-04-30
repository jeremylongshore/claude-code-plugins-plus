---
name: navan-ci-integration
description: 'Use when setting up CI/CD pipelines that validate Navan API integrations,
  run booking data health checks, or generate automated compliance reports.

  Trigger with "navan ci integration" or "navan pipeline" or "navan github actions".

  '
allowed-tools: Read, Write, Edit, Bash(git:*), Bash(gh:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan CI Integration

## Overview

Navan has no SDK — all CI integration uses raw REST calls against `https://api.navan.com` with OAuth 2.0 client_credentials authentication. This skill generates GitHub Actions workflows that validate your Navan integration on every push: token health checks, booking data schema validation, and travel policy compliance reports. Secrets (client_id, client_secret) are stored in GitHub Actions secrets, never in code.

## Prerequisites

- **Navan Admin access** to create OAuth 2.0 application credentials (Admin > API Settings)
- **GitHub repo** with Actions enabled
- **GitHub Secrets** configured: `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`
- Navan API base URL: `https://api.navan.com`

## Instructions

### Step 1 — Store OAuth Credentials in GitHub Secrets

Navigate to your GitHub repo > Settings > Secrets and variables > Actions. Add:

- `NAVAN_CLIENT_ID` — from Navan Admin > API Settings
- `NAVAN_CLIENT_SECRET` — from Navan Admin > API Settings

### Step 2 — Create the CI Workflow

```yaml
# .github/workflows/navan-integration-check.yml
name: Navan Integration Health Check
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6am UTC

jobs:
  navan-health:
    runs-on: ubuntu-latest
    env:
      NAVAN_BASE_URL: https://api.navan.com
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate with Navan OAuth 2.0
        id: auth
        run: |
          TOKEN_RESPONSE=$(curl -s -X POST \
            https://api.navan.com/ta-auth/oauth/token \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "grant_type=client_credentials" \
            -d "client_id=${{ secrets.NAVAN_CLIENT_ID }}" \
            -d "client_secret=${{ secrets.NAVAN_CLIENT_SECRET }}")

          ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
          if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
            echo "::error::OAuth authentication failed"
            echo "$TOKEN_RESPONSE" | jq .
            exit 1
          fi
          echo "::add-mask::$ACCESS_TOKEN"
          echo "token=$ACCESS_TOKEN" >> "$GITHUB_OUTPUT"

      - name: API Health Check — Fetch Bookings
        run: |
          HTTP_CODE=$(curl -s -o /tmp/bookings.json -w "%{http_code}" \
            "$NAVAN_BASE_URL/v1/bookings?page=0&size=5" \
            -H "Authorization: Bearer ${{ steps.auth.outputs.token }}")
          echo "Health check status: $HTTP_CODE"
          if [ "$HTTP_CODE" != "200" ]; then
            echo "::error::API health check failed with HTTP $HTTP_CODE"
            cat /tmp/bookings.json
            exit 1
          fi

      - name: Validate Booking Data Schema
        run: |
          # Response structure: records in .data array, primary key uuid
          REQUIRED_FIELDS='["uuid","traveler","status","created_at"]'
          echo "$REQUIRED_FIELDS" | jq -r '.[]' | while read field; do
            if ! jq -e ".data[0].$field" /tmp/bookings.json > /dev/null 2>&1; then
              echo "::warning::Missing expected field: $field"
            fi
          done

      - name: Generate Compliance Report
        run: |
          curl -s "$NAVAN_BASE_URL/v1/bookings?page=0&size=50" \
            -H "Authorization: Bearer ${{ steps.auth.outputs.token }}" \
            -o /tmp/compliance.json
          echo "## Navan Compliance Report" >> "$GITHUB_STEP_SUMMARY"
          jq -r '"| Metric | Value |\n|--------|-------|\n| Total Bookings | \(.total_bookings) |\n| In Policy | \(.in_policy) |\n| Out of Policy | \(.out_of_policy) |"' \
            /tmp/compliance.json >> "$GITHUB_STEP_SUMMARY" 2>/dev/null || echo "Report data unavailable" >> "$GITHUB_STEP_SUMMARY"
```

### Step 3 — Add Integration Test Script

```bash
#!/usr/bin/env bash
# scripts/navan-smoke-test.sh — Run locally or in CI
set -euo pipefail

BASE_URL="${NAVAN_BASE_URL:-https://api.navan.com}"

# Obtain token
TOKEN=$(curl -sf -X POST https://api.navan.com/ta-auth/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${NAVAN_CLIENT_ID}&client_secret=${NAVAN_CLIENT_SECRET}" \
  | jq -r '.access_token')

# Test endpoints (records returned in .data array)
ENDPOINTS=("v1/bookings?page=0&size=1")
FAILED=0
for ep in "${ENDPOINTS[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    "$BASE_URL/$ep" -H "Authorization: Bearer $TOKEN")
  if [ "$CODE" = "200" ]; then
    echo "PASS: $ep ($CODE)"
  else
    echo "FAIL: $ep ($CODE)"
    FAILED=$((FAILED + 1))
  fi
done

exit $FAILED
```

## Output

The CI workflow produces:
- **Pass/fail status** on each PR for Navan API connectivity
- **GitHub Step Summary** with a compliance report table
- **Annotations** warning about missing booking data fields
- **Weekly scheduled runs** catching credential expiration before it causes outages

## Error Handling

| HTTP Code | Meaning | CI Action |
|-----------|---------|-----------|
| `200` | Success | Continue |
| `401` | Invalid or expired OAuth token | Fail build, alert on credential rotation |
| `403` | Insufficient API scopes | Fail build, check OAuth app permissions |
| `404` | Endpoint not found (API version change) | Fail build, review API changelog |
| `429` | Rate limit exceeded | Retry with exponential backoff (max 3 attempts) |
| `500-503` | Navan server error | Warn but do not fail (transient) |

## Examples

**Parallel endpoint validation with matrix strategy:**

```yaml
jobs:
  validate-endpoints:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        endpoint: [bookings, expenses, users, invoices]
    steps:
      - name: Check ${{ matrix.endpoint }}
        run: |
          CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            "https://api.navan.com/v1/${{ matrix.endpoint }}?page=0&size=1" \
            -H "Authorization: Bearer $TOKEN")
          [ "$CODE" = "200" ] || exit 1
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — API documentation and guides
- [Navan Integrations](https://navan.com/integrations) — Supported third-party connectors
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

## Next Steps

- Add `navan-deploy-integration` for production deployment patterns
- Add `navan-observability` for runtime monitoring of the endpoints validated here
- See `navan-rate-limits` to configure retry policies in CI
