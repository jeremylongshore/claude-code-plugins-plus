---
name: clay-reference-architecture
description: |
  Design production Clay enrichment pipelines with table schemas, waterfall patterns, and CRM sync.
  Use when architecting new Clay integrations, reviewing data flow design,
  or establishing enrichment pipeline standards.
  Trigger with phrases like "clay architecture", "clay best practices",
  "clay pipeline design", "clay reference", "clay data flow".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, clay-reference]

---
# Clay Reference Architecture

## Overview

Production architecture for Clay-based lead enrichment and go-to-market data operations. Covers the three integration patterns (webhook-only, webhook + HTTP API, and full Enterprise API), table schema design, and CRM synchronization flows.

## Prerequisites

- Clay account with appropriate plan tier
- Clear understanding of data volume and enrichment needs
- CRM integration target (HubSpot, Salesforce, etc.)
- Defined Ideal Customer Profile (ICP)

## Instructions

### Step 1: Choose Your Integration Pattern

```
Pattern A: Webhook-Only (All Plans)
──────────────────────────────────────
Your App ──POST──> Clay Webhook ──> Clay Table ──> Enrichment
                                                      │
                                         Manual export via CSV
                                         or native CRM action

Pattern B: Webhook + HTTP API Callback (Growth+ Plans)
──────────────────────────────────────────────────────
Your App ──POST──> Clay Webhook ──> Clay Table ──> Enrichment
                                                      │
                                                HTTP API Column
                                                      │
                                               POST to your app
                                                      │
                                                  CRM / DB

Pattern C: Full Automation with Enterprise API (Enterprise)
──────────────────────────────────────────────────────────
Your App ──POST──> Clay Webhook ──> Clay Table ──> Enrichment
    │                                                  │
    │                                           HTTP API Column
    │                                                  │
    └──Enterprise API──> Person/Company lookup    POST to your app
                         (lightweight, fast)           │
                                                   CRM / DB
```

### Step 2: Design Table Schema

**Standard Lead Enrichment Table:**

```
┌─────────────────────────────────────────────────────────────┐
│ CLAY TABLE: Outbound Leads                                  │
├─────────────┬───────────────┬──────────────────────────────┤
│ Input Cols  │ Enrichment    │ AI + Formula + Output        │
├─────────────┼───────────────┼──────────────────────────────┤
│ domain      │ Company Name  │ ICP Score (formula)          │
│ first_name  │ Employee Count│ Lead Tier (formula: A/B/C)   │
│ last_name   │ Industry      │ Personalized Opener (AI)     │
│ source      │ Tech Stack    │ Recent News (Claygent)       │
│ linkedin_url│ Work Email    │ CRM Push (HTTP API)          │
│             │ Job Title     │ Outreach Push (HTTP API)     │
│             │ Phone Number  │                              │
│             │ LinkedIn URL  │                              │
└─────────────┴───────────────┴──────────────────────────────┘

Column execution order (left to right):
1. Company enrichment (Clearbit) ─ fast, provides context for later columns
2. Person enrichment (Apollo/PDL) ─ medium speed
3. Email waterfall (Apollo > Hunter) ─ conditional: requires domain + name
4. Phone lookup (if needed) ─ conditional: ICP Score >= 80
5. ICP Score formula ─ instant, computes from enriched data
6. Claygent research ─ slow, conditional: ICP Score >= 60
7. AI personalization ─ conditional: ICP Score >= 70
8. CRM push (HTTP API) ─ conditional: ICP Score >= 70 + has email
```

### Step 3: Configure Waterfall Pattern

```yaml
# Recommended waterfall configuration
email_waterfall:
  strategy: "cheapest-first, stop-on-match"
  providers:
    - name: apollo
      credits: 2
      coverage: ~70%
      speed: fast
    - name: hunter
      credits: 2
      coverage: ~60%
      speed: fast
  combined_coverage: ~83%
  max_credits: 4

company_enrichment:
  strategy: "single provider"
  provider: clearbit
  credits: 2
  coverage: ~90%
  fallback: apollo (if Clearbit returns empty)

person_enrichment:
  strategy: "primary + fallback"
  providers:
    - name: apollo
      credits: 2
    - name: people_data_labs
      credits: 3
```

### Step 4: Implement ICP Scoring

```
# Clay Formula Column: ICP Score (0-100)
LET(
  # Company size scoring (0-30)
  size, IF(Employee Count > 1000, 30,
       IF(Employee Count > 200, 25,
       IF(Employee Count > 50, 15,
       IF(Employee Count > 10, 5, 0)))),

  # Industry match (0-30)
  industry, IF(OR(
    Industry = "Software",
    Industry = "Technology",
    Industry = "SaaS",
    Industry = "Information Technology"
  ), 30, IF(OR(
    Industry = "Financial Services",
    Industry = "Healthcare"
  ), 20, 10)),

  # Title seniority (0-25)
  title, IF(OR(
    CONTAINS(Job Title, "CEO"), CONTAINS(Job Title, "CTO"),
    CONTAINS(Job Title, "VP"), CONTAINS(Job Title, "C-Suite")
  ), 25, IF(OR(
    CONTAINS(Job Title, "Director"), CONTAINS(Job Title, "Head of")
  ), 20, IF(
    CONTAINS(Job Title, "Manager"), 10, 5
  ))),

  # Data completeness (0-15)
  data, IF(ISNOTEMPTY(Work Email), 10, 0) +
        IF(ISNOTEMPTY(Phone Number), 5, 0),

  size + industry + title + data
)

# Lead Tier Column
IF(ICP Score >= 80, "A",
IF(ICP Score >= 60, "B",
IF(ICP Score >= 40, "C", "D")))
```

### Step 5: CRM Sync Architecture

```yaml
# HubSpot integration via HTTP API column
crm_sync:
  trigger: "ICP Score >= 70 AND ISNOTEMPTY(Work Email)"
  method: POST
  url: "https://api.hubapi.com/crm/v3/objects/contacts"
  dedup_key: email  # Prevent duplicate contacts
  field_mapping:
    email: "{{Work Email}}"
    firstname: "{{first_name}}"
    lastname: "{{last_name}}"
    company: "{{Company Name}}"
    jobtitle: "{{Job Title}}"
    hs_lead_status: "NEW"
    clay_icp_score: "{{ICP Score}}"
    clay_enrichment_date: "{{_clay_enriched_at}}"

# Alternative: Use Clay's native HubSpot/Salesforce action columns
# (simpler setup, fewer credits, built-in dedup)
native_crm_action:
  type: "HubSpot: Create/Update Contact"
  dedup: "Match on email"
  auto_run: true
  condition: "ICP Score >= 70"
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Enrichment credits exhausted | Too many lookups per row | Use conditional runs, connect own API keys |
| Duplicate CRM records | No dedup key in CRM push | Use email as unique identifier |
| Low email coverage | Single provider waterfall | Add second provider (Apollo + Hunter) |
| Slow table processing | Too many enrichment columns | Add conditional runs, order by speed |
| Stale enrichment data | No re-enrichment schedule | Re-run quarterly on existing contacts |

## Resources

- [Clay University -- Sources](https://university.clay.com/docs/sources)
- [Clay University -- Actions & Data Credits](https://university.clay.com/docs/actions-data-credits)
- [Clay University -- HubSpot Integration](https://university.clay.com/docs/hubspot-integration-overview)

## Next Steps

For multi-environment configuration, see `clay-multi-env-setup`.
