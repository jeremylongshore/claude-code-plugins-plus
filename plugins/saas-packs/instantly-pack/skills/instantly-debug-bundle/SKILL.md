---
name: instantly-debug-bundle
description: |
  Collect Instantly.ai debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or auditing campaign/account state.
  Trigger with phrases like "instantly debug", "instantly support ticket",
  "instantly diagnostic", "instantly audit", "collect instantly evidence".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, debugging, support]

---
# Instantly Debug Bundle

## Overview
Collect a comprehensive debug bundle from your Instantly workspace: campaign state, account health, warmup metrics, lead stats, webhook delivery status, and recent errors. Output is a JSON report suitable for support tickets or internal audits.

## Prerequisites
- Completed `instantly-install-auth` setup
- API key with `all:read` scope (or individual read scopes for each resource)

## Instructions

### Step 1: Collect Full Debug Bundle
```typescript
import { instantly } from "./src/instantly";
import { writeFileSync } from "fs";

interface DebugBundle {
  timestamp: string;
  workspace: unknown;
  campaigns: unknown[];
  accounts: unknown[];
  warmup_analytics: unknown[];
  webhooks: unknown[];
  webhook_event_summary: unknown;
  background_jobs: unknown[];
  lead_count_by_campaign: Record<string, number>;
  errors: string[];
}

async function collectDebugBundle(): Promise<DebugBundle> {
  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    workspace: null,
    campaigns: [],
    accounts: [],
    warmup_analytics: [],
    webhooks: [],
    webhook_event_summary: null,
    background_jobs: [],
    lead_count_by_campaign: {},
    errors: [],
  };

  // Workspace info
  try {
    bundle.workspace = await instantly("/workspaces/current");
  } catch (e: any) {
    bundle.errors.push(`workspace: ${e.message}`);
  }

  // All campaigns with status
  try {
    bundle.campaigns = await instantly("/campaigns?limit=100");
  } catch (e: any) {
    bundle.errors.push(`campaigns: ${e.message}`);
  }

  // All email accounts
  try {
    bundle.accounts = await instantly("/accounts?limit=100");
  } catch (e: any) {
    bundle.errors.push(`accounts: ${e.message}`);
  }

  // Warmup analytics for all accounts
  try {
    const accounts = bundle.accounts as Array<{ email: string }>;
    if (accounts.length > 0) {
      bundle.warmup_analytics = await instantly("/accounts/warmup-analytics", {
        method: "POST",
        body: JSON.stringify({ emails: accounts.map((a) => a.email) }),
      });
    }
  } catch (e: any) {
    bundle.errors.push(`warmup_analytics: ${e.message}`);
  }

  // Webhooks
  try {
    bundle.webhooks = await instantly("/webhooks?limit=50");
  } catch (e: any) {
    bundle.errors.push(`webhooks: ${e.message}`);
  }

  // Webhook event delivery summary
  try {
    bundle.webhook_event_summary = await instantly("/webhook-events/summary");
  } catch (e: any) {
    bundle.errors.push(`webhook_events: ${e.message}`);
  }

  // Recent background jobs
  try {
    bundle.background_jobs = await instantly("/background-jobs?limit=20");
  } catch (e: any) {
    bundle.errors.push(`background_jobs: ${e.message}`);
  }

  // Lead counts per campaign
  for (const c of (bundle.campaigns as Array<{ id: string; name: string }>).slice(0, 10)) {
    try {
      const analytics = await instantly<{ total_leads: number }>(
        `/campaigns/analytics?id=${c.id}`
      );
      bundle.lead_count_by_campaign[c.name] = analytics.total_leads;
    } catch {
      bundle.lead_count_by_campaign[c.name] = -1; // error
    }
  }

  return bundle;
}
```

