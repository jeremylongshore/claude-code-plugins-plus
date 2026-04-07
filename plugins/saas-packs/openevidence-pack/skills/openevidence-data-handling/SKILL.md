---
name: openevidence-data-handling
description: |
  Data Handling for OpenEvidence.
  Trigger: "openevidence data handling".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence Data Handling

## Overview

OpenEvidence provides AI-powered clinical evidence synthesis for healthcare professionals. Data types include clinical queries (potentially containing PHI), evidence citations from medical literature, patient-contextualized responses, research paper references, and usage analytics. All data handling must comply with HIPAA (PHI safeguards, minimum necessary standard, BAA requirements), GDPR for EU clinicians, and FDA guidance on clinical decision support. Query data may contain patient identifiers, diagnoses, or treatment details that require de-identification before storage or analytics.

## Data Classification

| Data Type | Sensitivity | Retention | Encryption |
|-----------|-------------|-----------|------------|
| Clinical queries (may contain PHI) | Critical | De-identify within 24h, purge raw in 7 days | AES-256 + TLS, field-level for PHI |
| Evidence citations | Low | Indefinite (public literature) | TLS in transit |
| Patient-contextualized responses | High (derived PHI) | 30 days max, then de-identify | AES-256 at rest |
| Research paper metadata | Low | Indefinite | TLS in transit |
| Clinician usage analytics | Medium | 1 year (de-identified) | AES-256 at rest |

## Data Import

```typescript
interface ClinicalQuery {
  queryId: string; clinicianId: string; queryText: string;
  patientContext?: { age?: number; sex?: string; conditions?: string[] };
  timestamp: string;
}

async function submitClinicalQuery(query: ClinicalQuery): Promise<string> {
  const sanitized = { ...query, queryText: deidentifyPHI(query.queryText) };
  const res = await fetch('https://api.openevidence.com/v1/query', {
    method: 'POST',
    headers: { Authorization: `Bearer ${process.env.OPENEVIDENCE_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(sanitized),
  });
  return (await res.json()).evidenceId;
}

function deidentifyPHI(text: string): string {
  return text
    .replace(/\b(MRN|mrn)[:\s]?\d{6,}\b/g, '[MRN_REDACTED]')
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN_REDACTED]')
    .replace(/\b(DOB|dob)[:\s]?\d{1,2}\/\d{1,2}\/\d{2,4}\b/g, '[DOB_REDACTED]')
    .replace(/\b[A-Z][a-z]+ [A-Z][a-z]+, (MD|DO|NP|PA)\b/g, '[PROVIDER_REDACTED]');
}
```

## Data Export

```typescript
async function exportEvidenceSummary(queryIds: string[]) {
  const summaries = [];
  for (const id of queryIds) {
    const res = await fetch(`https://api.openevidence.com/v1/evidence/${id}`, {
      headers: { Authorization: `Bearer ${process.env.OPENEVIDENCE_API_KEY}` },
    });
    const data = await res.json();
    summaries.push({ queryId: id, citations: data.citations,
      summary: deidentifyPHI(data.summary), confidence: data.confidenceScore });
  }
  return summaries;
}
```

## Data Validation

```typescript
function validateClinicalQuery(q: ClinicalQuery): string[] {
  const errors: string[] = [];
  if (!q.queryId) errors.push('Missing query ID');
  if (!q.clinicianId) errors.push('Missing clinician identifier');
  if (!q.queryText || q.queryText.length < 10) errors.push('Query too short for meaningful evidence retrieval');
  if (q.queryText.length > 5000) errors.push('Query exceeds 5000 char limit');
  if (/\b\d{3}-\d{2}-\d{4}\b/.test(q.queryText)) errors.push('CRITICAL: SSN detected in query text');
  if (/\b(MRN|mrn)[:\s]?\d{6,}\b/.test(q.queryText)) errors.push('CRITICAL: MRN detected in query text');
  if (q.timestamp && isNaN(Date.parse(q.timestamp))) errors.push('Invalid timestamp');
  return errors;
}
```

## Compliance

- [ ] HIPAA: BAA executed with OpenEvidence before any PHI transmission
- [ ] HIPAA: PHI de-identified using Safe Harbor method before storage/analytics
- [ ] HIPAA: Minimum necessary standard enforced — only transmit required clinical context
- [ ] HIPAA: Audit trail for all PHI access with clinician ID, timestamp, and query purpose
- [ ] HIPAA: Breach notification procedure documented (72-hour window)
- [ ] GDPR: EU clinician data subject rights (access, erasure, portability)
- [ ] FDA: Clinical decision support disclaimer included in all evidence responses
- [ ] Data retention: raw queries purged at 7 days, de-identified analytics retained 1 year

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| PHI detected in stored query | De-identification regex missed a pattern | Add pattern to `deidentifyPHI`, re-scan stored queries |
| API 403 on query submission | BAA not on file or expired API credentials | Verify BAA status, rotate API key |
| Evidence response contains patient name | Upstream model hallucinated PHI | Post-process all responses through de-identification before display |
| Audit log gap | Logging service outage during query window | Replay from API request logs, flag gap in compliance report |
| Export exceeds size limit | Too many citations in bulk export | Paginate export, limit to 50 evidence summaries per request |

## Resources

- [OpenEvidence Platform](https://www.openevidence.com)
- [HIPAA De-Identification Guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/)

## Next Steps

See `openevidence-security-basics`.
