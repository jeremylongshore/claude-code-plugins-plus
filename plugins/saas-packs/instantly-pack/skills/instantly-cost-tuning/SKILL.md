---
name: instantly-cost-tuning
description: |
  Optimize Instantly.ai costs through plan selection, account management, and usage monitoring.
  Use when analyzing Instantly billing, reducing per-campaign costs,
  or choosing between Instantly pricing tiers.
  Trigger with phrases like "instantly cost", "instantly pricing",
  "instantly billing", "reduce instantly cost", "instantly plan comparison".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, cost-optimization, pricing]

---
# Instantly Cost Tuning

## Overview
Optimize Instantly.ai costs by choosing the right plan, managing email account utilization, monitoring campaign efficiency, and reducing wasted sends. Instantly's pricing is based on sending accounts and features, not per-email — so the key to cost efficiency is maximizing the value per account.

## Instantly Pricing Tiers (2026)

| Plan | Monthly | Annual (per mo) | Email Accounts | Warmup | API Access | Webhooks |
|------|---------|----------------|----------------|--------|------------|----------|
| Growth | $30 | $24 | 5 | Included | v2 (limited) | No |
| Hypergrowth | $97.95 | $77.60 | 25 | Included | v2 (full) | Yes |
| Light Speed | $358.30 | $286.30 | 500+ | Included | v2 (full) | Yes |

**Key cost decision:** You need **Hypergrowth** ($97.95/mo) minimum for full API v2 access and webhooks.

## Instructions

### Step 1: Audit Current Account Utilization
```typescript
import { instantly } from "./src/instantly";

async function auditAccountUtilization() {
  // Get all accounts
  const accounts = await instantly<Array<{
    email: string;
    status: number;
    daily_limit: number | null;
    warmup_status: string;
  }>>("/accounts?limit=200");

  // Get daily analytics for the last 7 days
  const endDate = new Date().toISOString().split("T")[0];
  const startDate = new Date(Date.now() - 7 * 86400000).toISOString().split("T")[0];
  const dailyAnalytics = await instantly<Array<{
    email: string;
    date: string;
    emails_sent: number;
  }>>(`/accounts/analytics/daily?start_date=${startDate}&end_date=${endDate}&emails=${accounts.map(a => a.email).join(",")}`);

  // Calculate utilization
  console.log("=== Account Utilization Audit ===\n");

  let totalCapacity = 0;
  let totalSent = 0;
  const underutilized: string[] = [];

  for (const account of accounts) {
    const sent = dailyAnalytics
      .filter((d) => d.email === account.email)
      .reduce((sum, d) => sum + d.emails_sent, 0);
    const dailyAvg = sent / 7;
    const capacity = account.daily_limit || 50;
    const utilization = (dailyAvg / capacity) * 100;

    totalCapacity += capacity * 7;
    totalSent += sent;

    if (utilization < 20) {
      underutilized.push(account.email);
    }

    console.log(`${account.email}: ${dailyAvg.toFixed(0)}/day of ${capacity} limit (${utilization.toFixed(0)}% utilized)`);
  }

  console.log(`\nOverall: ${totalSent} sent of ${totalCapacity} capacity (${((totalSent / totalCapacity) * 100).toFixed(0)}%)`);
  console.log(`Underutilized accounts (<20%): ${underutilized.length}`);
  if (underutilized.length > 0) {
    console.log(`Consider removing: ${underutilized.join(", ")}`);
  }
}
```

### Step 2: Campaign Efficiency Analysis
```typescript
async function campaignEfficiency() {
  const campaigns = await instantly<Array<{ id: string; name: string; status: number }>>(
    "/campaigns?limit=100"
  );

  console.log("=== Campaign Efficiency ===\n");

  for (const campaign of campaigns.filter((c) => c.status === 1 || c.status === 3)) {
    const analytics = await instantly<{
      campaign_name: string;
      total_leads: number;
      emails_sent: number;
      emails_replied: number;
      emails_bounced: number;
      emails_opened: number;
    }>(`/campaigns/analytics?id=${campaign.id}`);

    if (analytics.emails_sent === 0) continue;

    const replyRate = (analytics.emails_replied / analytics.emails_sent * 100).toFixed(1);
    const bounceRate = (analytics.emails_bounced / analytics.emails_sent * 100).toFixed(1);
    const openRate = (analytics.emails_opened / analytics.emails_sent * 100).toFixed(1);

    // Cost per reply (assuming $97.95/mo plan, 25 accounts, ~30 days)
    const costPerEmail = 97.95 / (25 * 50 * 30); // ~$0.0026 per email
    const costPerReply = analytics.emails_replied > 0
      ? ((analytics.emails_sent * costPerEmail) / analytics.emails_replied).toFixed(2)
      : "N/A";

    console.log(`${analytics.campaign_name}`);
    console.log(`  Sent: ${analytics.emails_sent} | Open: ${openRate}% | Reply: ${replyRate}% | Bounce: ${bounceRate}%`);
    console.log(`  Est. cost/reply: $${costPerReply}`);

    // Warnings
    if (parseFloat(bounceRate) > 5) {
      console.log(`  WARNING: High bounce rate — clean lead list`);
    }
    if (parseFloat(replyRate) < 1) {
      console.log(`  WARNING: Low reply rate — review email copy and targeting`);
    }
    console.log();
  }
}
```

