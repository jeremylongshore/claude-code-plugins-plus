---
name: instantly-core-workflow-a
description: |
  Build and launch an Instantly.ai cold email campaign end-to-end.
  Use when creating campaigns, adding leads, configuring sequences,
  and launching outreach via the Instantly API v2.
  Trigger with phrases like "instantly campaign", "launch instantly campaign",
  "create instantly outreach", "instantly cold email", "instantly send campaign".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, workflow, campaigns, cold-email]

---
# Instantly Core Workflow A: Campaign Launch Pipeline

## Overview
Build the core Instantly outreach pipeline: create a campaign with email sequences, add leads with personalization, assign sending accounts, and launch. This is the primary money-path workflow for cold email outreach via Instantly API v2.

## Prerequisites
- Completed `instantly-install-auth` setup
- At least one warmed-up email account in Instantly
- Lead data (CSV or programmatic) with email + first name at minimum
- API key with `campaigns:all` and `leads:all` scopes

## Instructions

### Step 1: Create a Campaign with Sequences
```typescript
import { instantly } from "./src/instantly";

interface CreateCampaignPayload {
  name: string;
  campaign_schedule: {
    start_date: string;
    end_date?: string;
    schedules: Array<{
      name: string;
      timing: { from: string; to: string };
      days: Record<string, boolean>;
      timezone: string;
    }>;
  };
  sequences: Array<{
    steps: Array<{
      type: "email";
      delay: number;
      delay_unit?: "minutes" | "hours" | "days";
      variants: Array<{ subject: string; body: string }>;
    }>;
  }>;
  daily_limit?: number;
  stop_on_reply?: boolean;
  stop_on_auto_reply?: boolean;
  email_gap?: number;
  link_tracking?: boolean;
  open_tracking?: boolean;
}

async function createCampaign() {
  const payload: CreateCampaignPayload = {
    name: "Q1 Outbound — Decision Makers",
    campaign_schedule: {
      start_date: "2026-04-01",
      schedules: [
        {
          name: "Business Hours",
          timing: { from: "09:00", to: "17:00" },
          days: { "1": true, "2": true, "3": true, "4": true, "5": true, "0": false, "6": false },
          timezone: "America/New_York",
        },
      ],
    },
    // sequences array takes ONE element — add steps inside it
    sequences: [
      {
        steps: [
          {
            type: "email",
            delay: 0, // first email — no delay
            variants: [
              {
                subject: "{{firstName}}, quick question about {{companyName}}",
                body: `Hi {{firstName}},\n\nI noticed {{companyName}} is scaling its outbound — we help teams like yours book 3x more meetings without adding headcount.\n\nWorth a 15-min call this week?\n\nBest,\n{{senderName}}`,
              },
              {
                subject: "Idea for {{companyName}}",
                body: `Hey {{firstName}},\n\nSaw that {{companyName}} is growing fast. We helped [similar company] increase reply rates by 40%.\n\nOpen to a quick chat?\n\n{{senderName}}`,
              },
            ],
          },
          {
            type: "email",
            delay: 3,
            delay_unit: "days",
            variants: [
              {
                subject: "Re: {{firstName}}, quick question about {{companyName}}",
                body: `Hi {{firstName}},\n\nJust following up on my last note. Would love to share how we helped [company] with a similar challenge.\n\nHappy to work around your schedule.\n\n{{senderName}}`,
              },
            ],
          },
          {
            type: "email",
            delay: 4,
            delay_unit: "days",
            variants: [
              {
                subject: "Re: {{firstName}}, quick question about {{companyName}}",
                body: `Hi {{firstName}},\n\nI know you're busy — just wanted to check if improving outbound results is a priority right now.\n\nIf not, no worries at all. If so, I'd love 15 minutes.\n\nBest,\n{{senderName}}`,
              },
            ],
          },
        ],
      },
    ],
    daily_limit: 50,
    stop_on_reply: true,
    stop_on_auto_reply: false,
    email_gap: 120,        // seconds between emails
    link_tracking: false,  // disable for better deliverability
    open_tracking: true,
  };

  const campaign = await instantly<{ id: string; name: string; status: number }>(
    "/campaigns",
    { method: "POST", body: JSON.stringify(payload) }
  );

  console.log(`Campaign created: ${campaign.name} (${campaign.id})`);
  return campaign;
}
```

