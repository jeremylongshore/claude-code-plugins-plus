# Apollo Incident Runbook - Implementation Guide

> Full implementation details and code examples for the `apollo-incident-runbook` skill.

# Apollo Incident Runbook

## Overview
Structured incident response procedures for Apollo.io integration issues with diagnosis steps, mitigation actions, and recovery procedures.

## Incident Classification

| Severity | Impact | Response Time | Examples |
|----------|--------|---------------|----------|
| P1 - Critical | Complete outage | 15 min | API down, auth failed |
| P2 - Major | Degraded service | 1 hour | High error rate, slow responses |
| P3 - Minor | Limited impact | 4 hours | Cache issues, minor errors |
| P4 - Low | No user impact | Next day | Log warnings, cosmetic issues |

## Quick Diagnosis Commands

```bash
# Check Apollo status
curl -s https://status.apollo.io/api/v2/status.json | jq '.status'

# Verify API key
curl -s "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY" | jq

# Check rate limit status
curl -I "https://api.apollo.io/v1/people/search" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "'$APOLLO_API_KEY'", "per_page": 1}' 2>/dev/null \
  | grep -i "ratelimit"

# Check application health
curl -s http://localhost:3000/health/apollo | jq

# Check error logs
kubectl logs -l app=apollo-service --tail=100 | grep -i error

# Check metrics
curl -s http://localhost:3000/metrics | grep apollo_
```

## Incident Response Procedures

### P1: Complete API Failure

**Symptoms:**
- All Apollo requests returning 5xx errors
- Health check endpoint failing
- Alerts firing on error rate

**Immediate Actions (0-15 min):**

```bash
# 1. Confirm Apollo is down (not just us)
curl -s https://status.apollo.io/api/v2/status.json | jq

# 2. Enable circuit breaker / fallback mode
kubectl set env deployment/apollo-service APOLLO_FALLBACK_MODE=true

# 3. Notify stakeholders
# Post to #incidents Slack channel

# 4. Check if it's our API key
curl -s "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY"
# If 401: Key is invalid - check if rotated
```

**Fallback Mode Implementation:**

```typescript
// src/lib/apollo/circuit-breaker.ts
class CircuitBreaker {
  private failures = 0;
  private lastFailure: Date | null = null;
  private isOpen = false;

  async execute<T>(fn: () => Promise<T>, fallback: () => T): Promise<T> {
    if (this.isOpen) {
      if (this.shouldAttemptReset()) {
        this.isOpen = false;
      } else {
        console.warn('Circuit breaker open, using fallback');
        return fallback();
      }
    }

    try {
      const result = await fn();
      this.failures = 0;
      return result;
    } catch (error) {
      this.failures++;
      this.lastFailure = new Date();

      if (this.failures >= 5) {
        this.isOpen = true;
        console.error('Circuit breaker opened after 5 failures');
      }

      return fallback();
    }
  }

  private shouldAttemptReset(): boolean {
    if (!this.lastFailure) return true;
    const elapsed = Date.now() - this.lastFailure.getTime();
    return elapsed > 60000; // Try again after 1 minute
  }
}

// Fallback data source
async function getFallbackContacts(criteria: any) {
  // Return cached data
  const cached = await apolloCache.search(criteria);
  if (cached.length > 0) return cached;

  // Return empty with warning
  console.warn('No fallback data available');
  return [];
}
```

**Recovery Steps:**
```bash
# 1. Monitor Apollo status page for resolution
watch -n 30 'curl -s https://status.apollo.io/api/v2/status.json | jq'

# 2. When Apollo is back, disable fallback mode
kubectl set env deployment/apollo-service APOLLO_FALLBACK_MODE=false

# 3. Verify connectivity
curl -s "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY"

# 4. Check for request backlog
kubectl logs -l app=apollo-service | grep -c "queued"

# 5. Gradually restore traffic
kubectl scale deployment/apollo-service --replicas=1
# Wait, verify healthy
kubectl scale deployment/apollo-service --replicas=3
```

---

### P1: API Key Compromised

**Symptoms:**
- Unexpected 401 errors
- Unusual usage patterns
- Alert from Apollo about suspicious activity

**Immediate Actions:**

```bash
# 1. Rotate API key immediately in Apollo dashboard
# Settings > Integrations > API > Regenerate Key

# 2. Update secret in production
# Kubernetes
kubectl create secret generic apollo-secrets \
  --from-literal=api-key=NEW_KEY \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart deployments to pick up new key
kubectl rollout restart deployment/apollo-service

# 4. Audit usage logs
kubectl logs -l app=apollo-service --since=24h | grep "apollo_request"
```

**Post-Incident:**
- Review access controls
- Enable IP allowlisting if available
- Implement key rotation schedule

---

### P2: High Error Rate

**Symptoms:**
- Error rate > 5%
- Mix of successful and failed requests
- Alerts on `apollo_errors_total`

