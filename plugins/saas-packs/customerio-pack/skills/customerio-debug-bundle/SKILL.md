---
name: customerio-debug-bundle
description: |
  Collect Customer.io debug evidence for support tickets.
  Use when creating support requests, investigating delivery
  failures, or documenting integration issues.
  Trigger: "customer.io debug", "customer.io support ticket",
  "collect customer.io logs", "customer.io diagnostics".
allowed-tools: Read, Grep, Bash(curl:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, debugging, support]

---
# Customer.io Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'Node.js: not installed'`
!`npm list customerio-node 2>/dev/null | grep customerio || echo 'customerio-node: not installed'`

## Overview

Collect a comprehensive debug bundle for Customer.io support tickets: API connectivity tests, user profile inspection, SDK version info, environment validation, and a structured support report.

## Prerequisites

- Customer.io API credentials configured
- `curl` available for API tests
- User ID or email of the affected user/delivery

## Instructions

### Step 1: API Connectivity Diagnostic

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Customer.io Debug Bundle ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# 1. Check Customer.io status
echo "--- Platform Status ---"
curl -s "https://status.customer.io/api/v2/status.json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"][\"description\"]}')" \
  2>/dev/null || echo "Could not reach status page"

# 2. Test Track API authentication
echo ""
echo "--- Track API Auth ---"
TRACK_RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "${CUSTOMERIO_SITE_ID}:${CUSTOMERIO_TRACK_API_KEY}" \
  -X PUT "https://track.customer.io/api/v1/customers/debug-test-$(date +%s)" \
  -H "Content-Type: application/json" \
  -d '{"email":"debug-test@example.com"}')
echo "Track API: HTTP ${TRACK_RESULT}"

# 3. Test App API authentication
echo ""
echo "--- App API Auth ---"
APP_RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${CUSTOMERIO_APP_API_KEY}" \
  "https://api.customer.io/v1/campaigns")
echo "App API: HTTP ${APP_RESULT}"

# 4. DNS and latency
echo ""
echo "--- Network Diagnostics ---"
for host in track.customer.io api.customer.io; do
  LATENCY=$(curl -s -o /dev/null -w "%{time_total}" "https://${host}")
  echo "${host}: ${LATENCY}s"
done
```

### Step 2: User Profile Investigation

```typescript
// scripts/debug-user.ts
// Investigate a specific user's state in Customer.io
import { TrackClient, APIClient, RegionUS } from "customerio-node";

async function investigateUser(userId: string) {
  const cio = new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_TRACK_API_KEY!,
    { region: RegionUS }
  );

  console.log(`\n=== User Investigation: ${userId} ===\n`);

  // Test if we can identify (update) the user — confirms they exist
  try {
    await cio.identify(userId, {
      _debug_checked_at: Math.floor(Date.now() / 1000),
    });
    console.log("Profile: EXISTS (identify succeeded)");
  } catch (err: any) {
    console.log(`Profile: ERROR (${err.statusCode}: ${err.message})`);
  }

  // Test if we can track an event on the user
  try {
    await cio.track(userId, {
      name: "debug_check",
      data: { checked_at: new Date().toISOString() },
    });
    console.log("Event tracking: WORKING");
  } catch (err: any) {
    console.log(`Event tracking: ERROR (${err.statusCode}: ${err.message})`);
  }

  // Check suppression status by trying to unsuppress
  // (If user is not suppressed, this is a no-op)
  console.log("\nNote: Check suppression status in Customer.io dashboard:");
  console.log(`  People > Search "${userId}" > check Suppressed badge`);
  console.log("  Also check Activity tab for bounce/complaint events");
}

const userId = process.argv[2];
if (!userId) {
  console.error("Usage: npx tsx scripts/debug-user.ts <user-id>");
  process.exit(1);
}
investigateUser(userId);
```

### Step 3: SDK and Environment Info

```typescript
// scripts/debug-env.ts
import { readFileSync } from "fs";

