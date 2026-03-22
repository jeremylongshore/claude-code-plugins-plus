---
name: customerio-prod-checklist
description: |
  Execute Customer.io production deployment checklist.
  Use when preparing for production launch, auditing integration
  quality, or performing pre-launch validation.
  Trigger: "customer.io production", "customer.io checklist",
  "deploy customer.io", "customer.io go-live", "customer.io launch".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, deployment, production, audit]

---
# Customer.io Production Checklist

## Overview

Comprehensive go-live checklist for Customer.io integrations: credentials audit, integration quality review, email deliverability setup, monitoring configuration, smoke tests, and staged rollout plan.

## Prerequisites

- Customer.io integration complete and tested in staging
- Production workspace credentials ready
- Sending domain configured and verified

## Production Checklist

### 1. Credentials & Configuration

| Item | Check | How to Verify |
|------|-------|---------------|
| Production Site ID | Correct workspace | Settings > API & Webhook Credentials |
| Production Track API Key | Different from dev/staging | Compare with staging `.env` |
| Production App API Key | Set for transactional messages | Test with `curl` bearer auth |
| Region setting | Matches account region (US/EU) | Settings > Workspace Settings |
| Secrets storage | In secrets manager, not `.env` | Check deployment config |
| Key rotation schedule | Documented (90-day cycle) | Calendar reminder set |

### 2. Integration Quality

```typescript
// scripts/prod-audit.ts
import { TrackClient, RegionUS } from "customerio-node";

async function auditIntegration() {
  const checks: { name: string; pass: boolean; detail: string }[] = [];

  // Check 1: Credentials exist
  const siteId = process.env.CUSTOMERIO_SITE_ID;
  const trackKey = process.env.CUSTOMERIO_TRACK_API_KEY;
  const appKey = process.env.CUSTOMERIO_APP_API_KEY;
  checks.push({
    name: "Track credentials",
    pass: !!(siteId && trackKey),
    detail: siteId ? `Site ID: ${siteId.substring(0, 4)}...` : "MISSING",
  });
  checks.push({
    name: "App API credential",
    pass: !!appKey,
    detail: appKey ? "Set" : "MISSING (needed for transactional)",
  });

  // Check 2: API connectivity
  if (siteId && trackKey) {
    const cio = new TrackClient(siteId, trackKey, { region: RegionUS });
    try {
      await cio.identify("prod-audit-test", {
        email: "prod-audit@example.com",
      });
      await cio.suppress("prod-audit-test");
      checks.push({ name: "Track API", pass: true, detail: "Connected" });
    } catch (err: any) {
      checks.push({
        name: "Track API",
        pass: false,
        detail: `${err.statusCode}: ${err.message}`,
      });
    }
  }

  // Report
  console.log("\n=== Customer.io Production Audit ===\n");
  for (const check of checks) {
    const icon = check.pass ? "PASS" : "FAIL";
    console.log(`[${icon}] ${check.name}: ${check.detail}`);
  }
  const passed = checks.filter((c) => c.pass).length;
  console.log(`\nResult: ${passed}/${checks.length} passed`);
  return checks.every((c) => c.pass);
}

auditIntegration().then((ok) => process.exit(ok ? 0 : 1));
```

### 3. Email Deliverability

| Item | Status | Dashboard Location |
|------|--------|-------------------|
| Sending domain verified | Required | Settings > Sending Domains |
| SPF record published | Required | DNS TXT record |
| DKIM record published | Required | DNS CNAME record |
| DMARC policy set | Recommended | DNS TXT record `_dmarc.yourdomain.com` |
| Return-Path configured | Recommended | Settings > Sending Domains |
| Unsubscribe link in all marketing emails | Required (CAN-SPAM) | Template editor |
| Physical address in marketing emails | Required (CAN-SPAM) | Template editor |

### 4. Campaign Readiness

