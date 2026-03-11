# MaintainX Incident Runbook - Implementation Guide

> Full implementation details and code examples for the `maintainx-incident-runbook` skill.

# MaintainX Incident Runbook

## Overview

Step-by-step procedures for responding to MaintainX integration incidents, from detection through resolution.

## Prerequisites

- Access to monitoring dashboards
- MaintainX admin credentials
- On-call contact information

## Incident Classification

| Severity | Definition | Response Time | Example |
|----------|------------|---------------|---------|
| SEV1 | Complete outage | 15 min | API unreachable |
| SEV2 | Major degradation | 30 min | >50% errors |
| SEV3 | Minor degradation | 2 hours | Elevated latency |
| SEV4 | Informational | Next business day | Low cache hit rate |

## Incident Response Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   DETECT    │────▶│   TRIAGE    │────▶│  DIAGNOSE   │
│             │     │             │     │             │
│ Alert fires │     │ Determine   │     │ Identify    │
│ User report │     │ severity    │     │ root cause  │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                          │                    │
                          ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CLOSE     │◀────│   RECOVER   │◀────│  MITIGATE   │
│             │     │             │     │             │
│ Post-mortem │     │ Verify fix  │     │ Stop impact │
│ Document    │     │ Monitor     │     │ Temporary   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Runbook Procedures

### RB-001: MaintainX API Unreachable

**Symptoms:**
- All API calls failing with network errors
- Health check endpoint returning unhealthy
- Timeout errors in logs

**Diagnostic Steps:**

```bash
#!/bin/bash
# scripts/diagnose-api-unreachable.sh

echo "=== MaintainX API Connectivity Diagnostic ==="
echo ""

# Step 1: Basic connectivity
echo "1. Testing DNS resolution..."
nslookup api.getmaintainx.com

echo ""
echo "2. Testing TCP connectivity..."
nc -zv api.getmaintainx.com 443

echo ""
echo "3. Testing HTTPS endpoint..."
curl -v --max-time 10 https://api.getmaintainx.com/v1/users?limit=1 \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" 2>&1

echo ""
echo "4. Checking MaintainX status page..."
curl -s https://status.getmaintainx.com/api/v2/status.json | jq '.status.indicator'

echo ""
echo "5. Checking from different regions (if available)..."
# Add region-specific tests if you have multi-region deployment
```

