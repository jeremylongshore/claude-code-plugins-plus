# Customer.io Production Checklist - Implementation Guide

## Pre-Production Checklist

### 1. Credentials & Configuration

```bash
# Verify production credentials are set
echo "Checking credentials..."
[ -n "$CUSTOMERIO_SITE_ID" ] && echo "Site ID: OK" || echo "Site ID: MISSING"
[ -n "$CUSTOMERIO_API_KEY" ] && echo "API Key: OK" || echo "API Key: MISSING"

# Verify correct region
echo "Region: ${CUSTOMERIO_REGION:-us}"
```

**Checklist:**
- [ ] Production Site ID configured (different from dev)
- [ ] Production API Key configured (different from dev)
- [ ] Correct region selected (US or EU)
- [ ] Credentials stored in secrets manager
- [ ] API keys have appropriate permissions

### 2. Integration Quality

```typescript
// scripts/integration-audit.ts
async function auditIntegration(): Promise<AuditResult> {
  const results: AuditResult = {
    passed: [],
    warnings: [],
    failures: []
  };

  // Check identify calls have required attributes
  // Check event names follow naming convention
  // Check timestamps are Unix seconds
  // Check no PII in unsafe fields

  return results;
}
```

**Checklist:**
- [ ] All identify calls include email attribute
- [ ] User IDs are consistent across systems
- [ ] Event names follow `snake_case` convention
- [ ] Timestamps are Unix seconds (not milliseconds)
- [ ] No PII in event names or segment names
- [ ] Error handling implemented for all API calls

### 3. Campaign Configuration

**In Customer.io Dashboard:**
- [ ] Production campaigns created (not draft)
- [ ] Sender email verified and authenticated
- [ ] SPF/DKIM/DMARC configured for sending domain
- [ ] Unsubscribe links included in all emails
- [ ] Physical address included (CAN-SPAM)
- [ ] Test sends completed and reviewed

### 4. Deliverability

**Checklist:**
- [ ] Sender domain authenticated
- [ ] Dedicated IP warmed up (if applicable)
- [ ] Suppression list imported
- [ ] Bounce handling configured
- [ ] Complaint handling configured
- [ ] Reply-to address monitored

### 5. Monitoring & Alerting

```typescript
// lib/monitoring.ts
import { metrics } from './metrics';

// Key metrics to monitor
const customerIOMetrics = {
  // API metrics
  'customerio.api.latency': 'histogram',
  'customerio.api.errors': 'counter',
  'customerio.api.rate_limited': 'counter',

  // Delivery metrics
  'customerio.email.sent': 'counter',
  'customerio.email.delivered': 'counter',
  'customerio.email.bounced': 'counter',
  'customerio.email.complained': 'counter',

  // Business metrics
  'customerio.users.identified': 'counter',
  'customerio.events.tracked': 'counter'
};

// Recommended alerts
const alertThresholds = {
  'api_error_rate': { threshold: 0.01, window: '5m' },
  'bounce_rate': { threshold: 0.05, window: '1h' },
  'complaint_rate': { threshold: 0.001, window: '1h' },
  'delivery_latency_p99': { threshold: 5000, window: '5m' }
};
```

**Checklist:**
- [ ] API error rate alerting configured
- [ ] Delivery rate monitoring enabled
- [ ] Bounce rate alerting (threshold: 5%)
- [ ] Complaint rate alerting (threshold: 0.1%)
- [ ] Dashboard for key metrics created

### 6. Testing & Validation

```bash
#!/bin/bash
# production-smoke-test.sh

echo "Running production smoke tests..."

# Test 1: API connectivity
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://track.customer.io/api/v1/customers/smoke-test-$(date +%s)" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest@example.com","_test":true}' | grep -q "200" && \
  echo "API: OK" || echo "API: FAILED"

# Test 2: Event tracking
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://track.customer.io/api/v1/customers/smoke-test/events" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"smoke_test","data":{"timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}}' | grep -q "200" && \
  echo "Events: OK" || echo "Events: FAILED"

echo "Smoke tests complete"
```

**Checklist:**
- [ ] End-to-end test in staging passed
- [ ] Production smoke test passed
- [ ] Load test completed (if high volume)
- [ ] Failover test completed
- [ ] Manual campaign test send reviewed

### 7. Documentation & Runbooks

**Checklist:**
- [ ] Integration documentation updated
- [ ] Event catalog documented
- [ ] Attribute schema documented
- [ ] Runbook for common issues created
- [ ] Escalation path defined
- [ ] On-call rotation aware of integration

### 8. Rollback Plan

```typescript
// Rollback procedure documented
const rollbackPlan = {
  trigger: 'Error rate > 5% or delivery rate < 90%',
  steps: [
    '1. Disable new user identify calls',
    '2. Pause triggered campaigns',
    '3. Switch to backup messaging provider (if available)',
    '4. Notify stakeholders',
    '5. Investigate root cause',
    '6. Fix and redeploy',
    '7. Resume campaigns with reduced volume',
    '8. Monitor closely for 24 hours'
  ],
  contacts: {
    engineering: 'engineering@company.com',
    customerio_support: 'support@customer.io',
    escalation: 'oncall@company.com'
  }
};
```

**Checklist:**
- [ ] Rollback procedure documented
- [ ] Feature flags for quick disable
- [ ] Backup messaging path available
- [ ] Stakeholder notification plan ready
