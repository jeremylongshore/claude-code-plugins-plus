---
name: intercom-migration-deep-dive
description: |
  Execute major Intercom data migrations and re-platforming with the contacts,
  conversations, and articles APIs. Use when migrating from Zendesk/Freshdesk to
  Intercom, bulk-importing contacts, or re-platforming to Intercom.
  Trigger with phrases like "migrate to intercom", "intercom migration",
  "import contacts to intercom", "switch to intercom", "zendesk to intercom",
  "intercom data import".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Migration Deep Dive

## Overview

Comprehensive guide for migrating to Intercom from other platforms (Zendesk, Freshdesk, HelpScout) or bulk-importing data. Covers contact import, conversation history, Help Center articles, tags, and companies.

## Prerequisites

- Intercom workspace with access token
- Source system data exported (CSV or API access)
- Feature flag infrastructure for gradual cutover
- Rollback strategy tested

## Migration Types

| Type | Complexity | Duration | Risk |
|------|-----------|----------|------|
| Contact import | Low | Hours | Low |
| Zendesk/Freshdesk migration | Medium | 1-2 weeks | Medium |
| Full re-platform (with history) | High | 2-4 weeks | High |
| Help Center migration | Medium | Days | Low |

## Instructions

### Step 1: Contact Import

```typescript
import { IntercomClient, IntercomError } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

interface SourceContact {
  id: string;
  email: string;
  name: string;
  phone?: string;
  plan?: string;
  company?: string;
  created_at: string;
  custom_fields?: Record<string, any>;
}

async function importContacts(
  contacts: SourceContact[]
): Promise<{ created: number; updated: number; failed: number; errors: any[] }> {
  const stats = { created: 0, updated: 0, failed: 0, errors: [] as any[] };

  for (const contact of contacts) {
    try {
      // Search for existing contact by external_id or email
      const existing = await client.contacts.search({
        query: {
          operator: "OR",
          value: [
            { field: "external_id", operator: "=", value: contact.id },
            { field: "email", operator: "=", value: contact.email },
          ],
        },
      });

      if (existing.data.length > 0) {
        // Update existing contact
        await client.contacts.update({
          contactId: existing.data[0].id,
          name: contact.name,
          phone: contact.phone,
          customAttributes: {
            ...contact.custom_fields,
            plan: contact.plan,
            migrated_from: "source_system",
            migration_date: new Date().toISOString(),
          },
        });
        stats.updated++;
      } else {
        // Create new contact
        await client.contacts.create({
          role: "user",
          externalId: contact.id,
          email: contact.email,
          name: contact.name,
          phone: contact.phone,
          signedUpAt: Math.floor(new Date(contact.created_at).getTime() / 1000),
          customAttributes: {
            ...contact.custom_fields,
            plan: contact.plan,
            migrated_from: "source_system",
            migration_date: new Date().toISOString(),
          },
        });
        stats.created++;
      }

      // Rate limit: pause every 50 contacts
      if ((stats.created + stats.updated) % 50 === 0) {
        console.log(`Progress: ${stats.created} created, ${stats.updated} updated`);
        await new Promise(r => setTimeout(r, 500));
      }
    } catch (err) {
      stats.failed++;
      stats.errors.push({
        contact_id: contact.id,
        email: contact.email,
        error: err instanceof IntercomError
          ? `${err.statusCode}: ${err.message}`
          : (err as Error).message,
      });
    }
  }

  return stats;
}
```

### Step 2: Company Import

```typescript
async function importCompanies(
  companies: Array<{ id: string; name: string; plan?: string; size?: number }>
): Promise<void> {
  for (const company of companies) {
    await client.companies.create({
      companyId: company.id,
      name: company.name,
      plan: company.plan,
      size: company.size,
      customAttributes: {
        migrated_from: "source_system",
      },
    });

    await new Promise(r => setTimeout(r, 100)); // Rate limit
  }
}

// Attach contacts to companies
async function attachContactToCompany(
  contactId: string,
  companyId: string
): Promise<void> {
  await client.contacts.attachCompany({
    contactId,
    companyId,
  });
}
```

### Step 3: Tag Migration

```typescript
async function migrateTags(
  tagMappings: Array<{ sourceName: string; contactIds: string[] }>
): Promise<void> {
  for (const mapping of tagMappings) {
    // Create tag if it doesn't exist
    const tag = await client.tags.create({ name: mapping.sourceName });

    // Apply tag to contacts
    for (const contactId of mapping.contactIds) {
      try {
        await client.contacts.tag({ contactId, id: tag.id });
      } catch (err) {
        if (err instanceof IntercomError && err.statusCode === 404) {
          console.warn(`Contact ${contactId} not found, skipping tag`);
          continue;
        }
        throw err;
      }
    }

    console.log(`Tagged ${mapping.contactIds.length} contacts with "${mapping.sourceName}"`);
  }
}
```

### Step 4: Help Center Article Migration

