---
name: instantly-migration-deep-dive
description: |
  Execute complex Instantly.ai migration strategies for platform changes.
  Use when migrating between cold email platforms, consolidating workspaces,
  or re-architecting outreach infrastructure around Instantly.
  Trigger with phrases like "migrate to instantly", "instantly migration",
  "switch to instantly", "instantly platform migration", "outreach migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, migration, architecture]

---
# Instantly Migration Deep Dive

## Overview
Strategies for migrating to/from Instantly or consolidating multiple outreach tools into Instantly. Covers data migration (leads, campaigns, templates), account migration (email infrastructure), analytics preservation, and parallel-run strategies with zero-downtime cutover.

## Migration Scenarios

| Scenario | Complexity | Duration |
|----------|-----------|----------|
| Lemlist/Woodpecker/Mailshake to Instantly | Medium | 1-2 weeks |
| Salesloft/Outreach to Instantly | High | 2-4 weeks |
| Multiple Instantly workspaces to one | Low | 1 week |
| Manual outreach to Instantly automation | Low | 3-5 days |

## Instructions

### Step 1: Pre-Migration Audit
```typescript
import { InstantlyClient } from "./src/instantly/client";
const client = new InstantlyClient();

interface MigrationPlan {
  sourceLeadCount: number;
  sourceCampaignCount: number;
  sourceTemplateCount: number;
  emailAccountsToMigrate: string[];
  estimatedDuration: string;
  risks: string[];
}

async function preMigrationAudit(): Promise<MigrationPlan> {
  // Check current Instantly workspace state
  const existingCampaigns = await client.campaigns.list(100);
  const existingAccounts = await client.accounts.list(100);

  console.log("=== Current Instantly Workspace ===");
  console.log(`Campaigns: ${existingCampaigns.length}`);
  console.log(`Accounts: ${existingAccounts.length}`);

  // Check warmup status
  if (existingAccounts.length > 0) {
    const warmup = await client.accounts.warmupAnalytics(
      existingAccounts.map((a) => a.email)
    );
    console.log(`Accounts with warmup: ${(warmup as any[]).length}`);
  }

  console.log("\n=== Migration Checklist ===");
  console.log("[ ] Export leads from source platform (CSV)");
  console.log("[ ] Export campaign templates and sequences");
  console.log("[ ] Document sending schedules and daily limits");
  console.log("[ ] Export analytics/historical data for reference");
  console.log("[ ] Identify email accounts to migrate (IMAP/SMTP creds)");
  console.log("[ ] Map custom fields to Instantly custom_variables");
  console.log("[ ] Create block list from source platform unsubscribes");
  console.log("[ ] Plan warmup period (14+ days for new accounts)");

  return {
    sourceLeadCount: 0, // fill from source audit
    sourceCampaignCount: 0,
    sourceTemplateCount: 0,
    emailAccountsToMigrate: [],
    estimatedDuration: "2 weeks",
    risks: [
      "Warmup period delays campaign launch by 14+ days",
      "Custom field mapping may lose data if not 1:1",
      "Sending reputation doesn't transfer between platforms",
    ],
  };
}
```

### Step 2: Import Email Accounts
```typescript
// Add email accounts with IMAP/SMTP credentials
async function migrateEmailAccounts(accounts: Array<{
  email: string;
  first_name: string;
  last_name: string;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  imap_host: string;
  imap_port: number;
  imap_username: string;
  imap_password: string;
  daily_limit: number;
}>) {
  const results = { added: 0, failed: 0, errors: [] as string[] };

  for (const account of accounts) {
    try {
      await client.request("/accounts", {
        method: "POST",
        body: JSON.stringify({
          email: account.email,
          first_name: account.first_name,
          last_name: account.last_name,
          smtp_host: account.smtp_host,
          smtp_port: account.smtp_port,
          smtp_username: account.smtp_username,
          smtp_password: account.smtp_password,
          imap_host: account.imap_host,
          imap_port: account.imap_port,
          imap_username: account.imap_username,
          imap_password: account.imap_password,
          daily_limit: account.daily_limit,
        }),
      });
      results.added++;
      console.log(`Added: ${account.email}`);
    } catch (e: any) {
      results.failed++;
      results.errors.push(`${account.email}: ${e.message}`);
    }
  }

  // Enable warmup on all newly added accounts
  if (results.added > 0) {
    const addedEmails = accounts
      .slice(0, results.added)
      .map((a) => a.email);
    await client.accounts.enableWarmup(addedEmails);
    console.log(`Warmup enabled for ${addedEmails.length} accounts`);
  }

  console.log(`\nAccount migration: ${results.added} added, ${results.failed} failed`);
  return results;
}

// Or use OAuth for Google/Microsoft accounts
async function migrateWithOAuth(provider: "google" | "microsoft") {
  const endpoint = provider === "google"
    ? "/oauth/google/init"
    : "/oauth/microsoft/init";

  const session = await client.request<{ session_id: string; redirect_url: string }>(
    endpoint,
    { method: "POST" }
  );

  console.log(`OAuth flow started. Redirect user to: ${session.redirect_url}`);
  console.log(`Session ID: ${session.session_id}`);

  // Poll for completion
  let status = await client.request(`/oauth/session/status/${session.session_id}`);
  console.log("Session status:", status);
}
```

