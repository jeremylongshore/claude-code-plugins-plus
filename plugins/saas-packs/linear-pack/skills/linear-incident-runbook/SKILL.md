---
name: linear-incident-runbook
description: |
  Production incident response procedures for Linear integrations.
  Use when handling production issues, diagnosing outages,
  or responding to Linear-related incidents.
  Trigger: "linear incident", "linear outage", "linear production issue",
  "debug linear production", "linear down", "linear 500".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, debugging, incident-response]

---
# Linear Incident Runbook

## Overview
Step-by-step runbooks for handling production incidents with Linear integrations. Covers API authentication failures, rate limiting, webhook issues, and Linear platform outages.

## Incident Classification

| Severity | Impact | Response | Examples |
|----------|--------|----------|----------|
| SEV1 | Complete integration outage | < 15 min | Auth broken, API unreachable |
| SEV2 | Major degradation | < 30 min | High error rate, rate limited |
| SEV3 | Minor issues | < 2 hours | Some features affected |
| SEV4 | Low impact | < 24 hours | Warnings, non-critical |

## Immediate Actions (All Incidents)

### Step 1: Confirm the Issue
```bash
set -euo pipefail

# 1. Check Linear platform status
curl -s https://status.linear.app/api/v2/status.json | jq '.status'

# 2. Test your API key
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name email } }"}' | jq .

# 3. Check rate limit status
curl -s -I -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id } }"}' 2>&1 | grep -i ratelimit

# 4. Check your app health endpoint
curl -s https://yourapp.com/health/linear | jq .
```

### Step 2: Gather Diagnostic Info
```typescript
// scripts/incident-diagnostic.ts
import { LinearClient } from "@linear/sdk";

async function diagnose() {
  console.log("=== Linear Incident Diagnostic ===\n");

  // 1. Auth check
  console.log("1. Authentication:");
  try {
    const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
    const viewer = await client.viewer;
    console.log(`   OK: ${viewer.name} (${viewer.email})`);
  } catch (error: any) {
    console.log(`   FAILED: ${error.message}`);
  }

  // 2. Team access
  console.log("\n2. Team Access:");
  try {
    const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
    const teams = await client.teams();
    console.log(`   OK: ${teams.nodes.length} teams accessible`);
    teams.nodes.forEach(t => console.log(`     ${t.key}: ${t.name}`));
  } catch (error: any) {
    console.log(`   FAILED: ${error.message}`);
  }

  // 3. Write test
  console.log("\n3. Write Capability:");
  try {
    const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
    const teams = await client.teams();
    const result = await client.createIssue({
      teamId: teams.nodes[0].id,
      title: "[INCIDENT-DIAG] Safe to delete",
    });
    if (result.success) {
      const issue = await result.issue;
      await issue?.delete();
      console.log("   OK: Created and deleted test issue");
    }
  } catch (error: any) {
    console.log(`   FAILED: ${error.message}`);
  }

  // 4. Rate limit check
  console.log("\n4. Rate Limits:");
  try {
    const resp = await fetch("https://api.linear.app/graphql", {
      method: "POST",
      headers: {
        Authorization: process.env.LINEAR_API_KEY!,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: "{ viewer { id } }" }),
    });
    const remaining = resp.headers.get("x-ratelimit-requests-remaining");
    const limit = resp.headers.get("x-ratelimit-requests-limit");
    console.log(`   Requests: ${remaining}/${limit}`);
  } catch (error: any) {
    console.log(`   FAILED: ${error.message}`);
  }

  console.log("\n=== End Diagnostic ===");
}

diagnose();
```

## Runbook: API Authentication Failure

**Symptoms:** All API calls returning 401/403, "Authentication required" errors

**Diagnosis:**
```bash
set -euo pipefail
# Verify API key format
echo $LINEAR_API_KEY | head -c 8
# Should output: lin_api_

# Test directly
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id } }"}' | jq .errors
```

**Resolution:**
1. Verify key is loaded: `[ -n "$LINEAR_API_KEY" ] && echo "Set" || echo "NOT set"`
2. Check if rotated: Linear Settings > Account > API > Personal API keys
3. Generate new key if needed, update secret manager
4. Restart affected services
5. If recent deploy caused it: `git revert HEAD && npm run deploy`

## Runbook: Rate Limiting (HTTP 429)

**Symptoms:** HTTP 429 responses, "Rate limit exceeded", degraded performance

**Diagnosis:**
```bash
set -euo pipefail
curl -s -I -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id } }"}' 2>&1 | grep -i ratelimit
```

**Resolution:**
1. **Emergency throttle** -- add 5s delay between all requests:
   ```typescript
   const EMERGENCY_DELAY_MS = 5000;
   async function emergencyThrottle<T>(fn: () => Promise<T>): Promise<T> {
     await new Promise(r => setTimeout(r, EMERGENCY_DELAY_MS));
     return fn();
   }
   ```
2. Stop non-critical background jobs (polling, sync)
3. Disable bulk operations
4. Wait for bucket refill (Linear uses leaky bucket, refills continuously)
5. Post-incident: implement proper request queue and caching

## Runbook: Webhook Failures

**Symptoms:** Events not received, signature validation errors, processing timeouts

**Diagnosis:**
```bash
set -euo pipefail
# Check endpoint is reachable
curl -s -o /dev/null -w "%{http_code}" https://yourapp.com/webhooks/linear

# Verify secret length
echo -n "$LINEAR_WEBHOOK_SECRET" | wc -c
# Should be > 20 characters
```

**Resolution:**
1. **Endpoint unreachable:** Check DNS, SSL cert, firewall, load balancer health
2. **Signature mismatch:** Verify `LINEAR_WEBHOOK_SECRET` matches webhook config in Linear Settings > API > Webhooks
3. **Body parsing issue:** Ensure using `express.raw()` not `express.json()`
4. **Processing timeout:** Respond 200 immediately, process async
5. **Recreate webhook:** Linear Settings > API > Webhooks > delete + recreate

## Runbook: Linear Platform Outage

**Symptoms:** All API calls failing, status.linear.app reports issues

**Resolution:**
1. Confirm at https://status.linear.app
2. Enable graceful degradation in your app
3. Queue write operations for replay when API recovers
4. Serve cached data for read operations
5. Monitor status page for resolution
6. After recovery: run consistency check to detect missed webhook events

## Communication Templates

### Initial Announcement
```
INCIDENT: Linear Integration Issue
Severity: SEVX
Status: Investigating
Impact: [description]
Start: [UTC timestamp]

Investigating issues with Linear integration. Updates to follow.
```

### Resolution
```
RESOLVED: Linear Integration Issue
Duration: X hours Y minutes
Root Cause: [brief]
Impact: [what was affected]

Post-mortem within 48 hours.
```

## Post-Incident Checklist
```
[ ] All systems verified healthy
[ ] Stuck/queued jobs cleared
[ ] Data consistency validated
[ ] Stakeholders notified of resolution
[ ] Timeline documented
[ ] Root cause identified
[ ] Action items assigned
[ ] Monitoring gaps addressed
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Auth failure | Expired/rotated key | Regenerate and update secret manager |
| Rate limit | Budget exceeded | Emergency throttle, stop background jobs |
| Webhook failure | Secret mismatch or endpoint down | Verify secret, check endpoint health |
| Platform outage | Linear infrastructure issue | Graceful degradation, serve cached data |

## Resources
- [Linear Status Page](https://status.linear.app)
- [Linear API Documentation](https://linear.app/developers)
- [Rate Limiting](https://linear.app/developers/rate-limiting)