```typescript
async function migrateArticles(
  articles: Array<{
    title: string;
    body: string;     // HTML content
    category: string;
    state: "published" | "draft";
  }>,
  authorId: string   // Admin ID who will be the author
): Promise<void> {
  // Create or find collections for categories
  const collections = new Map<string, string>();

  for (const article of articles) {
    // Create collection if needed
    if (!collections.has(article.category)) {
      const collection = await client.helpCenter.createCollection({
        name: article.category,
      });
      collections.set(article.category, collection.id);
    }

    // Create article in collection
    await client.articles.create({
      title: article.title,
      body: article.body,
      authorId,
      parentId: collections.get(article.category),
      state: article.state,
    });

    console.log(`Migrated article: ${article.title}`);
    await new Promise(r => setTimeout(r, 200)); // Rate limit
  }
}
```

### Step 5: Migration Orchestrator

```typescript
interface MigrationPlan {
  contacts: SourceContact[];
  companies: Array<{ id: string; name: string; plan?: string }>;
  tags: Array<{ sourceName: string; contactIds: string[] }>;
  articles: Array<{ title: string; body: string; category: string; state: "published" | "draft" }>;
}

async function executeMigration(plan: MigrationPlan): Promise<void> {
  console.log("=== Starting Intercom Migration ===");
  const startTime = Date.now();

  // Phase 1: Companies (contacts reference these)
  console.log(`\n[Phase 1] Importing ${plan.companies.length} companies...`);
  await importCompanies(plan.companies);

  // Phase 2: Contacts
  console.log(`\n[Phase 2] Importing ${plan.contacts.length} contacts...`);
  const contactStats = await importContacts(plan.contacts);
  console.log(`  Created: ${contactStats.created}, Updated: ${contactStats.updated}, Failed: ${contactStats.failed}`);

  // Phase 3: Tags
  console.log(`\n[Phase 3] Migrating ${plan.tags.length} tags...`);
  await migrateTags(plan.tags);

  // Phase 4: Articles
  const adminList = await client.admins.list();
  const authorId = adminList.admins[0].id;
  console.log(`\n[Phase 4] Migrating ${plan.articles.length} articles...`);
  await migrateArticles(plan.articles, authorId);

  const duration = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
  console.log(`\n=== Migration complete in ${duration} minutes ===`);

  if (contactStats.errors.length > 0) {
    console.log(`\nFailed contacts: ${contactStats.errors.length}`);
    for (const err of contactStats.errors.slice(0, 10)) {
      console.log(`  ${err.email}: ${err.error}`);
    }
  }
}
```

### Step 6: Post-Migration Validation

```typescript
async function validateMigration(
  expectedCounts: { contacts: number; companies: number; tags: number; articles: number }
): Promise<{ passed: boolean; checks: any[] }> {
  const checks = [];

  // Check contact count
  const contacts = await client.contacts.list({ perPage: 1 });
  checks.push({
    name: "Contact count",
    expected: expectedCounts.contacts,
    actual: contacts.totalCount,
    passed: contacts.totalCount >= expectedCounts.contacts * 0.95, // 95% threshold
  });

  // Check tags exist
  const tags = await client.tags.list();
  checks.push({
    name: "Tag count",
    expected: expectedCounts.tags,
    actual: tags.data.length,
    passed: tags.data.length >= expectedCounts.tags,
  });

  // Check articles
  let articleCount = 0;
  const articles = await client.articles.list();
  for await (const _ of articles) articleCount++;
  checks.push({
    name: "Article count",
    expected: expectedCounts.articles,
    actual: articleCount,
    passed: articleCount >= expectedCounts.articles * 0.95,
  });

  const passed = checks.every(c => c.passed);
  console.log(`\nValidation: ${passed ? "PASSED" : "FAILED"}`);
  for (const check of checks) {
    console.log(`  ${check.passed ? "OK" : "FAIL"} ${check.name}: ${check.actual}/${check.expected}`);
  }

  return { passed, checks };
}
```

## Rollback Procedure

```bash
# If migration goes wrong:
# 1. Stop the migration script
# 2. Tag all migrated contacts for identification
# 3. Delete migrated contacts if needed:
#    Search by custom_attributes.migration_date = "today's date"
#    Delete in batches

# Keep source system active during migration
# Only decommission after validation + 2 weeks of parallel run
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 409 Conflict | Duplicate external_id/email | Search before create |
| 429 Rate Limited | Too fast | Add delays between batches |
| 422 Validation | Bad email/data format | Validate data before import |
| Partial migration | Script crashed | Use idempotent operations, re-run |
| Missing conversations | API doesn't support bulk import | Contact Intercom support for import |

## Resources

- [Contacts API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts)
- [Companies API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/companies)
- [Articles API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/articles)
- [Import Contacts Guide](https://developers.intercom.com/docs/guides/tickets/import-contacts)
- [Tags API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/tags)
