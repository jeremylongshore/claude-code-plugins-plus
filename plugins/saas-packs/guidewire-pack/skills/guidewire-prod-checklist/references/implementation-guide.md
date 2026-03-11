# Guidewire Production Checklist - Implementation Guide

## Production Readiness Checklist

### Security

| # | Item | Priority | Status |
|---|------|----------|--------|
| 1 | OAuth2 credentials rotated for production | Critical | [ ] |
| 2 | Service accounts use least privilege API roles | Critical | [ ] |
| 3 | All secrets stored in secret manager (not code) | Critical | [ ] |
| 4 | TLS 1.2+ enforced for all connections | Critical | [ ] |
| 5 | PII data encryption configured | Critical | [ ] |
| 6 | Security audit logging enabled | Critical | [ ] |
| 7 | Input validation on all API endpoints | High | [ ] |
| 8 | Rate limiting configured appropriately | High | [ ] |
| 9 | Webhook signature validation enabled | High | [ ] |
| 10 | Penetration testing completed | High | [ ] |

### Configuration

| # | Item | Priority | Status |
|---|------|----------|--------|
| 11 | Environment-specific configs separated | Critical | [ ] |
| 12 | Database connection pools sized appropriately | Critical | [ ] |
| 13 | JVM memory settings optimized | High | [ ] |
| 14 | Timeout values configured for production | High | [ ] |
| 15 | Retry policies with exponential backoff | High | [ ] |
| 16 | Circuit breakers configured | High | [ ] |
| 17 | Feature flags for rollback capability | Medium | [ ] |

### Performance

| # | Item | Priority | Status |
|---|------|----------|--------|
| 18 | Load testing completed at 2x expected traffic | Critical | [ ] |
| 19 | Database indexes optimized | Critical | [ ] |
| 20 | Query performance validated | High | [ ] |
| 21 | API response times < 2s for 95th percentile | High | [ ] |
| 22 | Batch job schedules don't conflict | High | [ ] |
| 23 | CDN configured for static assets | Medium | [ ] |
| 24 | Caching strategy implemented | Medium | [ ] |

### Monitoring & Observability

| # | Item | Priority | Status |
|---|------|----------|--------|
| 25 | Application health checks configured | Critical | [ ] |
| 26 | Error alerting to on-call team | Critical | [ ] |
| 27 | Dashboard for key metrics created | Critical | [ ] |
| 28 | Log aggregation configured | High | [ ] |
| 29 | Distributed tracing enabled | High | [ ] |
| 30 | SLA monitoring configured | High | [ ] |
| 31 | Capacity alerts for resources | Medium | [ ] |

### Data & Integration

| # | Item | Priority | Status |
|---|------|----------|--------|
| 32 | Data migration validated | Critical | [ ] |
| 33 | Integration endpoints point to production | Critical | [ ] |
| 34 | Message queue configurations verified | High | [ ] |
| 35 | Webhook endpoints registered | High | [ ] |
| 36 | Backup and recovery tested | Critical | [ ] |
| 37 | Data retention policies configured | High | [ ] |

### Operations

| # | Item | Priority | Status |
|---|------|----------|--------|
| 38 | Runbook documentation complete | Critical | [ ] |
| 39 | On-call rotation established | Critical | [ ] |
| 40 | Incident response plan documented | Critical | [ ] |
| 41 | Rollback procedure tested | Critical | [ ] |
| 42 | Change management process defined | High | [ ] |
| 43 | Support escalation path documented | High | [ ] |

## Validation Scripts

### Health Check Endpoint

```typescript
// Production health check implementation
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  checks: {
    [key: string]: {
      status: 'pass' | 'fail';
      latency?: number;
      message?: string;
    };
  };
}

async function healthCheck(): Promise<HealthStatus> {
  const checks: HealthStatus['checks'] = {};

  // Check PolicyCenter API
  checks.policycenter = await checkApiHealth('PolicyCenter', process.env.POLICYCENTER_URL!);

  // Check ClaimCenter API
  checks.claimcenter = await checkApiHealth('ClaimCenter', process.env.CLAIMCENTER_URL!);

  // Check BillingCenter API
  checks.billingcenter = await checkApiHealth('BillingCenter', process.env.BILLINGCENTER_URL!);

  // Check database connectivity
  checks.database = await checkDatabaseHealth();

  // Check message queue
  checks.messageQueue = await checkMessageQueueHealth();

  // Determine overall status
  const failedChecks = Object.values(checks).filter(c => c.status === 'fail');
  let overallStatus: HealthStatus['status'] = 'healthy';

  if (failedChecks.length > 0) {
    overallStatus = failedChecks.length >= 2 ? 'unhealthy' : 'degraded';
  }

  return {
    status: overallStatus,
    version: process.env.APP_VERSION || 'unknown',
    timestamp: new Date().toISOString(),
    checks
  };
}

async function checkApiHealth(
  name: string,
  baseUrl: string
): Promise<{ status: 'pass' | 'fail'; latency?: number; message?: string }> {
  const startTime = Date.now();
  try {
    const response = await fetch(`${baseUrl}/common/v1/system-info`, {
      headers: { Authorization: `Bearer ${await getToken()}` },
      signal: AbortSignal.timeout(5000)
    });

    return {
      status: response.ok ? 'pass' : 'fail',
      latency: Date.now() - startTime,
      message: response.ok ? undefined : `HTTP ${response.status}`
    };
  } catch (error) {
    return {
      status: 'fail',
      latency: Date.now() - startTime,
      message: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}
```

