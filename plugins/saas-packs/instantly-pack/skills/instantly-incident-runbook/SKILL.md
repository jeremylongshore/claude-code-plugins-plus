---
name: instantly-incident-runbook
description: |
  Execute Instantly.ai incident response procedures with triage, mitigation, and recovery.
  Use when responding to campaign failures, account health crises,
  deliverability drops, or Instantly API outages.
  Trigger with phrases like "instantly incident", "instantly outage",
  "instantly campaign failed", "instantly emergency", "instantly runbook".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, incident-response, runbook]

---
# Instantly Incident Runbook

## Overview
Structured incident response procedures for Instantly.ai integration failures. Covers campaign pause cascades, account health crises, bounce protect triggers, webhook delivery failures, and API outages.

## Severity Levels

| Severity | Criteria | Response Time | Examples |
|----------|----------|---------------|----------|
| P1 Critical | All campaigns stopped, sending halted | 15 min | All accounts unhealthy, API 5xx |
| P2 High | Multiple campaigns affected | 1 hour | Bounce protect on key campaign, warmup degraded |
| P3 Medium | Single campaign/account issue | 4 hours | One account SMTP failure, webhook delivery issue |
| P4 Low | Non-blocking issue | Next business day | Analytics gap, cosmetic dashboard issue |

## Incident: All Campaigns in Accounts Unhealthy (-1)

### Triage
```typescript
import { InstantlyClient } from "./src/instantly/client";
const client = new InstantlyClient();

async function triageCampaignHealth() {
  console.log("=== P1 TRIAGE: Campaign Health ===\n");

  // 1. Get all campaigns and their statuses
  const campaigns = await client.campaigns.list(100);
  const statusCounts: Record<number, number> = {};
  for (const c of campaigns) {
    statusCounts[c.status] = (statusCounts[c.status] || 0) + 1;
  }
  console.log("Campaign status distribution:", statusCounts);

  const unhealthy = campaigns.filter((c) => c.status === -1);
  console.log(`Unhealthy campaigns: ${unhealthy.length}`);

  // 2. Test ALL account vitals
  const accounts = await client.accounts.list(200);
  const vitals = await client.accounts.testVitals(accounts.map((a) => a.email));

  const broken = (vitals as any[]).filter((v) => v.smtp_status !== "ok" || v.imap_status !== "ok");
  const healthy = (vitals as any[]).filter((v) => v.smtp_status === "ok" && v.imap_status === "ok");

  console.log(`\nAccounts: ${accounts.length} total, ${healthy.length} healthy, ${broken.length} broken`);

  if (broken.length > 0) {
    console.log("\nBroken accounts:");
    for (const v of broken) {
      console.log(`  ${v.email}: SMTP=${v.smtp_status} IMAP=${v.imap_status} DNS=${v.dns_status}`);
    }
  }

  return { unhealthy, broken, healthy };
}
```

### Mitigation
```typescript
async function mitigateBrokenAccounts() {
  const { broken, healthy } = await triageCampaignHealth();

  // Step 1: Pause broken accounts
  for (const v of broken) {
    try {
      await client.accounts.pause(v.email);
      console.log(`Paused broken account: ${v.email}`);
    } catch (e: any) {
      console.log(`Failed to pause ${v.email}: ${e.message}`);
    }
  }

  // Step 2: Check if remaining healthy accounts can carry the load
  if (healthy.length < 3) {
    console.log("\nWARNING: Fewer than 3 healthy accounts. Campaign performance will be degraded.");
    console.log("Action: Fix broken account credentials or add new accounts.");
  }

  // Step 3: After fixing accounts, resume them
  console.log("\nTo resume fixed accounts:");
  for (const v of broken) {
    console.log(`  POST /accounts/${encodeURIComponent(v.email)}/resume`);
  }

  // Step 4: Re-activate unhealthy campaigns
  console.log("\nAfter accounts are fixed, reactivate campaigns:");
  console.log("  POST /campaigns/{id}/activate");
}
```

## Incident: Bounce Protect Triggered (-2)

### Triage & Response
```typescript
async function handleBounceProtect() {
  console.log("=== P2 TRIAGE: Bounce Protect ===\n");

  const campaigns = await client.campaigns.list(100);
  const bounceProtected = campaigns.filter((c) => c.status === -2);

  for (const campaign of bounceProtected) {
    const analytics = await client.campaigns.analytics(campaign.id);
    const bounceRate = ((analytics.emails_bounced / analytics.emails_sent) * 100).toFixed(1);

    console.log(`${campaign.name}: ${bounceRate}% bounce rate`);
    console.log(`  Sent: ${analytics.emails_sent}, Bounced: ${analytics.emails_bounced}`);

    // Check lead quality
    const leads = await client.leads.list({
      campaign: campaign.id,
      limit: 100,
    });
    const bouncedLeads = leads.filter((l) => l.status === -1); // Bounced
    console.log(`  Bounced leads: ${bouncedLeads.length} of ${leads.length} sampled`);
  }

  console.log("\n=== Recovery Steps ===");
  console.log("1. Export remaining leads and verify emails with external service");
  console.log("2. Remove bounced/invalid leads from the campaign");
  console.log("3. Add verified leads back or create new campaign with clean list");
  console.log("4. Re-activate campaign: POST /campaigns/{id}/activate");
  console.log("\n=== Prevention ===");
  console.log("- Set verify_leads_on_import: true on all lead imports");
  console.log("- Use email verification: POST /api/v2/email-verification");
  console.log("- Set allow_risky_contacts: false on campaign");
}
```