### Step 2: Save and Analyze
```typescript
async function main() {
  console.log("Collecting Instantly debug bundle...\n");
  const bundle = await collectDebugBundle();

  // Save to file
  const filename = `instantly-debug-${Date.now()}.json`;
  writeFileSync(filename, JSON.stringify(bundle, null, 2));
  console.log(`Saved debug bundle to ${filename}`);

  // Print summary
  const campaigns = bundle.campaigns as Array<{ name: string; status: number }>;
  const accounts = bundle.accounts as Array<{ email: string; status: number }>;

  console.log("\n=== Debug Summary ===");
  console.log(`Campaigns: ${campaigns.length}`);
  console.log(`  Active: ${campaigns.filter((c) => c.status === 1).length}`);
  console.log(`  Paused: ${campaigns.filter((c) => c.status === 2).length}`);
  console.log(`  Unhealthy: ${campaigns.filter((c) => c.status === -1).length}`);
  console.log(`  Bounce Protected: ${campaigns.filter((c) => c.status === -2).length}`);

  console.log(`\nAccounts: ${accounts.length}`);
  console.log(`Webhooks: ${(bundle.webhooks as any[]).length}`);
  console.log(`Background Jobs: ${(bundle.background_jobs as any[]).length}`);

  if (bundle.errors.length > 0) {
    console.log(`\nErrors during collection:`);
    bundle.errors.forEach((e) => console.log(`  - ${e}`));
  }
}

main().catch(console.error);
```

### Step 3: Account Vitals Deep Dive
```typescript
async function accountVitalsDiagnostic() {
  const accounts = await instantly<Array<{ email: string }>>(
    "/accounts?limit=100"
  );

  const vitals = await instantly("/accounts/test/vitals", {
    method: "POST",
    body: JSON.stringify({ accounts: accounts.map((a) => a.email) }),
  }) as Array<{ email: string; smtp_status: string; imap_status: string; dns_status: string }>;

  console.log("\n=== Account Vitals ===");
  const broken = vitals.filter((v) => v.smtp_status !== "ok" || v.imap_status !== "ok");
  const healthy = vitals.filter((v) => v.smtp_status === "ok" && v.imap_status === "ok");

  console.log(`Healthy: ${healthy.length} | Broken: ${broken.length}`);
  for (const v of broken) {
    console.log(`  BROKEN: ${v.email} — SMTP=${v.smtp_status} IMAP=${v.imap_status} DNS=${v.dns_status}`);
  }
}
```

### Step 4: Curl-Based Quick Diagnostic
```bash
set -euo pipefail
echo "=== Instantly Quick Diagnostic ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo -e "\n--- Campaigns ---"
curl -s https://api.instantly.ai/api/v2/campaigns?limit=100 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '[.[] | {name, status, id}] | length as $total |
    {total: $total,
     active: [.[] | select(.status==1)] | length,
     paused: [.[] | select(.status==2)] | length,
     unhealthy: [.[] | select(.status==-1)] | length}'

echo -e "\n--- Accounts ---"
curl -s https://api.instantly.ai/api/v2/accounts?limit=100 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq 'length as $total | {total: $total, accounts: [.[:5][] | {email, status}]}'

echo -e "\n--- Webhooks ---"
curl -s https://api.instantly.ai/api/v2/webhooks?limit=50 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '[.[] | {name, event_type, target_hook_url}]'

echo -e "\n--- Recent Background Jobs ---"
curl -s https://api.instantly.ai/api/v2/background-jobs?limit=5 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '[.[] | {id, status, timestamp_created}]'
```

## Output
- `instantly-debug-{timestamp}.json` — full debug bundle
- Console summary with campaign/account/webhook counts
- Broken account identification with SMTP/IMAP status
- Errors collected during diagnostic

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `403` on workspace endpoint | Key missing workspace scope | Add `all:read` scope to API key |
| Empty warmup analytics | No accounts have warmup enabled | Enable warmup first |
| Partial bundle | Some endpoints failed | Check `errors` array in bundle output |
| Large bundle (>10MB) | 100+ campaigns and accounts | Reduce limits or collect per-campaign |

## Resources
- [Instantly Help Center](https://help.instantly.ai)
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Background Jobs API](https://developer.instantly.ai/api/v2/backgroundjob)

## Next Steps
For error resolution patterns, see `instantly-common-errors`.