### Configuration Validation

```typescript
// Validate production configuration
interface ConfigValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

function validateProductionConfig(): ConfigValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Required environment variables
  const requiredVars = [
    'GW_TENANT_ID',
    'GW_CLIENT_ID',
    'GW_CLIENT_SECRET',
    'GW_HUB_URL',
    'POLICYCENTER_URL',
    'CLAIMCENTER_URL',
    'BILLINGCENTER_URL',
    'DATABASE_URL',
    'ENCRYPTION_KEY'
  ];

  for (const varName of requiredVars) {
    if (!process.env[varName]) {
      errors.push(`Missing required environment variable: ${varName}`);
    }
  }

  // Check for development-only settings
  if (process.env.NODE_ENV !== 'production') {
    errors.push('NODE_ENV must be set to "production"');
  }

  if (process.env.DEBUG === 'true') {
    warnings.push('DEBUG mode is enabled - disable for production');
  }

  // Validate URLs are HTTPS
  const urlVars = ['GW_HUB_URL', 'POLICYCENTER_URL', 'CLAIMCENTER_URL', 'BILLINGCENTER_URL'];
  for (const urlVar of urlVars) {
    const url = process.env[urlVar];
    if (url && !url.startsWith('https://')) {
      errors.push(`${urlVar} must use HTTPS`);
    }
  }

  // Check timeout settings
  const apiTimeout = parseInt(process.env.API_TIMEOUT_MS || '30000');
  if (apiTimeout < 5000 || apiTimeout > 120000) {
    warnings.push(`API_TIMEOUT_MS (${apiTimeout}) should be between 5000-120000ms`);
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  };
}
```

### Pre-Deployment Verification

```bash
#!/bin/bash
# pre-deploy-check.sh

echo "=== Guidewire Production Pre-Deployment Check ==="

# Check required environment variables
echo "Checking environment variables..."
REQUIRED_VARS="GW_TENANT_ID GW_CLIENT_ID GW_HUB_URL"
for var in $REQUIRED_VARS; do
  if [ -z "${!var}" ]; then
    echo "ERROR: Missing required variable: $var"
    exit 1
  fi
done
echo "Environment variables OK"

# Test API connectivity
echo "Testing API connectivity..."
TOKEN=$(curl -s -X POST "${GW_HUB_URL}/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${GW_CLIENT_ID}&client_secret=${GW_CLIENT_SECRET}" \
  | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "ERROR: Failed to obtain access token"
  exit 1
fi
echo "Authentication OK"

# Check PolicyCenter
PC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  "${POLICYCENTER_URL}/common/v1/system-info" \
  -H "Authorization: Bearer ${TOKEN}")

if [ "$PC_STATUS" != "200" ]; then
  echo "ERROR: PolicyCenter health check failed (HTTP $PC_STATUS)"
  exit 1
fi
echo "PolicyCenter OK"

# Check ClaimCenter
CC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  "${CLAIMCENTER_URL}/common/v1/system-info" \
  -H "Authorization: Bearer ${TOKEN}")

if [ "$CC_STATUS" != "200" ]; then
  echo "ERROR: ClaimCenter health check failed (HTTP $CC_STATUS)"
  exit 1
fi
echo "ClaimCenter OK"

echo "=== All pre-deployment checks passed ==="
```

## Go-Live Runbook

### T-24 Hours

1. [ ] Final code freeze confirmed
2. [ ] All production secrets deployed to secret manager
3. [ ] DNS changes prepared (if applicable)
4. [ ] Notify stakeholders of deployment window

### T-4 Hours

1. [ ] Run pre-deployment verification script
2. [ ] Confirm monitoring dashboards accessible
3. [ ] Verify on-call team availability
4. [ ] Confirm rollback procedure ready

### T-0 Deployment

1. [ ] Deploy application to production
2. [ ] Run smoke tests
3. [ ] Verify health check endpoints
4. [ ] Monitor error rates for 30 minutes

### Post-Deployment

1. [ ] Document deployment time and version
2. [ ] Notify stakeholders of successful deployment
3. [ ] Monitor closely for 24 hours
4. [ ] Conduct post-deployment review

## Monitoring Dashboard Queries

```yaml
# Key metrics to monitor
dashboards:
  api_performance:
    panels:
      - title: Request Rate
        query: rate(http_requests_total[5m])

      - title: Error Rate
        query: rate(http_requests_total{status=~"5.."}[5m])

      - title: P95 Latency
        query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

      - title: Active Connections
        query: sum(guidewire_active_connections)

  business_metrics:
    panels:
      - title: Submissions Created
        query: rate(policycenter_submissions_created_total[1h])

      - title: Claims Filed
        query: rate(claimcenter_claims_created_total[1h])

      - title: Policies Issued
        query: rate(policycenter_policies_issued_total[1h])
```

## Rollback Procedure

```bash
#!/bin/bash
# rollback.sh

echo "=== Starting Rollback ==="

# Get previous version
PREVIOUS_VERSION=$(kubectl get deployment my-app -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)
echo "Current version: $CURRENT_VERSION"
echo "Rolling back to: $PREVIOUS_VERSION"

# Perform rollback
kubectl rollout undo deployment/my-app

# Wait for rollback
kubectl rollout status deployment/my-app --timeout=300s

# Verify health
HEALTH=$(curl -s http://my-app/health | jq -r '.status')
if [ "$HEALTH" != "healthy" ]; then
  echo "WARNING: Health check failed after rollback"
  exit 1
fi

echo "=== Rollback Complete ==="
```
