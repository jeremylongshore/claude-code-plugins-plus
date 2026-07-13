# MaintainX Production Checklist - Implementation Guide

> Full implementation details and code examples for the `maintainx-prod-checklist` skill.

# MaintainX Production Checklist

## Overview

Comprehensive checklist for deploying MaintainX integrations to production with confidence.

## Prerequisites

- MaintainX integration developed and tested
- Production environment configured
- Deployment pipeline ready

## Production Checklist

### 1. Authentication & Security

- [ ] **API Key Management**
  - [ ] Production API key generated (not test key)
  - [ ] Key stored in secret manager (not environment variables in code)
  - [ ] Key rotation schedule established (90 days recommended)
  - [ ] Old keys revoked after rotation

- [ ] **Security Configuration**
  - [ ] HTTPS enforced for all API calls
  - [ ] TLS 1.2+ required
  - [ ] No credentials in source code
  - [ ] No credentials in logs
  - [ ] Input validation implemented
  - [ ] Output sanitization for logging

```bash
# Verify no secrets in codebase
git secrets --scan
grep -r "mx_live_" . --include="*.ts" --include="*.js"
grep -r "MAINTAINX_API_KEY.*=" . --include="*.ts" --include="*.js" | grep -v ".env"
```

### 2. Error Handling & Resilience

- [ ] **Retry Logic**
  - [ ] Exponential backoff implemented
  - [ ] Maximum retry limits set
  - [ ] Rate limit handling (429 responses)
  - [ ] Circuit breaker for cascading failures

- [ ] **Error Handling**
  - [ ] All API errors caught and handled
  - [ ] User-friendly error messages
  - [ ] Errors logged with context
  - [ ] Alert thresholds configured

```typescript
// Verify error handling coverage
const requiredErrorHandlers = [
  '401 - Unauthorized',
  '403 - Forbidden',
  '404 - Not Found',
  '422 - Validation Error',
  '429 - Rate Limited',
  '500+ - Server Errors',
  'Network Timeout',
  'Connection Refused',
];
```

### 3. Performance & Scalability

- [ ] **API Optimization**
  - [ ] Pagination implemented for large datasets
  - [ ] Appropriate page sizes (max 100)
  - [ ] Caching for frequently accessed data
  - [ ] Connection pooling configured

- [ ] **Load Testing**
  - [ ] Normal load tested
  - [ ] Peak load tested
  - [ ] Rate limits validated
  - [ ] Response times acceptable (<2s for most operations)

```bash
# Simple load test
for i in {1..10}; do
  time curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $MAINTAINX_API_KEY" \
    "https://api.getmaintainx.com/v1/workorders?limit=10"
done
```

### 4. Monitoring & Observability

- [ ] **Logging**
  - [ ] Structured logging implemented
  - [ ] Request/response logging (sanitized)
  - [ ] Error logging with stack traces
  - [ ] Log aggregation configured (CloudWatch, Stackdriver, etc.)

- [ ] **Metrics**
  - [ ] API call latency tracked
  - [ ] Error rate monitored
  - [ ] Rate limit usage tracked
  - [ ] Business metrics defined

- [ ] **Alerting**
  - [ ] Error rate alerts configured
  - [ ] Latency alerts configured
  - [ ] Authentication failure alerts
  - [ ] On-call rotation defined

```typescript
// Minimum metrics to track
const requiredMetrics = [
  'maintainx_api_requests_total',
  'maintainx_api_latency_seconds',
  'maintainx_api_errors_total',
  'maintainx_rate_limit_remaining',
  'maintainx_work_orders_created',
];
```

### 5. Data Integrity

- [ ] **Data Validation**
  - [ ] Input validation on all fields
  - [ ] Type checking implemented
  - [ ] Required fields enforced
  - [ ] Enum values validated

- [ ] **Data Sync**
  - [ ] Idempotency keys used where applicable
  - [ ] Duplicate handling logic
  - [ ] Data consistency checks
  - [ ] Reconciliation process defined

### 6. Documentation

- [ ] **Technical Documentation**
  - [ ] API integration documented
  - [ ] Data flow diagrams created
  - [ ] Error handling documented
  - [ ] Runbooks for common issues

- [ ] **Operational Documentation**
  - [ ] Deployment process documented
  - [ ] Rollback procedure documented
  - [ ] Incident response plan
  - [ ] Contact information updated

### 7. Compliance & Audit

- [ ] **Audit Trail**
  - [ ] All data modifications logged
  - [ ] User actions tracked
  - [ ] Logs retained per policy
  - [ ] Audit reports available

