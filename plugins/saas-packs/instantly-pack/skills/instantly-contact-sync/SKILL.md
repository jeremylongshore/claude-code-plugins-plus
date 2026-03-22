---
name: instantly-contact-sync
description: |
  Execute Instantly primary workflow: Contact Sync & Enrichment.
  Use when importing leads from a CSV or webhook into the CRM,
  enriching contacts with company data and social profiles, or deduplicating and merging contact records.
  Trigger with phrases like "instantly sync contacts",
  "import and enrich contacts with instantly".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, instantly]
---

# Instantly Contact Sync & Enrichment

## Overview
Import, enrich, and sync contacts between your CRM and other data sources.
This is the primary workflow — clean data in, qualified leads out.


## Prerequisites
- Completed `instantly-install-auth` setup

- Access to contacts/deals data in your Instantly instance

- Valid API credentials configured

## Instructions

### Step 1: Import Contacts
```typescript
const contacts = csvData.map(row => ({
  email: row.email,
  firstName: row.first_name,
  lastName: row.last_name,
  company: row.company,
  title: row.title,
}));
const result = await client.contacts.batchCreate(contacts);
console.log(`Imported: ${result.created} new, ${result.updated} updated, ${result.failed} failed`);

```

### Step 2: Enrich with Company Data
```typescript
for (const contact of result.created) {
  const enriched = await client.contacts.enrich(contact.id);
  console.log(`${contact.email}: ${enriched.company.industry} / ${enriched.company.size} employees`);
}

```

### Step 3: Assign to Pipeline
```typescript
const qualified = enrichedContacts.filter(c =>
  c.company.size >= 50 && c.company.industry === 'Technology'
);
for (const contact of qualified) {
  await client.deals.create({
    contactId: contact.id,
    pipeline: 'sales',
    stage: 'qualified',
    value: estimateACV(contact.company.size),
  });
}
console.log(`Created ${qualified.length} deals from ${enrichedContacts.length} contacts`);

```

## Output
- Completed Contact Sync & Enrichment execution

- Contacts imported, enriched, and assigned to pipeline
- Summary of created, updated, and failed records

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Duplicate Contact | Contact with same email already exists in CRM | Use upsert mode or merge duplicates. Check existing records before import. |
| Invalid Email | Email format validation failed or domain doesn't exist | Validate emails before import. Use email verification service. |

## Examples

### Complete Workflow
```typescript
// Full contact import + enrichment pipeline
const client = new CRMClient({ apiKey: process.env.API_KEY });

async function importAndEnrich(csvPath: string) {
  const raw = parseCsv(csvPath);
  const imported = await client.contacts.batchCreate(raw);
  for (const c of imported.created) {
    await client.contacts.enrich(c.id);
  }
  return imported;
}

```

### Common Variations
- **Webhook import**: Receive contacts from form submissions in real-time
- **Two-way sync**: Bi-directional sync between CRM and marketing platform
- **Score-based routing**: Auto-assign to reps based on lead scoring


## Resources
- [Instantly Documentation](https://docs.instantly.com)
- [Instantly API Reference](https://docs.instantly.com/api)

## Next Steps
For secondary workflow, see `instantly-deal-pipeline`.