---
name: instantly-common-errors
description: |
  Diagnose and fix Instantly.ai API v2 common errors and exceptions.
  Use when encountering Instantly errors, debugging failed requests,
  or troubleshooting campaign/account/lead issues.
  Trigger with phrases like "instantly error", "instantly 401", "instantly 429",
  "instantly api failed", "instantly debug", "instantly troubleshoot".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, debugging, errors]

---
# Instantly Common Errors

## Overview
Diagnostic reference for Instantly API v2 errors. Covers HTTP status codes, campaign state errors, account health issues, lead operation failures, and webhook delivery problems.

## Prerequisites
- Completed `instantly-install-auth` setup
- Access to Instantly dashboard for verification
- API key with appropriate scopes

## HTTP Status Codes

| Status | Meaning | Common Cause | Fix |
|--------|---------|-------------|-----|
| `400` | Bad Request | Malformed JSON, invalid field values | Validate request body against schema |
| `401` | Unauthorized | Invalid, expired, or revoked API key | Regenerate key in Settings > Integrations |
| `403` | Forbidden | API key missing required scope | Create key with correct scope (e.g., `campaigns:all`) |
| `404` | Not Found | Invalid campaign/lead/account ID | Verify resource exists with a GET call first |
| `422` | Unprocessable Entity | Business logic violation (duplicate lead, invalid state) | Check error body for details |
| `429` | Too Many Requests | Rate limit exceeded | Implement exponential backoff (see below) |
| `500` | Internal Server Error | Instantly server issue | Retry with backoff; check status.instantly.ai |

## Campaign Errors

### Campaign Won't Activate (Stuck in Draft)
```typescript
// Diagnosis: check campaign requirements
async function diagnoseCampaign(campaignId: string) {
  const campaign = await instantly<Campaign>(`/campaigns/${campaignId}`);

  const issues: string[] = [];

  // Check sequences
  if (!campaign.sequences?.length || !campaign.sequences[0]?.steps?.length) {
    issues.push("No email sequences — add at least one step with subject + body");
  }

  // Check schedule
  if (!campaign.campaign_schedule?.schedules?.length) {
    issues.push("No sending schedule — add schedule with timing and days");
  }

  // Check sending accounts
  const mappings = await instantly(`/account-campaign-mappings/${campaignId}`);
  if (!Array.isArray(mappings) || mappings.length === 0) {
    issues.push("No sending accounts assigned — add via PATCH /campaigns/{id} with email_list");
  }

  // Check for leads
  const leads = await instantly<Lead[]>("/leads/list", {
    method: "POST",
    body: JSON.stringify({ campaign: campaignId, limit: 1 }),
  });
  if (leads.length === 0) {
    issues.push("No leads — add leads via POST /leads");
  }

  if (issues.length === 0) {
    console.log("Campaign looks ready to activate");
  } else {
    console.log("Issues preventing activation:");
    issues.forEach((i) => console.log(`  - ${i}`));
  }
}
```

### Campaign Status Codes
| Status | Label | Meaning |
|--------|-------|---------|
| `0` | Draft | Not yet activated |
| `1` | Active | Currently sending |
| `2` | Paused | Manually paused |
| `3` | Completed | All leads processed |
| `4` | Running Subsequences | Main sequence done, subsequences active |
| `-1` | Accounts Unhealthy | Sending accounts have SMTP/IMAP errors |
| `-2` | Bounce Protect | Auto-paused due to high bounce rate |
| `-99` | Suspended | Account-level suspension |

### Fix: Accounts Unhealthy (-1)
```typescript
async function fixUnhealthyAccounts(campaignId: string) {
  // 1. Get accounts assigned to campaign
  const accounts = await instantly<Account[]>("/accounts?limit=100");

  // 2. Test vitals for each
  const vitals = await instantly("/accounts/test/vitals", {
    method: "POST",
    body: JSON.stringify({ accounts: accounts.map((a) => a.email) }),
  });

  // 3. Identify and fix broken accounts
  for (const v of vitals as any[]) {
    if (v.smtp_status !== "ok" || v.imap_status !== "ok") {
      console.log(`BROKEN: ${v.email} — SMTP=${v.smtp_status}, IMAP=${v.imap_status}`);
      // Pause the broken account
      await instantly(`/accounts/${encodeURIComponent(v.email)}/pause`, { method: "POST" });
      console.log(`  Paused ${v.email}. Fix credentials, then resume.`);
    }
  }
}
```

## Lead Errors

### Duplicate Lead (422)
```typescript
// Prevent duplicates by setting skip flags
await instantly("/leads", {
  method: "POST",
  body: JSON.stringify({
    campaign: campaignId,
    email: "user@example.com",
    first_name: "Jane",
    skip_if_in_workspace: true,   // skip if email exists anywhere in workspace
    skip_if_in_campaign: true,    // skip if already in this campaign
  }),
});
```

### Lead Status Reference
| Status | Label | Description |
|--------|-------|-------------|
| `1` | Active | Eligible to receive emails |
| `2` | Paused | Manually paused |
| `3` | Completed | All sequence steps sent |
| `-1` | Bounced | Email bounced |
| `-2` | Unsubscribed | Lead unsubscribed |
| `-3` | Skipped | Skipped (blocklist, duplicate, etc.) |

## Rate Limit Handling
```typescript
async function withBackoff<T>(
  operation: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      if (err.status === 429 && attempt < maxRetries) {
        const wait = Math.pow(2, attempt) * 1000;
        console.warn(`429 Rate Limited. Waiting ${wait}ms (attempt ${attempt + 1}/${maxRetries})`);
        await new Promise((r) => setTimeout(r, wait));
        continue;
      }
      throw err;
    }
  }
  throw new Error("Unreachable");
}
```

## Webhook Errors

| Issue | Diagnostic | Fix |
|-------|-----------|-----|
| Events not delivered | Check webhook status: `GET /webhooks` | Webhook may be paused — resume with `POST /webhooks/{id}/resume` |
| Wrong event format | Compare to expected schema | Ensure `event_type` matches: `email_sent`, `reply_received`, etc. |
| Delivery failures | Check `GET /webhook-events/summary` | Fix target URL, ensure 2xx response within 30s |
| Retries exhausting | Instantly retries 3x in 30s | Return 200 immediately, process async |

## Quick Diagnostic Script
```bash
set -euo pipefail
echo "=== Instantly Health Check ==="

# Test auth
curl -s -o /dev/null -w "Auth: HTTP %{http_code}\n" \
  https://api.instantly.ai/api/v2/campaigns?limit=1 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY"

# Count campaigns by status
curl -s https://api.instantly.ai/api/v2/campaigns?limit=100 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq 'group_by(.status) | map({status: .[0].status, count: length})'

# Check account health
curl -s https://api.instantly.ai/api/v2/accounts?limit=100 \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '[.[] | {email, status, warmup_status}] | .[:5]'
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401` after key rotation | Old key cached | Restart app / clear env cache |
| `403` on campaign activate | Missing `campaigns:update` scope | Regenerate API key with correct scopes |
| `422` duplicate lead | Lead already in workspace | Use `skip_if_in_workspace: true` |
| Campaign `-2` bounce protect | Bounce rate >5% | Clean lead list, verify emails before import |
| Warmup health dropping | Too many campaign emails too soon | Reduce daily_limit, extend warmup period |

## Resources
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [Instantly Help Center](https://help.instantly.ai)
- [API Schemas](https://developer.instantly.ai/api/v2/schemas)

## Next Steps
For structured debugging, see `instantly-debug-bundle`.