## Incident: Webhook Delivery Failure

### Triage & Recovery
```typescript
async function handleWebhookFailure() {
  console.log("=== P3 TRIAGE: Webhook Delivery ===\n");

  // Check webhook status
  const webhooks = await client.webhooks.list();

  for (const w of webhooks as any[]) {
    console.log(`${w.name}: ${w.event_type} -> ${w.target_hook_url}`);
    console.log(`  Status: ${w.status || "active"}`);
  }

  // Check delivery summary
  const summary = await client.request("/webhook-events/summary");
  console.log("\nDelivery summary:", JSON.stringify(summary, null, 2));

  // Check by date
  const byDate = await client.request("/webhook-events/summary-by-date");
  console.log("By date:", JSON.stringify(byDate, null, 2));

  // Resume paused webhooks
  for (const w of webhooks as any[]) {
    if (w.status === "paused") {
      console.log(`\nResuming paused webhook: ${w.name}`);
      try {
        await client.request(`/webhooks/${w.id}/resume`, { method: "POST" });
        console.log("  Resumed successfully");

        // Test delivery
        await client.request(`/webhooks/${w.id}/test`, { method: "POST" });
        console.log("  Test event sent");
      } catch (e: any) {
        console.log(`  Failed: ${e.message}`);
      }
    }
  }
}
```

## Incident: API Rate Limit Storm (429s)

### Response
```typescript
async function handleRateLimitStorm() {
  console.log("=== P2 TRIAGE: Rate Limit Storm ===\n");

  console.log("Immediate actions:");
  console.log("1. Stop all automated API calls (pause cron jobs, workers)");
  console.log("2. Check for runaway loops or misconfigured batch jobs");
  console.log("3. Implement exponential backoff if not already in place");

  // Check background jobs for stuck operations
  const jobs = await client.request<Array<{
    id: string; status: string; timestamp_created: string;
  }>>("/background-jobs?limit=20");

  const stuck = jobs.filter((j) => j.status === "in_progress");
  console.log(`\nBackground jobs in progress: ${stuck.length}`);
  for (const j of stuck) {
    console.log(`  ${j.id}: ${j.status} (created: ${j.timestamp_created})`);
  }

  console.log("\nRate limit guidelines:");
  console.log("  - Most endpoints: standard REST limits");
  console.log("  - GET /emails: 20 req/min (strictest)");
  console.log("  - Implement 2^attempt second backoff on 429");
  console.log("  - Add jitter to prevent thundering herd");
  console.log("  - Use request queue with max concurrency of 3-5");
}
```

## Incident: Warmup Degradation

### Response
```typescript
async function handleWarmupDegradation() {
  console.log("=== P2 TRIAGE: Warmup Degradation ===\n");

  const accounts = await client.accounts.list(200);
  const warmupData = await client.accounts.warmupAnalytics(
    accounts.map((a) => a.email)
  ) as Array<{
    email: string;
    warmup_emails_sent: number;
    warmup_emails_landed_inbox: number;
    warmup_emails_landed_spam: number;
  }>;

  const degraded = warmupData.filter((w) => {
    const sent = w.warmup_emails_sent || 1;
    return (w.warmup_emails_landed_inbox / sent) < 0.8;
  });

  if (degraded.length > 0) {
    console.log(`${degraded.length} accounts with low warmup inbox rate:\n`);
    for (const w of degraded) {
      const rate = ((w.warmup_emails_landed_inbox / (w.warmup_emails_sent || 1)) * 100).toFixed(1);
      console.log(`  ${w.email}: ${rate}% inbox rate (${w.warmup_emails_landed_spam} spam)`);
    }

    console.log("\n=== Recovery ===");
    console.log("1. Pause ALL campaigns using degraded accounts");
    console.log("2. Keep warmup running (don't disable)");
    console.log("3. Reduce campaign daily_limit to 10-20 per account");
    console.log("4. Wait 7-14 days for reputation recovery");
    console.log("5. Re-test inbox rates before re-enabling campaigns");
    console.log("6. Check DNS: SPF, DKIM, DMARC records are correct");
  } else {
    console.log("All accounts have healthy warmup rates (>80% inbox)");
  }
}
```

## Quick Diagnostic Script
```bash
set -euo pipefail
echo "=== Instantly Incident Diagnostic ==="
echo "Time: $(date -u)"
echo

echo "--- Campaign Status ---"
curl -s https://api.instantly.ai/api/v2/campaigns?limit=100 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq 'group_by(.status) | map({status: .[0].status, count: length})'

echo "--- Account Vitals ---"
EMAILS=$(curl -s https://api.instantly.ai/api/v2/accounts?limit=50 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | jq -r '[.[].email] | join(",")')
echo "Accounts: $EMAILS"

echo "--- Webhooks ---"
curl -s https://api.instantly.ai/api/v2/webhooks?limit=20 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '[.[] | {name, event_type, status}]'
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Can't reach API during incident | Instantly outage | Check status.instantly.ai, wait |
| Can't pause accounts | `403` scope error | Use dashboard as fallback |
| Runbook script rate-limited | Too many diagnostic calls | Space out requests, use backoff |

## Resources
- [Instantly Help Center](https://help.instantly.ai)
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Instantly Status Page](https://status.instantly.ai)

## Next Steps
For data handling and compliance, see `instantly-data-handling`.
