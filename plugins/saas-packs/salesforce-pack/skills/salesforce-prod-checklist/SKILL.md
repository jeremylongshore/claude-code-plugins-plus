---
name: salesforce-prod-checklist
description: |
  Execute Salesforce production deployment checklist with sandbox testing and rollback.
  Use when deploying Salesforce integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "salesforce production", "deploy salesforce",
  "salesforce go-live", "salesforce launch checklist", "salesforce sandbox to prod".
allowed-tools: Read, Bash(sf:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Production Checklist

## Overview
Complete checklist for deploying Salesforce integrations to production, including sandbox validation, API limit planning, and rollback procedures.

## Prerequisites
- Staging/sandbox environment tested and verified
- Production Connected App configured
- Dedicated integration user in production
- Monitoring and alerting ready

## Instructions

### Pre-Deployment Configuration
- [ ] Production Connected App has minimum OAuth scopes (not `full`)
- [ ] Dedicated integration user with restricted profile (not admin)
- [ ] SF_LOGIN_URL set to `https://login.salesforce.com` (not `test.salesforce.com`)
- [ ] All credentials stored in vault/secrets manager (not env files)
- [ ] IP restrictions configured on Connected App and user profile
- [ ] JWT certificate uploaded (if using JWT Bearer flow)

### API Limit Planning
- [ ] Estimated daily API calls documented
- [ ] API limit headroom > 20% (`GET /services/data/v59.0/limits/`)
- [ ] Bulk API used for operations > 200 records
- [ ] Composite API used for multi-object transactions
- [ ] sObject Collections used for batch CRUD (max 200/call)
- [ ] Caching implemented for describe/metadata calls

### Code Quality
- [ ] All SOQL queries use parameterized filters (no injection)
- [ ] Error handling covers Salesforce error codes (`INVALID_FIELD`, `REQUEST_LIMIT_EXCEEDED`, etc.)
- [ ] Retry logic implemented for transient errors (`UNABLE_TO_LOCK_ROW`, `SERVER_UNAVAILABLE`)
- [ ] No hardcoded Salesforce IDs (use External IDs or SOQL lookups)
- [ ] Connection auto-refreshes expired tokens
- [ ] Logging redacts PII and credentials

### Sandbox Validation
```bash
# Test in Full sandbox first (mirrors production data)
# 1. Deploy to sandbox
sf project deploy start --target-org my-sandbox

# 2. Run integration tests against sandbox
SF_LOGIN_URL=https://test.salesforce.com npm run test:integration

# 3. Verify API limits are within budget
sf limits api display --target-org my-sandbox --json | jq '.result[] | select(.name == "DailyApiRequests")'

# 4. Check Apex test results
sf apex run test --target-org my-sandbox --result-format human --code-coverage
```

### Health Check Endpoint
```typescript
async function salesforceHealthCheck(): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  details: Record<string, any>;
}> {
  const conn = await getConnection();
  const start = Date.now();

  try {
    const [identity, limits] = await Promise.all([
      conn.identity(),
      conn.request('/services/data/v59.0/limits/'),
    ]);

    const apiUsagePercent = ((limits.DailyApiRequests.Max - limits.DailyApiRequests.Remaining) / limits.DailyApiRequests.Max) * 100;

    return {
      status: apiUsagePercent > 90 ? 'degraded' : 'healthy',
      details: {
        connected: true,
        latencyMs: Date.now() - start,
        instance: conn.instanceUrl,
        apiRemaining: limits.DailyApiRequests.Remaining,
        apiUsagePercent: Math.round(apiUsagePercent),
      },
    };
  } catch (error: any) {
    return {
      status: 'unhealthy',
      details: { connected: false, error: error.message, latencyMs: Date.now() - start },
    };
  }
}
```

### Deployment Steps
```bash
# 1. Pre-flight: check Salesforce system status
curl -s https://api.status.salesforce.com/v1/incidents/active | jq 'length'

# 2. Verify production API limits
sf limits api display --target-org production --json

# 3. Deploy metadata (if applicable)
sf project deploy start --target-org production --dry-run  # Validate first
sf project deploy start --target-org production             # Then deploy

# 4. Verify health check
curl -sf https://yourapp.com/health | jq '.services.salesforce'

# 5. Monitor error rates for 30 minutes after deploy
```

### Rollback Procedure
```bash
# Metadata rollback
sf project deploy start --target-org production --metadata-dir rollback/

# Integration rollback: revert to previous version
# Feature flag: disable Salesforce integration without redeploying
SF_INTEGRATION_ENABLED=false
```

## Error Handling
| Alert | Condition | Severity |
|-------|-----------|----------|
| API Limit Warning | > 80% daily limit used | P3 |
| API Limit Critical | > 95% daily limit used | P1 |
| Auth Failure | INVALID_SESSION_ID errors | P1 |
| SOQL Errors | MALFORMED_QUERY or INVALID_FIELD | P2 |
| Record Lock | UNABLE_TO_LOCK_ROW spikes | P3 |

## Resources
- [Salesforce Status Page](https://status.salesforce.com)
- [Deployment Best Practices](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_develop.htm)
- [Sandbox Types](https://help.salesforce.com/s/articleView?id=sf.deploy_sandboxes_intro.htm)

## Next Steps
For version upgrades, see `salesforce-upgrade-migration`.
