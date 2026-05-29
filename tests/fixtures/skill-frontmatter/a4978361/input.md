---
name: product-researcher
description: |
  Competitive intelligence and product analysis for the claude-code-plugins repo
  and tonsofskills.com marketplace. Crawls competitor sites, analyzes gaps, and
  produces actionable reports with separate repo vs website recommendations.
  Trigger with "research my product", "competitive analysis", "product research",
  "analyze competitors", "/product-researcher".
allowed-tools: 'Read,Glob,Grep,WebSearch,WebFetch,Bash(wc:*),Bash(jq:*)'
metadata:
  author: 'Jeremy Longshore <jeremy@intentsolutions.io>'
  version: '1.0.0'
  tier: enterprise
  category: product-management
---

# Product Researcher

Competitive intelligence engine for Jeremy's two-product ecosystem:

1. **claude-code-plugins** — open-source monorepo (GitHub)
2. **tonsofskills.com** — Astro 5 marketplace frontend (Firebase hosting)

## Product Context (Baked In)

### claude-code-plugins repo

- **Location**: `~/000-projects/claude-code-plugins`
- **Stats**: 340 plugins, 1537+ skills, pnpm workspaces
- **Marketplace metadata**: `.claude-plugin/marketplace.extended.json`
- **Plugin categories**: ai-ml, devops, security, api-development, automation, business-tools, etc.
- **Key features**: SaaS integration packs, skill tiers, verification system
- **Differentiator**: Largest open-source Claude Code plugin collection

### tonsofskills.com website

- **Stack**: Astro 5, Firebase hosting
- **Purpose**: Marketplace frontend — browse, search, install plugins/skills
- **Key pages**: Plugin catalog, skill browser, SaaS pack landing pages

### Known Competitors

- awesome-claude-code (GitHub awesome lists)
- awesome-claude-skills repos
- VoltAgent and similar agent frameworks
- Individual plugin authors with standalone repos
- Anthropic's own plugin/skill ecosystem efforts

## Instructions

Execute all steps sequentially. Do NOT skip any step.

### Step 1: Read Current Product State

Read local repo data to establish baseline:

1. Read `~/000-projects/claude-code-plugins/.claude-plugin/marketplace.extended.json` — extract totalPlugins, skillsEnabled, version, lastUpdated
2. Use Glob to count plugin directories: `plugins/*/**/.claude-plugin`
3. Use Grep to find SaaS pack references and count them
4. Read any roadmap or tracker files if present

Summarize findings as a **Current State Snapshot** table.

### Step 2: Research Competitors

Use WebSearch to investigate each competitor category:

1. **Search queries** (run at least 4):
   - `"claude code plugins" marketplace OR collection 2026`
   - `"claude code skills" repository OR hub`
   - `awesome-claude-code github`
   - `claude code extension marketplace`
   - `VoltAgent claude code`

2. **For each competitor found**, use WebFetch to gather:
   - Plugin/skill count
   - Category coverage
   - Quality indicators (tests, docs, maintenance)
   - Pricing model (free/paid/freemium)
   - Community engagement (stars, forks, contributors)
   - Last update date

### Step 3: Build Comparison Matrix

Create a structured comparison table:

| Dimension               | claude-code-plugins | Competitor A | Competitor B | ... |
| ----------------------- | ------------------- | ------------ | ------------ | --- |
| Total plugins           |                     |              |              |     |
| Total skills            |                     |              |              |     |
| Categories              |                     |              |              |     |
| Quality (tests/docs)    |                     |              |              |     |
| Update frequency        |                     |              |              |     |
| Community (stars/forks) |                     |              |              |     |
| Pricing                 |                     |              |              |     |
| Unique features         |                     |              |              |     |
| Website/UX              |                     |              |              |     |

### Step 4: Gap Analysis

For each dimension, identify:

- **Strengths**: Where we lead and should double down
- **Gaps**: Where competitors do something we don't
- **Opportunities**: Unserved needs nobody addresses yet
- **Threats**: Emerging competitors or platform changes

### Step 5: Generate Recommendations

Split into two sections:

#### REPO Recommendations (claude-code-plugins)

Prioritized list of improvements with:

- **Action**: Specific, implementable change
- **Impact**: High/Medium/Low
- **Effort**: T-shirt size (S/M/L/XL)
- **Rationale**: Why this matters competitively

#### WEBSITE Recommendations (tonsofskills.com)

Same format, focused on:

- UX improvements
- SEO opportunities
- Conversion optimization
- Content gaps
- Feature additions

### Step 6: Output Report

Format the complete analysis as:

```
# Competitive Analysis Report
**Date**: {today}
**Products**: claude-code-plugins repo + tonsofskills.com

## Executive Summary
{3-4 sentence overview of competitive position}

## Current State
{Step 1 findings}

## Competitive Landscape
{Step 3 comparison matrix}

## Gap Analysis
{Step 4 findings}

## Recommendations: REPO
{Step 5 repo recommendations, numbered and prioritized}

## Recommendations: WEBSITE
{Step 5 website recommendations, numbered and prioritized}

## Next Actions
{Top 3 things to do this week}
```

## Examples

```
User: "research my product against competitors"
→ Reads marketplace.extended.json, runs 4+ WebSearch queries, fetches competitor
  repos, builds comparison matrix, outputs full report with separate REPO and
  WEBSITE recommendation sections.

User: "competitive analysis focused on plugin quality"
→ Same workflow but emphasizes quality dimensions (tests, docs, maintenance) in
  the comparison matrix and recommendations.

User: "how do we compare to awesome-claude-code?"
→ Focused single-competitor deep dive with detailed feature-by-feature comparison.
```

## Error Handling

| Error                             | Cause                                     | Solution                                                     |
| --------------------------------- | ----------------------------------------- | ------------------------------------------------------------ |
| WebSearch returns no results      | Query too specific or service unavailable | Broaden search terms, try alternative queries                |
| marketplace.extended.json missing | Repo not at expected path                 | Ask user for repo location                                   |
| WebFetch blocked/timeout          | Competitor site blocks scraping           | Note as "data unavailable" and proceed with what's available |
| No competitors found              | Niche too new or search terms off         | Report findings honestly, suggest manual competitor list     |
