---
name: linear-incident-runbook
description: |
  Production incident response procedures for Linear integrations.
  Use when handling production issues, diagnosing outages,
  or responding to Linear-related incidents.
  Trigger with phrases like "linear incident", "linear outage",
  "linear production issue", "debug linear production", "linear down".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Incident Runbook

## Overview
Step-by-step procedures for handling production incidents with Linear integrations.

## Prerequisites
- Production access credentials
- Monitoring dashboard access
- Communication channels configured
- Escalation paths defined

## Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| SEV1 | Complete outage | < 15 minutes | API unreachable, auth broken |
| SEV2 | Major degradation | < 30 minutes | High error rate, slow responses |
| SEV3 | Minor issues | < 2 hours | Some features affected |
| SEV4 | Low impact | < 24 hours | Cosmetic issues, warnings |

## Immediate Actions

### Step 1: Confirm the Issue
```bash
set -euo pipefail
# Check Linear API status
curl -s https://status.linear.app/api/v2/status.json | jq '.status'

# Quick health check
curl -s -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name } }"}' \
  https://api.linear.app/graphql | jq

# Check your application health endpoint
curl -s https://yourapp.com/api/health | jq
```

### Step 2: Gather Initial Information
```typescript
// scripts/incident-info.ts
import { LinearClient } from "@linear/sdk";

async function gatherIncidentInfo() {
  const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

  console.log("=== Linear Incident Information ===\n");

  // 1. Test authentication
  console.log("1. Authentication:");
  try {
    const viewer = await client.viewer;
    console.log(`   Status: OK (${viewer.name})`);
  } catch (error) {
    console.log(`   Status: FAILED - ${error}`);
  }

  // 2. Check teams access
  console.log("\n2. Team Access:");
  try {
    const teams = await client.teams();
    console.log(`   Accessible teams: ${teams.nodes.length}`);
  } catch (error) {
    console.log(`   Status: FAILED - ${error}`);
  }

  // 3. Test issue creation (dry run)
  console.log("\n3. Write Capability:");
  try {
    const teams = await client.teams();
    const result = await client.createIssue({
      teamId: teams.nodes[0].id,
      title: "[INCIDENT TEST] Delete immediately",
    });
    if (result.success) {
      const issue = await result.issue;
      await issue?.delete();
      console.log("   Status: OK (created and deleted test issue)");
    }
  } catch (error) {
    console.log(`   Status: FAILED - ${error}`);
  }

  console.log("\n=== End Information ===");
}

gatherIncidentInfo();
```

## Runbook: API Authentication Failure

### Symptoms
- All API calls returning 401/403
- "Authentication required" errors
- Sudden spike in auth errors

### Diagnosis
```bash
set -euo pipefail
# Test API key directly
curl -I -H "Authorization: $LINEAR_API_KEY" \
  https://api.linear.app/graphql

# Check for key format issues
echo $LINEAR_API_KEY | head -c 8
# Should output: lin_api_

# Verify key in secrets manager
vault read secret/data/linear/production
# or
aws secretsmanager get-secret-value --secret-id linear/production
```

### Resolution Steps
1. **Verify API key is loaded correctly**
   ```bash
   # Check env var is set (don't print actual key)
   [ -n "$LINEAR_API_KEY" ] && echo "Key is set" || echo "Key is NOT set"
   ```

2. **Check if key was rotated/revoked**
   - Log into Linear dashboard
   - Navigate to Settings > API > Personal API keys
   - Verify key exists and is active

3. **Generate new API key if needed**
   - Create new key in Linear dashboard
   - Update secrets manager
   - Restart affected services

4. **Rollback if recent deployment**
   ```bash
   # Check last deployment
   git log --oneline -5

   # Rollback to previous version
   git revert HEAD
   ```

## Runbook: Rate Limiting Issues

### Symptoms
- HTTP 429 responses
- "Rate limit exceeded" errors
- Degraded performance

### Diagnosis
```bash
set -euo pipefail
# Check current rate limit status
curl -I -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { name } }"}' \
  https://api.linear.app/graphql 2>&1 | grep -i ratelimit

# Check application metrics
curl -s http://localhost:9090/api/v1/query?query=linear_rate_limit_remaining | jq  # 9090: Prometheus port
```

