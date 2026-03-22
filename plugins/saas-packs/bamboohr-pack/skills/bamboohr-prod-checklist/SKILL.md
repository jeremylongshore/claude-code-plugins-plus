---
name: bamboohr-prod-checklist
description: |
  Execute BambooHR production deployment checklist and rollback procedures.
  Use when deploying BambooHR integrations to production, preparing for launch,
  or implementing go-live procedures with BambooHR API.
  Trigger with phrases like "bamboohr production", "deploy bamboohr",
  "bamboohr go-live", "bamboohr launch checklist", "bamboohr prod ready".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, production]
compatible-with: claude-code
---

# BambooHR Production Checklist

## Overview

Complete pre-launch checklist for deploying BambooHR integrations to production, covering API configuration, data integrity, monitoring, and rollback procedures.

## Prerequisites

- Staging environment tested and verified
- Production BambooHR API key ready
- Deployment pipeline configured
- Monitoring and alerting infrastructure available

## Instructions

### Pre-Deployment Checklist

#### Authentication & Secrets
- [ ] Production API key created under a service account (not personal account)
- [ ] API key stored in secrets manager (AWS Secrets Manager / GCP Secret Manager / Vault)
- [ ] `BAMBOOHR_COMPANY_DOMAIN` set correctly for production
- [ ] Webhook secret stored securely
- [ ] Key rotation procedure documented and tested
- [ ] Old staging/test keys will not be deployed to production

#### API Integration Quality
- [ ] All API calls use `Accept: application/json` header
- [ ] Error handling covers all BambooHR HTTP statuses (400, 401, 403, 404, 503)
- [ ] `X-BambooHR-Error-Message` header parsed for error details
- [ ] `Retry-After` header honored on 503 responses
- [ ] Exponential backoff with jitter implemented for retries
- [ ] Request queue limits concurrent API calls (max 3-5 parallel)
- [ ] No hardcoded employee IDs, company domains, or API keys

#### Data Integrity
- [ ] Custom reports validated against expected field schema
- [ ] Employee directory sync handles new, updated, and terminated employees
- [ ] Date fields parsed consistently (`YYYY-MM-DD` format)
- [ ] Null/empty field handling tested (BambooHR returns `null` or `""`)
- [ ] Unicode employee names handled correctly
- [ ] Large directory tested (500+ employees)

#### Security & Compliance
- [ ] PII fields redacted from application logs
- [ ] Webhook signatures verified with HMAC-SHA256
- [ ] Only necessary BambooHR fields requested (least data principle)
- [ ] No SSN, salary, or restricted data stored without encryption at rest
- [ ] API access audit trail enabled

### Health Check Endpoint

```typescript
// api/health.ts
import { BambooHRClient, BambooHRApiError } from '../bamboohr/client';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'down';
  bamboohr: {
    connected: boolean;
    latencyMs: number;
    error?: string;
    employeeCount?: number;
  };
  timestamp: string;
}

export async function healthCheck(client: BambooHRClient): Promise<HealthStatus> {
  const start = Date.now();
  try {
    const dir = await client.getDirectory();
    return {
      status: 'healthy',
      bamboohr: {
        connected: true,
        latencyMs: Date.now() - start,
        employeeCount: dir.employees.length,
      },
      timestamp: new Date().toISOString(),
    };
  } catch (err) {
    const latency = Date.now() - start;
    const errMsg = err instanceof BambooHRApiError ? err.message : 'Unknown error';

    return {
      status: err instanceof BambooHRApiError && err.retryable ? 'degraded' : 'down',
      bamboohr: { connected: false, latencyMs: latency, error: errMsg },
      timestamp: new Date().toISOString(),
    };
  }
}
```

### Monitoring & Alerting

```typescript
// Recommended alert thresholds for BambooHR integrations
const ALERTS = {
  p1_critical: [
    { name: 'Auth failure', condition: '401/403 errors > 0', action: 'Page on-call' },
    { name: 'API down', condition: 'Health check fails 3x consecutive', action: 'Page on-call' },
  ],
  p2_high: [
    { name: 'Rate limited', condition: '503 errors > 3/min', action: 'Slack alert' },
    { name: 'High latency', condition: 'p99 > 5000ms', action: 'Slack alert' },
    { name: 'Sync failure', condition: 'Sync job fails', action: 'Slack + ticket' },
  ],
  p3_medium: [
    { name: 'Elevated errors', condition: '4xx errors > 10/hour', action: 'Log + daily review' },
    { name: 'Data mismatch', condition: 'Schema validation failures', action: 'Log + ticket' },
  ],
};
```

### Gradual Rollout Strategy

```bash
#!/bin/bash
# deploy-bamboohr-integration.sh

echo "=== Pre-flight checks ==="
# 1. Verify BambooHR API is up
curl -sf "https://status.bamboohr.com" > /dev/null || { echo "BambooHR may be down!"; exit 1; }

# 2. Verify production credentials work
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -u "${BAMBOOHR_API_KEY}:x" \
  -H "Accept: application/json" \
  "https://api.bamboohr.com/api/gateway.php/${BAMBOOHR_COMPANY_DOMAIN}/v1/employees/directory")
[ "$STATUS" -eq 200 ] || { echo "Auth check failed: $STATUS"; exit 1; }
echo "API auth: OK"

# 3. Deploy
echo "=== Deploying ==="
# Platform-specific deployment command here
# kubectl apply -f k8s/production.yaml
# fly deploy
# gcloud run deploy ...

# 4. Post-deploy health check
echo "=== Post-deploy verification ==="
sleep 10
curl -sf "https://your-app.com/api/health" | jq .bamboohr
```

### Rollback Procedure

```bash
# Immediate rollback
# kubectl rollout undo deployment/bamboohr-integration
# fly releases rollback
# gcloud run services update-traffic --to-revisions=REVISION=100

# Verify rollback health
curl -sf "https://your-app.com/api/health" | jq .
```

## Output

- Completed pre-deployment checklist
- Health check endpoint deployed
- Monitoring alerts configured
- Gradual rollout with pre-flight checks
- Documented rollback procedure

## Error Handling

| Alert | Condition | Severity | Response |
|-------|-----------|----------|----------|
| Auth failure | 401/403 from BambooHR | P1 | Check API key; rotate if compromised |
| Rate limit storm | Continuous 503s | P2 | Pause sync jobs; reduce request rate |
| Sync data gap | Missing employees in sync | P2 | Run full resync; check changed-since |
| Schema mismatch | New/removed BambooHR fields | P3 | Update field mappings; add defaults |

## Resources

- [BambooHR Status Page](https://status.bamboohr.com)
- [BambooHR API Changes](https://documentation.bamboohr.com/docs/past-changes-to-the-api)
- [BambooHR Planned Changes](https://documentation.bamboohr.com/docs/planned-changes-to-the-api)

## Next Steps

For version upgrades, see `bamboohr-upgrade-migration`.
