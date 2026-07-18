# Intercom Migration — Full Implementation Walkthrough

This is the complete, runnable TypeScript walkthrough for a full Intercom
migration. It uses the official `intercom-client` SDK and executes in six phases
plus a post-migration validation pass. SKILL.md carries the high-level workflow
and the Step 1 skeleton; this file carries every phase in full.

## Authentication

All examples authenticate with a workspace access token read from the
`INTERCOM_ACCESS_TOKEN` environment variable — never hard-code the token. Create
an access token in the Intercom Developer Hub (Settings → Developers → your app →
Authentication) and export it before running any migration script:

```bash
export INTERCOM_ACCESS_TOKEN="your-workspace-access-token"
```

```typescript
import { IntercomClient, IntercomError } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});
```

## Step 1: Contact Import

Idempotent import: search by `external_id` or `email` first, then update or
create. Contacts carry `migrated_from` / `migration_date` custom attributes so a
rollback can find them.

```typescript
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

## Step 2: Company Import

Companies must exist before contacts reference them. Attach contacts after both
sides are imported.

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

## Step 3: Tag Migration

Create each tag, then apply it to its contacts. A missing contact (404) is
skipped rather than aborting the whole batch.

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

## Step 4: Help Center Article Migration

Group articles into collections by category, creating each collection once.

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

## Step 5: Migration Orchestrator

Runs the phases in dependency order (companies → contacts → tags → articles) and
prints a per-phase progress report plus a final failed-contact summary.

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

## Step 6: Post-Migration Validation

Compares live Intercom counts against expected source counts with a 95%
threshold on the fuzzy resources (contacts, articles) and an exact floor on tags.

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