### Step 2: Add Leads to the Campaign
```typescript
interface Lead {
  email: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  website?: string;
  phone?: string;
  personalization?: string;
  custom_variables?: Record<string, string>;
}

async function addLeads(campaignId: string, leads: Lead[]) {
  // POST /api/v2/leads — one at a time
  // For bulk: POST /api/v2/leads with list_id or loop
  const results = [];

  for (const lead of leads) {
    const created = await instantly("/leads", {
      method: "POST",
      body: JSON.stringify({
        campaign: campaignId,
        email: lead.email,
        first_name: lead.first_name,
        last_name: lead.last_name,
        company_name: lead.company_name,
        website: lead.website,
        personalization: lead.personalization,
        custom_variables: lead.custom_variables,
        skip_if_in_workspace: true,  // avoid duplicates
        verify_leads_on_import: true,
      }),
    });
    results.push(created);
  }

  console.log(`Added ${results.length} leads to campaign ${campaignId}`);
  return results;
}

// Example lead data
const sampleLeads: Lead[] = [
  {
    email: "jane@acmecorp.com",
    first_name: "Jane",
    last_name: "Smith",
    company_name: "Acme Corp",
    custom_variables: { companyName: "Acme Corp", senderName: "Alex" },
  },
  {
    email: "bob@techstart.io",
    first_name: "Bob",
    last_name: "Johnson",
    company_name: "TechStart",
    custom_variables: { companyName: "TechStart", senderName: "Alex" },
  },
];
```

### Step 3: Map Sending Accounts to Campaign
```typescript
async function assignAccounts(campaignId: string) {
  // Get available warmed-up accounts
  const accounts = await instantly<{ email: string; warmup_status: string }[]>(
    "/accounts?limit=50"
  );

  const warmedUp = accounts.filter((a) => a.warmup_status === "active");
  console.log(`Found ${warmedUp.length} warmed-up accounts`);

  // Check current account-campaign mappings
  for (const account of warmedUp.slice(0, 3)) {
    const mappings = await instantly(
      `/account-campaign-mappings/${encodeURIComponent(account.email)}?limit=10`
    );
    console.log(`${account.email} mapped to ${Array.isArray(mappings) ? mappings.length : 0} campaigns`);
  }

  // Accounts are assigned to campaigns in the Instantly dashboard or
  // via the PATCH campaign endpoint with email_list
  await instantly(`/campaigns/${campaignId}`, {
    method: "PATCH",
    body: JSON.stringify({
      email_list: warmedUp.slice(0, 3).map((a) => a.email),
    }),
  });

  console.log(`Assigned ${Math.min(3, warmedUp.length)} accounts to campaign`);
}
```

### Step 4: Launch the Campaign
```typescript
async function launchCampaign(campaignId: string) {
  // Activate (start) the campaign
  await instantly(`/campaigns/${campaignId}/activate`, { method: "POST" });
  console.log(`Campaign ${campaignId} is now ACTIVE`);

  // Verify sending status
  const status = await instantly<{ sending: boolean; reason?: string }>(
    `/campaigns/${campaignId}/sending-status`
  );
  console.log(`Sending status:`, status);
}

// Full pipeline
async function main() {
  const campaign = await createCampaign();
  await addLeads(campaign.id, sampleLeads);
  await assignAccounts(campaign.id);
  await launchCampaign(campaign.id);
  console.log("\nCampaign launched successfully!");
}

main().catch(console.error);
```

## Key API Endpoints Used
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/campaigns` | Create campaign with sequences |
| `PATCH` | `/campaigns/{id}` | Update campaign settings |
| `POST` | `/campaigns/{id}/activate` | Start sending |
| `POST` | `/campaigns/{id}/pause` | Stop sending |
| `GET` | `/campaigns/{id}/sending-status` | Check if actively sending |
| `POST` | `/leads` | Add a lead to campaign |
| `GET` | `/accounts` | List email accounts |
| `GET` | `/account-campaign-mappings/{email}` | Check account assignments |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `400 Bad Request` on create | Invalid schedule or sequence format | Ensure `days` keys are strings `"0"`-`"6"`, timing is `HH:MM` |
| Campaign stuck in Draft | No sending accounts assigned | Assign via `PATCH /campaigns/{id}` with `email_list` |
| Leads not receiving emails | Accounts not warmed up | Enable warmup first (see `instantly-core-workflow-b`) |
| `422` on lead add | Duplicate email in workspace | Set `skip_if_in_workspace: true` |
| Low open rates | Poor subject lines or spam folder | Disable link tracking, test with inbox placement |

## Resources
- [Create Campaign API](https://developer.instantly.ai/api/v2/campaign/createcampaign)
- [Campaign Schemas](https://developer.instantly.ai/api/v2/schemas)
- [Instantly Deliverability Guide](https://help.instantly.ai/en/articles/6222396-campaign-options)

## Next Steps
For account warmup and analytics, see `instantly-core-workflow-b`.