**Mitigation:**
1. Check [MaintainX Status Page](https://status.getmaintainx.com)
2. If MaintainX is down: Enable fallback mode / cached responses
3. If local network: Check firewall, DNS, proxy settings
4. Escalate to network team if needed

**Resolution:**
- Wait for MaintainX restoration
- Verify connectivity restored
- Monitor for data sync catch-up

---

### RB-002: High Error Rate (>5%)

**Symptoms:**
- `MaintainXHighErrorRate` alert firing
- 4xx or 5xx errors in logs
- Failed work order operations

**Diagnostic Steps:**

```typescript
// scripts/diagnose-errors.ts

async function diagnoseHighErrorRate() {
  console.log('=== Error Rate Diagnostic ===\n');

  // Get recent error logs
  const errors = await getRecentErrors(100);

  // Group by error type
  const errorGroups = new Map<string, number>();
  errors.forEach(e => {
    const key = `${e.status}:${e.endpoint}`;
    errorGroups.set(key, (errorGroups.get(key) || 0) + 1);
  });

  console.log('Error distribution:');
  errorGroups.forEach((count, key) => {
    console.log(`  ${key}: ${count}`);
  });

  // Check for patterns
  console.log('\nCommon patterns:');

  const status401 = errors.filter(e => e.status === 401);
  if (status401.length > 0) {
    console.log('  - 401 Unauthorized: Check API key validity');
  }

  const status429 = errors.filter(e => e.status === 429);
  if (status429.length > 0) {
    console.log('  - 429 Rate Limited: Reduce request rate');
  }

  const status5xx = errors.filter(e => e.status >= 500);
  if (status5xx.length > 0) {
    console.log('  - 5xx Server Errors: MaintainX side issue');
  }
}
```

**Mitigation by Error Type:**

| Error | Immediate Action |
|-------|-----------------|
| 401 | Rotate API key |
| 403 | Check permissions |
| 429 | Enable throttling |
| 5xx | Enable circuit breaker |

**Resolution:**
- Fix underlying issue
- Clear error state
- Monitor for recurrence

---

### RB-003: Webhook Processing Failures

**Symptoms:**
- Webhooks not being processed
- Events missing in local system
- `webhook_failures` metric elevated

**Diagnostic Steps:**

```bash
#!/bin/bash
# Check webhook endpoint health
curl -v https://your-app.com/webhooks/maintainx/health

# Check webhook queue depth
redis-cli LLEN maintainx:webhook:queue

# Check recent failed webhooks
redis-cli LRANGE maintainx:webhook:failed 0 10

# Test webhook signature verification
./scripts/test-webhook.sh
```

**Mitigation:**
1. Check webhook secret is correct
2. Verify endpoint is accessible from internet
3. Check for queue backlog
4. Temporarily pause webhook processing if overwhelmed

**Resolution:**
- Fix webhook handler
- Replay failed webhooks
- Verify event sync

---

### RB-004: Data Sync Out of Sync

**Symptoms:**
- Local data doesn't match MaintainX
- Missing work orders or updates
- Stale data being served

**Diagnostic Steps:**

```typescript
// scripts/diagnose-sync.ts

async function diagnoseSyncIssues() {
  const client = new MaintainXClient();

  console.log('=== Sync Diagnostic ===\n');

  // Get sample from MaintainX
  const maintainxWOs = await client.getWorkOrders({ limit: 100 });

  // Get sample from local
  const localWOs = await localStore.getWorkOrders({ limit: 100 });

  // Compare
  const maintainxIds = new Set(maintainxWOs.workOrders.map(wo => wo.id));
  const localIds = new Set(localWOs.map(wo => wo.id));

  const missingLocally = [...maintainxIds].filter(id => !localIds.has(id));
  const extraLocally = [...localIds].filter(id => !maintainxIds.has(id));

  console.log(`MaintainX work orders: ${maintainxIds.size}`);
  console.log(`Local work orders: ${localIds.size}`);
  console.log(`Missing locally: ${missingLocally.length}`);
  console.log(`Extra locally: ${extraLocally.length}`);

  if (missingLocally.length > 0) {
    console.log('\nMissing IDs (first 10):');
    missingLocally.slice(0, 10).forEach(id => console.log(`  - ${id}`));
  }
}
```

**Mitigation:**
1. Trigger full sync if data is stale
2. Check webhook delivery
3. Verify polling job is running

**Resolution:**
- Run reconciliation script
- Fix sync process
- Monitor for drift

---

### RB-005: Performance Degradation

**Symptoms:**
- `MaintainXHighLatency` alert firing
- Slow user experience
- Timeout errors

**Diagnostic Steps:**

```typescript
// scripts/diagnose-performance.ts

async function diagnosePerformance() {
  console.log('=== Performance Diagnostic ===\n');

  // Test API latency
  const endpoints = ['/workorders', '/assets', '/locations', '/users'];

  for (const endpoint of endpoints) {
    const start = Date.now();
    await client.request(`GET ${endpoint}?limit=10`);
    const latency = Date.now() - start;

    const status = latency > 1000 ? '[SLOW]' : '[OK]';
    console.log(`${status} ${endpoint}: ${latency}ms`);
  }

  // Check cache performance
  const cacheStats = await cache.getStats();
  console.log('\nCache stats:');
  console.log(`  Hit rate: ${cacheStats.hitRate}%`);
  console.log(`  Size: ${cacheStats.size}`);

  // Check connection pool
  const poolStats = await getConnectionPoolStats();
  console.log('\nConnection pool:');
  console.log(`  Active: ${poolStats.active}`);
  console.log(`  Idle: ${poolStats.idle}`);
  console.log(`  Waiting: ${poolStats.waiting}`);
}
```

**Mitigation:**
1. Enable aggressive caching
2. Reduce concurrent requests
3. Add request queuing

**Resolution:**
- Identify slow endpoints
- Optimize queries
- Scale resources if needed

## Emergency Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| On-call Engineer | PagerDuty | Automatic |
| MaintainX Support | support@getmaintainx.com | Manual |
| Infrastructure | #infra-oncall Slack | Manual |

## Post-Incident Template

```markdown
## Incident Report: [TITLE]

**Date:** YYYY-MM-DD
**Duration:** HH:MM - HH:MM (X hours)
**Severity:** SEVX
**Status:** Resolved

### Summary
Brief description of what happened.

### Timeline
- HH:MM - Alert fired
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Resolution confirmed

### Root Cause
What caused the incident.

### Impact
- X work orders affected
- Y minutes of downtime
- Z users impacted

### Resolution
What was done to fix it.

### Action Items
- [ ] Prevent recurrence
- [ ] Improve detection
- [ ] Update runbooks
```

## Output

- Incident diagnosed
- Mitigation applied
- Root cause identified
- Resolution documented

## Resources

- [MaintainX Status Page](https://status.getmaintainx.com)
- [MaintainX Support](https://help.getmaintainx.com)
- [MaintainX API Documentation](https://maintainx.dev/)

## Next Steps

For data handling patterns, see `maintainx-data-handling`.
