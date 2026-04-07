---
name: openevidence-prod-checklist
description: |
  Prod Checklist for OpenEvidence.
  Trigger: "openevidence prod checklist".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Production Checklist

## Overview
OpenEvidence provides clinical decision support backed by peer-reviewed medical literature. A production integration handles Protected Health Information (PHI) subject to HIPAA, serves evidence-based answers where accuracy directly impacts patient outcomes, and must maintain complete audit trails for regulatory review. Misconfigurations can expose PHI in logs, serve stale clinical guidance, or fail compliance audits that shut down your integration entirely. This checklist enforces HIPAA-grade security, citation verification, and the SLA discipline required for healthcare-adjacent systems.

## Prerequisites
- Production OpenEvidence API credentials (not trial/sandbox keys)
- Secrets manager configured (Vault, AWS Secrets Manager, or GCP Secret Manager)
- HIPAA-compliant monitoring stack (no PHI in log aggregators without BAA)
- Business Associate Agreement (BAA) executed with OpenEvidence
- Compliance officer sign-off on data flow architecture

## Authentication & Secrets
- [ ] API keys stored in vault/secrets manager (never in code, env files, or CI logs)
- [ ] Key rotation schedule configured (every 90 days, with zero-downtime swap)
- [ ] Separate keys for staging vs production (staging keys cannot reach production data)
- [ ] Service account permissions scoped to query-only (no admin endpoints)
- [ ] API key exposure detection automated (scan logs/repos for leaked credentials)

## API Integration
- [ ] Base URL points to production endpoint (not sandbox/staging)
- [ ] Request timeout set to 15 seconds for clinical queries (evidence synthesis is compute-heavy)
- [ ] Response time SLA monitored: p95 < 3 seconds per contractual agreement
- [ ] Pagination implemented for evidence result sets (token-based cursor)
- [ ] Clinical query payloads never include patient identifiers (de-identify before sending)
- [ ] Citation URLs in responses validated before displaying to clinicians
- [ ] Fallback behavior defined when evidence confidence score is below threshold (0.7)

## Error Handling & Resilience
- [ ] Circuit breaker configured for OpenEvidence API calls (open after 3 consecutive failures)
- [ ] Retry logic with exponential backoff for 429 (rate limit) and 5xx responses
- [ ] Clinical query failures surface explicit "no evidence available" (never silent failure)
- [ ] Timeout responses distinguished from empty-result responses in UI
- [ ] Stale cache clearly labeled with retrieval timestamp when serving cached evidence
- [ ] Degraded mode displays disclaimer: "Results may not reflect latest evidence"
- [ ] All API errors logged with correlation ID (without PHI in the log entry)

## Monitoring & Alerting
- [ ] API latency tracked (p50, p95, p99) with 3s p95 SLA threshold
- [ ] Error rate alerts configured (threshold: >0.5% over 5-minute window — stricter for clinical)
- [ ] Evidence citation link validity checked daily (alert on broken DOI/PubMed links)
- [ ] Query volume anomalies detected (sudden spike may indicate misuse or bot traffic)
- [ ] Response confidence score distribution tracked (alert if median drops below 0.8)
- [ ] Audit log completeness verified daily (every query must have a log entry)

## Security
- [ ] PHI never included in API request payloads (queries de-identified before transmission)
- [ ] PHI never written to application logs, error reports, or monitoring dashboards
- [ ] All data in transit encrypted via TLS 1.2+ (certificate pinning recommended)
- [ ] All cached clinical responses encrypted at rest (AES-256)
- [ ] Access to clinical query history restricted by role (clinician-only, auditor read-only)
- [ ] Audit log captures: user ID, query timestamp, evidence IDs returned, confidence scores
- [ ] Data retention policy enforced: clinical query logs retained per HIPAA minimum (6 years)
- [ ] Annual HIPAA risk assessment includes OpenEvidence integration scope

## Validation Script
```typescript
async function validateOpenEvidenceProduction(apiKey: string): Promise<void> {
  const base = process.env.OPENEVIDENCE_API_URL ?? 'https://api.openevidence.com/v1';
  const headers = { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' };

  // 1. Connectivity check
  const ping = await fetch(`${base}/health`, { headers, signal: AbortSignal.timeout(5000) });
  console.assert(ping.ok, `API unreachable: ${ping.status}`);

  // 2. Auth validation
  const auth = await fetch(`${base}/me`, { headers });
  console.assert(auth.status !== 401, 'Invalid API key');
  console.assert(auth.status !== 403, 'Insufficient permissions — check scope');

  // 3. Clinical query round-trip (de-identified test query)
  const query = await fetch(`${base}/query`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ question: 'What is the standard treatment for hypertension?' }),
    signal: AbortSignal.timeout(15000),
  });
  console.assert(query.ok, `Clinical query failed: ${query.status}`);
  const result = await query.json();
  console.assert(result.citations?.length > 0, 'No citations returned — evidence pipeline may be down');

  // 4. Response time SLA
  const start = Date.now();
  await fetch(`${base}/query`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ question: 'Recommended dosage for metformin in type 2 diabetes?' }),
    signal: AbortSignal.timeout(15000),
  });
  const elapsed = Date.now() - start;
  console.assert(elapsed < 3000, `Response time ${elapsed}ms exceeds 3s SLA`);

  // 5. Audit log endpoint accessible
  const audit = await fetch(`${base}/audit-log?limit=1`, { headers });
  console.assert(audit.ok, `Audit log endpoint failed: ${audit.status}`);
  console.log('All OpenEvidence production checks passed');
}
```

## Risk Matrix
| Check | Risk if Skipped | Priority |
|---|---|---|
| PHI excluded from API payloads | HIPAA violation, regulatory penalty, BAA breach | Critical |
| PHI excluded from logs | Data breach via log aggregator, OCR enforcement action | Critical |
| Audit log completeness | Failed compliance audit, integration shutdown | Critical |
| Citation URL validation | Clinicians follow broken links, lose trust in evidence | High |
| Confidence score monitoring | Low-quality answers served without clinician awareness | High |

## Resources
- [OpenEvidence Platform](https://www.openevidence.com)

## Next Steps
See `openevidence-security-basics`.
