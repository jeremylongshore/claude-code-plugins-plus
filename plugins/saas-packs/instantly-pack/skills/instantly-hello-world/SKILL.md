---
name: instantly-hello-world
description: |
  Create a minimal working Instantly.ai example with real API calls.
  Use when starting a new Instantly integration, testing your setup,
  or learning basic Instantly API v2 patterns.
  Trigger with phrases like "instantly hello world", "instantly example",
  "instantly quick start", "simple instantly code", "test instantly api".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, api, getting-started]

---
# Instantly Hello World

## Overview
Minimal working example that lists your campaigns, checks email account health, and pulls campaign analytics — all using real Instantly API v2 endpoints.

## Prerequisites
- Completed `instantly-install-auth` setup
- At least one email account connected in Instantly
- `INSTANTLY_API_KEY` environment variable set

## Instructions

### Step 1: List Your Campaigns
```typescript
import { instantly } from "./src/instantly";

interface Campaign {
  id: string;
  name: string;
  status: number; // 0=Draft, 1=Active, 2=Paused, 3=Completed
}

const STATUS_LABELS: Record<number, string> = {
  0: "Draft", 1: "Active", 2: "Paused", 3: "Completed",
  4: "Running Subsequences", [-99]: "Suspended",
  [-1]: "Accounts Unhealthy", [-2]: "Bounce Protect",
};

async function listCampaigns() {
  const campaigns = await instantly<Campaign[]>("/campaigns?limit=10");

  console.log(`Found ${campaigns.length} campaigns:\n`);
  for (const c of campaigns) {
    console.log(`  ${c.name} [${STATUS_LABELS[c.status] ?? c.status}] — ${c.id}`);
  }
  return campaigns;
}
```

### Step 2: Check Email Account Health
```typescript
interface Account {
  email: string;
  status: number;
  warmup_status: string;
  daily_limit: number | null;
}

async function checkAccounts() {
  const accounts = await instantly<Account[]>("/accounts?limit=5");

  console.log(`\nEmail Accounts (${accounts.length}):`);
  for (const a of accounts) {
    console.log(`  ${a.email} — status: ${a.status}, warmup: ${a.warmup_status}, daily_limit: ${a.daily_limit}`);
  }

  // Test vitals for the first account
  if (accounts.length > 0) {
    const vitals = await instantly("/accounts/test/vitals", {
      method: "POST",
      body: JSON.stringify({ accounts: [accounts[0].email] }),
    });
    console.log(`\nVitals for ${accounts[0].email}:`, JSON.stringify(vitals, null, 2));
  }
}
```

### Step 3: Pull Campaign Analytics
```typescript
async function getAnalytics(campaignId: string) {
  const stats = await instantly<{
    campaign_id: string;
    total_leads: number;
    leads_contacted: number;
    emails_sent: number;
    emails_opened: number;
    emails_replied: number;
    emails_bounced: number;
  }>(`/campaigns/analytics?id=${campaignId}`);

  console.log(`\nCampaign Analytics:`);
  console.log(`  Leads: ${stats.total_leads} total, ${stats.leads_contacted} contacted`);
  console.log(`  Sent: ${stats.emails_sent}`);
  console.log(`  Opened: ${stats.emails_opened} (${((stats.emails_opened / stats.emails_sent) * 100).toFixed(1)}%)`);
  console.log(`  Replied: ${stats.emails_replied} (${((stats.emails_replied / stats.emails_sent) * 100).toFixed(1)}%)`);
  console.log(`  Bounced: ${stats.emails_bounced}`);
}
```

### Step 4: Run It All
```typescript
async function main() {
  console.log("=== Instantly API v2 Hello World ===\n");

  const campaigns = await listCampaigns();
  await checkAccounts();

  if (campaigns.length > 0) {
    await getAnalytics(campaigns[0].id);
  }

  console.log("\nDone! Your Instantly connection is working.");
}

main().catch(console.error);
```

### Quick Test with curl
```bash
set -euo pipefail
# List campaigns
curl -s https://api.instantly.ai/api/v2/campaigns?limit=3 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | jq '.[] | {name, status, id}'

# List email accounts
curl -s https://api.instantly.ai/api/v2/accounts?limit=3 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | jq '.[] | {email, status}'
```

## Output
- List of campaigns with names and statuses
- Email account health overview
- Campaign analytics summary (open rate, reply rate, bounce count)
- Confirmation that Instantly API v2 is reachable

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Bad API key | Regenerate in Settings > Integrations |
| `403 Forbidden` | Missing `campaigns:read` scope | Edit API key scopes |
| Empty campaign list | No campaigns created yet | Create one in the Instantly dashboard first |
| `429 Too Many Requests` | Rate limited | Wait and retry with backoff |

## Resources
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Campaign Endpoints](https://developer.instantly.ai/api/v2/campaign)
- [Account Endpoints](https://developer.instantly.ai/api/v2/account)

## Next Steps
Proceed to `instantly-core-workflow-a` to build a full campaign launch workflow.
