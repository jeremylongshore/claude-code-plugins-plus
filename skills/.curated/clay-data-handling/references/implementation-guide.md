# Clay Data Handling — Implementation Guide

## Import Data Validation

```typescript
import { z } from 'zod';

const LeadImportSchema = z.object({
  email: z.string().email().toLowerCase(),
  first_name: z.string().min(1).optional(),
  last_name: z.string().min(1).optional(),
  company_domain: z.string().url().or(z.string().regex(/^[\w.-]+\.\w{2,}$/)),
  company_name: z.string().optional(),
  linkedin_url: z.string().url().optional(),
});

function validateImportData(records: any[]) {
  const valid: any[] = [];
  const invalid: Array<{ record: any; error: string }> = [];

  for (const record of records) {
    const result = LeadImportSchema.safeParse(record);
    if (result.success) {
      valid.push(result.data);
    } else {
      invalid.push({
        record,
        error: result.error.issues.map(i => i.message).join('; '),
      });
    }
  }

  return { valid, invalid, validRate: (valid.length / records.length * 100).toFixed(1) + '%' };
}
```

## Deduplication

```typescript
interface DedupeResult {
  unique: any[];
  duplicates: any[];
  dedupeRate: string;
}

function deduplicateLeads(leads: any[]): DedupeResult {
  const seen = new Map<string, any>();
  const duplicates: any[] = [];

  for (const lead of leads) {
    const key = lead.email ||
      `${lead.company_domain}:${lead.first_name}:${lead.last_name}`;

    if (seen.has(key)) {
      duplicates.push(lead);
    } else {
      seen.set(key, lead);
    }
  }

  return {
    unique: Array.from(seen.values()),
    duplicates,
    dedupeRate: ((duplicates.length / leads.length) * 100).toFixed(1) + '%',
  };
}
```

## Retention Metadata

```typescript
interface EnrichedLead {
  email: string;
  company_name?: string;
  enrichment_source: string;
  enriched_at: string;
  retention_expires: string;
  data: Record<string, any>;
}

function addRetentionMetadata(lead: any, retentionDays = 365): EnrichedLead {
  const enrichedAt = new Date();
  const expiresAt = new Date(enrichedAt);
  expiresAt.setDate(expiresAt.getDate() + retentionDays);

  return {
    ...lead,
    enriched_at: enrichedAt.toISOString(),
    retention_expires: expiresAt.toISOString(),
    enrichment_source: 'clay',
  };
}

async function cleanExpiredData(leads: EnrichedLead[]) {
  const now = new Date();
  const active = leads.filter(l => new Date(l.retention_expires) > now);
  const expired = leads.filter(l => new Date(l.retention_expires) <= now);
  return { active, expired };
}
```

## GDPR-Compliant Export

```typescript
function prepareForExport(leads: EnrichedLead[], destination: 'crm' | 'csv' | 'analytics') {
  return leads.map(lead => {
    const exported: Record<string, any> = {
      email: lead.email,
      company_name: lead.company_name,
    };

    if (destination === 'analytics') {
      delete exported.email;
      exported.company_hash = hashString(lead.company_name || '');
    }

    if (destination === 'crm') {
      exported.source = 'clay_enrichment';
      exported.enriched_at = lead.enriched_at;
      exported.consent_basis = 'legitimate_interest';
    }

    return exported;
  });
}

function hashString(s: string): string {
  const { createHash } = require('crypto');
  return createHash('sha256').update(s).digest('hex').slice(0, 12);
}
```

## Full Import Pipeline

```typescript
async function importLeads(rawRecords: any[]) {
  const { valid, invalid } = validateImportData(rawRecords);
  const { unique, duplicates } = deduplicateLeads(valid);
  const enriched = unique.map(l => addRetentionMetadata(l));

  console.log(`Import: ${rawRecords.length} total, ${unique.length} unique, ${invalid.length} rejected`);
  return enriched;
}
```
