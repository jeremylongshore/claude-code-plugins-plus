---
name: maintainx-incident-runbook
description: |
  Manage incident response for MaintainX integration failures.
  Use when experiencing outages, investigating issues,
  or responding to MaintainX integration incidents.
  Trigger with phrases like "maintainx incident", "maintainx outage",
  "maintainx down", "maintainx emergency", "maintainx runbook".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Incident Runbook

## Overview
Step-by-step procedures for responding to MaintainX integration incidents, from detection through resolution and post-mortem.

## Prerequisites
- Access to monitoring dashboards
- MaintainX admin API credentials
- On-call contact list

## Severity Classification

| Severity | Definition | Response Time |
|----------|-----------|---------------|
| **SEV-1** | Complete integration failure, no work orders processing | 15 min |
| **SEV-2** | Partial failure, some endpoints degraded | 1 hour |
| **SEV-3** | Performance degradation, slow responses | 4 hours |
| **SEV-4** | Non-critical feature broken, workaround available | Next business day |

## Instructions

### Step 1: Immediate Triage (First 5 Minutes)

```bash
#!/bin/bash
echo "=== MaintainX Incident Triage ==="
echo "Time: $(date -u)"

# Check MaintainX API status
echo -e "\n--- API Health ---"
for endpoint in users workorders assets locations; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://api.getmaintainx.com/v1/$endpoint?limit=1" \
    -H "Authorization: Bearer $MAINTAINX_API_KEY")
  echo "  /$endpoint: HTTP $CODE"
done

# Check your integration service
echo -e "\n--- Integration Service ---"
curl -s http://localhost:3000/health | jq . 2>/dev/null || echo "  Service unreachable"

# Check recent error logs
echo -e "\n--- Recent Errors (last 10 min) ---"
# Adjust for your log system:
# journalctl -u maintainx-sync --since "10 min ago" --no-pager | grep -i error | tail -10
```

### Step 2: Determine Root Cause

| Symptom | Likely Cause | Check |
|---------|-------------|-------|
| All endpoints return 401 | API key expired | `echo ${#MAINTAINX_API_KEY}` and test with curl |
| All endpoints return 5xx | MaintainX platform outage | Check [status.getmaintainx.com](https://status.getmaintainx.com) |
| 429 on all requests | Rate limit exceeded | Review request volume in last hour |
| Specific endpoint 404 | API path changed | Check [MaintainX changelog](https://developer.maintainx.com) |
| Timeouts | Network issue | `curl -w "Total: %time_total seconds" ...` |
| Your service crashes | Application error | Check container logs, OOM, disk space |

### Step 3: Apply Mitigation

**API Key Expired (SEV-1)**:
```bash
# Generate new key: MaintainX > Settings > Integrations > New Key
# Update in production:
# GCP Secret Manager:
echo -n "NEW_KEY_HERE" | gcloud secrets versions add maintainx-api-key --data-file=-
# Restart service to pick up new key:
gcloud run services update maintainx-integration --region us-central1 --no-traffic
```

**Rate Limited (SEV-2)**:
```typescript
// Immediately reduce request volume
// 1. Enable emergency rate limiting
process.env.MAINTAINX_MAX_REQUESTS_PER_SEC = '1';
// 2. Disable non-critical sync jobs
await disableScheduledJobs(['asset-sync', 'report-generator']);
// 3. Keep only critical work order processing
```

**MaintainX Platform Outage (SEV-1)**:
```typescript
// Switch to queue-based processing
// Buffer all outgoing requests for replay after recovery
const queue: Array<{ method: string; path: string; body: any }> = [];

function bufferRequest(method: string, path: string, body?: any) {
  queue.push({ method, path, body });
  console.log(`Buffered: ${method} ${path} (queue size: ${queue.length})`);
}

// When MaintainX recovers, replay buffered requests
async function replayQueue(client: MaintainXClient) {
  console.log(`Replaying ${queue.length} buffered requests...`);
  for (const req of queue) {
    await withRetry(() => client.request(req.method, req.path, req.body));
  }
  queue.length = 0;
}
```

### Step 4: Verify Resolution

```bash
# Run full health check
curl -s http://localhost:3000/health | jq .

# Verify data flow
echo "Work orders created in last hour:"
curl -s "https://api.getmaintainx.com/v1/workorders?createdAtGte=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)&limit=5" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq '.workOrders | length'

# Check for data gaps
echo "Checking sync state..."
cat .maintainx-sync-state.json 2>/dev/null || echo "No sync state file found"
```

### Step 5: Post-Incident Documentation

```markdown
## Incident Report Template

**Date**: YYYY-MM-DD
**Severity**: SEV-X
**Duration**: X hours Y minutes
**Impact**: [What was affected - e.g., "work order sync halted for 2 hours"]

### Timeline
- HH:MM - Alert triggered
- HH:MM - Triage started
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Full recovery confirmed

### Root Cause
[Technical explanation]

### Resolution
[What was done to fix it]

### Action Items
- [ ] Implement [specific improvement]
- [ ] Add monitoring for [gap found]
- [ ] Update runbook with [lesson learned]
```

## Output
- Incident triaged and severity classified
- Root cause identified using diagnostic steps
- Mitigation applied (key rotation, rate reduction, or request buffering)
- Recovery verified with health checks and data flow validation
- Post-incident report documented

## Error Handling
| Scenario | Immediate Action |
|----------|-----------------|
| Total API failure | Buffer requests, check status page, escalate |
| Intermittent 500s | Enable retry logic, reduce request rate |
| Data sync gap | Note gap window, schedule backfill after recovery |
| Webhook delivery failure | Fall back to polling, queue missed events |

## Resources
- [MaintainX Status Page](https://status.getmaintainx.com)
- [MaintainX API Reference](https://developer.maintainx.com/reference)
- [MaintainX Help Center](https://help.getmaintainx.com)

## Next Steps
For data handling patterns, see `maintainx-data-handling`.

## Examples

**Automated alerting on integration health**:

```typescript
// Check health every 5 minutes, alert on failure
import cron from 'node-cron';

cron.schedule('*/5 * * * *', async () => {
  try {
    const res = await fetch('http://localhost:3000/health');
    const health = await res.json();
    if (health.status !== 'healthy') {
      await sendPagerDutyAlert({
        severity: 'critical',
        summary: `MaintainX integration degraded: ${JSON.stringify(health.checks)}`,
      });
    }
  } catch {
    await sendPagerDutyAlert({
      severity: 'critical',
      summary: 'MaintainX integration service unreachable',
    });
  }
});
```
