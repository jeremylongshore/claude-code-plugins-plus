---
name: clay-reference-architecture
description: |
  Implement Clay reference architecture with best-practice project layout.
  Use when designing new Clay integrations, reviewing project structure,
  or establishing architecture standards for Clay applications.
  Trigger with phrases like "clay architecture", "clay best practices",
  "clay project structure", "how to organize clay", "clay layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clay Reference Architecture

## Overview
Production architecture for Clay-based lead enrichment and data operations. Covers table design, enrichment pipeline patterns, webhook integration, and CRM synchronization flows.

## Prerequisites
- Clay account with API access
- Understanding of Clay tables and enrichment columns
- CRM integration configured (HubSpot, Salesforce)
- Webhook endpoint for automation triggers

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Data Sources                        │
│  CSV Upload │ CRM Import │ API Trigger │ Webhook    │
└──────┬──────────┬──────────┬──────────────┬─────────┘
       │          │          │              │
       ▼          ▼          ▼              ▼
┌─────────────────────────────────────────────────────┐
│              Clay Tables                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Inbound  │  │ Outbound │  │ Enrichment       │   │
│  │ Leads    │  │ Targets  │  │ Queue            │   │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       │              │                 │             │
│       ▼              ▼                 ▼             │
│  ┌──────────────────────────────────────────────┐    │
│  │         Enrichment Columns                    │    │
│  │  Email Finder │ Company Data │ LinkedIn │ AI  │    │
│  └──────────────────────┬───────────────────────┘    │
│                         │                            │
│                         ▼                            │
│  ┌──────────────────────────────────────────────┐    │
│  │         Formula & AI Columns                  │    │
│  │  Lead Score │ ICP Match │ Personalization     │    │
│  └──────────────────────┬───────────────────────┘    │
└─────────────────────────┼───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Destinations                            │
│  CRM Push │ Instantly │ Webhook │ CSV Export         │
└─────────────────────────────────────────────────────┘
```

## Instructions

### Step 1: Design Table Schema
```typescript
// Table structure for lead enrichment pipeline
interface ClayTableSchema {
  // Input columns (from import)
  company_name: string;
  company_domain: string;
  contact_name?: string;
  linkedin_url?: string;

  // Enrichment columns (auto-populated by Clay)
  company_size?: string;       // From Clearbit/Apollo enrichment
  industry?: string;           // From company enrichment
  email?: string;              // From email finder
  phone?: string;              // From phone finder
  technologies?: string[];     // From technographics

  // Formula columns (computed)
  icp_score?: number;          // Formula: weighted scoring
  lead_tier?: 'A' | 'B' | 'C'; // Formula: based on icp_score

  // AI columns
  personalized_intro?: string; // AI: generate intro line
  pain_points?: string;        // AI: identify from company data
}
```

### Step 2: Configure Enrichment Waterfall
```typescript
// Enrichment priority order for email finding
const EMAIL_WATERFALL = [
  { provider: 'apollo', credits: 1 },
  { provider: 'hunter', credits: 1 },
  { provider: 'dropcontact', credits: 2 },
  { provider: 'findymail', credits: 3 },
];

// API trigger for enrichment
async function triggerEnrichment(tableId: string, rowIds: string[]) {
  const response = await fetch('https://api.clay.com/v1/tables/enrich', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.CLAY_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      table_id: tableId,
      row_ids: rowIds,
      columns: ['email', 'company_size', 'industry'],
    }),
  });
  return response.json();
}
```

### Step 3: Webhook Integration for Real-Time Processing
```typescript
import express from 'express';
const app = express();

// Clay sends webhook when enrichment completes
app.post('/webhooks/clay', express.json(), async (req, res) => {
  const { table_id, row_id, data } = req.body;

  if (data.icp_score >= 80 && data.email) {
    // High-value lead: push to CRM immediately
    await pushToCRM({
      email: data.email,
      company: data.company_name,
      score: data.icp_score,
      tier: data.lead_tier,
    });
  }

  if (data.lead_tier === 'A') {
    // Add to outreach sequence
    await addToInstantly(data.email, data.personalized_intro);
  }

  res.json({ status: 'processed' });
});
```

### Step 4: ICP Scoring Formula Pattern
```javascript
// Clay formula column for ICP scoring
// Weighted scoring based on enriched data

function calculateICPScore(row) {
  let score = 0;

  // Company size scoring
  const sizeScores = { '1-10': 10, '11-50': 30, '51-200': 50, '201-500': 40, '500+': 20 };
  score += sizeScores[row.company_size] || 0;

  // Industry match
  const targetIndustries = ['SaaS', 'Technology', 'Software', 'AI'];
  if (targetIndustries.includes(row.industry)) score += 30;

  // Technology match
  const targetTech = ['React', 'Node.js', 'AWS', 'Kubernetes'];
  const techMatches = (row.technologies || []).filter(t => targetTech.includes(t));
  score += techMatches.length * 10;

  return Math.min(score, 100);
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Enrichment credits exhausted | Too many lookups | Use waterfall pattern, set daily limits |
| Duplicate records | Re-importing same list | Deduplicate on domain + contact name |
| Webhook timeout | Processing too slow | Acknowledge immediately, process async |
| Low email find rate | Bad input data | Validate domains before enrichment |

## Examples

### Quick Table Health Check
```typescript
async function checkTableHealth(tableId: string) {
  const rows = await fetchTableRows(tableId);
  return {
    totalRows: rows.length,
    enriched: rows.filter(r => r.email).length,
    scored: rows.filter(r => r.icp_score > 0).length,
    tierA: rows.filter(r => r.lead_tier === 'A').length,
    emailRate: ((rows.filter(r => r.email).length / rows.length) * 100).toFixed(1) + '%',
  };
}
```

## Resources
- [Clay API Documentation](https://docs.clay.com/api)
- [Clay Enrichment Providers](https://docs.clay.com/enrichments)
- [Clay Formulas Guide](https://docs.clay.com/formulas)
