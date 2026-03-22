---
name: instantly-data-handling
description: |
  Implement Instantly.ai lead data management, GDPR/CAN-SPAM compliance, and list operations.
  Use when handling lead imports, managing block lists, implementing unsubscribe flows,
  or ensuring compliance with email regulations.
  Trigger with phrases like "instantly leads", "instantly data", "instantly GDPR",
  "instantly block list", "instantly lead management", "instantly unsubscribe".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, data-handling, gdpr, compliance, leads]

---
# Instantly Data Handling

## Overview
Manage leads, lead lists, block lists, and regulatory compliance in Instantly API v2. Covers lead CRUD operations, list management, bulk import patterns, unsubscribe handling, GDPR right-to-deletion, CAN-SPAM compliance, and block list automation. Cold email has specific legal requirements — this skill ensures your integrations are compliant.

## Prerequisites
- Completed `instantly-install-auth` setup
- API key with `leads:all` scope
- Understanding of CAN-SPAM / GDPR requirements for cold outreach

## Instructions

### Step 1: Lead List Management
```typescript
import { InstantlyClient } from "./src/instantly/client";
const client = new InstantlyClient();

// Create a lead list (container for leads outside campaigns)
async function createLeadList(name: string) {
  const list = await client.request<{ id: string; name: string }>("/lead-lists", {
    method: "POST",
    body: JSON.stringify({
      name,
      has_enrichment_task: false,
    }),
  });
  console.log(`Created list: ${list.name} (${list.id})`);
  return list;
}

// List all lead lists
async function getLeadLists() {
  return client.request<Array<{
    id: string; name: string; timestamp_created: string;
  }>>("/lead-lists?limit=50");
}

// Delete a lead list
async function deleteLeadList(listId: string) {
  await client.request(`/lead-lists/${listId}`, { method: "DELETE" });
}
```

### Step 2: Lead Import with Validation
```typescript
interface LeadImport {
  email: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  website?: string;
  phone?: string;
  custom_variables?: Record<string, string>;
}

async function importLeads(
  campaignId: string,
  leads: LeadImport[],
  options = { skipDuplicates: true, verifyEmails: true }
) {
  const results = { added: 0, skipped: 0, failed: 0, errors: [] as string[] };

  for (const lead of leads) {
    try {
      // Validate email format
      if (!lead.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(lead.email)) {
        results.failed++;
        results.errors.push(`Invalid email: ${lead.email}`);
        continue;
      }

      // Check against block list patterns
      const domain = lead.email.split("@")[1];
      if (BLOCKED_PATTERNS.some((p) => domain.includes(p))) {
        results.skipped++;
        continue;
      }

      await client.request("/leads", {
        method: "POST",
        body: JSON.stringify({
          campaign: campaignId,
          email: lead.email,
          first_name: lead.first_name,
          last_name: lead.last_name,
          company_name: lead.company_name,
          website: lead.website,
          phone: lead.phone,
          custom_variables: lead.custom_variables,
          skip_if_in_workspace: options.skipDuplicates,
          skip_if_in_campaign: true,
          verify_leads_on_import: options.verifyEmails,
        }),
      });
      results.added++;
    } catch (e: any) {
      results.failed++;
      results.errors.push(`${lead.email}: ${e.message}`);
    }
  }

  console.log(`Import: ${results.added} added, ${results.skipped} skipped, ${results.failed} failed`);
  return results;
}

// Role-based emails and internal domains to always skip
const BLOCKED_PATTERNS = [
  "noreply", "no-reply", "donotreply",
  "info@", "admin@", "support@", "help@", "abuse@",
  "postmaster@", "webmaster@", "hostmaster@",
];
```

