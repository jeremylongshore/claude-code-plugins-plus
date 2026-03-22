---
name: customerio-advanced-troubleshooting
description: |
  Apply Customer.io advanced debugging and incident response.
  Use when diagnosing complex delivery issues, investigating
  campaign failures, or running incident playbooks.
  Trigger: "debug customer.io", "customer.io investigation",
  "customer.io troubleshoot", "customer.io incident", "customer.io not delivering".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, debugging, incident-response]

---
# Customer.io Advanced Troubleshooting

## Overview

Advanced debugging techniques for complex Customer.io issues: systematic investigation framework, API debug client, user profile analysis, campaign/broadcast debugging, network diagnostics, and incident response runbooks.

## Prerequisites

- Access to Customer.io dashboard (admin recommended)
- Application logs access
- `curl` for API testing

## Troubleshooting Framework

For every issue, answer these five questions first:

1. **What** is the expected vs actual behavior?
2. **When** did the issue start? (Check deploy history, CIO status page)
3. **Who** is affected — one user, a segment, or everyone?
4. **Where** in the pipeline — API call, delivery, or rendering?
5. **How** often — every time, intermittent, or one-time?

## Instructions

### Step 1: API Debug Client

```typescript
// lib/customerio-debug.ts
import { TrackClient, APIClient, RegionUS } from "customerio-node";

export class DebugCioClient {
  private track: TrackClient;

  constructor() {
    this.track = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_TRACK_API_KEY!,
      { region: RegionUS }
    );
  }

  async debugIdentify(userId: string, attrs: Record<string, any>) {
    console.log(`\n--- Debug: identify("${userId}") ---`);
    console.log("Attributes:", JSON.stringify(attrs, null, 2));

    const start = Date.now();
    try {
      await this.track.identify(userId, attrs);
      const latency = Date.now() - start;
      console.log(`Result: SUCCESS (${latency}ms)`);
      return { success: true, latency };
    } catch (err: any) {
      const latency = Date.now() - start;
      console.log(`Result: FAILED (${latency}ms)`);
      console.log(`Status: ${err.statusCode}`);
      console.log(`Message: ${err.message}`);
      console.log(`Body: ${JSON.stringify(err.body ?? err.response)}`);
      return { success: false, latency, statusCode: err.statusCode, message: err.message };
    }
  }

  async debugTrack(userId: string, name: string, data?: any) {
    console.log(`\n--- Debug: track("${userId}", "${name}") ---`);
    console.log("Data:", JSON.stringify(data, null, 2));

    const start = Date.now();
    try {
      await this.track.track(userId, { name, data });
      const latency = Date.now() - start;
      console.log(`Result: SUCCESS (${latency}ms)`);
      return { success: true, latency };
    } catch (err: any) {
      const latency = Date.now() - start;
      console.log(`Result: FAILED (${latency}ms)`);
      console.log(`Status: ${err.statusCode}`);
      console.log(`Message: ${err.message}`);
      return { success: false, latency, statusCode: err.statusCode };
    }
  }
}
```

### Step 2: User Investigation Script

```bash
#!/usr/bin/env bash
set -euo pipefail
# scripts/investigate-user.sh <user-id>

USER_ID="${1:?Usage: investigate-user.sh <user-id>}"
SITE_ID="${CUSTOMERIO_SITE_ID:?Missing CUSTOMERIO_SITE_ID}"
API_KEY="${CUSTOMERIO_TRACK_API_KEY:?Missing CUSTOMERIO_TRACK_API_KEY}"

echo "=== Investigating User: ${USER_ID} ==="
echo ""

# 1. Check if user exists (try to identify with minimal data)
echo "--- API Connectivity Test ---"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "${SITE_ID}:${API_KEY}" \
  -X PUT "https://track.customer.io/api/v1/customers/${USER_ID}" \
  -H "Content-Type: application/json" \
  -d '{"_debug_check":"true"}')
echo "Track API for user: HTTP ${HTTP_CODE}"

echo ""
echo "--- Dashboard Checklist ---"
echo "Check the following in Customer.io dashboard:"
echo "1. People > Search '${USER_ID}'"
echo "   - Does profile exist?"
echo "   - Does it have an email attribute?"
echo "   - Is there a 'Suppressed' badge?"
echo ""
echo "2. Activity tab:"
echo "   - Are events being received?"
echo "   - Any bounce/complaint events?"
echo "   - Last identify timestamp correct?"
echo ""
echo "3. Segments tab:"
echo "   - Which segments does user belong to?"
echo "   - Does segment match campaign audience?"
echo ""
echo "4. Campaigns > Find relevant campaign:"
echo "   - Is campaign status Active?"
echo "   - Does trigger event match?"
echo "   - Check 'Messages' tab for delivery attempts"
```

### Step 3: Campaign Debugging

Common campaign issues and their investigation path:

| Symptom | Check First | Then Check |
|---------|------------|------------|
| Campaign not triggering | Event name match (case-sensitive) | Campaign status (Active?) |
| User not matched | Segment conditions | User attributes match segment? |
| Email not delivered | User has `email` attribute | Bounce/suppression status |
| Liquid template broken | `message_data` has all required fields | Preview with real data in dashboard |
| Wrong email content | Correct campaign version is Active | Template variables populated |
| Delayed sends | Campaign "Wait" steps | Queue backlog in Customer.io |

