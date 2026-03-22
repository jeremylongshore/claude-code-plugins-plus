---
name: instantly-core-workflow-b
description: |
  Manage Instantly.ai email account warmup, analytics, and deliverability.
  Use when enabling warmup, monitoring sender reputation, pulling analytics,
  or troubleshooting deliverability issues.
  Trigger with phrases like "instantly warmup", "instantly analytics",
  "email warmup instantly", "instantly deliverability", "instantly account health".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, workflow, warmup, analytics, deliverability]

---
# Instantly Core Workflow B: Warmup & Analytics Pipeline

## Overview
Manage the email account warmup lifecycle and campaign analytics. Warmup builds sender reputation through controlled email exchanges across Instantly's 4.2M+ account network before you start cold outreach. This workflow covers enabling warmup, monitoring warmup health, pulling campaign analytics, and daily send tracking.

## Prerequisites
- Completed `instantly-install-auth` setup
- Email accounts connected in Instantly (IMAP/SMTP or Google/Microsoft OAuth)
- API key with `accounts:update` and `campaigns:read` scopes

## Instructions

### Step 1: Enable Warmup on Email Accounts
```typescript
import { instantly } from "./src/instantly";

// Enable warmup — triggers a background job
async function enableWarmup(emails: string[]) {
  const job = await instantly<{ id: string; status: string }>(
    "/accounts/warmup/enable",
    {
      method: "POST",
      body: JSON.stringify({ emails }),
    }
  );

  console.log(`Warmup enable job started: ${job.id} (status: ${job.status})`);

  // Poll background job until complete
  let result = job;
  while (result.status !== "completed" && result.status !== "failed") {
    await new Promise((r) => setTimeout(r, 2000));
    result = await instantly<{ id: string; status: string }>(
      `/background-jobs/${job.id}`
    );
  }

  console.log(`Warmup job ${result.status}`);
  return result;
}

// Enable for specific accounts
await enableWarmup(["outreach1@yourdomain.com", "outreach2@yourdomain.com"]);

// Or enable for ALL accounts at once
await instantly("/accounts/warmup/enable", {
  method: "POST",
  body: JSON.stringify({ include_all_emails: true }),
});
```

### Step 2: Configure Warmup Settings
```typescript
// PATCH account to tune warmup parameters
async function configureWarmup(email: string) {
  await instantly(`/accounts/${encodeURIComponent(email)}`, {
    method: "PATCH",
    body: JSON.stringify({
      warmup: {
        limit: 40,           // max warmup emails per day
        increment: "2",      // daily limit increment (0-4 or "disabled")
        advanced: {
          open_rate: 0.95,       // target open rate for warmup
          reply_rate: 0.1,       // target reply rate
          spam_save_rate: 0.02,  // rate of rescuing from spam
          read_emulation: true,  // simulate reading behavior
          weekday_only: true,    // warmup only on weekdays
          warm_ctd: false,       // custom tracking domain warmup
        },
      },
      daily_limit: 50,      // max campaign emails per day
      enable_slow_ramp: true,
    }),
  });

  console.log(`Warmup configured for ${email}`);
}
```

### Step 3: Monitor Warmup Health
```typescript
interface WarmupAnalytics {
  email: string;
  warmup_emails_sent: number;
  warmup_emails_received: number;
  warmup_emails_landed_inbox: number;
  warmup_emails_landed_spam: number;
  warmup_emails_saved_from_spam: number;
  warmup_health_score: number;
}

async function checkWarmupHealth(emails: string[]) {
  const analytics = await instantly<WarmupAnalytics[]>(
    "/accounts/warmup-analytics",
    {
      method: "POST",
      body: JSON.stringify({ emails }),
    }
  );

  console.log("\nWarmup Health Report:");
  for (const a of analytics) {
    const inboxRate = a.warmup_emails_landed_inbox /
      (a.warmup_emails_sent || 1) * 100;
    console.log(`${a.email}`);
    console.log(`  Sent: ${a.warmup_emails_sent} | Inbox: ${a.warmup_emails_landed_inbox} | Spam: ${a.warmup_emails_landed_spam}`);
    console.log(`  Inbox Rate: ${inboxRate.toFixed(1)}% | Health: ${a.warmup_health_score}`);
  }
  return analytics;
}
```

