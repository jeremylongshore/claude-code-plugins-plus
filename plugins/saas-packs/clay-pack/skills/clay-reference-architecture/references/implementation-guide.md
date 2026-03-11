# Clay Reference Architecture — Implementation Guide

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

## Table Schema Design

```typescript
interface ClayTableSchema {
  // Input columns (from import)
  company_name: string;
  company_domain: string;
  contact_name?: string;
  linkedin_url?: string;

  // Enrichment columns (auto-populated by Clay)
  company_size?: string;
  industry?: string;
  email?: string;
  phone?: string;
  technologies?: string[];

  // Formula columns (computed)
  icp_score?: number;
  lead_tier?: 'A' | 'B' | 'C';

  // AI columns
  personalized_intro?: string;
  pain_points?: string;
}
```

## Enrichment Waterfall Configuration

```typescript
const EMAIL_WATERFALL = [
  { provider: 'apollo', credits: 1 },
  { provider: 'hunter', credits: 1 },
  { provider: 'dropcontact', credits: 2 },
  { provider: 'findymail', credits: 3 },
];

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

## Webhook Integration for Real-Time Processing

```typescript
import express from 'express';
const app = express();

app.post('/webhooks/clay', express.json(), async (req, res) => {
  const { table_id, row_id, data } = req.body;

  if (data.icp_score >= 80 && data.email) {
    await pushToCRM({
      email: data.email,
      company: data.company_name,
      score: data.icp_score,
      tier: data.lead_tier,
    });
  }

  if (data.lead_tier === 'A') {
    await addToInstantly(data.email, data.personalized_intro);
  }

  res.json({ status: 'processed' });
});
```

## ICP Scoring Formula

```javascript
function calculateICPScore(row) {
  let score = 0;

  const sizeScores = { '1-10': 10, '11-50': 30, '51-200': 50, '201-500': 40, '500+': 20 };
  score += sizeScores[row.company_size] || 0;

  const targetIndustries = ['SaaS', 'Technology', 'Software', 'AI'];
  if (targetIndustries.includes(row.industry)) score += 30;

  const targetTech = ['React', 'Node.js', 'AWS', 'Kubernetes'];
  const techMatches = (row.technologies || []).filter(t => targetTech.includes(t));
  score += techMatches.length * 10;

  return Math.min(score, 100);
}
```

## Table Health Check

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
