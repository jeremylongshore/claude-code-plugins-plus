---
name: instantly-prod-checklist
description: |
  Execute Instantly.ai production launch checklist and pre-flight validation.
  Use when deploying Instantly integrations to production, launching first campaign,
  or auditing production readiness.
  Trigger with phrases like "instantly production", "instantly launch checklist",
  "instantly go-live", "instantly pre-flight", "instantly prod ready".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, production, deployment]

---
# Instantly Production Checklist

## Overview
Pre-flight checklist for launching Instantly cold email campaigns in production. Covers account warmup verification, deliverability testing, lead list hygiene, campaign configuration, webhook setup, and monitoring. Skip any step that doesn't apply to your use case.

## Prerequisites
- Completed `instantly-install-auth` setup
- Email accounts connected and warmed up (minimum 14 days recommended)
- Lead list prepared with verified emails

## Production Launch Checklist

### Phase 1: Account Health (2-4 weeks before launch)

```typescript
import { instantly } from "./src/instantly";

async function phase1AccountHealth() {
  console.log("=== Phase 1: Account Health ===\n");

  // 1. Verify all accounts have healthy SMTP/IMAP
  const accounts = await instantly<Array<{ email: string }>>(
    "/accounts?limit=100"
  );
  const vitals = await instantly("/accounts/test/vitals", {
    method: "POST",
    body: JSON.stringify({ accounts: accounts.map((a) => a.email) }),
  }) as Array<{ email: string; smtp_status: string; imap_status: string }>;

  const broken = vitals.filter((v) => v.smtp_status !== "ok" || v.imap_status !== "ok");
  console.log(`Accounts: ${accounts.length} total, ${broken.length} broken`);
  if (broken.length > 0) {
    console.log("FIX THESE FIRST:");
    broken.forEach((v) => console.log(`  ${v.email}: SMTP=${v.smtp_status} IMAP=${v.imap_status}`));
    return false;
  }

  // 2. Verify warmup is active and healthy
  const warmup = await instantly("/accounts/warmup-analytics", {
    method: "POST",
    body: JSON.stringify({ emails: accounts.map((a) => a.email) }),
  }) as Array<{ email: string; warmup_emails_landed_inbox: number; warmup_emails_sent: number }>;

  for (const w of warmup) {
    const inboxRate = (w.warmup_emails_landed_inbox / (w.warmup_emails_sent || 1)) * 100;
    const healthy = inboxRate >= 80;
    console.log(`  ${w.email}: inbox rate ${inboxRate.toFixed(1)}% ${healthy ? "OK" : "LOW — extend warmup"}`);
  }

  // 3. Check daily limits are set
  const acctDetails = await instantly<Array<{ email: string; daily_limit: number | null }>>(
    "/accounts?limit=100"
  );
  const noLimit = acctDetails.filter((a) => !a.daily_limit);
  if (noLimit.length > 0) {
    console.log(`\nWARNING: ${noLimit.length} accounts have no daily limit set`);
  }

  return broken.length === 0;
}
```

### Phase 2: Campaign Configuration (1 week before)

```typescript
async function phase2CampaignConfig(campaignId: string) {
  console.log("\n=== Phase 2: Campaign Configuration ===\n");
  const campaign = await instantly<{
    name: string;
    sequences: Array<{ steps: Array<{ variants: Array<{ subject: string; body: string }> }> }>;
    campaign_schedule: { schedules: any[] };
    daily_limit: number | null;
    stop_on_reply: boolean;
    link_tracking: boolean;
    open_tracking: boolean;
    stop_on_auto_reply: boolean;
    email_gap: number;
  }>(`/campaigns/${campaignId}`);

  const checks = [
    { label: "Has sequences", pass: campaign.sequences?.length > 0 },
    { label: "Has email steps", pass: campaign.sequences?.[0]?.steps?.length > 0 },
    { label: "Has schedule", pass: campaign.campaign_schedule?.schedules?.length > 0 },
    { label: "Stop on reply enabled", pass: campaign.stop_on_reply === true },
    { label: "Link tracking disabled", pass: campaign.link_tracking === false },
    { label: "Open tracking enabled", pass: campaign.open_tracking === true },
    { label: "Daily limit set", pass: (campaign.daily_limit ?? 0) > 0 },
    { label: "Email gap >= 60s", pass: (campaign.email_gap ?? 0) >= 60 },
  ];

  let allPass = true;
  for (const check of checks) {
    console.log(`  ${check.pass ? "PASS" : "FAIL"}: ${check.label}`);
    if (!check.pass) allPass = false;
  }

  // Check A/B variants
  const step1 = campaign.sequences?.[0]?.steps?.[0];
  if (step1) {
    console.log(`  INFO: Step 1 has ${step1.variants.length} variant(s)`);
  }

  return allPass;
}
```

