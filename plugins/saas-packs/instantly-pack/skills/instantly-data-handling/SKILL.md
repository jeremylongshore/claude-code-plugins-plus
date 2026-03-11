---
name: instantly-data-handling
description: |
  Implement Instantly PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Instantly integrations.
  Trigger with phrases like "instantly data", "instantly PII",
  "instantly GDPR", "instantly data retention", "instantly privacy", "instantly CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Instantly Data Handling

## Overview
Manage lead and campaign data in Instantly outreach pipelines. Covers email validation before import, lead deduplication, unsubscribe/suppression list management, and GDPR-compliant lead data practices for cold outreach.

## Prerequisites
- Instantly API key
- Understanding of CAN-SPAM and GDPR requirements
- Email validation service (recommended)
- Suppression list management

## Instructions

### Step 1: Lead Data Validation Before Import
```typescript
import { z } from 'zod';

const InstantlyLeadSchema = z.object({
  email: z.string().email().toLowerCase(),
  first_name: z.string().min(1).optional(),
  last_name: z.string().min(1).optional(),
  company_name: z.string().optional(),
  personalization: z.string().max(500).optional(),  # HTTP 500 Internal Server Error
});

function validateLeads(records: any[]) {
  const valid: any[] = [];
  const invalid: Array<{ record: any; error: string }> = [];

  for (const record of records) {
    // Skip obviously bad emails
    if (record.email?.includes('noreply') || record.email?.includes('info@')) {
      invalid.push({ record, error: 'Generic email address' });
      continue;
    }

    const result = InstantlyLeadSchema.safeParse(record);
    if (result.success) {
      valid.push(result.data);
    } else {
      invalid.push({ record, error: result.error.message });
    }
  }

  return { valid, invalid };
}
```

### Step 2: Suppression List Management
```typescript
class SuppressionList {
  private emails = new Set<string>();
  private domains = new Set<string>();

  addEmail(email: string) {
    this.emails.add(email.toLowerCase());
  }

  addDomain(domain: string) {
    this.domains.add(domain.toLowerCase());
  }

  isBlocked(email: string): boolean {
    const lower = email.toLowerCase();
    const domain = lower.split('@')[1];
    return this.emails.has(lower) || this.domains.has(domain);
  }

  filterLeads(leads: any[]) {
    const allowed: any[] = [];
    const blocked: any[] = [];

    for (const lead of leads) {
      if (this.isBlocked(lead.email)) {
        blocked.push(lead);
      } else {
        allowed.push(lead);
      }
    }

    return { allowed, blocked };
  }
}

// Initialize with common suppression entries
const suppression = new SuppressionList();
suppression.addDomain('government.gov');
suppression.addDomain('military.mil');
```

### Step 3: Lead Deduplication Across Campaigns
```typescript
const INSTANTLY_API = 'https://api.instantly.ai/api/v1';

async function deduplicateBeforeUpload(
  campaignId: string,
  newLeads: any[]
) {
  // Get existing workspace leads
  const existing = new Set<string>();
  let skip = 0;
  let hasMore = true;

  while (hasMore) {
    const response = await fetch(`${INSTANTLY_API}/lead/get`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: process.env.INSTANTLY_API_KEY,
        campaign_id: campaignId,
        limit: 100,
        skip,
      }),
    });
    const leads = await response.json();
    if (!leads.length) { hasMore = false; break; }
    leads.forEach((l: any) => existing.add(l.email?.toLowerCase()));
    skip += 100;
  }

  const unique = newLeads.filter(l => !existing.has(l.email?.toLowerCase()));
  return {
    unique,
    duplicatesSkipped: newLeads.length - unique.length,
  };
}
```

### Step 4: Unsubscribe Webhook Handler
```typescript
import express from 'express';
const app = express();

app.post('/webhooks/instantly/unsubscribe', express.json(), async (req, res) => {
  const { lead_email, campaign_id } = req.body;

  // Add to global suppression list
  suppression.addEmail(lead_email);

  // Remove from all active campaigns
  await removeFromAllCampaigns(lead_email);

  // Log for compliance
  console.log(`Unsubscribe: ${lead_email} from campaign ${campaign_id}`);

  res.json({ processed: true });
});

async function removeFromAllCampaigns(email: string) {
  await fetch(`${INSTANTLY_API}/lead/delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: process.env.INSTANTLY_API_KEY,
      delete_all_from_company: false,
      delete_list: [email],
    }),
  });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High bounce rate | Invalid emails imported | Validate before upload |
| Compliance violation | Emailing unsubscribed leads | Check suppression list before import |
| Duplicate sends | Lead in multiple campaigns | Use `skip_if_in_workspace` or manual dedup |
| Missing opt-out link | Template misconfigured | Always include `{unsubscribe}` variable |

## Examples

### Full Import Pipeline
```typescript
async function safeImport(campaignId: string, rawLeads: any[]) {
  const { valid, invalid } = validateLeads(rawLeads);
  const { allowed, blocked } = suppression.filterLeads(valid);
  const { unique } = await deduplicateBeforeUpload(campaignId, allowed);

  console.log(`Import: ${rawLeads.length} total -> ${unique.length} to upload`);
  console.log(`Rejected: ${invalid.length} invalid, ${blocked.length} suppressed`);

  return unique;
}
```

## Resources
- [Instantly API Docs](https://developer.instantly.ai/)
- [CAN-SPAM Compliance](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale