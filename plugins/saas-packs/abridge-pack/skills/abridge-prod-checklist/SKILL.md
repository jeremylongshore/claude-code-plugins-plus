---
name: abridge-prod-checklist
description: |
  Execute Abridge production readiness checklist for clinical AI deployment.
  Use when launching Abridge in a healthcare org, preparing for go-live,
  or validating HIPAA compliance before production deployment.
  Trigger: "abridge production checklist", "abridge go-live",
  "abridge launch readiness", "abridge prod deploy".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, production]
compatible-with: claude-code
---

# Abridge Production Checklist

## Overview

Production readiness checklist for deploying Abridge clinical AI in a healthcare organization. Clinical documentation systems are safety-critical — this checklist covers HIPAA compliance, EHR integration validation, provider onboarding, and rollback procedures.

## Pre-Launch Checklist

### Legal & Compliance

- [ ] **BAA signed** — Business Associate Agreement executed with Abridge
- [ ] **HIPAA risk assessment** — Completed and documented
- [ ] **Data flow diagram** — PHI flow mapped: microphone → Abridge → EHR
- [ ] **Breach notification plan** — 60-day notification procedure documented
- [ ] **Patient consent** — State-specific recording consent requirements met
- [ ] **Medical staff approval** — Clinical AI usage approved by medical staff committee

### Infrastructure

- [ ] **TLS 1.3** — Enforced on all Abridge API connections
- [ ] **Secrets management** — Credentials in secret manager (not env files)
- [ ] **Audit logging** — All PHI access logged with 6-year retention
- [ ] **Monitoring** — Health checks, latency alerts, error rate dashboards
- [ ] **Backup connectivity** — Fallback for Abridge outages (manual documentation)

### EHR Integration

- [ ] **FHIR R4 endpoint** — Verified DocumentReference POST works
- [ ] **Epic SmartPhrases** — Mapped to Abridge note templates
- [ ] **Provider enrollment** — All go-live providers registered in Abridge
- [ ] **Specialty configuration** — Licensed specialties configured per contract
- [ ] **Note templates** — SOAP/H&P/Progress templates validated with clinical leads

### Validation Script

```typescript
// src/prod/readiness-check.ts
interface ReadinessResult {
  check: string;
  status: 'pass' | 'fail' | 'warn';
  detail: string;
}

async function runReadinessChecks(): Promise<ReadinessResult[]> {
  const results: ReadinessResult[] = [];

  // 1. API connectivity
  try {
    const res = await fetch(`${process.env.ABRIDGE_BASE_URL}/health`, {
      headers: { 'Authorization': `Bearer ${process.env.ABRIDGE_CLIENT_SECRET}` },
    });
    results.push({ check: 'API Health', status: res.ok ? 'pass' : 'fail', detail: `HTTP ${res.status}` });
  } catch (err) {
    results.push({ check: 'API Health', status: 'fail', detail: (err as Error).message });
  }

  // 2. FHIR endpoint
  try {
    const res = await fetch(`${process.env.EPIC_FHIR_BASE_URL}/metadata`);
    results.push({ check: 'FHIR Server', status: res.ok ? 'pass' : 'fail', detail: `HTTP ${res.status}` });
  } catch (err) {
    results.push({ check: 'FHIR Server', status: 'fail', detail: (err as Error).message });
  }

  // 3. TLS version
  results.push({
    check: 'TLS Version',
    status: process.env.NODE_TLS_MIN_VERSION === 'TLSv1.3' ? 'pass' : 'warn',
    detail: `Min TLS: ${process.env.NODE_TLS_MIN_VERSION || 'not set'}`,
  });

  // 4. Secrets not in env file
  const envFiles = ['.env', '.env.local', '.env.production'];
  for (const f of envFiles) {
    try {
      const content = await import('fs').then(fs => fs.readFileSync(f, 'utf8'));
      if (content.includes('ABRIDGE_CLIENT_SECRET')) {
        results.push({ check: `Secrets in ${f}`, status: 'fail', detail: 'Credentials in file — use secret manager' });
      }
    } catch { /* file doesn't exist — good */ }
  }

  // 5. Audit logging
  results.push({
    check: 'Audit Logging',
    status: process.env.AUDIT_LOG_ENABLED === 'true' ? 'pass' : 'fail',
    detail: 'HIPAA requires audit trail for all PHI access',
  });

  return results;
}

// Run and display
runReadinessChecks().then(results => {
  console.log('\n=== Abridge Production Readiness ===\n');
  for (const r of results) {
    const icon = r.status === 'pass' ? 'PASS' : r.status === 'warn' ? 'WARN' : 'FAIL';
    console.log(`[${icon}] ${r.check}: ${r.detail}`);
  }
  const failures = results.filter(r => r.status === 'fail');
  console.log(`\n${failures.length === 0 ? 'READY FOR PRODUCTION' : `${failures.length} BLOCKING ISSUES`}`);
});
```

### Rollback Plan

```bash
#!/bin/bash
# scripts/abridge-rollback.sh
# Rollback Abridge integration — revert to manual documentation

echo "=== Abridge Rollback Procedure ==="

# 1. Disable Abridge in EHR
echo "Step 1: Disable Abridge module in Epic App Orchard"
echo "  - Navigate to Epic > Admin > App Orchard > Abridge"
echo "  - Set status: DISABLED"

# 2. Notify providers
echo "Step 2: Send notification to enrolled providers"
echo "  - Subject: Abridge temporarily offline — use manual documentation"

# 3. Verify EHR still accepts manual notes
echo "Step 3: Verify manual note creation in Epic works"
curl -X POST "${EPIC_FHIR_BASE_URL}/DocumentReference" \
  -H "Authorization: Bearer $EPIC_TOKEN" \
  -H "Content-Type: application/fhir+json" \
  -d '{"resourceType":"DocumentReference","status":"current","content":[{"attachment":{"contentType":"text/plain","data":"'"$(echo 'Manual note test' | base64)"'"}}]}'

echo "=== Rollback Complete ==="
```

## Post-Launch Monitoring

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Note generation latency | < 30s | > 60s |
| API error rate | < 1% | > 5% |
| Provider adoption | > 80% in 30 days | < 50% |
| Note acceptance rate | > 90% | < 70% |
| Patient summary delivery | < 5s | > 15s |

## Output

- Readiness check script with pass/fail results
- Rollback procedure documented and tested
- Post-launch monitoring thresholds configured
- Go/no-go decision evidence collected

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [HIPAA Security Rule Checklist](https://www.hhs.gov/hipaa/for-professionals/security/)
- [Epic Go-Live Best Practices](https://www.epic.com/)

## Next Steps

For version upgrades, see `abridge-upgrade-migration`.
