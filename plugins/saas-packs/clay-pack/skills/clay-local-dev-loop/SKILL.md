---
name: clay-local-dev-loop
description: |
  Set up a local development loop for building and testing Clay integrations.
  Use when iterating on Clay webhook handlers, testing enrichment pipelines,
  or building scripts that push data into Clay tables.
  Trigger with phrases like "clay local dev", "clay development setup",
  "clay testing locally", "clay dev workflow", "iterate clay integration".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Bash(npx:*), Bash(node:*), Bash(python3:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, development, testing]

---
# Clay Local Dev Loop

## Overview

Clay is a web-based platform with no local runtime. Your local dev loop consists of: (1) scripts that push data into Clay via webhooks, (2) Clay enrichment running in the cloud, and (3) HTTP API columns pushing enriched data back to your local endpoint via ngrok. This skill sets up that feedback loop.

## Prerequisites

- Completed `clay-install-auth` setup
- Node.js 18+ or Python 3.10+
- ngrok installed (`npm install -g ngrok` or [ngrok.com](https://ngrok.com))
- Clay table with webhook source configured

## Instructions

### Step 1: Expose Your Local Server via ngrok

Clay's HTTP API enrichment columns need a public URL to call your local endpoints.

```bash
# Start ngrok tunnel to your local server
ngrok http 3000
# Copy the HTTPS forwarding URL (e.g., https://abc123.ngrok-free.app)
```

### Step 2: Create a Local Webhook Receiver

```typescript
// src/clay-receiver.ts — receives enriched data from Clay HTTP API columns
import express from 'express';

const app = express();
app.use(express.json());

// Clay HTTP API column calls this endpoint
app.post('/api/clay/enriched', (req, res) => {
  const enrichedData = req.body;
  console.log('Enriched record received from Clay:', {
    email: enrichedData.email,
    company: enrichedData.company_name,
    title: enrichedData.job_title,
    enrichment_source: enrichedData._clay_source,
  });

  // Process the enriched data (save to DB, trigger outreach, etc.)
  res.json({ status: 'received', timestamp: new Date().toISOString() });
});

// Health check for Clay HTTP API column testing
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'clay-dev-receiver' });
});

app.listen(3000, () => {
  console.log('Clay dev receiver listening on http://localhost:3000');
  console.log('Configure Clay HTTP API column to POST to: <ngrok-url>/api/clay/enriched');
});
```

### Step 3: Build a Test Data Sender

```typescript
// src/send-test-leads.ts — push test data into Clay via webhook
const CLAY_WEBHOOK_URL = process.env.CLAY_WEBHOOK_URL!;

const testLeads = [
  { email: 'cto@stripe.com', domain: 'stripe.com', source: 'dev-test' },
  { email: 'vp@notion.so', domain: 'notion.so', source: 'dev-test' },
  { email: 'head@figma.com', domain: 'figma.com', source: 'dev-test' },
];

async function sendTestBatch() {
  for (const lead of testLeads) {
    const res = await fetch(CLAY_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(lead),
    });
    console.log(`Sent ${lead.email}: ${res.status}`);
    await new Promise(r => setTimeout(r, 200)); // Respect rate limits
  }
  console.log('\nCheck your Clay table — enrichment columns should auto-run.');
  console.log('Enriched data will POST back to your ngrok endpoint.');
}

sendTestBatch();
```

### Step 4: Configure Clay HTTP API Column to Call You Back

In your Clay table:

1. Click **+ Add Column > HTTP API**
2. Set **Method**: POST
3. Set **URL**: `https://your-ngrok-url.ngrok-free.app/api/clay/enriched`
4. Set **Body** (JSON): Map enriched columns using Clay's `{{column_name}}` syntax:

```json
{
  "email": "{{Email}}",
  "company_name": "{{Company Name}}",
  "job_title": "{{Job Title}}",
  "employee_count": "{{Employee Count}}",
  "linkedin_url": "{{LinkedIn URL}}"
}
```

5. Enable **Auto-run on new rows**

### Step 5: Dev Loop Iteration Cycle

```bash
# Terminal 1: Run ngrok
ngrok http 3000

# Terminal 2: Run your local receiver
npx tsx src/clay-receiver.ts

# Terminal 3: Send test data to Clay
npx tsx src/send-test-leads.ts

# Watch Terminal 2 for enriched data flowing back from Clay
```

**Iteration cycle:**
1. Modify enrichment columns or Claygent prompts in Clay UI
2. Re-send test data via webhook
3. Observe enriched results in your local receiver
4. Adjust and repeat

### Step 6: Mock Clay Responses for Unit Tests

```typescript
// tests/clay-webhook.test.ts — test without hitting Clay
import { describe, it, expect } from 'vitest';

const mockClayEnrichedPayload = {
  email: 'jane@stripe.com',
  company_name: 'Stripe',
  employee_count: 8000,
  industry: 'Financial Technology',
  job_title: 'VP Engineering',
  linkedin_url: 'https://linkedin.com/in/janedoe',
  _clay_source: 'clearbit',
  _clay_enriched_at: '2026-03-22T10:00:00Z',
};

describe('Clay enriched data handler', () => {
  it('processes enriched lead correctly', async () => {
    const res = await fetch('http://localhost:3000/api/clay/enriched', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mockClayEnrichedPayload),
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('received');
  });
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| ngrok tunnel drops | Free tier session expired | Restart ngrok or upgrade to paid plan |
| Clay HTTP API column returns error | ngrok URL changed | Update the URL in Clay column settings |
| No data flows back | Auto-run disabled | Enable auto-run on the HTTP API column |
| Webhook returns 422 | Bad JSON in test data | Validate payload with `jq . <<< '$JSON'` |
| Enrichment columns empty | No provider configured | Add enrichment provider in Clay table |

## Output

- Local server receiving enriched data from Clay
- Test data pipeline: local script -> Clay webhook -> enrichment -> HTTP API -> local server
- Unit tests with mocked Clay payloads

## Resources

- [Clay University -- HTTP API Integration](https://university.clay.com/docs/http-api-integration-overview)
- [ngrok Documentation](https://ngrok.com/docs)

## Next Steps

Once your dev loop works, see `clay-sdk-patterns` for production-ready integration patterns.
