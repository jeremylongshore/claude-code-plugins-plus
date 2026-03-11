---
name: openevidence-prod-checklist
description: |
  Production readiness checklist for OpenEvidence clinical AI deployments.
  Use when preparing for production launch, conducting pre-deployment reviews,
  or auditing OpenEvidence integration for compliance.
  Trigger with phrases like "openevidence production", "openevidence go-live",
  "openevidence checklist", "deploy openevidence", "openevidence readiness".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Production Checklist

## Overview
Comprehensive checklist for deploying OpenEvidence clinical AI integrations to production healthcare environments.

## Prerequisites
- Completed development and testing phases
- Signed BAA with OpenEvidence
- Security review completed
- Compliance team sign-off

## Production Readiness Checklist

### 1. Legal & Compliance

- [ ] **Business Associate Agreement (BAA) signed**
  - Contact: compliance@openevidence.com
  - Required for any PHI handling

- [ ] **API Terms of Service accepted**
  - Review: https://www.openevidence.com/policies/api

- [ ] **Clinical use disclaimers in place**
  - All clinical outputs must include appropriate disclaimers
  - "For informational purposes only. Verify with current guidelines."

- [ ] **Liability and malpractice considerations reviewed**
  - Legal review of clinical decision support usage

- [ ] **Data processing agreement documented**
  - What data is sent, stored, processed

### 2. Security

- [ ] **Production API keys generated**
  - Separate keys from development/staging
  - Stored in secret manager (not environment variables)

- [ ] **Key rotation schedule established**
  - Recommend: 90-day rotation cycle

- [ ] **IP allowlist configured** (if available)
  - Restrict API access to known IP ranges

- [ ] **TLS 1.2+ enforced**
  - No fallback to older protocols

- [ ] **PHI sanitization implemented**
  - Review `openevidence-security-basics`

- [ ] **Webhook signature verification active**
  - All webhook endpoints validate signatures

- [ ] **Audit logging enabled**
  - HIPAA-compliant access logging
  - Minimum 6-year retention

### 3. Infrastructure

- [ ] **High availability configuration**
  ```typescript
  // Multiple API endpoints for failover
  const config = {
    primaryEndpoint: 'https://api.openevidence.com',
    fallbackEndpoint: 'https://api-fallback.openevidence.com',
    timeout: 30000,
    retries: 3,
  };
  ```

- [ ] **Circuit breaker implemented**
  ```typescript
  import CircuitBreaker from 'opossum';

  const breaker = new CircuitBreaker(clinicalQuery, {
    timeout: 30000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
  });
  ```

- [ ] **Rate limit handling configured**
  - Review `openevidence-rate-limits`
  - Request queuing for traffic spikes

- [ ] **Timeout configuration appropriate**
  - Clinical queries: 15-30s
  - DeepConsult: 5-10 minutes

- [ ] **Health check endpoint implemented**
  ```typescript
  app.get('/health/openevidence', async (req, res) => {
    try {
      await client.health.check();
      res.json({ status: 'healthy' });
    } catch (error) {
      res.status(503).json({ status: 'unhealthy', error: error.message });
    }
  });
  ```

### 4. Monitoring & Alerting

- [ ] **Metrics collection active**
  - Request count, latency, error rate
  - Review `openevidence-observability`

- [ ] **Alert rules configured**
  | Alert | Threshold | Severity |
  |-------|-----------|----------|
  | Error rate > 5% | 5 min window | Warning |
  | Error rate > 20% | 5 min window | Critical |
  | P95 latency > 15s | 5 min window | Warning |
  | Health check failed | 2 consecutive | Critical |

- [ ] **Dashboard created**
  - Real-time visibility into OpenEvidence integration health

- [ ] **Log aggregation configured**
  - Centralized logging for debugging
  - PHI excluded from logs

### 5. Error Handling & Resilience

