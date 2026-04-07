---
name: finta-common-errors
description: |
  Diagnose and fix common Finta CRM issues with email sync, deal rooms, and pipeline.
  Trigger with phrases like "finta error", "finta not working", "fix finta".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, fundraising-crm, investor-management, finta]
compatible-with: claude-code
---

# Finta Common Errors

## Overview

Finta is a fundraising CRM that manages investor pipelines, deal rooms, email sync, and payment collection for startups raising capital. Common errors involve round state transition violations (e.g., moving a round backward from "Closing" to "Outreach"), investor deduplication failures during CSV imports, and pipeline sync breakdowns between email providers and the deal tracker. Aurora AI suggestions depend on complete company profiles, and incomplete data is the top cause of empty recommendations. This reference covers API-level errors and CRM workflow issues that disrupt fundraising operations.

## Error Reference

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| `400` | `Invalid round transition` | Moving round to an invalid state | Follow valid transitions: Draft > Active > Closing > Closed |
| `401` | `Invalid API key` | Expired or revoked `FINTA_API_KEY` | Regenerate at Settings > API Access |
| `404` | `Investor not found` | Deleted or merged investor record | Search by email to find merged record |
| `409` | `Duplicate investor` | Email already exists in pipeline | Use dedup endpoint before CSV import |
| `422` | `Missing required fields` | Incomplete investor or round data | Include `name`, `email`, `stage` at minimum |
| `429` | `Rate limit exceeded` | Too many API calls | Implement backoff; batch operations where possible |
| `500` | `Pipeline sync failed` | Email provider OAuth expired | Reconnect Gmail/Outlook at Settings > Integrations |
| `502` | `Stripe webhook failed` | Payment collection error | Verify Stripe integration and webhook URL |

## Error Handler

```typescript
interface FintaError {
  code: number;
  message: string;
  category: "auth" | "rate_limit" | "validation" | "sync";
}

function classifyFintaError(status: number, body: string): FintaError {
  if (status === 401) {
    return { code: 401, message: body, category: "auth" };
  }
  if (status === 429) {
    return { code: 429, message: "Rate limit exceeded", category: "rate_limit" };
  }
  if (status === 400 || status === 404 || status === 409 || status === 422) {
    return { code: status, message: body, category: "validation" };
  }
  return { code: status, message: body, category: "sync" };
}
```

## Debugging Guide

### Authentication Errors
Finta API keys are scoped per workspace. Verify the key matches the active workspace at Settings > API Access. Keys are revoked automatically when team members are removed. Re-invite and regenerate if a team change caused the failure. Test connectivity with a simple GET to the rounds endpoint before running complex operations.

### Rate Limit Errors
Finta enforces 60 requests/minute per API key. Batch investor updates using the bulk endpoint instead of individual PUT calls. CSV imports bypass the rate limit -- prefer bulk import for large datasets.

### Validation Errors
Round state transitions must follow the sequence: Draft, Active, Closing, Closed. Skipping states returns 400. Backward transitions (e.g., Closing to Active) are also rejected. Investor deduplication matches on email -- always check for existing records before creating. Deal room links expire after 30 days by default; regenerate from the round settings page. CSV imports require `name`, `email`, and `stage` columns with dates in YYYY-MM-DD format.

## Error Handling

| Scenario | Pattern | Recovery |
|----------|---------|----------|
| Round state transition rejected | Invalid backward move | Query current state, advance only forward |
| CSV import partial failure | Duplicate emails found | Run dedup pass, retry failed rows |
| Email sync disconnected | OAuth token expired | Reconnect provider at Settings > Integrations |
| Aurora AI no suggestions | Incomplete company profile | Fill all profile fields: sector, stage, location, raise amount |
| Payment link mismatch | Amount differs from commitment | Regenerate Stripe payment link with correct amount |

## Quick Diagnostic

```bash
# Verify API connectivity
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $FINTA_API_KEY" \
  https://api.trustfinta.com/v1/rounds
```

## Resources

- [Finta Help Center](https://www.trustfinta.com)
- [Finta API Documentation](https://docs.trustfinta.com)

## Next Steps

See `finta-debug-bundle`.
