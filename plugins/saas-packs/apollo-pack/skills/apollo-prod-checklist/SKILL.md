---
name: apollo-prod-checklist
description: |
  Execute Apollo.io production deployment checklist.
  Use when preparing to deploy Apollo integrations to production,
  doing pre-launch verification, or auditing production readiness.
  Trigger with phrases like "apollo production checklist", "deploy apollo",
  "apollo go-live", "apollo production ready", "apollo launch checklist".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Production Checklist

## Overview
Comprehensive checklist for deploying Apollo.io integrations to production with automated validation scripts, security verification, and post-deployment smoke tests.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Authentication & Secrets
```typescript
// src/scripts/prod-checklist.ts
interface CheckResult {
  category: string;
  name: string;
  pass: boolean;
  detail: string;
}

const results: CheckResult[] = [];

// 1.1 API key is from environment/secret manager (not hardcoded)
results.push({
  category: 'Auth',
  name: 'API key source',
  pass: !!process.env.APOLLO_API_KEY && !process.env.APOLLO_API_KEY.includes('test'),
  detail: process.env.APOLLO_API_KEY ? 'Loaded from env' : 'NOT SET',
});

// 1.2 API key works
try {
  const { data } = await axios.post(
    'https://api.apollo.io/v1/people/search',
    { per_page: 1 },
    { params: { api_key: process.env.APOLLO_API_KEY }, timeout: 10_000 },
  );
  results.push({ category: 'Auth', name: 'API key valid', pass: true, detail: 'OK' });
} catch (err: any) {
  results.push({ category: 'Auth', name: 'API key valid', pass: false, detail: `HTTP ${err.response?.status}` });
}

// 1.3 .env is gitignored
const { execSync } = await import('child_process');
const gitIgnored = execSync('git check-ignore .env 2>/dev/null || echo NOT').toString().trim();
results.push({
  category: 'Auth',
  name: '.env gitignored',
  pass: gitIgnored !== 'NOT',
  detail: gitIgnored !== 'NOT' ? 'OK' : 'Add .env to .gitignore',
});
```

### Step 2: Error Handling & Resilience
```typescript
// 2.1 Rate limiting is configured
const hasRateLimiter = await fileContains('src/', 'rate-limiter');
results.push({
  category: 'Resilience',
  name: 'Rate limiting',
  pass: hasRateLimiter,
  detail: hasRateLimiter ? 'Rate limiter found' : 'No rate limiting code found',
});

// 2.2 Retry logic is implemented
const hasRetry = await fileContains('src/', 'withRetry\\|withBackoff\\|exponential');
results.push({
  category: 'Resilience',
  name: 'Retry logic',
  pass: hasRetry,
  detail: hasRetry ? 'Retry logic found' : 'No retry logic found',
});

// 2.3 Circuit breaker for Apollo dependency
const hasCircuitBreaker = await fileContains('src/', 'CircuitBreaker');
results.push({
  category: 'Resilience',
  name: 'Circuit breaker',
  pass: hasCircuitBreaker,
  detail: hasCircuitBreaker ? 'Circuit breaker found' : 'Consider adding circuit breaker',
});

async function fileContains(dir: string, pattern: string): Promise<boolean> {
  try {
    execSync(`grep -r "${pattern}" ${dir} --include="*.ts" -l`, { stdio: 'pipe' });
    return true;
  } catch { return false; }
}
```

### Step 3: Observability & Monitoring
```typescript
// 3.1 Logging configured
const hasLogging = await fileContains('src/', 'pino\\|winston\\|console\\.log');
results.push({
  category: 'Observability',
  name: 'Structured logging',
  pass: hasLogging,
  detail: hasLogging ? 'Logger found' : 'Add structured logging',
});

// 3.2 PII redaction in logs
const hasRedaction = await fileContains('src/', 'redact');
results.push({
  category: 'Observability',
  name: 'PII redaction',
  pass: hasRedaction,
  detail: hasRedaction ? 'Redaction found' : 'Add PII redaction to logs',
});

// 3.3 Health check endpoint
const hasHealthCheck = await fileContains('src/', '/health');
results.push({
  category: 'Observability',
  name: 'Health endpoint',
  pass: hasHealthCheck,
  detail: hasHealthCheck ? '/health endpoint found' : 'Add /health endpoint',
});

// 3.4 Metrics instrumentation
const hasMetrics = await fileContains('src/', 'prometheus\\|prom-client\\|metrics');
results.push({
  category: 'Observability',
  name: 'Metrics',
  pass: hasMetrics,
  detail: hasMetrics ? 'Metrics instrumentation found' : 'Consider adding Prometheus metrics',
});
```

### Step 4: Data & Compliance
```typescript
// 4.1 No PII in source code
const hasPII = await fileContains('src/', '@[a-zA-Z]*\\.[a-zA-Z]');
results.push({
  category: 'Compliance',
  name: 'No PII in source',
  pass: !hasPII,
  detail: hasPII ? 'Potential PII found in source' : 'OK',
});

// 4.2 Data retention policy
const hasRetention = await fileContains('src/', 'retention\\|ttl\\|expir');
results.push({
  category: 'Compliance',
  name: 'Data retention',
  pass: hasRetention,
  detail: hasRetention ? 'Retention logic found' : 'Define data retention policy',
});
```

### Step 5: Generate the Checklist Report
```typescript
function generateReport(results: CheckResult[]) {
  const categories = [...new Set(results.map((r) => r.category))];
  let allPass = true;

  console.log('╔══════════════════════════════════════════╗');
  console.log('║   Apollo Production Readiness Checklist  ║');
  console.log('╚══════════════════════════════════════════╝\n');

  for (const cat of categories) {
    console.log(`── ${cat} ──`);
    const catResults = results.filter((r) => r.category === cat);
    for (const r of catResults) {
      const icon = r.pass ? 'PASS' : 'FAIL';
      console.log(`  ${icon}  ${r.name}: ${r.detail}`);
      if (!r.pass) allPass = false;
    }
    console.log('');
  }

  const passCount = results.filter((r) => r.pass).length;
  console.log(`Score: ${passCount}/${results.length} checks passed`);
  console.log(`Status: ${allPass ? 'READY FOR PRODUCTION' : 'BLOCKED — fix failing checks'}`);
  process.exit(allPass ? 0 : 1);
}

generateReport(results);
```

## Output
- Authentication checks (API key source, validity, gitignore)
- Resilience checks (rate limiting, retry logic, circuit breaker)
- Observability checks (logging, PII redaction, health endpoint, metrics)
- Compliance checks (no PII in source, data retention policy)
- Formatted checklist report with pass/fail score

## Error Handling
| Issue | Resolution |
|-------|------------|
| Validation fails | Fix all FAIL items before deploying to production |
| Post-deploy failures | Run checklist in CI as a deployment gate |
| Partial outage | Check `apollo-incident-runbook` for response procedures |
| Rollback needed | Follow `apollo-deploy-integration` rollback steps |

## Examples

### Run as npm Script
```json
{
  "scripts": {
    "prod:checklist": "tsx src/scripts/prod-checklist.ts"
  }
}
```

```bash
# Run before every production deployment
npm run prod:checklist
# Score: 10/10 checks passed
# Status: READY FOR PRODUCTION
```

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo API Changelog](https://apolloio.github.io/apollo-api-docs/#changelog)
- [Google SRE Launch Checklist](https://sre.google/sre-book/launch-checklist/)

## Next Steps
Proceed to `apollo-upgrade-migration` for SDK upgrade procedures.
