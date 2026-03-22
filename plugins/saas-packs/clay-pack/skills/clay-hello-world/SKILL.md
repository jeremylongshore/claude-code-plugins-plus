---
name: clay-hello-world
description: |
  Send your first record to Clay and get enriched data back.
  Use when starting a new Clay integration, testing webhook setup,
  or verifying that enrichment columns are working.
  Trigger with phrases like "clay hello world", "clay example",
  "clay quick start", "first clay enrichment", "test clay webhook".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, api, testing]

---
# Clay Hello World

## Overview

Minimal working example: send a company domain to a Clay table via webhook, let Clay's enrichment columns fill in company data, and retrieve the enriched result. Clay does not have a traditional SDK — you interact with it via webhooks (data in), HTTP API columns (data out), and the web UI.

## Prerequisites

- Completed `clay-install-auth` setup
- Clay workbook with a webhook source configured
- At least one enrichment column added to the table

## Instructions

### Step 1: Create a Clay Table with Enrichment

In the Clay web UI:

1. Create a new workbook
2. Add columns: `domain`, `company_name`, `employee_count`, `industry`
3. Click **+ Add** at bottom, select **Webhooks > Monitor webhook**
4. Copy the webhook URL
5. Add an enrichment column: **+ Add Column > Enrich Company** (uses the `domain` column as input)

### Step 2: Send Your First Record via Webhook

```bash
# Send a single company domain to your Clay table
curl -X POST "https://app.clay.com/api/v1/webhooks/YOUR_WEBHOOK_ID" \
  -H "Content-Type: application/json" \
  -d '{"domain": "openai.com"}'
```

Within seconds, Clay creates a new row and auto-runs the enrichment column. The `company_name`, `employee_count`, and `industry` columns fill in automatically.

### Step 3: Send Multiple Records

```bash
# Batch send — each object becomes a row
for domain in stripe.com notion.so figma.com linear.app; do
  curl -s -X POST "https://app.clay.com/api/v1/webhooks/YOUR_WEBHOOK_ID" \
    -H "Content-Type: application/json" \
    -d "{\"domain\": \"$domain\"}"
  echo " -> Sent $domain"
done
```

### Step 4: Send from Node.js

```typescript
// hello-clay.ts — send records to Clay via webhook
const CLAY_WEBHOOK_URL = process.env.CLAY_WEBHOOK_URL!;

interface LeadInput {
  email?: string;
  domain?: string;
  first_name?: string;
  last_name?: string;
  linkedin_url?: string;
}

async function sendToClay(lead: LeadInput): Promise<Response> {
  const response = await fetch(CLAY_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lead),
  });

  if (!response.ok) {
    throw new Error(`Clay webhook failed: ${response.status} ${response.statusText}`);
  }
  return response;
}

// Send a test lead
await sendToClay({
  email: 'jane@stripe.com',
  first_name: 'Jane',
  last_name: 'Doe',
  domain: 'stripe.com',
});
console.log('Record sent to Clay — check your table for enriched data.');
```

### Step 5: Send from Python

```python
import requests
import os

CLAY_WEBHOOK_URL = os.environ["CLAY_WEBHOOK_URL"]

def send_to_clay(lead: dict) -> requests.Response:
    """Send a lead record to a Clay table via webhook."""
    response = requests.post(
        CLAY_WEBHOOK_URL,
        json=lead,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return response

# Test it
send_to_clay({
    "email": "jane@stripe.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "domain": "stripe.com",
})
print("Record sent to Clay — check your table for enriched data.")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `404 Not Found` | Invalid webhook URL | Re-copy URL from Clay table settings |
| `422 Unprocessable` | Invalid JSON payload | Validate JSON structure before sending |
| Row appears but no enrichment | Enrichment column not configured | Add enrichment column in Clay UI, enable auto-run |
| `429 Too Many Requests` | Exceeded webhook rate limit | Add 100ms delay between requests |
| Webhook limit reached (50K) | Webhook exhausted | Create a new webhook source on the table |

## Output

- New row(s) visible in your Clay table
- Enrichment columns auto-populated with company/person data
- Console confirmation of successful webhook delivery

## Resources

- [Clay University — Webhook Integration Guide](https://university.clay.com/docs/webhook-integration-guide)
- [Clay University — Using Clay as an API](https://www.clay.com/university/guide/using-clay-as-an-api)

## Next Steps

Proceed to `clay-local-dev-loop` for iterating on enrichment workflows locally.
