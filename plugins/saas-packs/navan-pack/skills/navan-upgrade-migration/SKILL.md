---
name: navan-upgrade-migration
description: "Use when handling Navan API changes in production \u2014 defensive coding\
  \ patterns, schema validation, deprecation monitoring, and gradual rollout strategies\
  \ for unversioned APIs.\nTrigger with \"navan upgrade migration\" or \"navan api\
  \ change handling\".\n"
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Upgrade Migration

## Overview

Defensive patterns for maintaining Navan API integrations over time. Navan does not publicly version their API, publish a changelog, or guarantee backward compatibility. Every API response should be treated as potentially different from the last.

## Prerequisites

- Existing Navan API integration in production
- OAuth credentials (`client_id`, `client_secret`) stored in a secret manager
- Baseline API response snapshots for comparison (see Step 1)
- `curl`, `jq`, and `diff` for schema comparison

## Instructions

### Step 1 — Capture Response Baselines

Store known-good API responses as reference schemas. Compare against these regularly to detect drift.

```bash
TOKEN=$(curl -s -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | jq -r '.access_token')

BASELINE_DIR="navan-api-baselines/$(date +%Y%m%d)"
mkdir -p "$BASELINE_DIR"

# Capture response structure (keys only, no values)
for ENDPOINT in users bookings; do
  curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.navan.com/v1/${ENDPOINT}?page=0&size=1" \
    | jq '[.data[] | keys] | .[0]' > "$BASELINE_DIR/${ENDPOINT}-schema.json" 2>/dev/null
  echo "Captured: $ENDPOINT → $(cat "$BASELINE_DIR/${ENDPOINT}-schema.json" | jq length) fields"
done
```

### Step 2 — Schema Drift Detection

Run this periodically (daily cron or CI pipeline) to detect API changes:

```bash
LATEST_BASELINE=$(ls -d navan-api-baselines/*/ | sort | tail -1)

for ENDPOINT in users bookings; do
  CURRENT=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.navan.com/v1/${ENDPOINT}?page=0&size=1" \
    | jq '[.data[] | keys] | .[0]' 2>/dev/null)

  BASELINE=$(cat "${LATEST_BASELINE}${ENDPOINT}-schema.json" 2>/dev/null)

  # Compare field sets
  ADDED=$(comm -13 <(echo "$BASELINE" | jq -r '.[]' | sort) <(echo "$CURRENT" | jq -r '.[]' | sort))
  REMOVED=$(comm -23 <(echo "$BASELINE" | jq -r '.[]' | sort) <(echo "$CURRENT" | jq -r '.[]' | sort))

  [ -n "$ADDED" ] && echo "WARNING: $ENDPOINT has NEW fields: $ADDED"
  [ -n "$REMOVED" ] && echo "CRITICAL: $ENDPOINT has REMOVED fields: $REMOVED"
  [ -z "$ADDED" ] && [ -z "$REMOVED" ] && echo "OK: $ENDPOINT schema unchanged"
done
```

### Step 3 — Defensive Response Parsing

Never assume a fixed schema. Use defensive patterns that tolerate changes:

```bash
# BAD: Assumes exact structure — breaks if fields are renamed or removed
# jq '.trips[0].flight_number'

# GOOD: Defensive parsing with fallbacks
jq '
  if type == "array" then
    .[0] // {} |
    {
      id: (.id // .uuid // .booking_id // "unknown"),
      flight: (.flight_number // .flight_no // .flightNumber // "N/A"),
      status: (.status // .booking_status // "unknown"),
      _extra_fields: (keys - ["id","uuid","booking_id","flight_number","flight_no",
                               "flightNumber","status","booking_status"])
    }
  else
    {error: "unexpected response type", type: type}
  end
' /tmp/navan-trips.json
```

**Key defensive principles:**
- Always provide fallback field names (Navan may rename without notice)
- Log unknown fields rather than ignoring them — they signal upcoming changes
- Never hard-code array lengths or object depth assumptions
- Parse dates permissively (ISO 8601, Unix timestamp, and custom formats)

### Step 4 — Deprecation Signal Monitoring

Check HTTP response headers for deprecation or sunset signals:

```bash
# Capture and inspect response headers for deprecation notices
curl -s -D - -o /dev/null \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/users" \
  | grep -iE "deprecat|sunset|warning|x-api-version|x-deprecated"

# Check response body for deprecation warnings
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/users" \
  | jq '{
    has_deprecation_warning: (._deprecated // .deprecated // .warning // null),
    has_version_header: (.api_version // ._api_version // null)
  }'
```

