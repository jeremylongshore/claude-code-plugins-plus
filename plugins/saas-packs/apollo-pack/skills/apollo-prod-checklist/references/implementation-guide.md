# Apollo Production Checklist - Implementation Guide

> Full implementation details and code examples for the `apollo-prod-checklist` skill.

# Apollo Production Checklist

## Overview
Comprehensive checklist for deploying Apollo.io integrations to production with validation scripts and verification steps.

## Pre-Deployment Checklist

### 1. API Configuration
```bash
# Verify production API key
echo "Key length: $(echo -n $APOLLO_API_KEY | wc -c)"
echo "Key prefix: ${APOLLO_API_KEY:0:8}..."

# Test API connectivity
curl -s "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY" | jq
```

- [ ] Production API key configured
- [ ] API key stored in secure secrets manager
- [ ] API key has appropriate permissions
- [ ] Backup/secondary key configured

### 2. Error Handling
```typescript
// Verify error handlers are in place
const requiredHandlers = [
  'ApolloAuthError',
  'ApolloRateLimitError',
  'ApolloValidationError',
  'ApolloServerError',
];

// Check each handler exists and is tested
```

- [ ] All error types handled
- [ ] Error logging configured
- [ ] Alert thresholds set
- [ ] Fallback behavior defined

### 3. Rate Limiting
```typescript
// Verify rate limit configuration
const config = {
  maxRequestsPerMinute: 90, // Buffer below 100
  retryConfig: {
    maxRetries: 3,
    initialDelay: 1000,
    maxDelay: 60000,
  },
  queueConcurrency: 5,
};
```

- [ ] Rate limiter implemented
- [ ] Exponential backoff configured
- [ ] Request queue with concurrency limits
- [ ] Rate limit monitoring enabled

### 4. Security
- [ ] API keys not in code
- [ ] .env files in .gitignore
- [ ] HTTPS only
- [ ] PII redaction in logs
- [ ] Data retention policy implemented

### 5. Monitoring
- [ ] Request/response logging
- [ ] Error rate alerts
- [ ] Latency monitoring
- [ ] Rate limit utilization tracking
- [ ] Health check endpoint

## Deployment Validation Script

```typescript
// scripts/validate-production.ts
import { apollo } from '../src/lib/apollo/client';

interface ValidationResult {
  check: string;
  status: 'pass' | 'fail' | 'warn';
  message: string;
}

async function validateProduction(): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];

  // 1. API Key Validation
  try {
    await apollo.healthCheck();
    results.push({
      check: 'API Key',
      status: 'pass',
      message: 'API key is valid and active',
    });
  } catch (error: any) {
    results.push({
      check: 'API Key',
      status: 'fail',
      message: `API key validation failed: ${error.message}`,
    });
  }

  // 2. People Search Test
  try {
    const searchResult = await apollo.searchPeople({
      q_organization_domains: ['apollo.io'],
      per_page: 1,
    });
    results.push({
      check: 'People Search',
      status: searchResult.people.length > 0 ? 'pass' : 'warn',
      message: `Found ${searchResult.pagination.total_entries} contacts`,
    });
  } catch (error: any) {
    results.push({
      check: 'People Search',
      status: 'fail',
      message: `Search failed: ${error.message}`,
    });
  }

  // 3. Organization Enrichment Test
  try {
    const orgResult = await apollo.enrichOrganization('apollo.io');
    results.push({
      check: 'Org Enrichment',
      status: orgResult.organization ? 'pass' : 'warn',
      message: orgResult.organization
        ? `Enriched: ${orgResult.organization.name}`
        : 'No organization data returned',
    });
  } catch (error: any) {
    results.push({
      check: 'Org Enrichment',
      status: 'fail',
      message: `Enrichment failed: ${error.message}`,
    });
  }

  // 4. Environment Variables
  const requiredEnvVars = ['APOLLO_API_KEY'];
  const optionalEnvVars = ['APOLLO_RATE_LIMIT', 'APOLLO_TIMEOUT'];

  for (const envVar of requiredEnvVars) {
    results.push({
      check: `Env: ${envVar}`,
      status: process.env[envVar] ? 'pass' : 'fail',
      message: process.env[envVar] ? 'Set' : 'Missing required variable',
    });
  }

  for (const envVar of optionalEnvVars) {
    results.push({
      check: `Env: ${envVar}`,
      status: process.env[envVar] ? 'pass' : 'warn',
      message: process.env[envVar] ? 'Set' : 'Using default value',
    });
  }

  // 5. Response Time Check
  const startTime = Date.now();
  try {
    await apollo.searchPeople({ per_page: 1 });
    const latency = Date.now() - startTime;
    results.push({
      check: 'Latency',
      status: latency < 2000 ? 'pass' : latency < 5000 ? 'warn' : 'fail',
      message: `Response time: ${latency}ms`,
    });
  } catch {
    results.push({
      check: 'Latency',
      status: 'fail',
      message: 'Could not measure latency',
    });
  }

  return results;
}

// Run validation
async function main() {
  console.log('=== Apollo Production Validation ===\n');

  const results = await validateProduction();

  // Display results
  for (const result of results) {
    const icon = result.status === 'pass' ? '[OK]' : result.status === 'warn' ? '[!!]' : '[XX]';
    console.log(`${icon} ${result.check}: ${result.message}`);
  }

  // Summary
  const passed = results.filter((r) => r.status === 'pass').length;
  const warned = results.filter((r) => r.status === 'warn').length;
  const failed = results.filter((r) => r.status === 'fail').length;

  console.log(`\n=== Summary ===`);
  console.log(`Passed: ${passed}, Warnings: ${warned}, Failed: ${failed}`);

  if (failed > 0) {
    console.error('\n[FAIL] Production validation failed. Fix issues before deploying.');
    process.exit(1);
  } else if (warned > 0) {
    console.warn('\n[WARN] Validation passed with warnings. Review before deploying.');
  } else {
    console.log('\n[PASS] All checks passed. Ready for production.');
  }
}

main().catch(console.error);
```

