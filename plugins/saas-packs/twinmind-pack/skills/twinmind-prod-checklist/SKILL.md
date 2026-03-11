---
name: twinmind-prod-checklist
description: |
  Complete production deployment checklist for TwinMind integrations.
  Use when preparing to deploy, auditing production readiness,
  or ensuring best practices are followed.
  Trigger with phrases like "twinmind production", "deploy twinmind",
  "twinmind go-live checklist", "twinmind production ready".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Production Checklist

## Overview
Comprehensive checklist for deploying TwinMind integrations to production.

## Prerequisites
- Development and staging environments tested
- API credentials for production
- Infrastructure provisioned
- Team roles assigned

## Production Readiness Checklist

### 1. Authentication & Security

```markdown
## Authentication
- [ ] Production API key generated (separate from dev/staging)
- [ ] API key stored in secrets manager (not env vars)
- [ ] API key rotation procedure documented
- [ ] Webhook secrets configured
- [ ] All OAuth tokens refreshed and valid

## Security
- [ ] HTTPS enforced on all endpoints
- [ ] Webhook signature verification enabled
- [ ] CORS configured correctly
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection protection verified
- [ ] XSS protection enabled
- [ ] CSP headers configured
```

### 2. Data & Privacy

```markdown
## Data Protection
- [ ] Transcripts encrypted at rest (AES-256)  # 256 bytes
- [ ] PII redaction enabled and tested
- [ ] Data retention policies configured
- [ ] Backup encryption verified
- [ ] Data residency requirements met

## Privacy Compliance
- [ ] GDPR compliance verified (if applicable)
- [ ] User consent flow implemented
- [ ] Data deletion API integrated
- [ ] Privacy policy updated
- [ ] Cookie consent banner (if applicable)

## Audit Trail
- [ ] Audit logging enabled for all operations
- [ ] Log retention configured
- [ ] Sensitive data excluded from logs
- [ ] Log access restricted
```

### 3. Infrastructure

```markdown
## Compute
- [ ] Auto-scaling configured
- [ ] Health checks enabled
- [ ] Graceful shutdown implemented
- [ ] Resource limits set (CPU, memory)
- [ ] Container security scanned

## Networking
- [ ] Load balancer configured
- [ ] TLS 1.3 enforced
- [ ] DNS records verified
- [ ] CDN configured (if applicable)
- [ ] Firewall rules reviewed

## Storage
- [ ] Database backups automated
- [ ] Storage encryption enabled
- [ ] Disaster recovery plan tested
- [ ] Data migration scripts ready
```

### 4. Monitoring & Observability

```markdown
## Metrics
- [ ] Prometheus/Datadog metrics configured
- [ ] Custom TwinMind metrics added:
  - [ ] twinmind_transcriptions_total
  - [ ] twinmind_transcription_duration_seconds
  - [ ] twinmind_errors_total
  - [ ] twinmind_api_latency_seconds
- [ ] Dashboards created

## Alerting
- [ ] Alert rules configured:
  - [ ] Error rate > 5%
  - [ ] P95 latency > 5s
  - [ ] Rate limit warnings
  - [ ] API availability
- [ ] On-call rotation set up
- [ ] Escalation policy defined

## Logging
- [ ] Structured logging implemented
- [ ] Log levels configured (INFO in prod)
- [ ] Log aggregation set up
- [ ] Log-based alerts configured

## Tracing
- [ ] Distributed tracing enabled
- [ ] Trace sampling configured
- [ ] Trace retention set
```

### 5. Error Handling

```markdown
## Error Recovery
- [ ] Retry logic with exponential backoff
- [ ] Circuit breaker pattern implemented
- [ ] Fallback behavior defined
- [ ] Dead letter queue for failed webhooks
- [ ] Error notification system

## Graceful Degradation
- [ ] Offline mode behavior defined
- [ ] Cached data fallback
- [ ] User-friendly error messages
- [ ] Status page integration
```

### 6. Performance

```markdown
## Optimization
- [ ] Response caching configured
- [ ] Database queries optimized
- [ ] Connection pooling enabled
- [ ] Async processing for heavy tasks
- [ ] CDN for static assets

## Load Testing
- [ ] Load tests performed
- [ ] Peak traffic simulated
- [ ] Breaking point identified
- [ ] Auto-scaling verified
- [ ] Performance baselines documented
```

### 7. Deployment

```markdown
## CI/CD
- [ ] Build pipeline configured
- [ ] Automated tests passing
- [ ] Security scanning integrated
- [ ] Deployment automation ready
- [ ] Rollback procedure tested

## Release Process
- [ ] Blue-green or canary deployment
- [ ] Feature flags configured
- [ ] Database migrations automated
- [ ] Smoke tests defined
- [ ] Release notes prepared
```

### 8. Documentation

