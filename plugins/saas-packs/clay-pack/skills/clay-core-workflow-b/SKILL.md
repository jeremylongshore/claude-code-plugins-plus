---
name: clay-core-workflow-b
description: |
  Use Claygent AI research and AI-powered personalization to generate outreach copy from enriched data.
  Use when writing personalized email openers, running Claygent research prompts,
  or configuring AI columns for campaign personalization at scale.
  Trigger with phrases like "clay AI personalization", "claygent research",
  "clay outreach copy", "clay secondary workflow", "clay AI column".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, workflow, ai, claygent]

---
# Clay Core Workflow B: Claygent AI Research & Personalization

## Overview

Complements the enrichment pipeline (`clay-core-workflow-a`) with AI-powered research and personalization. Uses **Claygent** (Clay's built-in AI research agent powered by GPT-4) to scrape websites, extract insights, and generate personalized outreach copy for each prospect. 30% of Clay customers use Claygent daily, generating 500K+ research tasks per day.

## Prerequisites

- Completed `clay-core-workflow-a` with enriched table
- Clay Pro plan or higher (Claygent requires Pro+)
- Understanding of prompt engineering basics

## Instructions

### Step 1: Add a Claygent Research Column

In your Clay table with enriched leads:

1. Click **+ Add Column > Use AI (Claygent)**
2. Choose model: **Claygent Neon** (best for data extraction and formatting)
3. Write your research prompt referencing table columns:

```
Research {{Company Name}} ({{domain}}) and find:
1. Their most recent funding round (amount, date, investors)
2. Any recent product launches or major announcements from the last 6 months
3. Their primary competitors

Return results as structured data. If information is not found, return "Not found" for that field.
```

4. Enable **Auto-run on new rows**

### Step 2: Configure Multi-Output Claygent (Neon Model)

Claygent Neon can extract multiple data points into separate columns from a single run:

```
Research the company at {{domain}} and extract:

Output 1 (Recent News): The most notable company news from the last 90 days. One sentence.
Output 2 (Tech Stack): List the main technologies they use (check job postings, BuiltWith, Wappalyzer data).
Output 3 (Pain Points): Based on their Glassdoor reviews and recent job postings, identify likely operational pain points.
Output 4 (Competitor): Name their primary competitor.
```

Map each output to a separate column for downstream use in personalization.

### Step 3: Build a Personalized Email Opener Column

Add an **AI column** (not Claygent -- use the faster AI model for text generation):

```
You are a sales copywriter. Write a personalized 2-sentence email opener for {{first_name}} at {{Company Name}}.

Context about the prospect:
- Title: {{Job Title}}
- Company size: {{Employee Count}} employees
- Industry: {{Industry}}
- Recent news: {{Recent News}}
- Tech stack: {{Tech Stack}}

Rules:
- Reference one specific fact about their company (not generic)
- Do NOT use "I noticed" or "I came across" (overused)
- Keep it under 40 words
- Sound human, not AI-generated
- End with a natural transition to your value prop
```

### Step 4: Quality-Check AI Output Before Campaign Launch

Before using AI-generated copy in outreach:

```typescript
// src/workflows/qa-clay-output.ts
interface ClayRow {
  email: string;
  company_name: string;
  personalized_opener: string;
  icp_score: number;
  recent_news: string;
}

function qaCheck(row: ClayRow): { pass: boolean; issues: string[] } {
  const issues: string[] = [];

  // Check opener quality
  if (!row.personalized_opener || row.personalized_opener.length < 20) {
    issues.push('Opener too short or empty');
  }
  if (row.personalized_opener?.includes('{{')) {
    issues.push('Unresolved template variable in opener');
  }
  if (/I noticed|I came across|I saw that/i.test(row.personalized_opener || '')) {
    issues.push('Opener uses banned phrases');
  }

  // Check data completeness
  if (!row.email) issues.push('Missing email');
  if (row.recent_news === 'Not found') issues.push('No research data found');
  if (row.icp_score < 50) issues.push('Low ICP score');

  return { pass: issues.length === 0, issues };
}
```

### Step 5: Export Campaign-Ready Data

Configure an HTTP API column to push qualified, personalized leads to your outreach tool:

```json
{
  "method": "POST",
  "url": "https://api.instantly.ai/api/v1/lead/add",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer {{Instantly API Key}}"
  },
  "body": {
    "campaign_id": "your-campaign-id",
    "email": "{{Work Email}}",
    "first_name": "{{first_name}}",
    "last_name": "{{last_name}}",
    "company_name": "{{Company Name}}",
    "personalization": "{{personalized_opener}}",
    "custom_variables": {
      "recent_news": "{{Recent News}}",
      "tech_stack": "{{Tech Stack}}"
    }
  }
}
```

Set conditional run: `ICP Score >= 70 AND ISNOTEMPTY(Work Email) AND ISNOTEMPTY(personalized_opener)`

### Step 6: Claygent Navigator for Dynamic Websites

For sites that require interaction (filtering, clicking, scrolling):

1. Add a Claygent column with **Navigator** mode enabled
2. Navigator can click buttons, fill search forms, and extract data from dynamic pages

```
Navigate to {{domain}}/pricing and extract:
1. Number of pricing tiers
2. Starting price
3. Whether they offer a free tier
4. Enterprise pricing model (contact sales vs. listed)

If the pricing page requires interaction (e.g., toggle annual/monthly), switch to annual pricing first.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Claygent returns "Not found" | Company too small or private | Skip personalization, use generic opener |
| AI opener references wrong company | Column mapping error | Verify `{{column}}` references match table headers |
| Claygent timeout | Complex research prompt | Simplify prompt, break into multiple columns |
| High credit cost per row | Claygent + AI + enrichment stacking | Run Claygent only on ICP-qualified rows (score >= 60) |
| Template variables in output | AI hallucinating Clay syntax | Add "Do not include curly braces" to prompt |

## Output

- Claygent research data (news, tech stack, competitors) per prospect
- Personalized email openers at scale
- Campaign-ready export to outreach tools
- QA report flagging low-quality rows

## Resources

- [Clay University -- Claygent AI Web Scraper](https://www.clay.com/university/lesson/claygent-ai-web-scraper-clay-101)
- [Clay -- 11 AI Prompts for Prospect Research](https://www.clay.com/university/lesson/11-ai-prompts-to-automate-prospect-research-with-claygent-automated-outbound)
- [Claygent Product Page](https://www.clay.com/claygent)

## Next Steps

For common errors, see `clay-common-errors`.