**Diagnosis:**

```bash
# Check error distribution
curl -s http://localhost:3000/metrics | grep apollo_errors_total

# Sample recent errors
kubectl logs -l app=apollo-service --tail=500 | grep -A2 "apollo_error"

# Check if specific endpoint is failing
curl -s http://localhost:3000/metrics | grep apollo_requests_total | sort
```

**Common Causes & Fixes:**

| Error Type | Likely Cause | Fix |
|------------|--------------|-----|
| validation_error | Bad request format | Check request payload |
| rate_limit | Too many requests | Enable backoff, reduce concurrency |
| auth_error | Key issue | Verify API key |
| timeout | Network/Apollo slow | Increase timeout, add retry |

**Mitigation:**

```bash
# Reduce request rate
kubectl set env deployment/apollo-service APOLLO_RATE_LIMIT=50

# Enable aggressive caching
kubectl set env deployment/apollo-service APOLLO_CACHE_TTL=3600

# Scale down to reduce load
kubectl scale deployment/apollo-service --replicas=1
```

---

### P2: Rate Limit Exceeded

**Symptoms:**
- 429 responses
- `apollo_rate_limit_hits_total` increasing
- Requests queuing

**Immediate Actions:**

```bash
# 1. Check current rate limit status
curl -I "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY" \
  | grep -i ratelimit

# 2. Pause non-essential operations
kubectl set env deployment/apollo-service \
  APOLLO_PAUSE_BACKGROUND_JOBS=true

# 3. Reduce concurrency
kubectl set env deployment/apollo-service \
  APOLLO_MAX_CONCURRENT=2

# 4. Wait for rate limit to reset (typically 1 minute)
sleep 60

# 5. Gradually resume
kubectl set env deployment/apollo-service \
  APOLLO_MAX_CONCURRENT=5 \
  APOLLO_PAUSE_BACKGROUND_JOBS=false
```

**Prevention:**
```typescript
// Implement request budgeting
class RequestBudget {
  private used = 0;
  private resetTime: Date;

  constructor(private limit: number = 90) {
    this.resetTime = this.getNextMinute();
  }

  async acquire(): Promise<boolean> {
    if (new Date() > this.resetTime) {
      this.used = 0;
      this.resetTime = this.getNextMinute();
    }

    if (this.used >= this.limit) {
      const waitMs = this.resetTime.getTime() - Date.now();
      console.warn(`Budget exhausted, waiting ${waitMs}ms`);
      await new Promise(r => setTimeout(r, waitMs));
      return this.acquire();
    }

    this.used++;
    return true;
  }

  private getNextMinute(): Date {
    const next = new Date();
    next.setSeconds(0, 0);
    next.setMinutes(next.getMinutes() + 1);
    return next;
  }
}
```

---

### P3: Slow Responses

**Symptoms:**
- P95 latency > 5 seconds
- Timeouts occurring
- User complaints about slow search

**Diagnosis:**

```bash
# Check latency metrics
curl -s http://localhost:3000/metrics \
  | grep apollo_request_duration

# Check Apollo's response time
time curl -s "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY"

# Check our application latency
kubectl top pods -l app=apollo-service
```

**Mitigation:**

```bash
# Increase timeout
kubectl set env deployment/apollo-service APOLLO_TIMEOUT=60000

# Enable request hedging (send duplicate requests)
kubectl set env deployment/apollo-service APOLLO_HEDGE_REQUESTS=true

# Reduce payload size (request fewer results)
kubectl set env deployment/apollo-service APOLLO_DEFAULT_PER_PAGE=25
```

## Post-Incident Template

```markdown
## Incident Report: [Title]

**Date:** [Date]
**Duration:** [Start] - [End] ([X] minutes)
**Severity:** P[1-4]
**Affected Systems:** Apollo integration

### Summary
[1-2 sentence description]

### Timeline
- HH:MM - Issue detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Service restored

### Root Cause
[Description of what caused the incident]

### Impact
- [Number] of failed requests
- [Number] of affected users
- [Duration] of degraded service

### Resolution
[What was done to fix the issue]

### Action Items
- [ ] [Preventive measure 1]
- [ ] [Preventive measure 2]
- [ ] [Monitoring improvement]

### Lessons Learned
[What we learned from this incident]
```

## Output
- Incident classification matrix
- Quick diagnosis commands
- Response procedures by severity
- Circuit breaker implementation
- Post-incident template

## Error Handling
| Issue | Escalation |
|-------|------------|
| P1 > 30 min | Page on-call lead |
| P2 > 2 hours | Notify management |
| Recurring P3 | Create P2 tracking |
| Apollo outage | Open support ticket |

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support](https://support.apollo.io)
- [On-Call Runbook Template](https://sre.google/workbook/on-call/)

## Next Steps
Proceed to `apollo-data-handling` for data management.
