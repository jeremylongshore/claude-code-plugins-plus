# Lindy Incident Runbook - Implementation Guide

# Lindy Incident Runbook

## Overview
Incident response procedures for Lindy AI integration issues.

## Prerequisites
- Access to Lindy dashboard
- Monitoring dashboards available
- Escalation contacts known
- Admin access to production

## Incident Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| SEV1 | Complete outage | 15 minutes | All agents failing |
| SEV2 | Partial outage | 30 minutes | One critical agent down |
| SEV3 | Degraded | 2 hours | High latency, some errors |
| SEV4 | Minor | 24 hours | Cosmetic issues |

## Quick Diagnostics

### Step 1: Check Lindy Status
```bash
# Check Lindy status page
curl -s https://status.lindy.ai/api/v1/status | jq '.status'

# Check API health
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $LINDY_API_KEY" \
  https://api.lindy.ai/v1/health
```

### Step 2: Verify Authentication
```bash
# Test API key
curl -s -H "Authorization: Bearer $LINDY_API_KEY" \
  https://api.lindy.ai/v1/users/me | jq '.email'
```

### Step 3: Check Rate Limits
```bash
# Check rate limit headers
curl -sI -H "Authorization: Bearer $LINDY_API_KEY" \
  https://api.lindy.ai/v1/users/me | grep -i "x-ratelimit"
```

## Common Incidents

### Incident: Complete API Outage

**Symptoms:**
- All API calls failing
- 5xx errors from Lindy

**Runbook:**
```markdown
1. [ ] Check https://status.lindy.ai
2. [ ] Verify it's not a local network issue
3. [ ] Check if other services on same network work
4. [ ] Enable fallback mode if available
5. [ ] Notify stakeholders
6. [ ] Open support ticket with Lindy
7. [ ] Monitor status page for updates
```

**Fallback Code:**
```typescript
async function runWithFallback(agentId: string, input: string) {
  try {
    return await lindy.agents.run(agentId, { input });
  } catch (error: any) {
    if (error.status >= 500) {
      // Enable fallback mode
      return {
        output: 'Service temporarily unavailable. Please try again later.',
        fallback: true,
      };
    }
    throw error;
  }
}
```

### Incident: Rate Limiting

**Symptoms:**
- 429 errors
- "Rate limit exceeded" messages

**Runbook:**
```markdown
1. [ ] Check current usage in dashboard
2. [ ] Identify spike source (which agent/automation)
3. [ ] Reduce request rate or implement throttling
4. [ ] Consider upgrading plan if legitimate traffic
5. [ ] Implement request queuing
```

**Throttling Code:**
```typescript
const queue = new PQueue({ concurrency: 5, interval: 1000, intervalCap: 10 });

async function throttledRun(agentId: string, input: string) {
  return queue.add(() => lindy.agents.run(agentId, { input }));
}
```

### Incident: Agent Failures

**Symptoms:**
- Specific agent not responding
- Unexpected outputs
- Timeout errors

**Runbook:**
```markdown
1. [ ] Identify affected agent(s)
2. [ ] Check agent configuration hasn't changed
3. [ ] Review recent runs for patterns
4. [ ] Test with simple input
5. [ ] Check if tools are working
6. [ ] Rollback to previous version if needed
```

**Diagnostic Script:**
```typescript
async function diagnoseAgent(agentId: string) {
  const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

  // Get agent details
  const agent = await lindy.agents.get(agentId);
  console.log('Agent:', agent.name, agent.status);

  // Check recent runs
  const runs = await lindy.runs.list({ agentId, limit: 10 });
  const failures = runs.filter((r: any) => r.status === 'failed');
  console.log(`Failures: ${failures.length}/${runs.length}`);

  // Test run
  try {
    const test = await lindy.agents.run(agentId, { input: 'Hello' });
    console.log('Test run: SUCCESS');
  } catch (e: any) {
    console.log('Test run: FAILED -', e.message);
  }

  return { agent, runs, failures };
}
```

### Incident: High Latency

**Symptoms:**
- Response times > 10 seconds
- Timeouts increasing

**Runbook:**
```markdown
1. [ ] Check Lindy status page for degradation
2. [ ] Review latency metrics by agent
3. [ ] Check if issue is with specific agent
4. [ ] Verify instructions aren't causing long responses
5. [ ] Consider reducing max_tokens
6. [ ] Implement streaming if not already
```

## Escalation Matrix

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | Initial response |
| L2 | Engineering lead | After 30 min SEV1/2 |
| L3 | VP Engineering | After 1 hour SEV1 |
| Lindy | support@lindy.ai | External issue confirmed |

## Post-Incident

### Incident Report Template
```markdown
## Incident Report: [Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** SEV1/2/3/4
**Impact:** [Description of user impact]

### Timeline
- HH:MM - Incident detected
- HH:MM - On-call paged
- HH:MM - Root cause identified
- HH:MM - Resolution applied
- HH:MM - All clear

### Root Cause
[What caused the incident]

### Resolution
[What fixed it]

### Action Items
- [ ] [Preventive action 1]
- [ ] [Preventive action 2]
```

## Output
- Quick diagnostic commands
- Common incident runbooks
- Fallback code patterns
- Escalation procedures
- Post-incident template

## Resources
- [Lindy Status](https://status.lindy.ai)
- [Lindy Support](https://support.lindy.ai)
- [API Reference](https://docs.lindy.ai/api)

## Next Steps
Proceed to `lindy-data-handling` for data management.