```typescript
// Programmatic campaign debug
async function debugCampaignTrigger(
  userId: string,
  eventName: string,
  eventData: Record<string, any>
) {
  const debug = new DebugCioClient();

  console.log("=== Campaign Trigger Debug ===\n");

  // 1. Can we identify the user?
  const identifyResult = await debug.debugIdentify(userId, {
    _debug_campaign_check: true,
  });

  if (!identifyResult.success) {
    console.log("\nBLOCKER: Cannot identify user. Fix auth first.");
    return;
  }

  // 2. Can we track the event?
  const trackResult = await debug.debugTrack(userId, eventName, eventData);

  if (!trackResult.success) {
    console.log("\nBLOCKER: Cannot track event. Check error above.");
    return;
  }

  console.log("\n=== API Side OK ===");
  console.log("If campaign still not triggering, check in dashboard:");
  console.log(`1. Event name: "${eventName}" (must match exactly, case-sensitive)`);
  console.log("2. Campaign status: must be Active (not Draft/Paused)");
  console.log("3. Campaign audience: user must match segment/filter");
  console.log("4. Campaign frequency: check if user already received");
  console.log("5. Suppression: check if user is suppressed");
}
```

### Step 4: Network Diagnostics

```bash
#!/usr/bin/env bash
set -euo pipefail
# scripts/cio-network-diag.sh

echo "=== Customer.io Network Diagnostics ==="
echo ""

# DNS resolution
echo "--- DNS Resolution ---"
for host in track.customer.io api.customer.io status.customer.io; do
  IP=$(dig +short "$host" 2>/dev/null | head -1)
  echo "${host}: ${IP:-FAILED}"
done

echo ""

# TLS check
echo "--- TLS Certificate ---"
echo | openssl s_client -connect track.customer.io:443 -servername track.customer.io 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates 2>/dev/null \
  || echo "TLS check failed"

echo ""

# Latency test
echo "--- Latency (5 samples) ---"
for i in $(seq 1 5); do
  LATENCY=$(curl -s -o /dev/null -w "%{time_total}" "https://track.customer.io")
  echo "Request ${i}: ${LATENCY}s"
done

echo ""

# Status page
echo "--- Platform Status ---"
curl -s "https://status.customer.io/api/v2/status.json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"][\"description\"]}')" \
  2>/dev/null || echo "Could not fetch status"
```

### Step 5: Incident Response Runbooks

**P1 — Complete outage (all API calls failing):**
1. Check https://status.customer.io — is Customer.io down?
2. If CIO is up: check your credentials (rotate if compromised)
3. Enable circuit breaker to stop retries hitting a dead endpoint
4. Switch to fallback queue (events stored in Redis/Kafka)
5. Notify affected teams
6. When restored: drain fallback queue, verify event delivery

**P2 — High error rate (>5% failures):**
1. Check error breakdown: which status codes?
2. If 429: reduce concurrency, check rate limiter config
3. If 5xx: check CIO status page, enable backoff
4. If 401: credentials may have been rotated — check secrets manager
5. Monitor error rate — escalate to P1 if not recovering

**P3 — Delivery issues (messages not arriving):**
1. Verify user has `email` attribute (People > user profile)
2. Check suppression status (Suppressed badge)
3. Check bounce history (Activity tab > filter bounces)
4. Verify sending domain (Settings > Sending Domains)
5. Check campaign is Active, trigger event matches
6. Review spam folder and email headers

**P4 — Webhook processing failures:**
1. Verify webhook endpoint is publicly accessible
2. Check signature verification (secret matches dashboard?)
3. Review webhook event logs for parsing errors
4. Check queue health if using async processing
5. Verify Customer.io IP allowlist if using firewall

## Diagnostic Commands

```bash
# Quick API health check
curl -s -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_TRACK_API_KEY" \
  -X PUT "https://track.customer.io/api/v1/customers/health-check" \
  -H "Content-Type: application/json" \
  -d '{"_diag":true}' \
  -w "\nHTTP: %{http_code} Time: %{time_total}s\n"

# Check App API
curl -s -H "Authorization: Bearer $CUSTOMERIO_APP_API_KEY" \
  "https://api.customer.io/v1/campaigns" \
  -w "\nHTTP: %{http_code}\n" | head -5

# Platform status
curl -s "https://status.customer.io/api/v2/status.json" | python3 -m json.tool
```

## Error Handling

| Issue | Solution |
|-------|----------|
| Intermittent 5xx | Transient — retry with backoff handles it |
| Consistent 401 after deploy | Credentials changed — check env vars and secrets |
| User receiving duplicate messages | Event deduplication or campaign frequency cap |
| Webhook events stop arriving | Check endpoint health, CIO IP allowlist, SSL cert validity |

## Resources

- [Customer.io Status Page](https://status.customer.io/)
- [Customer.io Community](https://community.customer.io/)
- [Reporting Webhooks Reference](https://docs.customer.io/integrations/api/webhooks/)
- [Troubleshooting Deliverability](https://docs.customer.io/journeys/deliverability/)

## Next Steps

After troubleshooting, proceed to `customerio-reliability-patterns` for fault tolerance.
