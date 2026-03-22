---
name: instantly-observability
description: |
  Set up monitoring, alerting, and dashboards for Instantly.ai integrations.
  Use when implementing campaign health monitoring, account health alerts,
  or building analytics dashboards from Instantly data.
  Trigger with phrases like "instantly monitoring", "instantly dashboard",
  "instantly alerts", "instantly observability", "monitor instantly campaigns".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, observability, monitoring, alerting]

---
# Instantly Observability

## Overview
Build monitoring and alerting for Instantly integrations. Covers campaign health checks, account warmup monitoring, webhook delivery tracking, deliverability alerts, and performance dashboards. Uses Instantly API v2 analytics endpoints combined with webhook events for real-time awareness.

## Prerequisites
- Completed `instantly-install-auth` setup
- API key with `campaigns:read`, `accounts:read`, and `all:read` scopes
- Notification channel (Slack, email, PagerDuty, etc.)

## Instructions

### Step 1: Campaign Health Monitor
```typescript
import { InstantlyClient } from "./src/instantly/client";

const client = new InstantlyClient();

interface HealthCheck {
  check: string;
  status: "ok" | "warning" | "critical";
  message: string;
}

async function campaignHealthCheck(): Promise<HealthCheck[]> {
  const checks: HealthCheck[] = [];
  const campaigns = await client.campaigns.list(100);

  for (const campaign of campaigns.filter((c) => c.status === 1)) { // Active only
    const analytics = await client.campaigns.analytics(campaign.id);
    const sent = analytics.emails_sent || 1;

    // Bounce rate check (critical if > 5%)
    const bounceRate = (analytics.emails_bounced / sent) * 100;
    if (bounceRate > 5) {
      checks.push({
        check: `bounce_rate:${campaign.name}`,
        status: "critical",
        message: `Bounce rate ${bounceRate.toFixed(1)}% exceeds 5% threshold. Campaign may be auto-paused.`,
      });
    } else if (bounceRate > 3) {
      checks.push({
        check: `bounce_rate:${campaign.name}`,
        status: "warning",
        message: `Bounce rate ${bounceRate.toFixed(1)}% approaching 5% threshold.`,
      });
    }

    // Reply rate check (warning if < 1%)
    const replyRate = (analytics.emails_replied / sent) * 100;
    if (replyRate < 1 && sent > 100) {
      checks.push({
        check: `reply_rate:${campaign.name}`,
        status: "warning",
        message: `Reply rate ${replyRate.toFixed(1)}% is below 1% after ${sent} sends. Review email copy.`,
      });
    }

    // Open rate check (warning if < 20%)
    const openRate = (analytics.emails_opened / sent) * 100;
    if (openRate < 20 && sent > 100) {
      checks.push({
        check: `open_rate:${campaign.name}`,
        status: "warning",
        message: `Open rate ${openRate.toFixed(1)}% below 20%. Check subject lines and deliverability.`,
      });
    }
  }

  // Campaign status checks
  const unhealthy = campaigns.filter((c) => c.status === -1);
  const bounceProtected = campaigns.filter((c) => c.status === -2);

  if (unhealthy.length > 0) {
    checks.push({
      check: "unhealthy_campaigns",
      status: "critical",
      message: `${unhealthy.length} campaign(s) in Accounts Unhealthy state: ${unhealthy.map((c) => c.name).join(", ")}`,
    });
  }

  if (bounceProtected.length > 0) {
    checks.push({
      check: "bounce_protected_campaigns",
      status: "critical",
      message: `${bounceProtected.length} campaign(s) paused by Bounce Protect: ${bounceProtected.map((c) => c.name).join(", ")}`,
    });
  }

  return checks;
}
```

### Step 2: Account Warmup Monitor
```typescript
async function warmupHealthCheck(): Promise<HealthCheck[]> {
  const checks: HealthCheck[] = [];
  const accounts = await client.accounts.list(100);
  const emails = accounts.map((a) => a.email);

  if (emails.length === 0) return checks;

  // Get warmup analytics
  const warmup = await client.accounts.warmupAnalytics(emails);

  for (const w of warmup as Array<{
    email: string;
    warmup_emails_sent: number;
    warmup_emails_landed_inbox: number;
    warmup_emails_landed_spam: number;
  }>) {
    const sent = w.warmup_emails_sent || 1;
    const inboxRate = (w.warmup_emails_landed_inbox / sent) * 100;
    const spamRate = (w.warmup_emails_landed_spam / sent) * 100;

    if (inboxRate < 80) {
      checks.push({
        check: `warmup_inbox_rate:${w.email}`,
        status: inboxRate < 60 ? "critical" : "warning",
        message: `${w.email} warmup inbox rate ${inboxRate.toFixed(1)}% (${inboxRate < 60 ? "critical" : "below 80%"})`,
      });
    }

    if (spamRate > 10) {
      checks.push({
        check: `warmup_spam_rate:${w.email}`,
        status: "critical",
        message: `${w.email} warmup spam rate ${spamRate.toFixed(1)}% — reputation issue`,
      });
    }
  }

  // Test vitals
  const vitals = await client.accounts.testVitals(emails) as Array<{
    email: string; smtp_status: string; imap_status: string;
  }>;

  const broken = vitals.filter((v) => v.smtp_status !== "ok" || v.imap_status !== "ok");
  if (broken.length > 0) {
    checks.push({
      check: "account_vitals",
      status: "critical",
      message: `${broken.length} account(s) with broken SMTP/IMAP: ${broken.map((v) => v.email).join(", ")}`,
    });
  }

  return checks;
}
```

