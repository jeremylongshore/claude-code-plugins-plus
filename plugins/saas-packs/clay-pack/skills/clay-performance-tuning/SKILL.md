---
name: clay-performance-tuning
description: |
  Optimize Clay table enrichment throughput, reduce processing time, and improve hit rates.
  Use when experiencing slow enrichment, poor email find rates,
  or needing to process large tables efficiently.
  Trigger with phrases like "clay performance", "optimize clay", "clay slow",
  "clay throughput", "clay fast enrichment", "clay batch optimization".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, api, performance]

---
# Clay Performance Tuning

## Overview

Optimize Clay table processing speed, enrichment hit rates, and credit efficiency. Clay processes enrichment columns sequentially per row, and each enrichment column makes external API calls. Performance tuning focuses on reducing wasted enrichments, ordering columns optimally, and managing table auto-run behavior.

## Prerequisites

- Clay table with enrichment columns configured
- Understanding of which providers are in your waterfall
- Access to Clay table settings and column configuration

## Instructions

### Step 1: Order Enrichment Columns by Speed

Clay runs enrichment columns left-to-right. Place fast columns first:

| Column Type | Typical Speed | Position |
|-------------|---------------|----------|
| Company lookup (Clearbit) | ~100ms | First (fastest) |
| Email finder (single provider) | ~200ms | Second |
| Email waterfall (multi-provider) | 1-10s | Middle |
| Claygent AI research | 5-30s | Later |
| HTTP API (outbound call) | Variable | Last |
| AI text generation | 2-5s | After Claygent |

**Why order matters:** Fast columns populate data that slow columns may need as input (e.g., company name feeds into Claygent research prompt).

### Step 2: Add Conditional Run Rules

Prevent enrichments from running on rows that won't yield results:

```
# In Clay column settings > "Only run if" condition:

# Email waterfall: only run if we have enough input data
ISNOTEMPTY(domain) AND ISNOTEMPTY(first_name) AND ISNOTEMPTY(last_name)

# Claygent: only run for high-value prospects
ICP Score >= 60 AND ISNOTEMPTY(Company Name)

# CRM push: only run for enriched, qualified leads
ICP Score >= 70 AND ISNOTEMPTY(Work Email)
```

This prevents:
- Waterfall enrichment on rows with missing domains (wasted credits)
- Claygent research on low-value prospects (expensive AI credits)
- CRM pushes for incomplete records

### Step 3: Optimize Input Data Before Import

```typescript
// src/clay/pre-process.ts — clean data before sending to Clay
interface RawLead {
  domain?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
}

function preProcessForClay(rows: RawLead[]): {
  ready: RawLead[];
  filtered: { row: RawLead; reason: string }[];
  stats: { total: number; ready: number; filtered: number; deduped: number };
} {
  const personalDomains = new Set([
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
    'icloud.com', 'aol.com', 'protonmail.com', 'mail.com',
  ]);

  const seen = new Set<string>();
  const ready: RawLead[] = [];
  const filtered: { row: RawLead; reason: string }[] = [];
  let deduped = 0;

  for (const row of rows) {
    // Normalize domain
    const domain = row.domain?.toLowerCase().trim().replace(/^(https?:\/\/)?(www\.)?/, '').replace(/\/.*$/, '');

    // Filter invalid
    if (!domain || !domain.includes('.')) {
      filtered.push({ row, reason: 'invalid domain' });
      continue;
    }
    if (personalDomains.has(domain)) {
      filtered.push({ row, reason: 'personal email domain' });
      continue;
    }
    if (!row.first_name?.trim() || !row.last_name?.trim()) {
      filtered.push({ row, reason: 'missing name' });
      continue;
    }

    // Deduplicate
    const key = `${domain}:${row.first_name?.toLowerCase()}:${row.last_name?.toLowerCase()}`;
    if (seen.has(key)) {
      deduped++;
      continue;
    }
    seen.add(key);

    ready.push({ ...row, domain });
  }

  return {
    ready,
    filtered,
    stats: {
      total: rows.length,
      ready: ready.length,
      filtered: filtered.length,
      deduped,
    },
  };
}

// Usage
const { ready, stats } = preProcessForClay(rawLeads);
console.log(`Pre-processing: ${stats.total} total -> ${stats.ready} ready (${stats.filtered} filtered, ${stats.deduped} deduped)`);
// Typical result: 30-50% of rows filtered, saving that many credits
```

### Step 4: Limit Waterfall Depth

Each additional waterfall provider adds 1-5 seconds per row and burns credits if the previous providers already found data:

```yaml
# Before: 5-provider waterfall (slow, expensive)
# Each provider: ~2 credits, ~2s
# Worst case: 10 credits, 10s per row
waterfall_deep:
  providers: [apollo, hunter, prospeo, dropcontact, findymail]
  max_time_per_row: "~10s"
  max_credits_per_row: 10

# After: 2-provider waterfall (fast, cheap)
# Covers 80%+ of findable emails with 2 providers
waterfall_optimized:
  providers: [apollo, hunter]
  max_time_per_row: "~4s"
  max_credits_per_row: 4
  coverage_loss: "~5-10%"
```

**Rule of thumb:** Apollo + one backup provider covers 80-85% of findable work emails. Adding more providers gives diminishing returns.

### Step 5: Use Table-Level Auto-Update Controls

```yaml
# Table Settings in Clay UI:
table_auto_update: ON   # Parent switch: if OFF, nothing auto-runs
column_settings:
  company_lookup:
    auto_run: ON          # Runs on every new row
  email_waterfall:
    auto_run: ON          # Runs on every new row (if condition met)
    condition: "ISNOTEMPTY(domain)"
  claygent_research:
    auto_run: OFF         # Manual trigger only (expensive)
  crm_push:
    auto_run: ON          # Auto-push qualified leads
    condition: "ICP Score >= 70"
```

### Step 6: Schedule Large Imports for Off-Peak

Clay's enrichment providers respond faster during off-peak hours (US nighttime):

```typescript
// src/clay/scheduler.ts
function shouldProcessNow(rowCount: number): { proceed: boolean; reason: string } {
  const hour = new Date().getUTCHours();
  const isOffPeak = hour >= 2 && hour <= 8; // 2am-8am UTC

  if (rowCount < 100) {
    return { proceed: true, reason: 'Small batch — process anytime' };
  }

  if (rowCount >= 1000 && !isOffPeak) {
    return {
      proceed: false,
      reason: `Large batch (${rowCount} rows). Schedule for 02:00-08:00 UTC for faster provider responses.`,
    };
  }

  return { proceed: true, reason: isOffPeak ? 'Off-peak — optimal time' : 'Medium batch — acceptable' };
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Table stuck processing | Provider rate limit hit | Wait for reset or reduce concurrency |
| Slow enrichment (>10s/row) | Deep waterfall (5+ providers) | Reduce to 2-3 providers |
| Low hit rate (<40%) | Bad input data | Pre-validate and filter before import |
| Credits burning with no results | No conditional run rules | Add "Only run if" conditions to columns |
| Enrichment re-runs on edit | Table auto-update triggered | Turn off auto-update during bulk edits |

## Output

- Optimized table with conditional enrichment rules
- Pre-processed input data (30-50% credit savings typical)
- Column order optimized for speed
- Waterfall depth reduced to 2-3 providers

## Resources

- [Clay University -- Table Management Settings](https://university.clay.com/docs/table-management-settings)
- [Clay University -- Actions & Data Credits](https://university.clay.com/docs/actions-data-credits)

## Next Steps

For cost optimization, see `clay-cost-tuning`.