### Step 3: Import Leads from CSV
```typescript
import { readFileSync } from "fs";
import { parse } from "csv-parse/sync";

async function importLeadsFromCSV(
  filePath: string,
  campaignId: string,
  fieldMapping: Record<string, string>
) {
  const csv = readFileSync(filePath, "utf-8");
  const records = parse(csv, { columns: true, skip_empty_lines: true });

  console.log(`Importing ${records.length} leads from ${filePath}`);

  const results = { added: 0, skipped: 0, failed: 0 };

  for (let i = 0; i < records.length; i++) {
    const row = records[i];
    try {
      const lead: Record<string, unknown> = {
        campaign: campaignId,
        skip_if_in_workspace: true,
        verify_leads_on_import: true,
      };

      // Map CSV columns to Instantly fields
      for (const [csvCol, instantlyField] of Object.entries(fieldMapping)) {
        if (row[csvCol]) {
          lead[instantlyField] = row[csvCol];
        }
      }

      // Handle custom variables (anything not in standard fields)
      const standardFields = ["email", "first_name", "last_name", "company_name", "website", "phone"];
      const customVars: Record<string, string> = {};
      for (const [csvCol, instantlyField] of Object.entries(fieldMapping)) {
        if (!standardFields.includes(instantlyField) && row[csvCol]) {
          customVars[instantlyField] = row[csvCol];
        }
      }
      if (Object.keys(customVars).length > 0) {
        lead.custom_variables = customVars;
      }

      await client.request("/leads", {
        method: "POST",
        body: JSON.stringify(lead),
      });
      results.added++;
    } catch (e: any) {
      if (e.message.includes("422")) {
        results.skipped++; // duplicate
      } else {
        results.failed++;
      }
    }

    // Progress report every 100 leads
    if ((i + 1) % 100 === 0) {
      console.log(`Progress: ${i + 1}/${records.length}`);
    }
  }

  console.log(`Import complete: ${results.added} added, ${results.skipped} skipped, ${results.failed} failed`);
}

// Example field mapping: CSV column -> Instantly field
const mapping = {
  "Email": "email",
  "First Name": "first_name",
  "Last Name": "last_name",
  "Company": "company_name",
  "Website": "website",
  "Title": "title",         // goes to custom_variables
  "Industry": "industry",   // goes to custom_variables
};
```

### Step 4: Migrate Unsubscribes to Block List
```typescript
async function migrateUnsubscribes(unsubscribedEmails: string[]) {
  console.log(`Migrating ${unsubscribedEmails.length} unsubscribes to block list`);

  // Bulk add to block list
  const batchSize = 100;
  for (let i = 0; i < unsubscribedEmails.length; i += batchSize) {
    const batch = unsubscribedEmails.slice(i, i + batchSize);
    await client.request("/block-lists-entries/bulk-create", {
      method: "POST",
      body: JSON.stringify({ entries: batch }),
    });
    console.log(`Batch ${Math.floor(i / batchSize) + 1}: ${batch.length} entries added`);
  }

  console.log("Block list migration complete");
}
```

### Step 5: Parallel Run Strategy
```typescript
// Run old and new platforms simultaneously during transition
async function parallelRunMonitor() {
  console.log("=== Parallel Run Status ===\n");

  // Check Instantly campaign performance
  const campaigns = await client.campaigns.list(50);
  const activeCampaigns = campaigns.filter((c) => c.status === 1);

  for (const campaign of activeCampaigns) {
    const analytics = await client.campaigns.analytics(campaign.id);
    const sent = analytics.emails_sent || 1;
    console.log(`${campaign.name}:`);
    console.log(`  Sent: ${analytics.emails_sent} | Open: ${((analytics.emails_opened / sent) * 100).toFixed(1)}% | Reply: ${((analytics.emails_replied / sent) * 100).toFixed(1)}%`);
  }

  console.log("\n=== Cutover Checklist ===");
  console.log("[ ] Instantly campaigns matching old platform performance");
  console.log("[ ] All leads migrated and deduplicated");
  console.log("[ ] Webhooks delivering to CRM correctly");
  console.log("[ ] Block list complete (all unsubscribes migrated)");
  console.log("[ ] Warmup healthy (>80% inbox rate) for all accounts");
  console.log("[ ] Old platform campaigns paused");
  console.log("[ ] Team trained on Instantly dashboard");
}
```

## Migration Timeline
```
Week 1: Setup & Warmup
  - Add email accounts to Instantly
  - Enable warmup (runs for 14+ days)
  - Import block list / unsubscribes
  - Map custom fields

Week 2: Data Migration
  - Import leads from CSV
  - Recreate campaign templates as sequences
  - Set up webhooks and CRM integration
  - Configure sending schedules

Week 3: Parallel Run
  - Launch test campaign on Instantly (small list)
  - Compare metrics with old platform
  - Fix any delivery or integration issues

Week 4: Cutover
  - Pause old platform campaigns
  - Activate full Instantly campaigns
  - Monitor for 48 hours
  - Decommission old platform
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Account SMTP auth fails | Wrong credentials from old platform | Re-check app password or OAuth flow |
| Leads rejected as duplicates | Already imported | Use `skip_if_in_workspace: true` |
| Custom fields lost | No matching Instantly field | Map to `custom_variables` object |
| Performance worse than old platform | Accounts not warmed up | Wait 14+ days, check inbox rates |

## Resources
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Instantly Account API](https://developer.instantly.ai/api/v2/account)
- [Instantly Quick Start Guide](https://help.instantly.ai/en/articles/6451970-quick-start-guide-all-in-one)

## Next Steps
After migration, set up monitoring with `instantly-observability`.