### Phase 3: Lead List Hygiene

```typescript
async function phase3LeadHygiene(campaignId: string) {
  console.log("\n=== Phase 3: Lead List Hygiene ===\n");

  // Check lead count
  const analytics = await instantly<{ total_leads: number }>(
    `/campaigns/analytics?id=${campaignId}`
  );
  console.log(`Total leads: ${analytics.total_leads}`);

  // Check block list
  const blocklist = await instantly<Array<{ bl_value: string }>>(
    "/block-lists-entries?limit=10"
  );
  console.log(`Block list entries: ${blocklist.length}+`);

  // Verify no internal domains are in lead list
  console.log("\nChecklist:");
  console.log("  [ ] Leads verified with email verification service");
  console.log("  [ ] Company domains in block list (your own + competitors)");
  console.log("  [ ] No role-based emails (info@, admin@, support@)");
  console.log("  [ ] Personalization variables populated (firstName, companyName)");
  console.log("  [ ] Test lead (your own email) included for QA");
}
```

### Phase 4: Test Email & Webhook Verification

```typescript
async function phase4TestAndWebhooks(campaignId: string) {
  console.log("\n=== Phase 4: Test & Webhooks ===\n");

  // Send test email
  const accounts = await instantly<Array<{ email: string }>>(
    "/accounts?limit=1"
  );
  if (accounts.length > 0) {
    await instantly("/emails/test", {
      method: "POST",
      body: JSON.stringify({
        eaccount: accounts[0].email,
        to_address_email_list: [process.env.TEST_EMAIL || "test@yourdomain.com"],
        subject: "Production Test — Instantly Integration",
        body: "This is a test email from the Instantly integration. If you received this, the setup is working correctly.",
      }),
    });
    console.log("Test email sent from:", accounts[0].email);
  }

  // Verify webhooks are registered
  const webhooks = await instantly<Array<{
    name: string; event_type: string; target_hook_url: string;
  }>>("/webhooks?limit=50");
  console.log(`\nWebhooks registered: ${webhooks.length}`);
  for (const w of webhooks) {
    console.log(`  ${w.name}: ${w.event_type} -> ${w.target_hook_url}`);
  }

  // Test webhook delivery
  if (webhooks.length > 0) {
    for (const w of webhooks.slice(0, 2) as Array<{ id: string; name: string }>) {
      try {
        await instantly(`/webhooks/${w.id}/test`, { method: "POST" });
        console.log(`  Tested: ${w.name} — check your endpoint`);
      } catch (e: any) {
        console.log(`  FAILED: ${w.name} — ${e.message}`);
      }
    }
  }
}
```

### Phase 5: Launch & Monitor

```typescript
async function phase5Launch(campaignId: string) {
  console.log("\n=== Phase 5: Launch ===\n");

  // Final confirmation
  const campaign = await instantly<{ name: string; status: number }>(
    `/campaigns/${campaignId}`
  );
  console.log(`Campaign: ${campaign.name} (status: ${campaign.status})`);

  // Activate
  await instantly(`/campaigns/${campaignId}/activate`, { method: "POST" });
  console.log("Campaign ACTIVATED");

  // Verify sending status
  const status = await instantly(`/campaigns/${campaignId}/sending-status`);
  console.log("Sending status:", JSON.stringify(status));

  // Monitor for first hour
  console.log("\nPost-launch monitoring:");
  console.log("  [ ] Check analytics after 1 hour for send activity");
  console.log("  [ ] Monitor bounce rate (should be <3%)");
  console.log("  [ ] Verify webhook events are arriving");
  console.log("  [ ] Check Unibox for replies");
}

// Run full checklist
async function main() {
  const campaignId = process.env.CAMPAIGN_ID!;
  const accountsOk = await phase1AccountHealth();
  if (!accountsOk) { console.log("\nFix account issues before proceeding."); return; }
  const configOk = await phase2CampaignConfig(campaignId);
  await phase3LeadHygiene(campaignId);
  await phase4TestAndWebhooks(campaignId);
  if (configOk) await phase5Launch(campaignId);
}

main().catch(console.error);
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Campaign won't activate | Missing sequences/accounts/leads | Run Phase 2 checks |
| Test email not received | Account SMTP broken | Run vitals test |
| Webhook test fails | Target URL unreachable | Verify endpoint is public HTTPS |
| High bounce rate post-launch | Unverified leads | Pause campaign, clean list |

## Resources
- [Instantly Campaign Options](https://help.instantly.ai/en/articles/6222396-campaign-options)
- [Instantly Quick Start](https://help.instantly.ai/en/articles/6451970-quick-start-guide-all-in-one)
- [Instantly API v2 Docs](https://developer.instantly.ai/)

## Next Steps
For version migration, see `instantly-upgrade-migration`.
