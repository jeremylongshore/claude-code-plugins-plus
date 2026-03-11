# Documenso Incident Runbook - Implementation Guide

## Incident Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| P1 Critical | Complete service outage | 15 minutes | API down, all signing blocked |
| P2 High | Significant degradation | 30 minutes | High error rates, slow responses |
| P3 Medium | Partial impact | 2 hours | Some operations failing |
| P4 Low | Minor issues | 24 hours | Cosmetic issues, warnings |

## Quick Diagnostic Commands

```bash
# Check Documenso API status
curl -s https://status.documenso.com/api/v2/status.json | jq '.status'

# Test API connectivity
curl -v -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  https://app.documenso.com/api/v2/documents?perPage=1

# Check your service health
curl -s https://your-app.com/health | jq

# View recent error logs
kubectl logs -l app=signing-service --since=10m | grep -i error

# Check pod status
kubectl get pods -l app=signing-service
```

## Incident Response Procedures

### Procedure 1: Documenso API Unresponsive

**Symptoms:**
- Connection timeouts
- 5xx errors from Documenso
- Health checks failing

**Steps:**

1. **Confirm the issue (2 min)**
   ```bash
   # Check Documenso status page
   curl -s https://status.documenso.com/api/v2/status.json | jq

   # Direct API test
   curl -v --max-time 10 \
     -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
     https://app.documenso.com/api/v2/documents?perPage=1
   ```

2. **Enable graceful degradation (5 min)**
   ```bash
   # If using feature flags
   curl -X POST https://your-feature-flags.com/api/flags \
     -d '{"flag": "documenso_enabled", "value": false}'

   # Or via kubectl
   kubectl set env deployment/signing-service DOCUMENSO_ENABLED=false
   ```

3. **Notify stakeholders**
   ```
   Subject: [P1] Documenso Integration Degraded

   Status: Documenso API is unresponsive
   Impact: Document signing temporarily unavailable
   Action: Graceful degradation enabled
   ETA: Monitoring for recovery
   ```

4. **Monitor for recovery**
   ```bash
   # Watch for recovery
   watch -n 30 'curl -s https://status.documenso.com/api/v2/status.json | jq .status'
   ```

5. **Re-enable after recovery**
   ```bash
   kubectl set env deployment/signing-service DOCUMENSO_ENABLED=true
   ```

### Procedure 2: High Error Rate (4xx/5xx)

**Symptoms:**
- Error rate > 5%
- Mixed successful and failed requests
- Specific operations failing

**Steps:**

1. **Identify error pattern (5 min)**
   ```bash
   # Check recent errors
   kubectl logs -l app=signing-service --since=30m | \
     grep -E "statusCode.*[45][0-9]{2}" | \
     sort | uniq -c | sort -rn | head -20
   ```

2. **Check specific error types**
   ```bash
   # 401 Unauthorized - API key issue
   # 403 Forbidden - Permission issue
   # 404 Not Found - Resource deleted
   # 422 Validation - Bad request data
   # 429 Rate Limited - Too many requests
   # 500+ Server Error - Documenso issue
   ```

3. **For 401/403 errors:**
   ```bash
   # Verify API key
   echo $DOCUMENSO_API_KEY | head -c 10

   # Test key directly
   curl -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
     https://app.documenso.com/api/v2/documents?perPage=1
   ```

4. **For 429 errors:**
   ```bash
   # Check request rate
   kubectl logs -l app=signing-service --since=5m | \
     grep "documenso" | wc -l

   # Reduce concurrency
   kubectl set env deployment/signing-service DOCUMENSO_CONCURRENCY=1
   ```

5. **For 5xx errors:**
   - Check Documenso status page
   - Enable circuit breaker
   - Implement retry with backoff

### Procedure 3: Document Stuck in Pending

**Symptoms:**
- Documents not completing
- Recipients not receiving emails
- Webhooks not firing

**Steps:**

1. **Check document status**
   ```bash
   curl -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
     https://app.documenso.com/api/v2/documents/{documentId}
   ```

2. **Check recipient status**
   ```bash
   # Look for recipient signing status
   curl -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
     https://app.documenso.com/api/v2/documents/{documentId} | \
     jq '.recipients[] | {email, signingStatus}'
   ```

3. **Verify webhook delivery**
   - Check Documenso dashboard for webhook logs
   - Check your webhook endpoint logs
   - Test webhook endpoint manually

4. **Manual intervention**
   ```bash
   # Resend document
   curl -X POST \
     -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
     https://app.documenso.com/api/v2/documents/{documentId}/resend
   ```

### Procedure 4: Webhook Not Receiving Events

**Symptoms:**
- No webhook events received
- Events delayed significantly
- Partial event delivery

**Steps:**

1. **Verify webhook configuration**
   - Check Documenso dashboard webhook settings
   - Verify URL is correct and HTTPS
   - Confirm events are subscribed

2. **Test webhook endpoint**
   ```bash
   curl -X POST https://your-app.com/webhooks/documenso \
     -H "Content-Type: application/json" \
     -H "X-Documenso-Secret: your-secret" \
     -d '{"event":"test","payload":{}}'
   ```

3. **Check webhook logs in Documenso**
   - Dashboard -> Team Settings -> Webhooks
   - View delivery attempts and responses

4. **Check your endpoint**
   ```bash
   # Verify endpoint is responding
   curl -I https://your-app.com/webhooks/documenso

   # Check for errors in logs
   kubectl logs -l app=signing-service | grep webhook
   ```

5. **Resend failed webhooks**
   - Use Documenso dashboard to retry failed deliveries

## Circuit Breaker Implementation

```typescript
// Emergency circuit breaker
class DocumensoCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: "closed" | "open" | "half-open" = "closed";

  private readonly threshold = 5;
  private readonly timeout = 60000; // 1 minute

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailure > this.timeout) {
        this.state = "half-open";
      } else {
        throw new Error("Circuit breaker is open");
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = "closed";
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = "open";
      console.error("Circuit breaker opened!");
    }
  }

  getState(): string {
    return this.state;
  }
}
```

## Post-Incident Review Template

```markdown
## Incident Report: [Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P1/P2/P3/P4
**Author:** [Name]

### Summary
Brief description of what happened.

### Timeline
- HH:MM - Initial alert triggered
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Service restored

### Root Cause
Technical explanation of why the incident occurred.

### Impact
- X documents affected
- Y users impacted
- Z minutes of downtime

### Resolution
What was done to resolve the incident.

### Action Items
- [ ] Implement additional monitoring
- [ ] Update runbook
- [ ] Add circuit breaker

### Lessons Learned
What we learned from this incident.
```

## Emergency Contacts

| Role | Contact | Escalation Time |
|------|---------|-----------------|
| On-call Engineer | [Slack/Phone] | Immediate |
| Team Lead | [Slack/Phone] | 15 minutes |
| Documenso Support | support@documenso.com | 30 minutes |
| Engineering Manager | [Slack/Phone] | 1 hour |