## Post-Deployment Verification

```bash
#!/bin/bash
# scripts/verify-deployment.sh

echo "=== Post-Deployment Verification ==="

# 1. Health check
echo -n "Health check: "
curl -s -o /dev/null -w "%{http_code}" "$PROD_URL/health" && echo " OK" || echo " FAILED"

# 2. Apollo integration check
echo -n "Apollo integration: "
curl -s -o /dev/null -w "%{http_code}" "$PROD_URL/api/apollo/health" && echo " OK" || echo " FAILED"

# 3. Sample search
echo -n "Sample search: "
RESULT=$(curl -s "$PROD_URL/api/apollo/search?domain=apollo.io&limit=1")
echo $RESULT | jq -e '.contacts | length > 0' > /dev/null && echo " OK" || echo " FAILED"

# 4. Error handling
echo -n "Error handling: "
curl -s "$PROD_URL/api/apollo/search?invalid=true" | jq -e '.error' > /dev/null && echo " OK" || echo " FAILED"

echo ""
echo "Verification complete."
```

## Rollback Plan

```typescript
// src/lib/apollo/feature-flags.ts
const APOLLO_FEATURES = {
  peopleSearch: process.env.APOLLO_FEATURE_PEOPLE_SEARCH !== 'false',
  enrichment: process.env.APOLLO_FEATURE_ENRICHMENT !== 'false',
  sequences: process.env.APOLLO_FEATURE_SEQUENCES !== 'false',
};

export function isFeatureEnabled(feature: keyof typeof APOLLO_FEATURES): boolean {
  return APOLLO_FEATURES[feature];
}

// Usage
if (isFeatureEnabled('peopleSearch')) {
  const results = await apollo.searchPeople(params);
} else {
  throw new Error('Apollo people search is currently disabled');
}
```

## Runbook

| Scenario | Action | Command |
|----------|--------|---------|
| API Key Compromised | Rotate immediately | Update secrets, deploy |
| Rate Limited | Enable backoff | Set `APOLLO_RATE_LIMIT=50` |
| Search Down | Disable feature | Set `APOLLO_FEATURE_PEOPLE_SEARCH=false` |
| Full Outage | Disable all | Set `APOLLO_ENABLED=false` |
| Rollback | Revert deployment | `kubectl rollout undo` |

## Output
- Pre-deployment checklist completed
- Validation script results
- Post-deployment verification
- Rollback procedures documented

## Error Handling
| Issue | Resolution |
|-------|------------|
| Validation fails | Fix issues before deploy |
| Post-deploy fails | Execute rollback |
| Partial outage | Disable affected features |
| Full outage | Contact Apollo support |

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support](https://support.apollo.io)
- [Apollo API Changelog](https://apolloio.github.io/apollo-api-docs/#changelog)

## Next Steps
Proceed to `apollo-upgrade-migration` for SDK upgrade procedures.