### Step 3: Lead Operations (Move, Update, Delete)
```typescript
// Move leads between campaigns or lists
async function moveLeads(opts: {
  fromCampaign?: string;
  fromList?: string;
  toCampaign?: string;
  toList?: string;
  limit?: number;
}) {
  return client.request("/leads/move", {
    method: "POST",
    body: JSON.stringify({
      in_campaign: opts.fromCampaign,
      in_list: opts.fromList,
      to_campaign_id: opts.toCampaign,
      to_list_id: opts.toList,
      limit: opts.limit || 1000,
      check_duplicates: true,
    }),
  });
}

// Update lead interest status
async function updateLeadInterest(
  email: string,
  campaignId: string,
  status: "interested" | "not_interested" | "meeting_booked" | "closed"
) {
  const interestMap: Record<string, number> = {
    interested: 1,
    not_interested: -1,
    meeting_booked: 2,
    closed: 3,
  };

  await client.request("/leads/update-interest-status", {
    method: "POST",
    body: JSON.stringify({
      lead_email: email,
      campaign_id: campaignId,
      interest_value: interestMap[status],
    }),
  });
}

// Update lead data
async function updateLead(leadId: string, data: Partial<LeadImport>) {
  await client.request(`/leads/${leadId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// Delete leads from a campaign (bulk)
async function deleteLeadsFromCampaign(campaignId: string, status?: number) {
  await client.request("/leads", {
    method: "DELETE",
    body: JSON.stringify({
      campaign_id: campaignId,
      status, // e.g., -1 for bounced only
    }),
  });
}
```

### Step 4: Block List Management
```typescript
// Add entries to workspace block list
async function addToBlockList(entries: string[]) {
  // Single entry
  for (const entry of entries) {
    await client.request("/block-lists-entries", {
      method: "POST",
      body: JSON.stringify({ bl_value: entry }), // email or domain
    });
  }

  // Or bulk add
  await client.request("/block-lists-entries/bulk-create", {
    method: "POST",
    body: JSON.stringify({ entries }),
  });
}

// Seed block list with standard entries
async function seedBlockList() {
  const standardBlocks = [
    // Your own domains
    "yourdomain.com",
    "yourcompany.com",
    // Competitor domains
    "competitor1.com",
    "competitor2.com",
    // ISP domains (not your target audience)
    "gmail.com",      // uncomment if B2B only
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    // Trap/spamtrap domains
    "spamtrap.com",
  ];

  await addToBlockList(standardBlocks);
  console.log(`Seeded block list with ${standardBlocks.length} entries`);
}

// List and audit block list
async function auditBlockList() {
  const entries = await client.request<Array<{
    id: string; bl_value: string;
  }>>("/block-lists-entries?limit=100");
  console.log(`Block list: ${entries.length} entries`);
  for (const e of entries) {
    console.log(`  ${e.bl_value}`);
  }
}
```

### Step 5: GDPR / CAN-SPAM Compliance
```typescript
// GDPR: Right to deletion — remove lead from everywhere
async function handleDeletionRequest(email: string) {
  console.log(`Processing GDPR deletion request for: ${email}`);

  // 1. Find all campaigns containing this lead
  const campaigns = await client.request<Array<{ id: string }>>(
    `/campaigns/search-by-contact?search=${encodeURIComponent(email)}`
  );

  // 2. Delete lead from each campaign
  for (const campaign of campaigns) {
    const leads = await client.leads.list({ campaign: campaign.id });
    const matchingLead = leads.find((l) => l.email === email);
    if (matchingLead) {
      await client.leads.delete(matchingLead.id);
      console.log(`  Deleted from campaign ${campaign.id}`);
    }
  }

  // 3. Add to workspace block list (prevent re-import)
  await addToBlockList([email]);
  console.log(`  Added to block list`);

  // 4. Log for compliance records
  console.log(`  Deletion complete. Log this for GDPR records.`);
}

// CAN-SPAM: Ensure unsubscribe is honored
async function handleUnsubscribe(email: string) {
  // 1. Add to block list (global across all campaigns)
  await addToBlockList([email]);

  // 2. Also add the domain if it's a business-wide request
  // const domain = email.split("@")[1];
  // await addToBlockList([domain]);

  console.log(`Unsubscribe processed: ${email} added to global block list`);
}

// Email verification before import
async function verifyEmail(email: string) {
  // Start verification
  await client.request("/email-verification", {
    method: "POST",
    body: JSON.stringify({
      email,
      webhook_url: "https://api.yourapp.com/webhooks/verification",
    }),
  });

  // Check status (may need to poll)
  const result = await client.request<{
    email: string; status: string; reason: string;
  }>(`/email-verification/${encodeURIComponent(email)}`);

  return result;
}
```

## Key API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/leads` | Create lead |
| `POST` | `/leads/list` | List/filter leads |
| `PATCH` | `/leads/{id}` | Update lead |
| `DELETE` | `/leads/{id}` | Delete single lead |
| `DELETE` | `/leads` | Bulk delete leads |
| `POST` | `/leads/move` | Move leads between campaigns/lists |
| `POST` | `/leads/update-interest-status` | Update interest status |
| `POST` | `/lead-lists` | Create lead list |
| `GET` | `/lead-lists` | List lead lists |
| `POST` | `/block-lists-entries` | Add block list entry |
| `POST` | `/block-lists-entries/bulk-create` | Bulk add entries |
| `POST` | `/email-verification` | Verify email |
| `GET` | `/campaigns/search-by-contact` | Find campaigns by lead |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422` on lead create | Duplicate in workspace | Use `skip_if_in_workspace: true` |
| Lead not found in campaign | Already deleted or moved | Search across campaigns first |
| Block list full | Too many entries | Remove outdated entries periodically |
| Email verification timeout | External service delay | Poll status endpoint |

## Resources
- [Instantly Lead API](https://developer.instantly.ai/api/v2/lead/listleads)
- [Instantly Block List API](https://developer.instantly.ai/api/v2/schemas)
- [CAN-SPAM Requirements](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business)

## Next Steps
For workspace access control, see `instantly-enterprise-rbac`.