- [ ] **Compliance**
  - [ ] Data handling reviewed
  - [ ] PII handling compliant
  - [ ] Data retention policy applied

## Pre-Deployment Script

```typescript
// scripts/pre-deploy-check.ts
import { MaintainXClient } from '../src/api/maintainx-client';

interface CheckResult {
  name: string;
  passed: boolean;
  message: string;
}

async function runPreDeployChecks(): Promise<CheckResult[]> {
  const results: CheckResult[] = [];

  // Check 1: API connectivity
  try {
    const client = new MaintainXClient();
    await client.getUsers({ limit: 1 });
    results.push({
      name: 'API Connectivity',
      passed: true,
      message: 'Successfully connected to MaintainX API',
    });
  } catch (error: any) {
    results.push({
      name: 'API Connectivity',
      passed: false,
      message: `Failed to connect: ${error.message}`,
    });
  }

  // Check 2: Environment variables
  const requiredEnvVars = [
    'MAINTAINX_API_KEY',
    'NODE_ENV',
  ];

  for (const envVar of requiredEnvVars) {
    results.push({
      name: `Env: ${envVar}`,
      passed: !!process.env[envVar],
      message: process.env[envVar] ? 'Set' : 'Missing',
    });
  }

  // Check 3: Dependencies
  try {
    const { execSync } = require('child_process');
    execSync('npm audit --production --audit-level=high', { stdio: 'pipe' });
    results.push({
      name: 'Dependency Audit',
      passed: true,
      message: 'No high-severity vulnerabilities',
    });
  } catch (error) {
    results.push({
      name: 'Dependency Audit',
      passed: false,
      message: 'High-severity vulnerabilities found',
    });
  }

  // Check 4: Build
  try {
    const { execSync } = require('child_process');
    execSync('npm run build', { stdio: 'pipe' });
    results.push({
      name: 'Build',
      passed: true,
      message: 'Build successful',
    });
  } catch (error) {
    results.push({
      name: 'Build',
      passed: false,
      message: 'Build failed',
    });
  }

  // Check 5: Tests
  try {
    const { execSync } = require('child_process');
    execSync('npm test', { stdio: 'pipe' });
    results.push({
      name: 'Tests',
      passed: true,
      message: 'All tests passed',
    });
  } catch (error) {
    results.push({
      name: 'Tests',
      passed: false,
      message: 'Tests failed',
    });
  }

  return results;
}

async function main() {
  console.log('=== MaintainX Pre-Deployment Checks ===\n');

  const results = await runPreDeployChecks();

  results.forEach(r => {
    const status = r.passed ? '[PASS]' : '[FAIL]';
    console.log(`${status} ${r.name}: ${r.message}`);
  });

  const failed = results.filter(r => !r.passed);
  console.log(`\n${results.length - failed.length}/${results.length} checks passed`);

  if (failed.length > 0) {
    console.log('\nFix the following before deploying:');
    failed.forEach(f => console.log(`  - ${f.name}: ${f.message}`));
    process.exit(1);
  }

  console.log('\nAll checks passed. Ready for deployment!');
}

main().catch(console.error);
```

## Post-Deployment Verification

```bash
#!/bin/bash
# scripts/post-deploy-verify.sh

echo "=== Post-Deployment Verification ==="

# Check 1: Health endpoint
echo -n "Health check... "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://your-app.com/health)
if [ "$HEALTH" == "200" ]; then
  echo "PASS"
else
  echo "FAIL (HTTP $HEALTH)"
fi

# Check 2: MaintainX API connectivity
echo -n "MaintainX API... "
API_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  https://api.getmaintainx.com/v1/users?limit=1)
if [ "$API_CHECK" == "200" ]; then
  echo "PASS"
else
  echo "FAIL (HTTP $API_CHECK)"
fi

# Check 3: Create test work order
echo -n "Create work order... "
WO_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Post-Deploy Test - DELETE ME","priority":"LOW"}' \
  https://api.getmaintainx.com/v1/workorders)
if echo "$WO_RESPONSE" | grep -q '"id"'; then
  echo "PASS"
  # Extract and delete test work order
  WO_ID=$(echo "$WO_RESPONSE" | jq -r '.id')
  echo "  Created test work order: $WO_ID (delete manually)"
else
  echo "FAIL"
fi

echo ""
echo "=== Verification Complete ==="
```

## Output

- All checklist items verified
- Pre-deployment checks passed
- Post-deployment verification completed
- Production deployment documented

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [MaintainX Status Page](https://status.getmaintainx.com)
- [12 Factor App](https://12factor.net/)

## Next Steps

For API version migrations, see `maintainx-upgrade-migration`.
