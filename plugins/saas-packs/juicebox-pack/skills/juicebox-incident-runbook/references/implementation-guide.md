# Juicebox Incident Runbook - Implementation Guide

Detailed implementation examples and code patterns.

## Incident Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| P1 | Critical | < 15 min | Complete outage, data loss |
| P2 | High | < 1 hour | Major feature broken, degraded performance |
| P3 | Medium | < 4 hours | Minor feature issue, workaround exists |
| P4 | Low | < 24 hours | Cosmetic, non-blocking |

## Quick Diagnostics

### Step 1: Immediate Assessment
```bash
#!/bin/bash
# quick-diag.sh - Run immediately when incident detected

echo "=== Juicebox Quick Diagnostics ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Check Juicebox status page
echo ""
echo "=== Juicebox Status ==="
curl -s https://status.juicebox.ai/api/status | jq '.status'

# Check our API health
echo ""
echo "=== Our API Health ==="
curl -s http://localhost:8080/health/ready | jq '.'

# Check recent error logs
echo ""
echo "=== Recent Errors (last 5 min) ==="
kubectl logs -l app=juicebox-integration --since=5m | grep -i error | tail -20

# Check metrics
echo ""
echo "=== Error Rate ==="
curl -s http://localhost:9090/api/v1/query?query=rate\(juicebox_requests_total\{status=\"error\"\}\[5m\]\) | jq '.data.result[0].value[1]'
```

### Step 2: Identify Root Cause
```markdown

## Incident Triage Decision Tree

1. Is Juicebox status page showing issues?
   - YES → External outage, skip to "External Outage Response"
   - NO → Continue

2. Are we getting authentication errors (401)?
   - YES → Check API key validity, skip to "Auth Issues"
   - NO → Continue

3. Are we getting rate limited (429)?
   - YES → Skip to "Rate Limit Response"
   - NO → Continue

4. Are requests timing out?
   - YES → Skip to "Timeout Response"
   - NO → Continue

5. Are we getting unexpected errors?
   - YES → Skip to "Application Error Response"
   - NO → Gather more data
```

## Response Procedures

### External Outage Response
```markdown

## When Juicebox is Down

1. **Confirm Outage**
   - Check https://status.juicebox.ai
   - Verify with curl test to API

2. **Enable Fallback Mode**
   ```bash
   kubectl set env deployment/juicebox-integration JUICEBOX_FALLBACK=true
   ```

3. **Notify Stakeholders**
   - Post to #incidents channel
   - Update status page if customer-facing

4. **Monitor Recovery**
   - Set up alert for Juicebox status change
   - Prepare to disable fallback mode

5. **Post-Incident**
   - Disable fallback when Juicebox recovers
   - Document timeline and impact
```

### Auth Issues Response
```markdown

## When Authentication Fails

1. **Verify API Key**
   ```bash
   # Mask key for logging
   echo "Key prefix: ${JUICEBOX_API_KEY:0:10}..."

   # Test auth
   curl -H "Authorization: Bearer $JUICEBOX_API_KEY" \
     https://api.juicebox.ai/v1/auth/me
   ```

2. **Check Key Status in Dashboard**
   - Log into https://app.juicebox.ai
   - Verify key is active and not revoked

3. **Rotate Key if Compromised**
   - Generate new key in dashboard
   - Update secret manager
   - Restart pods
   ```bash
   kubectl rollout restart deployment/juicebox-integration
   ```

4. **Verify Recovery**
   - Check health endpoint
   - Monitor error rate
```

### Rate Limit Response
```markdown

## When Rate Limited

1. **Check Current Usage**
   ```bash
   curl -H "Authorization: Bearer $JUICEBOX_API_KEY" \
     https://api.juicebox.ai/v1/usage
   ```

2. **Immediate Mitigation**
   - Enable aggressive caching
   - Reduce request rate
   ```bash
   kubectl set env deployment/juicebox-integration JUICEBOX_RATE_LIMIT=10
   ```

3. **If Quota Exhausted**
   - Contact Juicebox support for temporary increase
   - Implement request queuing

4. **Long-term Fix**
   - Review usage patterns
   - Implement better caching
   - Consider plan upgrade
```

### Timeout Response
```markdown

## When Requests Timeout

1. **Check Network**
   ```bash
   # DNS resolution
   nslookup api.juicebox.ai

   # Connectivity
   curl -v --connect-timeout 5 https://api.juicebox.ai/v1/health
   ```

2. **Check Load**
   - Review query complexity
   - Check for unusually large requests

3. **Increase Timeout**
   ```bash
   kubectl set env deployment/juicebox-integration JUICEBOX_TIMEOUT=60000
   ```

4. **Implement Circuit Breaker**
   - Enable circuit breaker if repeated timeouts
   - Serve cached/fallback data
```

## Incident Communication Template

```markdown

## Incident Report Template

**Incident ID:** INC-YYYY-MM-DD-XXX
**Status:** Investigating | Identified | Monitoring | Resolved
**Severity:** P1 | P2 | P3 | P4
**Start Time:** YYYY-MM-DD HH:MM UTC
**End Time:** (when resolved)

### Summary
[Brief description of the incident]

### Impact
- Users affected: [number/percentage]
- Features affected: [list]
- Duration: [time]

### Timeline
- HH:MM - Incident detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Incident resolved

### Root Cause
[Description of what caused the incident]

### Resolution
[What was done to fix it]

### Action Items
- [ ] Action 1 (Owner, Due Date)
- [ ] Action 2 (Owner, Due Date)
```

## On-Call Checklist

```markdown

## On-Call Handoff Checklist

### Before Shift
- [ ] Access to all monitoring dashboards
- [ ] VPN/access to production systems
- [ ] Runbook bookmarked
- [ ] Escalation contacts available

### During Shift
- [ ] Check dashboards every 30 min
- [ ] Respond to alerts within SLA
- [ ] Document all incidents
- [ ] Escalate P1/P2 immediately

### End of Shift
- [ ] Handoff open incidents
- [ ] Update incident log
- [ ] Brief incoming on-call
```