### Step 5 — Gradual Rollout Strategy

When you detect or anticipate an API change, use feature flags to roll out handling changes gradually:

```bash
# Feature flag pattern for API response handling
# Store flag in environment or config service
export NAVAN_USE_NEW_TRIP_SCHEMA="${NAVAN_USE_NEW_TRIP_SCHEMA:-false}"

# In your integration code, branch on the flag
if [ "$NAVAN_USE_NEW_TRIP_SCHEMA" = "true" ]; then
  # New parsing logic for updated schema
  jq '.[] | {id: .booking_uuid, flight: .flight_number}' /tmp/trips.json
else
  # Legacy parsing logic (current production)
  jq '.[] | {id: .id, flight: .flight_no}' /tmp/trips.json
fi
```

**Rollout procedure:**
1. Deploy new parsing logic behind a feature flag (flag = off)
2. Enable for 5% of traffic — compare outputs between old and new parsers
3. If outputs match or new parser handles additional fields, increase to 25%
4. Monitor error rates at each stage for 24 hours
5. Full rollout at 100% when confidence is high
6. Remove old parsing logic and feature flag after 2 weeks at 100%

### Step 6 — Automated Regression Testing

Run regression tests against live API responses on a schedule:

```bash
# Regression test: verify critical fields still exist
FAILURES=0

USERS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/users")

# Check required fields exist
for FIELD in id email; do
  HAS_FIELD=$(echo "$USERS_RESPONSE" | jq ".data[0] | has(\"$FIELD\")")
  if [ "$HAS_FIELD" != "true" ]; then
    echo "REGRESSION: /v1/users missing required field: $FIELD"
    FAILURES=$((FAILURES + 1))
  fi
done

BOOKINGS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/bookings?page=0&size=1")

for FIELD in uuid; do
  HAS_FIELD=$(echo "$BOOKINGS_RESPONSE" | jq ".data[0] | has(\"$FIELD\")")
  if [ "$HAS_FIELD" != "true" ]; then
    echo "REGRESSION: /v1/bookings missing required field: $FIELD"
    FAILURES=$((FAILURES + 1))
  fi
done

echo "Regression result: $FAILURES failures"
[ "$FAILURES" -gt 0 ] && exit 1
```

### Step 7 — Change Response Playbook

When a schema change is detected:

| Change Type | Severity | Response |
|-------------|----------|----------|
| New field added | Low | Log it, update baseline, no code change needed |
| Field renamed | High | Add new name as fallback, deploy behind flag |
| Field removed | Critical | Identify impact, implement fallback, alert team |
| Type changed (string to int) | High | Update parser, add type coercion |
| Endpoint URL changed | Critical | Update client config, monitor old URL for redirect |
| Auth flow changed | Critical | Immediate attention — test `/ta-auth/oauth/token` |

## Output

- Baseline schema snapshots stored in version control
- Drift detection script running on a schedule (cron or CI)
- Defensive parsing patterns applied to all API response handlers
- Feature flag configuration for gradual rollout of schema changes
- Regression test suite covering critical field presence

## Error Handling

| Issue | Detection | Response |
|-------|-----------|----------|
| New unknown fields in response | Drift detection script | Log, update baseline, no action unless field replaces existing |
| Required field missing | Regression test failure | Roll back to cached data, alert team, open support ticket |
| Response type changed | jq parse error | Add type checking, coerce if possible, alert if not |
| Endpoint returns 404 | Health check failure | Check for URL changes, contact Navan support |
| Auth endpoint behavior change | Token acquisition failure | Test `/ta-auth/oauth/token` manually, check Admin > Integrations |

## Examples

Quick schema health check:

```bash
# One-liner: check if API response structure matches expectations
TOKEN=$(curl -s -X POST "https://api.navan.com/ta-auth/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | jq -r '.access_token')

echo "Users fields: $(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/users" | jq '.data[0] | keys | length') keys"
echo "Bookings fields: $(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.navan.com/v1/bookings?page=0&size=1" | jq '.data[0] | keys | length') keys"
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — API documentation and change notices
- [Navan Security](https://navan.com/security) — Infrastructure and TLS/encryption details
- [Navan Integrations](https://navan.com/integrations) — Connector ecosystem and partner updates

## Next Steps

- Use `navan-debug-bundle` to capture current API state as a baseline
- Use `navan-prod-checklist` to verify production hardening after changes
- Use `navan-ci-integration` to add regression tests to your CI pipeline