- [ ] **Graceful degradation implemented**
  ```typescript
  async function clinicalQueryWithFallback(question: string) {
    try {
      return await openEvidenceQuery(question);
    } catch (error) {
      // Log error, alert, return cached or default response
      await alertService.send('OpenEvidence unavailable');
      return {
        answer: 'Clinical evidence service temporarily unavailable. Please consult current guidelines directly.',
        fallback: true,
      };
    }
  }
  ```

- [ ] **Retry logic tested**
  - Exponential backoff with jitter
  - Respects Retry-After headers

- [ ] **Error classification implemented**
  - Review `openevidence-common-errors`

### 6. Performance

- [ ] **Response caching strategy**
  - Cache frequently queried clinical information
  - Cache TTL appropriate for clinical data freshness

- [ ] **Connection pooling configured**
  - Reuse HTTP connections

- [ ] **Query optimization reviewed**
  - Clear, specific clinical questions
  - Appropriate context provided

- [ ] **Load testing completed**
  - Test at 2x expected peak traffic
  - Verify rate limits not exceeded

### 7. Documentation & Training

- [ ] **Runbook created**
  - Incident response procedures
  - Review `openevidence-incident-runbook`

- [ ] **On-call training completed**
  - Team knows how to triage OpenEvidence issues

- [ ] **User documentation updated**
  - How to use clinical decision support
  - Limitations and appropriate use

- [ ] **Clinical staff training**
  - Understanding AI-assisted decision support
  - When to rely on vs. question AI recommendations

### 8. Testing & Validation

- [ ] **Integration tests passing**
  - Against sandbox environment

- [ ] **End-to-end tests passing**
  - Full workflow validation

- [ ] **Clinical validation completed**
  - Sample queries reviewed by clinical team
  - Responses appropriate and accurate

- [ ] **Performance benchmarks met**
  - P50 < 5s, P95 < 15s for clinical queries
  - P50 < 3min, P95 < 5min for DeepConsult

### 9. Deployment

- [ ] **Blue-green or canary deployment planned**
  - Gradual rollout with monitoring

- [ ] **Rollback procedure documented**
  - Quick revert if issues detected

- [ ] **Feature flags configured**
  - Ability to disable OpenEvidence quickly

- [ ] **Database migrations completed**
  - Audit log tables, cache tables ready

### 10. Post-Launch

- [ ] **Monitoring dashboard reviewed daily** (first week)

- [ ] **Error reports triaged immediately**

- [ ] **User feedback collection active**

- [ ] **Performance baseline established**

## Production Configuration Example

```typescript
// config/openevidence.production.ts
export const productionConfig = {
  // Credentials from secret manager
  credentials: {
    source: 'secret-manager',
    apiKeyPath: 'projects/prod/secrets/openevidence-api-key',
    orgIdPath: 'projects/prod/secrets/openevidence-org-id',
  },

  // Endpoints
  api: {
    baseUrl: 'https://api.openevidence.com',
    timeout: 30000,  # 30000: 30 seconds in ms
    retries: 3,
  },

  // Rate limiting
  rateLimits: {
    enabled: true,
    maxConcurrent: 10,
    requestsPerMinute: 100,
  },

  // Circuit breaker
  circuitBreaker: {
    enabled: true,
    errorThreshold: 50,
    resetTimeout: 30000,  # 30 seconds in ms
  },

  // Caching
  cache: {
    enabled: true,
    ttlSeconds: 3600,  # 3600: timeout: 1 hour
    maxEntries: 10000,  # 10000: 10 seconds in ms
  },

  // Monitoring
  monitoring: {
    metricsEnabled: true,
    tracingEnabled: true,
    logLevel: 'info',
  },
};
```

## Output
- Completed production readiness checklist
- Configuration validated
- All stakeholders signed off
- Go-live approved

## Resources
- [OpenEvidence](https://www.openevidence.com/)
- [OpenEvidence Security](https://www.openevidence.com/security)

## Next Steps
For version upgrades, see `openevidence-upgrade-migration`.

## Instructions

1. Assess the current state of the deployment configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with deployment |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply openevidence prod checklist to a standard project setup with default configuration options.

**Advanced scenario**: Customize openevidence prod checklist for production environments with multiple constraints and team-specific requirements.