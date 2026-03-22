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
tags: [saas, apollo, deployment, audit]

---
# Apollo Production Checklist

## Overview
Comprehensive pre-production checklist for Apollo.io integrations with automated validation scripts. Covers authentication, resilience, observability, compliance, and credit management.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Authentication & Key Management
```typescript
// src/scripts/prod-checklist.ts
import axios from 'axios';

interface Check { category: string; name: string; pass: boolean; detail: string; }
const results: Check[] = [];

// 1.1 API key is set (not hardcoded)
results.push({
  category: 'Auth', name: 'API key from env/secrets',
  pass: !!process.env.APOLLO_API_KEY,
  detail: process.env.APOLLO_API_KEY ? 'Loaded from env' : 'NOT SET',
});

// 1.2 Using x-api-key header (not query param)
const { execSync } = await import('child_process');
let usesHeader = true;
try { execSync('grep -rn "params.*api_key" src/ --include="*.ts"', { stdio: 'pipe' }); usesHeader = false; } catch {}
results.push({ category: 'Auth', name: 'x-api-key header auth', pass: usesHeader, detail: usesHeader ? 'OK' : 'Switch to x-api-key header' });

// 1.3 API key is valid
try {
  const resp = await axios.get('https://api.apollo.io/api/v1/auth/health', {
    headers: { 'x-api-key': process.env.APOLLO_API_KEY! },
  });
  results.push({ category: 'Auth', name: 'Key valid', pass: resp.data.is_logged_in, detail: resp.data.is_logged_in ? 'OK' : 'Invalid key' });
} catch (err: any) {
  results.push({ category: 'Auth', name: 'Key valid', pass: false, detail: `HTTP ${err.response?.status}` });
}

// 1.4 .env gitignored
const gitIgnored = execSync('git check-ignore .env 2>/dev/null || echo NOT').toString().trim();
results.push({ category: 'Auth', name: '.env gitignored', pass: gitIgnored !== 'NOT', detail: gitIgnored !== 'NOT' ? 'OK' : 'Add .env to .gitignore' });
```

### Step 2: Resilience & Error Handling
```typescript
async function fileContains(dir: string, pattern: string): Promise<boolean> {
  try { execSync(`grep -r "${pattern}" ${dir} --include="*.ts" -l`, { stdio: 'pipe' }); return true; }
  catch { return false; }
}

results.push({ category: 'Resilience', name: 'Rate limiting',
  pass: await fileContains('src/', 'rate-limiter\\|SlidingWindow\\|RateLimit'),
  detail: 'Rate limiter implementation' });

results.push({ category: 'Resilience', name: 'Retry logic',
  pass: await fileContains('src/', 'withRetry\\|withBackoff\\|exponential'),
  detail: 'Exponential backoff for 429/5xx' });

results.push({ category: 'Resilience', name: 'Error categorization',
  pass: await fileContains('src/', 'categorizeError\\|ApolloApiError'),
  detail: 'Typed error handling' });

results.push({ category: 'Resilience', name: 'Timeout configured',
  pass: await fileContains('src/', 'timeout.*\\d'),
  detail: 'Request timeout set' });
```

### Step 3: Observability
```typescript
results.push({ category: 'Observability', name: 'PII redaction',
  pass: await fileContains('src/', 'redact'),
  detail: 'PII redaction in logs' });

results.push({ category: 'Observability', name: 'Structured logging',
  pass: await fileContains('src/', 'pino\\|winston\\|console\\.log.*Apollo'),
  detail: 'Logger with Apollo context' });

results.push({ category: 'Observability', name: 'Health endpoint',
  pass: await fileContains('src/', '/health'),
  detail: '/health endpoint checking Apollo connectivity' });
```

### Step 4: Credit & Cost Controls
```typescript
results.push({ category: 'Credits', name: 'Credit tracking',
  pass: await fileContains('src/', 'credit\\|CreditTracker'),
  detail: 'Track enrichment credit usage' });

results.push({ category: 'Credits', name: 'Deduplication',
  pass: await fileContains('src/', 'dedup\\|isAlreadyEnriched'),
  detail: 'Prevent duplicate enrichment charges' });

results.push({ category: 'Credits', name: 'Budget controls',
  pass: await fileContains('src/', 'budget\\|isOverBudget'),
  detail: 'Daily credit budget enforcement' });
```

### Step 5: Generate Report
```typescript
function generateReport(results: Check[]) {
  const categories = [...new Set(results.map((r) => r.category))];
  let allPass = true;

  console.log('\n  Apollo Production Readiness Checklist\n');

  for (const cat of categories) {
    console.log(`-- ${cat} --`);
    for (const r of results.filter((r) => r.category === cat)) {
      console.log(`  ${r.pass ? 'PASS' : 'FAIL'}  ${r.name}: ${r.detail}`);
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
- Authentication checks (key source, header auth, validity, gitignore)
- Resilience checks (rate limiting, retry, error typing, timeouts)
- Observability checks (PII redaction, logging, health endpoint)
- Credit controls (tracking, dedup, budget enforcement)
- Formatted report with pass/fail score and exit code

## Error Handling
| Issue | Resolution |
|-------|------------|
| Auth checks fail | Verify `APOLLO_API_KEY` env var, switch to `x-api-key` header |
| Missing rate limiting | Add `apollo-rate-limits` skill patterns |
| No credit tracking | Add `apollo-cost-tuning` skill patterns |
| Post-deploy failures | Run checklist in CI as a deployment gate |

## Examples

### Run as CI Gate
```json
{ "scripts": { "prod:checklist": "tsx src/scripts/prod-checklist.ts" } }
```
```bash
npm run prod:checklist && npm run deploy
```

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo API Pricing](https://docs.apollo.io/docs/api-pricing)
- [Create API Keys](https://docs.apollo.io/docs/create-api-key)

## Next Steps
Proceed to `apollo-upgrade-migration` for API upgrade procedures.
