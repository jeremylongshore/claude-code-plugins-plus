---
name: clay-core-workflow-a
description: |
  Build a complete lead enrichment pipeline using Clay tables, webhooks, and waterfall enrichment.
  Use when building lead generation features, enriching prospect lists,
  or creating automated data enrichment workflows.
  Trigger with phrases like "clay lead enrichment", "clay main workflow",
  "enrich contacts in clay", "clay prospect list", "clay enrichment pipeline".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, workflow]

---
# Clay Core Workflow A: Lead Enrichment Pipeline

## Overview

Primary workflow for Clay: take a list of companies or contacts, push them into a Clay table via webhook, let Clay's enrichment columns fill in missing data (emails, titles, company info, tech stack), and export the enriched results to your CRM or outreach tool. This is the core use case for 90%+ of Clay users.

## Prerequisites

- Completed `clay-install-auth` setup
- Clay table with webhook source configured
- At least one enrichment provider connected (Apollo, Clearbit, Hunter, etc.)
- Destination CRM or outreach tool (HubSpot, Salesforce, Instantly, etc.)

## Instructions

### Step 1: Design Your Clay Table Schema

In the Clay web UI, create a table with these column types:

| Column | Type | Purpose |
|--------|------|---------|
| `domain` | Input (webhook) | Company domain to enrich |
| `first_name` | Input (webhook) | Contact first name |
| `last_name` | Input (webhook) | Contact last name |
| `Company Name` | Enrichment (Clearbit/Apollo) | Auto-filled from domain |
| `Employee Count` | Enrichment (Clearbit) | Company headcount |
| `Industry` | Enrichment (Clearbit) | Industry classification |
| `Work Email` | Enrichment (Waterfall) | Verified work email |
| `Job Title` | Enrichment (Apollo/PDL) | Current title |
| `LinkedIn URL` | Enrichment (Apollo) | Profile link |
| `ICP Score` | Formula | Computed fit score |

### Step 2: Set Up Waterfall Email Enrichment

In Clay UI, add a waterfall enrichment column:

1. Click **+ Add Column > Find Work Email (Waterfall)**
2. Configure provider order (cheapest first):
   - **Apollo** (2 credits) -- highest coverage
   - **Hunter.io** (2 credits) -- strong for smaller companies
   - **Prospeo** (2 credits) -- European coverage
3. Map input: `first_name`, `last_name`, `domain`
4. Enable **Stop on first result** to save credits
5. Enable **Auto-run on new rows**

### Step 3: Push Leads into Clay via Webhook

```typescript
// src/workflows/enrich-leads.ts
import { getClayClient } from '../clay/instance';

interface LeadInput {
  domain: string;
  first_name: string;
  last_name: string;
  source?: string;
}

async function enrichLeadList(leads: LeadInput[]): Promise<void> {
  const clay = getClayClient();

  // Validate and deduplicate before sending
  const cleaned = leads
    .filter(l => l.domain?.includes('.') && l.first_name && l.last_name)
    .filter((l, i, arr) =>
      arr.findIndex(x => x.domain === l.domain && x.first_name === l.first_name) === i
    );

  console.log(`Sending ${cleaned.length} leads to Clay (filtered ${leads.length - cleaned.length} invalid/dupes)`);

  const result = await clay.sendBatch(cleaned, 200);
  console.log(`Sent: ${result.sent}, Failed: ${result.failed}`);

  if (result.errors.length > 0) {
    console.error('Failed rows:', result.errors);
  }
}
```

### Step 4: Add ICP Scoring Formula

In Clay, add a **Formula** column named `ICP Score`:

```
// Clay formula syntax (similar to spreadsheet formulas)
// Score 0-100 based on company fit

LET(
  size_score, IF(Employee Count > 500, 30, IF(Employee Count > 100, 20, IF(Employee Count > 20, 10, 0))),
  industry_score, IF(OR(Industry = "Software", Industry = "Technology", Industry = "SaaS"), 30, IF(Industry = "Financial Services", 20, 10)),
  title_score, IF(OR(CONTAINS(Job Title, "VP"), CONTAINS(Job Title, "Director"), CONTAINS(Job Title, "Head")), 25, IF(CONTAINS(Job Title, "Manager"), 15, 5)),
  email_score, IF(ISNOTEMPTY(Work Email), 15, 0),
  size_score + industry_score + title_score + email_score
)
```

### Step 5: Configure CRM Export

Add an **HTTP API** column to push high-scoring leads to your CRM:

1. Click **+ Add Column > HTTP API**
2. Set conditional run: `ICP Score >= 70 AND ISNOTEMPTY(Work Email)`
3. Configure the API call to your CRM:

```json
{
  "method": "POST",
  "url": "https://api.hubapi.com/crm/v3/objects/contacts",
  "headers": {
    "Authorization": "Bearer {{HubSpot API Key}}",
    "Content-Type": "application/json"
  },
  "body": {
    "properties": {
      "email": "{{Work Email}}",
      "firstname": "{{first_name}}",
      "lastname": "{{last_name}}",
      "company": "{{Company Name}}",
      "jobtitle": "{{Job Title}}"
    }
  }
}
```

### Step 6: Monitor Enrichment Results

```bash
# Check your table's enrichment progress in the Clay UI
# Key metrics to watch:
# - Email find rate: target >60%
# - Company enrichment rate: target >85%
# - Average credits per row: target <10
# - ICP score distribution: should have clear A/B/C tiers
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Low email find rate (<40%) | Bad input data | Clean domains, remove personal email domains |
| Credits burning fast | Waterfall hitting all providers | Enable "stop on first result" |
| Duplicate rows in table | Same lead sent twice | Deduplicate before webhook submission |
| CRM push failing | Invalid field mapping | Test HTTP API column on single row first |
| Enrichment not running | Auto-run disabled | Enable auto-run in column settings |

## Output

- Enriched lead table with emails, titles, company data
- ICP scores for lead prioritization
- Qualified leads auto-pushed to CRM
- Credit usage report for cost tracking

## Resources

- [Clay University -- Enrichment Overview](https://university.clay.com/docs/actions-data-credits)
- [Clay University -- CSV Import](https://university.clay.com/docs/csv-import-overview)
- [Clay University -- Sources](https://university.clay.com/docs/sources)

## Next Steps

For AI-powered personalization and CRM sync, see `clay-core-workflow-b`.
