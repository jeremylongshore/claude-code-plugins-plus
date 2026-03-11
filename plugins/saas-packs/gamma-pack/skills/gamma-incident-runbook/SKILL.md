---
name: gamma-incident-runbook
description: |
  Incident response runbook for Gamma integration issues.
  Use when experiencing production incidents, outages,
  or need systematic troubleshooting procedures.
  Trigger with phrases like "gamma incident", "gamma outage",
  "gamma down", "gamma emergency", "gamma runbook".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Incident Runbook

## Overview
Systematic procedures for responding to and resolving Gamma integration incidents.

## Prerequisites
- Access to monitoring dashboards
- Access to application logs
- On-call responsibilities defined
- Communication channels established

## Incident Severity Levels

| Level | Description | Response Time | Escalation |
|-------|-------------|---------------|------------|
| P1 | Complete outage, no presentations | < 15 min | Immediate |
| P2 | Degraded, slow or partial failures | < 30 min | 1 hour |
| P3 | Minor issues, workaround available | < 2 hours | 4 hours |
| P4 | Cosmetic or non-urgent | < 24 hours | None |

## Quick Diagnostics

### Step 1: Check Gamma Status
```bash
set -euo pipefail
# Check Gamma status page
curl -s https://status.gamma.app/api/v2/status.json | jq '.status'

# Check our integration health
curl -s https://your-app.com/health/gamma | jq '.'

# Quick connectivity test
curl -w "\nTime: %{time_total}s\n" \
  -H "Authorization: Bearer $GAMMA_API_KEY" \
  https://api.gamma.app/v1/ping
```

### Step 2: Review Key Metrics
```bash
set -euo pipefail
# Check error rate (Prometheus)
curl -s 'http://prometheus:9090/api/v1/query?query=rate(gamma_requests_total{status=~"5.."}[5m])' | jq '.data.result'  # 9090: Prometheus port

# Check latency P95
curl -s 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(gamma_request_duration_seconds_bucket[5m]))' | jq '.data.result'  # Prometheus port

# Check rate limit
curl -s 'http://prometheus:9090/api/v1/query?query=gamma_rate_limit_remaining' | jq '.data.result'  # Prometheus port
```

### Step 3: Review Recent Logs
```bash
# Last 100 error logs
grep -i "gamma.*error" /var/log/app/gamma-*.log | tail -100

# Rate limit hits
grep "429" /var/log/app/gamma-*.log | wc -l  # HTTP 429 Too Many Requests

# Timeout errors
grep -i "timeout" /var/log/app/gamma-*.log | tail -50
```

## Incident Response Procedures

### Scenario 1: API Returning 5xx Errors

**Symptoms:**
- High error rate in monitoring
- Users reporting failed presentations
- 500/502/503 responses from Gamma

**Actions:**
1. Verify Gamma status: https://status.gamma.app
2. If Gamma outage confirmed:
   - Enable degraded mode / show maintenance message
   - Monitor status page for updates
   - No action needed on our side

3. If Gamma is operational:
   ```bash
   # Check our request patterns
   grep "5[0-9][0-9]" /var/log/app/gamma-*.log | \
     awk '{print $1}' | sort | uniq -c | sort -rn

   # Look for malformed requests
   grep -B5 "500" /var/log/app/gamma-*.log | grep "request"
   ```

4. Rollback recent deployments if issue correlates

### Scenario 2: Rate Limit Exceeded (429)

**Symptoms:**
- 429 responses in logs
- Rate limit metrics at zero
- Slow or queued requests

**Actions:**
1. Immediate mitigation:
   ```bash
   # Enable request throttling
   curl -X POST http://localhost:8080/admin/throttle \
     -d '{"gamma": {"rps": 10}}'
   ```

2. Check for runaway processes:
   ```bash
   # Find high-volume clients
   grep "gamma" /var/log/app/*.log | \
     awk '{print $5}' | sort | uniq -c | sort -rn | head -20
   ```

3. Enable circuit breaker:
   ```bash
   curl -X POST http://localhost:8080/admin/circuit-breaker \
     -d '{"service": "gamma", "state": "open"}'
   ```

4. Long-term: Review rate limit tier with Gamma

### Scenario 3: High Latency

**Symptoms:**
- Slow presentation creation
- Timeouts in logs
- P95 latency > 10s

**Actions:**
1. Check Gamma latency vs our latency:
   ```bash
   # Direct Gamma latency
   for i in {1..5}; do
     curl -w "%{time_total}\n" -o /dev/null -s \
       -H "Authorization: Bearer $GAMMA_API_KEY" \
       https://api.gamma.app/v1/ping
   done
   ```

2. If Gamma is slow:
   - Increase timeouts temporarily
   - Enable async mode for non-critical operations
   - Queue heavy operations

3. If our infrastructure is slow:
   - Check CPU/memory on app servers
   - Review connection pool settings
   - Check network connectivity

### Scenario 4: Authentication Failures (401/403)

**Symptoms:**
- All requests failing with 401
- "Invalid API key" errors
- Sudden authentication failures

**Actions:**
1. Verify API key:
   ```bash
   # Test key directly
   curl -H "Authorization: Bearer $GAMMA_API_KEY" \
     https://api.gamma.app/v1/ping

   # Check key format
   echo $GAMMA_API_KEY | head -c 20
   ```

2. If key is invalid:
   - Check if key was rotated
   - Deploy backup key: `GAMMA_API_KEY_SECONDARY`
   - Generate new key in Gamma dashboard

3. Notify team and update secrets

## Communication Templates

### Internal Notification
```
INCIDENT: Gamma Integration Issue

Severity: P[X]
Status: Investigating / Identified / Mitigating / Resolved
Impact: [Description of user impact]
Start Time: [ISO timestamp]

Summary: [Brief description]

Current Actions:
- [Action 1]
- [Action 2]

Next Update: [Time]
```

### User-Facing Message
```
We're currently experiencing issues with presentation generation.
Our team is actively working to resolve this.

Workaround: [If available]
Status updates: [Link to status page]
ETA: [If known]
```

## Post-Incident Checklist

- [ ] Incident timeline documented
- [ ] Root cause identified
- [ ] User impact quantified
- [ ] Fix verified in production
- [ ] Monitoring gaps identified
- [ ] Preventive measures documented
- [ ] Post-mortem scheduled (for P1/P2)

## Resources
- [Gamma Status](https://status.gamma.app)
- [Gamma Support](https://gamma.app/support)
- [Internal Runbook Wiki]()
- [On-Call Schedule]()

## Next Steps
Proceed to `gamma-data-handling` for data management.

## Instructions

1. Assess the current state of the Gamma configuration
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
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Gamma |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply gamma incident runbook to a standard project setup with default configuration options.

**Advanced scenario**: Customize gamma incident runbook for production environments with multiple constraints and team-specific requirements.