```markdown
## Technical Docs
- [ ] API documentation current
- [ ] Architecture diagrams updated
- [ ] Runbook created
- [ ] Troubleshooting guide ready

## Operational Docs
- [ ] Incident response plan
- [ ] Escalation contacts
- [ ] Vendor contact info
- [ ] SLA documentation
```

## Pre-Launch Verification Script

```bash
#!/bin/bash
set -euo pipefail
# pre-launch-check.sh

echo "TwinMind Production Pre-Launch Check"
echo "====================================="

# Check environment
echo -n "Checking NODE_ENV... "
if [ "$NODE_ENV" = "production" ]; then
  echo "OK (production)"
else
  echo "WARNING: NODE_ENV=$NODE_ENV"
fi

# Check API key
echo -n "Checking API key... "
if [ -n "$TWINMIND_API_KEY" ]; then
  PREFIX=${TWINMIND_API_KEY:0:10}
  echo "OK ($PREFIX...)"
else
  echo "FAIL: TWINMIND_API_KEY not set"
fi

# Test API connectivity
echo -n "Testing API connectivity... "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health)
if [ "$HEALTH" = "200" ]; then  # HTTP 200 OK
  echo "OK"
else
  echo "FAIL: HTTP $HEALTH"
fi

# Check webhook secret
echo -n "Checking webhook secret... "
if [ -n "$TWINMIND_WEBHOOK_SECRET" ]; then
  echo "OK"
else
  echo "WARNING: TWINMIND_WEBHOOK_SECRET not set"
fi

# Check encryption key
echo -n "Checking encryption key... "
if [ -n "$TWINMIND_ENCRYPTION_KEY" ]; then
  KEY_LEN=${#TWINMIND_ENCRYPTION_KEY}
  if [ "$KEY_LEN" -ge 64 ]; then
    echo "OK (256-bit)"  # 256 bytes
  else
    echo "WARNING: Key too short"
  fi
else
  echo "WARNING: TWINMIND_ENCRYPTION_KEY not set"
fi

# Check database
echo -n "Checking database... "
if [ -n "$DATABASE_URL" ]; then
  echo "OK"
else
  echo "FAIL: DATABASE_URL not set"
fi

echo ""
echo "Pre-launch check complete."
```

## Post-Launch Verification

```typescript
// scripts/post-launch-verify.ts
async function verifyProduction() {
  const checks = [
    { name: 'API Health', fn: checkApiHealth },
    { name: 'Database', fn: checkDatabase },
    { name: 'Transcription', fn: testTranscription },
    { name: 'Webhook', fn: testWebhook },
    { name: 'Metrics', fn: checkMetrics },
  ];

  console.log('Post-Launch Verification');
  console.log('========================');

  for (const check of checks) {
    try {
      await check.fn();
      console.log(`[PASS] ${check.name}`);
    } catch (error) {
      console.log(`[FAIL] ${check.name}: ${error.message}`);
    }
  }
}

async function checkApiHealth() {
  const response = await fetch('https://api.twinmind.com/v1/health', {
    headers: { 'Authorization': `Bearer ${process.env.TWINMIND_API_KEY}` },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
}

async function testTranscription() {
  // Test with a known audio sample
  const client = getTwinMindClient();
  const result = await client.transcribe('https://example.com/test-audio.mp3');
  if (!result.id) throw new Error('No transcript ID returned');
}

// Run verification
verifyProduction();
```

## Rollback Plan

```markdown
## Rollback Procedure

### Immediate Rollback (< 5 minutes)
1. Trigger deployment rollback via CI/CD
2. Verify previous version is running
3. Confirm health checks passing

### Database Rollback (if needed)
1. Stop application traffic
2. Run migration rollback script
3. Verify data integrity
4. Resume traffic

### Communication
1. Update status page
2. Notify affected users
3. Create incident report

### Post-Rollback
1. Identify root cause
2. Create fix
3. Test in staging
4. Schedule re-deployment
```

## Output
- Complete production checklist
- Pre-launch verification script
- Post-launch verification tests
- Rollback procedure

## Error Handling

| Issue | Impact | Mitigation |
|-------|--------|------------|
| API key invalid | Service down | Verify key in staging first |
| Missing metrics | Blind spots | Test dashboards pre-launch |
| No rollback plan | Extended outage | Document and test rollback |
| Inadequate alerts | Delayed response | Test alert routes |

## Resources
- [TwinMind Enterprise SLA](https://twinmind.com/enterprise)
- [Production Best Practices](https://twinmind.com/docs/production)
- [Status Page](https://status.twinmind.com)

## Next Steps
For upgrading between tiers, see `twinmind-upgrade-migration`.

## Instructions

1. Assess the current state of the deployment configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Examples

**Basic usage**: Apply twinmind prod checklist to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind prod checklist for production environments with multiple constraints and team-specific requirements.