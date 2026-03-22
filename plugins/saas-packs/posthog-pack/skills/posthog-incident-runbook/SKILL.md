---
name: posthog-incident-runbook
description: |
  PostHog incident response: triage decision tree, immediate actions for
  401/429/500 errors, graceful degradation, evidence collection, and postmortem.
  Trigger: "posthog incident", "posthog outage", "posthog down",
  "posthog on-call", "posthog emergency", "posthog broken production".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, incident-response]
---

# PostHog Incident Runbook

## Overview

Rapid incident response for PostHog integration failures. PostHog Cloud has its own status page (status.posthog.com) — the first step is always determining whether the issue is PostHog-side or your integration.

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Analytics completely down | < 15 min | All capture calls failing, feature flags returning defaults |
| P2 | Degraded analytics | < 1 hour | High latency, partial event loss, slow flag eval |
| P3 | Minor impact | < 4 hours | Webhook delays, specific event type missing |
| P4 | No user impact | Next day | Monitoring gaps, dashboard stale data |

## Quick Triage (Run First)

```bash
set -euo pipefail
echo "=== PostHog Triage ==="
echo ""

# 1. Is PostHog Cloud up?
echo -n "PostHog US Cloud: "
curl -sf -o /dev/null -w "%{http_code}" https://us.i.posthog.com/healthz || echo "UNREACHABLE"
echo ""

# 2. Can we capture events?
echo -n "Event capture: "
curl -sf -o /dev/null -w "%{http_code}" -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"${NEXT_PUBLIC_POSTHOG_KEY}\",\"event\":\"triage_test\",\"distinct_id\":\"triage\"}" || echo "FAILED"
echo ""

# 3. Can we evaluate flags?
echo -n "Flag evaluation: "
curl -sf -o /dev/null -w "%{http_code}" -X POST 'https://us.i.posthog.com/decide/?v=3' \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"${NEXT_PUBLIC_POSTHOG_KEY}\",\"distinct_id\":\"triage\"}" || echo "FAILED"
echo ""

# 4. Can we access admin API?
if [ -n "${POSTHOG_PERSONAL_API_KEY:-}" ]; then
  echo -n "Admin API: "
  curl -sf -o /dev/null -w "%{http_code}" "https://app.posthog.com/api/projects/" \
    -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" || echo "FAILED"
  echo ""
fi

# 5. Check our integration health
echo -n "Our health endpoint: "
curl -sf -o /dev/null -w "%{http_code}" "https://your-app.com/api/health" || echo "UNREACHABLE"
echo ""
```

## Decision Tree

```
Is PostHog Cloud healthy (status.posthog.com)?
├── NO → PostHog outage
│   ├── Enable graceful degradation (feature flags return defaults)
│   ├── Monitor status.posthog.com for resolution
│   └── Events will be lost during outage (capture is fire-and-forget)
│
└── YES → Our integration issue
    ├── Are we getting 401? → API key issue (see Error 401 below)
    ├── Are we getting 429? → Rate limited (see Error 429 below)
    ├── Are events just not appearing? → Check flush/shutdown (see below)
    └── Are flags returning defaults? → Check personalApiKey (see below)
```

## Immediate Actions by Error Type

### 401/403 — Authentication Failed

```bash
set -euo pipefail
# Verify API key type and validity
echo "Project key prefix: $(echo "$NEXT_PUBLIC_POSTHOG_KEY" | head -c 4)"
echo "Personal key prefix: $(echo "$POSTHOG_PERSONAL_API_KEY" | head -c 4)"

# Test project key (should return HTTP 200)
curl -s -o /dev/null -w "Capture: %{http_code}\n" -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"$NEXT_PUBLIC_POSTHOG_KEY\",\"event\":\"test\",\"distinct_id\":\"test\"}"

# Test personal key (should return project list)
curl -s -o /dev/null -w "Admin: %{http_code}\n" "https://app.posthog.com/api/projects/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY"

# Fix: If key is invalid, rotate in PostHog dashboard and update secrets
```

### 429 — Rate Limited

```bash
set -euo pipefail
# PostHog rate limits (private API only):
# - Analytics endpoints: 240/min, 1200/hour
# - HogQL query: 1200/hour
# - Local flag eval polling: 600/min
# - Capture endpoints: NO LIMIT

# Immediate: Cache API responses, reduce polling frequency
# Long-term: See posthog-rate-limits skill
```

### Events Not Appearing

```bash
set -euo pipefail
# Most common cause: not calling flush/shutdown in serverless

# Check 1: Is capture endpoint reachable?
curl -s -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"$NEXT_PUBLIC_POSTHOG_KEY\",\"event\":\"debug_test\",\"distinct_id\":\"debug-$(date +%s)\"}" | jq .
# Expected: {"status": 1}

# Check 2: Verify API host is correct (common mistake)
# WRONG: https://app.posthog.com (this is the UI)
# RIGHT: https://us.i.posthog.com (this is the ingest endpoint)
```

### Feature Flags Returning Defaults

```typescript
// Most common causes:
// 1. No personalApiKey → falls back to remote eval which may fail
// 2. Flags not loaded yet → check timing
// 3. Wrong project key → flags from different project

// Fix 1: Add personalApiKey
const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY, // Required for local eval
});

// Fix 2: Wait for flags in browser
posthog.onFeatureFlags(() => {
  // Now flags are loaded
  const value = posthog.isFeatureEnabled('my-flag');
});
```

## Graceful Degradation Pattern

```typescript
// PostHog should NEVER crash your app
function safeCapture(distinctId: string, event: string, props?: Record<string, any>) {
  try {
    posthog.capture({ distinctId, event, properties: props });
  } catch {
    // Swallow error — analytics failure should never impact users
  }
}

async function safeFlag(key: string, userId: string, fallback: boolean = false): Promise<boolean> {
  try {
    const result = await posthog.isFeatureEnabled(key, userId);
    return result ?? fallback;
  } catch {
    return fallback; // Return safe default
  }
}
```

## Post-Incident Evidence Collection

```bash
set -euo pipefail
INCIDENT_DIR="posthog-incident-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$INCIDENT_DIR"

# Collect diagnostics
echo "Incident: $(date -u)" > "$INCIDENT_DIR/timeline.txt"
curl -s https://us.i.posthog.com/healthz > "$INCIDENT_DIR/healthz.json" 2>&1
env | grep -i posthog | sed 's/=.*/=***/' > "$INCIDENT_DIR/env-redacted.txt"
npm list posthog-js posthog-node 2>/dev/null > "$INCIDENT_DIR/versions.txt"

tar -czf "$INCIDENT_DIR.tar.gz" "$INCIDENT_DIR"
echo "Evidence collected: $INCIDENT_DIR.tar.gz"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Complete analytics outage | PostHog Cloud down | Enable graceful degradation, monitor status page |
| Partial event loss | Serverless not flushing | Add `await posthog.shutdown()` |
| All flags return false | `personalApiKey` missing or expired | Add/rotate personal API key |
| Admin API 401 | Personal key revoked | Generate new key in PostHog settings |
| High latency | Network path to PostHog | Check reverse proxy, try direct connection |

## Output

- Triage commands identifying issue source
- Immediate remediation for each error type
- Graceful degradation wrappers
- Post-incident evidence bundle

## Resources

- [PostHog Status Page](https://status.posthog.com)
- [PostHog Support](https://posthog.com/docs/support)
- [PostHog API Overview](https://posthog.com/docs/api)

## Next Steps

For data handling, see `posthog-data-handling`.