function collectEnvInfo() {
  const report: Record<string, string> = {};

  // Node.js version
  report["node_version"] = process.version;
  report["platform"] = `${process.platform} ${process.arch}`;

  // SDK version
  try {
    const pkg = JSON.parse(
      readFileSync("node_modules/customerio-node/package.json", "utf-8")
    );
    report["customerio_node_version"] = pkg.version;
  } catch {
    report["customerio_node_version"] = "NOT INSTALLED";
  }

  // Environment config (redacted)
  report["site_id_set"] = process.env.CUSTOMERIO_SITE_ID ? "YES" : "NO";
  report["track_key_set"] = process.env.CUSTOMERIO_TRACK_API_KEY ? "YES" : "NO";
  report["app_key_set"] = process.env.CUSTOMERIO_APP_API_KEY ? "YES" : "NO";
  report["region"] = process.env.CUSTOMERIO_REGION ?? "us (default)";

  // Redacted key prefix for identification
  const siteId = process.env.CUSTOMERIO_SITE_ID ?? "";
  report["site_id_prefix"] = siteId.substring(0, 4) + "...";

  console.log("\n=== Environment Debug Info ===\n");
  for (const [key, value] of Object.entries(report)) {
    console.log(`${key}: ${value}`);
  }
}

collectEnvInfo();
```

### Step 4: Generate Support Report

```typescript
// scripts/generate-support-report.ts
function generateReport(issue: {
  summary: string;
  userId?: string;
  deliveryId?: string;
  errorCode?: number;
  errorMessage?: string;
  reproducible: boolean;
  startedAt?: string;
}) {
  const report = `
## Customer.io Support Report
Generated: ${new Date().toISOString()}

### Issue Summary
${issue.summary}

### Affected Resources
- User ID: ${issue.userId ?? "N/A"}
- Delivery ID: ${issue.deliveryId ?? "N/A"}
- Error Code: ${issue.errorCode ?? "N/A"}
- Error Message: ${issue.errorMessage ?? "N/A"}

### Reproduction
- Reproducible: ${issue.reproducible ? "Yes" : "Intermittent"}
- First observed: ${issue.startedAt ?? "Unknown"}

### Environment
- Node.js: ${process.version}
- Region: ${process.env.CUSTOMERIO_REGION ?? "us"}
- Site ID prefix: ${(process.env.CUSTOMERIO_SITE_ID ?? "").substring(0, 4)}...

### Steps to Reproduce
1. [Describe the action taken]
2. [Describe the expected result]
3. [Describe the actual result]

### Attachments
- [ ] Application logs (relevant time window)
- [ ] API request/response captures
- [ ] Screenshot of user profile in dashboard
- [ ] Screenshot of campaign/broadcast configuration
`.trim();

  console.log(report);
}
```

### Step 5: Collect Application Logs

```bash
# Collect recent Customer.io related logs (adjust path for your setup)
# Grep for CIO/customerio in your application logs
grep -i "customer\\.io\\|customerio\\|cio_" /var/log/app/*.log \
  | tail -100 \
  > /tmp/cio-debug-logs.txt 2>/dev/null

# Or from Docker
docker logs your-app-container 2>&1 \
  | grep -i "customer\\.io\\|customerio\\|cio_" \
  | tail -100 \
  > /tmp/cio-debug-logs.txt

# Redact sensitive data before sharing
sed -i 's/\(api_key\|apikey\|secret\)=[^&]*/\1=REDACTED/gi' /tmp/cio-debug-logs.txt
```

## Debug Checklist

- [ ] Customer.io status page checked (https://status.customer.io)
- [ ] Track API auth verified (HTTP 200)
- [ ] App API auth verified (HTTP 200)
- [ ] User profile exists and has `email` attribute
- [ ] User is not suppressed
- [ ] SDK version documented
- [ ] Region configuration correct (US vs EU)
- [ ] Error logs collected and redacted
- [ ] Reproduction steps documented

## Error Handling

| Issue | Solution |
|-------|----------|
| Status page unreachable | Check your network; try from a different network |
| Both APIs return 401 | Credentials are wrong — regenerate in dashboard |
| Track OK but App 401 | Using Track API key for App API — they're separate keys |
| Logs contain PII | Run redaction script before sharing with support |

## Resources

- [Customer.io Support](https://customer.io/contact/)
- [Customer.io Community](https://community.customer.io/)
- [Status Page](https://status.customer.io/)

## Next Steps

After creating debug bundle, proceed to `customerio-rate-limits` to implement proper rate limiting.