- [ ] All campaigns tested with test sends
- [ ] Liquid templates render correctly (preview with real data)
- [ ] Segment conditions verified with known test users
- [ ] Transactional templates have all required `message_data` fields
- [ ] Broadcast triggers tested end-to-end
- [ ] Unsubscribe flow tested (click unsubscribe link, verify suppression)

### 5. Monitoring & Alerting

```typescript
// Set up these alerts in your monitoring system:
const ALERT_THRESHOLDS = {
  // API health
  api_error_rate: 0.01,       // Alert if > 1% of API calls fail
  api_p99_latency_ms: 5000,   // Alert if p99 > 5 seconds

  // Delivery health
  bounce_rate: 0.05,          // Alert if > 5% bounce rate
  complaint_rate: 0.001,      // Alert if > 0.1% spam complaints
  delivery_rate: 0.95,        // Alert if < 95% delivery rate

  // Operational health
  queue_depth: 10000,         // Alert if event queue > 10K pending
  webhook_error_rate: 0.05,   // Alert if > 5% webhook processing failures
};
```

### 6. Smoke Test Script

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Customer.io Production Smoke Test ==="

# Test 1: Track API connectivity
TRACK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "${CUSTOMERIO_SITE_ID}:${CUSTOMERIO_TRACK_API_KEY}" \
  -X PUT "https://track.customer.io/api/v1/customers/smoke-test-$(date +%s)" \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@example.com","_smoke_test":true}')

if [ "$TRACK_STATUS" = "200" ]; then
  echo "[PASS] Track API: HTTP 200"
else
  echo "[FAIL] Track API: HTTP ${TRACK_STATUS}"
  exit 1
fi

# Test 2: App API connectivity
APP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${CUSTOMERIO_APP_API_KEY}" \
  "https://api.customer.io/v1/campaigns")

if [ "$APP_STATUS" = "200" ]; then
  echo "[PASS] App API: HTTP 200"
else
  echo "[FAIL] App API: HTTP ${APP_STATUS}"
  exit 1
fi

echo ""
echo "All smoke tests passed"
```

### 7. Staged Rollout Plan

| Time | Action | Rollback Trigger |
|------|--------|-----------------|
| T-24h | Final staging test pass | Any test failure |
| T-12h | Production smoke tests | Smoke test failure |
| T-1h | Enable for internal team (feature flag) | Error reports |
| T-0 | Enable for 10% of users | Error rate > 1% |
| T+1h | Increase to 50% | Error rate > 1% or bounce rate > 5% |
| T+2h | 100% traffic | Same thresholds |
| T+24h | Post-launch review | N/A |

```typescript
// Feature flag integration for staged rollout
function shouldUseCio(userId: string, rolloutPercent: number): boolean {
  // Deterministic — same user always gets same result
  const hash = createHash("md5").update(userId).digest("hex");
  const bucket = parseInt(hash.substring(0, 8), 16) % 100;
  return bucket < rolloutPercent;
}
```

## Rollback Procedure

1. Set feature flag to 0% (immediate — no deploy needed)
2. Pause all active campaigns in Customer.io dashboard
3. Investigate logs and error reports
4. Fix issue, test in staging
5. Resume staged rollout from 10%

## Error Handling

| Issue | Solution |
|-------|----------|
| Smoke test fails in production | Verify production credentials (different from staging) |
| High bounce rate post-launch | Check sending domain verification, review bounce logs |
| Spam complaints spike | Review email content, verify unsubscribe links work |
| Feature flag not working | Check feature flag service connectivity |

## Resources

- [Customer.io Email Deliverability](https://docs.customer.io/journeys/deliverability/)
- [Sending Domain Setup](https://docs.customer.io/accounts-and-workspaces/managing-credentials/)
- [Campaign Best Practices](https://docs.customer.io/journeys/campaigns-in-customerio/)

## Next Steps

After production launch, proceed to `customerio-upgrade-migration` for SDK maintenance.