### Step 3: Webhook Delivery Monitor
```typescript
async function webhookHealthCheck(): Promise<HealthCheck[]> {
  const checks: HealthCheck[] = [];

  const summary = await client.request<{
    total_delivered: number;
    total_failed: number;
    total_pending: number;
  }>("/webhook-events/summary");

  if (summary.total_failed > 0) {
    const failRate = (summary.total_failed / (summary.total_delivered + summary.total_failed)) * 100;
    checks.push({
      check: "webhook_delivery",
      status: failRate > 10 ? "critical" : "warning",
      message: `Webhook delivery: ${summary.total_delivered} delivered, ${summary.total_failed} failed (${failRate.toFixed(1)}% fail rate)`,
    });
  }

  // Check for paused webhooks
  const webhooks = await client.webhooks.list();
  const paused = webhooks.filter((w: any) => w.status === "paused");
  if (paused.length > 0) {
    checks.push({
      check: "webhooks_paused",
      status: "critical",
      message: `${paused.length} webhook(s) are paused — events are being dropped`,
    });
  }

  return checks;
}
```

### Step 4: Alerting Pipeline
```typescript
async function runHealthChecks() {
  console.log(`\n=== Instantly Health Check — ${new Date().toISOString()} ===\n`);

  const allChecks: HealthCheck[] = [
    ...await campaignHealthCheck(),
    ...await warmupHealthCheck(),
    ...await webhookHealthCheck(),
  ];

  // Log all checks
  for (const check of allChecks) {
    const icon = check.status === "ok" ? "OK" : check.status === "warning" ? "WARN" : "CRIT";
    console.log(`[${icon}] ${check.check}: ${check.message}`);
  }

  // Alert on critical/warning
  const critical = allChecks.filter((c) => c.status === "critical");
  const warnings = allChecks.filter((c) => c.status === "warning");

  if (critical.length > 0) {
    await sendAlert("critical", critical);
  }
  if (warnings.length > 0) {
    await sendAlert("warning", warnings);
  }

  console.log(`\nSummary: ${critical.length} critical, ${warnings.length} warnings, ${allChecks.length} total checks`);
}

async function sendAlert(severity: string, checks: HealthCheck[]) {
  // Slack notification
  const color = severity === "critical" ? "#FF0000" : "#FFA500";
  const text = checks.map((c) => `*${c.check}*: ${c.message}`).join("\n");

  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      attachments: [{
        color,
        title: `Instantly ${severity.toUpperCase()} Alert`,
        text,
        ts: Math.floor(Date.now() / 1000),
      }],
    }),
  });
}
```

### Step 5: Scheduled Monitoring (Cron)
```typescript
// Run health checks on a schedule
// Deploy as Cloud Run job, GitHub Action, or cron task

// package.json script:
// "monitor": "npx tsx scripts/health-check.ts"

// crontab: every 15 minutes
// */15 * * * * cd /app && npm run monitor >> /var/log/instantly-health.log 2>&1

// GitHub Actions schedule:
// on:
//   schedule:
//     - cron: '*/15 * * * *'

import cron from "node-cron";

cron.schedule("*/15 * * * *", async () => {
  try {
    await runHealthChecks();
  } catch (err) {
    console.error("Health check failed:", err);
    await sendAlert("critical", [{ check: "monitor", status: "critical", message: `Monitor itself failed: ${err}` }]);
  }
});
```

## Dashboard Metrics Summary
| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| Campaign bounce rate | `GET /campaigns/analytics` | >5% critical |
| Campaign reply rate | `GET /campaigns/analytics` | <1% warning |
| Campaign open rate | `GET /campaigns/analytics` | <20% warning |
| Warmup inbox rate | `POST /accounts/warmup-analytics` | <80% warning, <60% critical |
| Account vitals | `POST /accounts/test/vitals` | Any non-ok = critical |
| Webhook delivery | `GET /webhook-events/summary` | >10% fail rate = critical |
| Unhealthy campaigns | `GET /campaigns` | status=-1 = critical |
| Bounce protected campaigns | `GET /campaigns` | status=-2 = critical |

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Monitor itself rate-limited | Too-frequent checks | Increase interval to 15-30 min |
| Slack alert not delivered | Invalid webhook URL | Verify `SLACK_WEBHOOK_URL` |
| Stale analytics data | Instantly updates delay | Allow 1-hour data lag |

## Resources
- [Instantly Analytics API](https://developer.instantly.ai/api/v2/analytics)
- [Instantly Account API](https://developer.instantly.ai/api/v2/account)
- [Instantly Webhook Events](https://developer.instantly.ai/api/v2/webhook)

## Next Steps
For incident response, see `instantly-incident-runbook`.