### Resolution Steps
1. **Identify rate limit cause**
   ```bash
   # Check request patterns
   grep "linear" /var/log/app/*.log | grep -E "[0-9]{4}-[0-9]{2}-[0-9]{2}" | wc -l
   ```

2. **Implement emergency throttling**
   ```typescript
   // Emergency rate limiter
   const EMERGENCY_MODE = true;
   const MIN_DELAY_MS = 5000;

   async function emergencyThrottle<T>(fn: () => Promise<T>): Promise<T> {
     if (EMERGENCY_MODE) {
       await new Promise(r => setTimeout(r, MIN_DELAY_MS));
     }
     return fn();
   }
   ```

3. **Disable non-critical operations**
   - Stop background sync jobs
   - Disable polling (if using)
   - Queue non-urgent requests

4. **Wait for rate limit reset**
   - Linear resets every minute
   - Monitor X-RateLimit-Reset header

## Runbook: Webhook Failures

### Symptoms
- Events not being received
- Webhook signature validation failing
- Processing timeouts

### Diagnosis
```bash
set -euo pipefail
# Check webhook endpoint is reachable
curl -I https://yourapp.com/api/webhooks/linear

# Check recent webhook logs
tail -100 /var/log/webhooks.log | grep linear

# Verify webhook secret
echo $LINEAR_WEBHOOK_SECRET | wc -c
# Should be > 20 characters
```

### Resolution Steps
1. **Verify endpoint health**
   ```typescript
   app.get("/api/webhooks/linear/health", (req, res) => {
     res.json({ status: "ok", timestamp: new Date().toISOString() });
   });
   ```

2. **Check signature verification**
   ```typescript
   // Debug signature verification
   function debugVerifySignature(payload: string, signature: string): boolean {
     const secret = process.env.LINEAR_WEBHOOK_SECRET!;
     const expected = crypto.createHmac("sha256", secret).update(payload).digest("hex");

     console.log("Debug: Received signature:", signature);
     console.log("Debug: Expected signature:", expected);
     console.log("Debug: Secret length:", secret.length);

     return signature === expected;
   }
   ```

3. **Recreate webhook if needed**
   - Go to Linear Settings > API > Webhooks
   - Delete existing webhook
   - Create new webhook with same URL
   - Update webhook secret in secrets manager

## Communication Templates

### Initial Incident Announcement
```markdown
**INCIDENT: Linear Integration Issue**
Severity: SEVX
Status: Investigating
Impact: [Description of user impact]
Start Time: [UTC timestamp]

We are investigating issues with our Linear integration. Updates will follow.
```

### Status Update
```markdown
**UPDATE: Linear Integration Issue**
Status: [Investigating/Identified/Mitigating/Resolved]
Time: [UTC timestamp]

Update: [What we know/did]
Next Steps: [What we're doing next]
ETA: [If known]
```

### Resolution Notice
```markdown
**RESOLVED: Linear Integration Issue**
Duration: [X hours Y minutes]
Root Cause: [Brief description]
Impact: [What was affected]

A full post-mortem will follow within 48 hours.
```

## Post-Incident

### Immediate Actions
```
[ ] Verify all systems are healthy
[ ] Clear any queued/stuck jobs
[ ] Validate data consistency
[ ] Notify stakeholders of resolution
```

### Post-Mortem Checklist
```
[ ] Timeline of events
[ ] Root cause analysis
[ ] Impact assessment
[ ] What went well
[ ] What could be improved
[ ] Action items with owners
```

## Resources
- [Linear Status Page](https://status.linear.app)
- [Linear API Documentation](https://developers.linear.app/docs)
- Internal: On-call runbook wiki
- Internal: Escalation contacts

## Next Steps
Learn data handling patterns with `linear-data-handling`.

## Instructions

1. Assess the current state of the debugging configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with debugging |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply linear incident runbook to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear incident runbook for production environments with multiple constraints and team-specific requirements.