### Step 3: Plan Right-Sizing
```typescript
async function recommendPlan() {
  const accounts = await instantly<Array<{ email: string }>>(
    "/accounts?limit=200"
  );
  const webhooks = await instantly<Array<{ id: string }>>(
    "/webhooks?limit=50"
  );

  const accountCount = accounts.length;
  const usesWebhooks = webhooks.length > 0;

  console.log("=== Plan Recommendation ===\n");
  console.log(`Active accounts: ${accountCount}`);
  console.log(`Uses webhooks: ${usesWebhooks}`);

  if (accountCount <= 5 && !usesWebhooks) {
    console.log("\nRecommended: Growth ($30/mo)");
    console.log("  You're within the 5-account limit and don't need webhooks.");
  } else if (accountCount <= 25) {
    console.log("\nRecommended: Hypergrowth ($97.95/mo)");
    console.log("  Full API v2 access, webhooks, and 25 accounts.");
  } else {
    console.log("\nRecommended: Light Speed ($358.30/mo)");
    console.log(`  You have ${accountCount} accounts — need the 500+ tier.`);
  }

  // Check billing details via API
  try {
    const billing = await instantly("/workspace-billing/plan-details");
    console.log("\nCurrent plan:", JSON.stringify(billing, null, 2));
  } catch {
    console.log("\n(Could not fetch billing details — scope may be missing)");
  }
}
```

### Step 4: Cost Reduction Strategies
```typescript
async function applyOptimizations() {
  console.log("=== Cost Optimization Actions ===\n");

  // 1. Pause unused accounts to free up slots
  const accounts = await instantly<Array<{
    email: string; status: number; daily_limit: number | null;
  }>>("/accounts?limit=200");

  for (const account of accounts) {
    if (account.status === 0) { // inactive
      console.log(`Consider removing inactive account: ${account.email}`);
    }
  }

  // 2. Clean up completed campaigns
  const campaigns = await instantly<Array<{ id: string; name: string; status: number }>>(
    "/campaigns?limit=100"
  );
  const completed = campaigns.filter((c) => c.status === 3);
  console.log(`\nCompleted campaigns to archive: ${completed.length}`);

  // 3. Check for duplicate leads across campaigns
  // (Leads in multiple campaigns waste sends)
  console.log("\nDuplicate prevention:");
  console.log("  Use skip_if_in_workspace: true on all lead imports");
  console.log("  Use skip_if_in_campaign: true for campaign-specific dedup");

  // 4. Verify email quality before import
  console.log("\nEmail verification:");
  console.log("  POST /api/v2/email-verification — verify before importing");
  console.log("  Set verify_leads_on_import: true in lead creation");

  // 5. Block list maintenance
  const blocklist = await instantly<unknown[]>("/block-lists-entries?limit=1");
  console.log(`\nBlock list entries: ${blocklist.length}+`);
  console.log("  Add competitor domains, role-based emails (info@, admin@)");
  console.log("  Add internal domains to prevent self-emailing");
}
```

## Cost Optimization Checklist
- [ ] Right-sized plan for account count and feature needs
- [ ] Underutilized accounts identified and removed
- [ ] Duplicate leads prevented with `skip_if_in_workspace`
- [ ] Lead emails verified before import
- [ ] Block list populated with competitor/internal domains
- [ ] Campaigns with >5% bounce rate cleaned up
- [ ] Daily limits tuned per account (not over-provisioned)
- [ ] Completed campaigns archived
- [ ] Warmup-only accounts tracked separately

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Can't access billing API | Missing workspace scope | Use dashboard instead |
| Analytics return empty | Campaign too new | Wait 24h for data |
| Account count exceeds plan | Plan limits reached | Upgrade or remove accounts |

## Resources
- [Instantly Pricing](https://instantly.ai/pricing)
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Workspace Billing API](https://developer.instantly.ai/api/v2/schemas)

## Next Steps
For reference architecture, see `instantly-reference-architecture`.
