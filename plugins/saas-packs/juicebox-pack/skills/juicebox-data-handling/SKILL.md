---
name: juicebox-data-handling
description: |
  Juicebox data privacy and GDPR.
  Trigger: "juicebox data privacy", "juicebox gdpr".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox Data Handling

## Overview

Juicebox AI processes people datasets for talent intelligence and analysis workflows. Data types include people search results, enriched profile records (employment history, skills, social links), analysis exports, and outreach logs. Profile data often contains personal information governed by GDPR, CCPA, and recruitment privacy regulations. All enrichment results must be handled with consent tracking, purpose limitation, and right-to-deletion support. Contact data requires field-level encryption and strict access controls to prevent unauthorized disclosure.

## Data Classification

| Data Type | Sensitivity | Retention | Encryption |
|-----------|-------------|-----------|------------|
| Search results | Low | Session only (ephemeral) | TLS in transit |
| Enriched profiles | High (PII) | Per data policy, max 1 year | AES-256 at rest |
| Contact data (email/phone) | High (PII) | Until candidate objects or deletion | Field-level encryption |
| Analysis exports | Medium | 90 days | AES-256 at rest |
| Outreach logs | Medium | 6 months | AES-256 at rest |

## Data Import

```typescript
interface JuiceboxProfile {
  id: string; name: string; email?: string; phone?: string;
  company: string; title: string; skills: string[];
  source: string; enrichedAt: string;
}

async function importPeopleDataset(query: string, maxResults = 100): Promise<JuiceboxProfile[]> {
  const profiles: JuiceboxProfile[] = [];
  let offset = 0;
  do {
    const res = await fetch(`https://api.juicebox.ai/v1/search`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.JUICEBOX_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit: 50, offset }),
    });
    const data = await res.json();
    if (!data.results?.length) break;
    for (const p of data.results) {
      if (!p.id || !p.name) throw new Error(`Invalid profile: missing required fields`);
      profiles.push(p);
    }
    offset += 50;
  } while (profiles.length < maxResults);
  return profiles;
}
```

## Data Export

```typescript
async function exportAnalysisResults(profiles: JuiceboxProfile[], format: 'csv' | 'json') {
  // Strip direct contact info from exports unless explicitly authorized
  const sanitized = profiles.map(({ email, phone, ...rest }) => ({
    ...rest,
    email: email ? '[CONSENT_REQUIRED]' : undefined,
    phone: phone ? '[CONSENT_REQUIRED]' : undefined,
  }));
  if (format === 'csv') {
    const header = Object.keys(sanitized[0]).join(',');
    const rows = sanitized.map(r => Object.values(r).join(','));
    return [header, ...rows].join('\n');
  }
  return JSON.stringify(sanitized, null, 2);
}
```

## Data Validation

```typescript
function validateProfile(p: JuiceboxProfile): string[] {
  const errors: string[] = [];
  if (!p.id) errors.push('Missing profile ID');
  if (!p.name || p.name.length > 200) errors.push('Invalid or missing name');
  if (p.email && !/^[\w.+-]+@[\w-]+\.[\w.]+$/.test(p.email)) errors.push('Invalid email format');
  if (p.phone && !/^\+?[\d\s()-]{7,20}$/.test(p.phone)) errors.push('Invalid phone format');
  if (!p.source) errors.push('Missing data source attribution');
  if (p.enrichedAt && isNaN(Date.parse(p.enrichedAt))) errors.push('Invalid enrichment timestamp');
  return errors;
}
```

## Compliance

- [ ] GDPR consent tracked per profile: lawful basis recorded (consent, legitimate interest)
- [ ] Right-to-deletion: purge profile, enrichment data, and outreach logs within 30 days of request
- [ ] GDPR data subject access: export all stored data for a candidate on request
- [ ] CCPA opt-out: honor Do Not Sell signals for California residents
- [ ] Purpose limitation: enrichment data used only for stated recruitment/analysis purpose
- [ ] Contact data encrypted at field level with per-tenant keys
- [ ] Audit log for all profile access, export, and deletion events
- [ ] Data minimization: auto-purge enriched profiles older than retention window

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| API 401 unauthorized | Expired or revoked API key | Rotate key in secret manager, update env |
| Duplicate profiles in import | Same person from multiple sources | Deduplicate by email hash before storage |
| GDPR deletion incomplete | Outreach logs not purged alongside profile | Cascade delete across all related tables |
| Export contains raw PII | Consent flag not checked before export | Add consent gate in `exportAnalysisResults` |
| Enrichment timeout | Upstream data provider slow | Implement 10s timeout with retry, fallback to cached |

## Resources

- [Juicebox Privacy Policy](https://juicebox.ai/privacy)
- [GDPR Data Subject Rights](https://gdpr.eu/tag/chapter-3/)

## Next Steps

See `juicebox-security-basics`.