### Step 4: Pull Campaign Analytics
```typescript
// Aggregate analytics for one or more campaigns
async function getCampaignAnalytics(campaignIds: string[]) {
  const params = campaignIds.map((id) => `ids=${id}`).join("&");
  const data = await instantly<Array<{
    campaign_id: string;
    campaign_name: string;
    total_leads: number;
    leads_contacted: number;
    emails_sent: number;
    emails_opened: number;
    emails_replied: number;
    emails_bounced: number;
  }>>(`/campaigns/analytics?${params}`);

  for (const c of data) {
    const openRate = ((c.emails_opened / c.emails_sent) * 100).toFixed(1);
    const replyRate = ((c.emails_replied / c.emails_sent) * 100).toFixed(1);
    const bounceRate = ((c.emails_bounced / c.emails_sent) * 100).toFixed(1);

    console.log(`\n${c.campaign_name}`);
    console.log(`  Leads: ${c.total_leads} total, ${c.leads_contacted} contacted`);
    console.log(`  Open: ${openRate}% | Reply: ${replyRate}% | Bounce: ${bounceRate}%`);
  }
}

// Daily breakdown
async function getDailyAnalytics(campaignId: string) {
  const daily = await instantly<Array<{
    date: string; emails_sent: number; emails_opened: number; emails_replied: number;
  }>>(`/campaigns/analytics/daily?campaign_id=${campaignId}&start_date=2026-03-01&end_date=2026-03-31`);

  for (const day of daily) {
    console.log(`  ${day.date}: sent=${day.emails_sent} opened=${day.emails_opened} replied=${day.emails_replied}`);
  }
}

// Step-level analytics — which sequence step performs best
async function getStepAnalytics(campaignId: string) {
  const steps = await instantly<Array<{
    step_number: number; emails_sent: number; emails_opened: number; emails_replied: number;
  }>>(`/campaigns/analytics/steps?campaign_id=${campaignId}`);

  for (const s of steps) {
    console.log(`  Step ${s.step_number}: sent=${s.emails_sent} opened=${s.emails_opened} replied=${s.emails_replied}`);
  }
}
```

### Step 5: Test Account Vitals
```typescript
async function testAccountVitals(emails: string[]) {
  const vitals = await instantly<Array<{
    email: string; smtp_status: string; imap_status: string; dns_status: string;
  }>>("/accounts/test/vitals", {
    method: "POST",
    body: JSON.stringify({ accounts: emails }),
  });

  for (const v of vitals) {
    const ok = v.smtp_status === "ok" && v.imap_status === "ok";
    console.log(`${v.email}: SMTP=${v.smtp_status} IMAP=${v.imap_status} DNS=${v.dns_status} ${ok ? "HEALTHY" : "FIX NEEDED"}`);
  }
}
```

## Key API Endpoints Used
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/accounts/warmup/enable` | Start warmup (background job) |
| `POST` | `/accounts/warmup/disable` | Stop warmup |
| `POST` | `/accounts/warmup-analytics` | Warmup metrics per account |
| `POST` | `/accounts/test/vitals` | Test SMTP/IMAP/DNS health |
| `PATCH` | `/accounts/{email}` | Configure warmup settings |
| `GET` | `/accounts/analytics/daily` | Daily send counts per account |
| `GET` | `/campaigns/analytics` | Aggregate campaign metrics |
| `GET` | `/campaigns/analytics/daily` | Daily campaign breakdown |
| `GET` | `/campaigns/analytics/steps` | Per-step performance |
| `GET` | `/background-jobs/{id}` | Poll async job status |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Warmup not starting | SMTP/IMAP credentials invalid | Run vitals test, fix credentials |
| Low inbox rate (<80%) | Sender reputation damaged | Pause campaigns, extend warmup |
| `422` on warmup enable | Account already warming | Check state with `GET /accounts/{email}` |
| Missing analytics data | Campaign too new (<24h) | Wait for data to populate |
| Background job `failed` | Invalid email in batch | Retry failed emails individually |

## Resources
- [Instantly Email Warmup](https://instantly.ai/email-warmup)
- [Account Endpoints](https://developer.instantly.ai/api/v2/account)
- [Analytics Endpoints](https://developer.instantly.ai/api/v2/analytics)

## Next Steps
For lead management and list operations, see `instantly-data-handling`.
