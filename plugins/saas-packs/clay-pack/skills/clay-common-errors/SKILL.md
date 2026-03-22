---
name: clay-common-errors
description: |
  Diagnose and fix the most common Clay errors and integration issues.
  Use when encountering Clay errors, debugging failed enrichments,
  or troubleshooting webhook delivery problems.
  Trigger with phrases like "clay error", "fix clay", "clay not working",
  "debug clay", "clay enrichment failed", "clay webhook error".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, debugging]

---
# Clay Common Errors

## Overview

Quick reference for the top 12 most common Clay errors across webhooks, enrichment columns, HTTP API columns, Claygent, and CRM integrations. Each error includes the exact symptom, root cause, and fix.

## Prerequisites

- Clay account with an active table
- Access to Clay table error indicators (red cells, exclamation marks)
- Browser developer tools for webhook debugging

## Instructions

### Error 1: Webhook Returns 422 Unprocessable Entity

**Symptom:** Data sent to webhook URL but rows never appear in table.

**Cause:** Invalid JSON payload or missing Content-Type header.

**Fix:**
```bash
# Always include Content-Type header
curl -X POST "$CLAY_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "domain": "example.com"}'

# Validate JSON before sending
echo '{"email": "test@example.com"}' | jq . || echo "Invalid JSON!"
```

---

### Error 2: Webhook URL Returns 404

**Symptom:** `404 Not Found` when POSTing to webhook URL.

**Cause:** Table was deleted, webhook was replaced, or URL was copied incorrectly.

**Fix:** Open the Clay table, click **+ Add > Webhooks > Monitor webhook**, and re-copy the URL. Each table has a unique webhook ID.

---

### Error 3: Enrichment Column Shows "No Data Found"

**Symptom:** Enrichment column returns empty for most rows.

**Cause:** Input data quality is poor (personal email domains, invalid domains, missing fields).

**Fix:**
```typescript
// Pre-validate before sending to Clay
const personalDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com'];

function isEnrichable(row: { domain?: string; email?: string }): boolean {
  if (!row.domain || !row.domain.includes('.')) return false;
  if (personalDomains.some(d => row.domain!.endsWith(d))) return false;
  if (row.email && personalDomains.some(d => row.email!.endsWith(d))) return false;
  return true;
}
```

---

### Error 4: "Credit Balance Insufficient"

**Symptom:** Enrichment stops mid-table with credit error.

**Cause:** Monthly credit allowance exhausted.

**Fix:** Check credit balance in **Settings > Plans & Billing**. Options:
- Connect your own provider API keys (saves 70-80% credits)
- Reduce waterfall depth (fewer providers = fewer credits per row)
- Upgrade plan for more monthly credits

---

### Error 5: Webhook Submission Limit Reached (50K)

**Symptom:** Webhook stops accepting new submissions silently.

**Cause:** Each webhook source has a hard limit of 50,000 submissions.

**Fix:** Create a new webhook source on the same table. The 50K limit persists even after deleting rows -- you must create a fresh webhook.

---

### Error 6: HTTP API Column Returns Error

**Symptom:** Red error indicator on HTTP API enrichment column cells.

**Cause:** Target API URL is wrong, auth header is incorrect, or response format unexpected.

**Fix:**
1. Click the errored cell to see the full error response
2. Test the API call independently with curl:
```bash
curl -X POST "https://api.example.com/endpoint" \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```
3. Verify the response JSON path selector matches the actual response structure

---

### Error 7: Claygent Returns "Could Not Find Information"

**Symptom:** Claygent column returns empty or generic responses.

**Cause:** Prompt is too vague, company is too small/private, or website blocks bots.

**Fix:**
- Make prompts specific: "Find the CEO's name from the About page at {{domain}}" vs "Research this company"
- Add fallback instructions: "If the information is not on the website, check LinkedIn and Crunchbase"
- Use **Navigator** mode for JavaScript-heavy sites

---

### Error 8: Enrichment Runs on Existing Rows Unexpectedly

**Symptom:** Credits consumed on rows that were already enriched.

**Cause:** Table-level auto-update is ON and a column was edited, triggering re-enrichment.

**Fix:** Go to **Table Settings** and toggle auto-update OFF at the table level. Then enable auto-run only on specific columns that need it. The table-level setting is the parent: if OFF, no columns auto-run.

---

### Error 9: Rate Limited (429) on Webhook Submissions

**Symptom:** `429 Too Many Requests` when sending data via webhook.

**Cause:** Explorer plan has a 400 records/hour throttle.

**Fix:**
```typescript
// Add delay between webhook submissions
async function sendWithThrottle(rows: any[], webhookUrl: string) {
  for (const row of rows) {
    const res = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(row),
    });
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      console.log(`Rate limited. Waiting ${retryAfter}s...`);
      await new Promise(r => setTimeout(r, retryAfter * 1000));
    }
    await new Promise(r => setTimeout(r, 250)); // 250ms between requests
  }
}
```

---

### Error 10: CRM Sync Creates Duplicate Contacts

**Symptom:** Same contact appears multiple times in HubSpot/Salesforce.

**Cause:** No deduplication key configured in the CRM push action.

**Fix:** When configuring the CRM action column, use email as the unique identifier and select **Update existing record if found** rather than always creating new.

---

### Error 11: CSV Import Column Mapping Wrong

**Symptom:** Data appears in wrong columns after CSV import.

**Cause:** CSV headers don't match Clay column names exactly.

**Fix:** Normalize headers before import: trim whitespace, match case exactly. "Company Name" and "company_name" are treated as different columns.

---

### Error 12: Formula Column Shows Error

**Symptom:** Formula column displays `#ERROR` or `#REF`.

**Cause:** Column name referenced in formula was renamed or deleted.

**Fix:** Edit the formula column and update all column references to match current names. Clay formulas reference columns by their display name (case-sensitive).

## Error Handling

| Symptom | Quick Check | Likely Fix |
|---------|------------|------------|
| Red cell indicator | Click cell for error detail | Fix API config or input data |
| Empty enrichment | Check provider connection | Reconnect in Settings > Connections |
| No new rows from webhook | Test webhook URL with curl | Re-create webhook source |
| Credits depleting fast | Check waterfall depth | Reduce to 2 providers, add conditions |

## Resources

- [Clay University -- HTTP API Integration](https://university.clay.com/docs/http-api-integration-overview)
- [Clay Community Support](https://community.clay.com)
- [Clay University -- Table Management](https://university.clay.com/docs/table-management-settings)

## Next Steps

For systematic debugging, see `clay-debug-bundle`.
