---
name: clay-cost-tuning
description: |
  Optimize Clay credit spending with provider key management, waterfall tuning, and budget controls.
  Use when analyzing Clay costs, reducing credit consumption,
  or implementing spending alerts and caps.
  Trigger with phrases like "clay cost", "clay billing", "reduce clay costs",
  "clay pricing", "clay expensive", "clay budget", "clay credits".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, api, monitoring, cost-optimization]

---
# Clay Cost Tuning

## Overview

Reduce Clay data enrichment spending by connecting your own API keys (70-80% savings), optimizing waterfall depth, improving input data quality, and implementing budget controls. Clay's March 2026 pricing split credits into Data Credits and Actions, changing the optimization calculus.

## Prerequisites

- Clay account with visibility into credit consumption
- Understanding of which enrichment columns are in your tables
- Access to Clay Settings > Plans & Billing

## Instructions

### Step 1: Connect Your Own Provider API Keys (Biggest Savings)

This is the single most impactful cost reduction. Clay charges 0 Data Credits when you use your own API keys:

| Provider | Clay-Managed Cost | Own Key Cost | Annual Savings (10K rows/mo) |
|----------|-------------------|-------------|------------------------------|
| Apollo | 2 credits/lookup | 0 credits | ~240K credits/year |
| Clearbit | 2-5 credits | 0 credits | ~360K credits/year |
| Hunter.io | 2 credits | 0 credits | ~240K credits/year |
| Prospeo | 2 credits | 0 credits | ~240K credits/year |
| People Data Labs | 3 credits | 0 credits | ~360K credits/year |
| ZoomInfo | 5-13 credits | 0 credits | ~1M+ credits/year |

**Setup:** Go to **Settings > Connections** in Clay, click **Add Connection**, and paste your provider API key. All enrichments using that provider will consume 0 Clay credits (1 Action is still consumed per enrichment).

### Step 2: Optimize Waterfall Enrichment Depth

Each waterfall step costs credits (if using Clay-managed keys) and time:

```yaml
# Expensive waterfall (5 providers, 10-15 credits/row):
expensive:
  - apollo:      2 credits
  - hunter:      2 credits
  - prospeo:     2 credits
  - dropcontact: 3 credits
  - findymail:   3 credits
  total_max: 12 credits/row
  coverage: ~92%

# Optimized waterfall (2 providers, 4 credits/row):
optimized:
  - apollo:      2 credits  # Highest coverage provider first
  - hunter:      2 credits  # Strong backup
  total_max: 4 credits/row
  coverage: ~83%
  savings: "67% credit reduction, ~9% coverage loss"
```

**March 2026 change:** Failed lookups no longer cost Data Credits. This makes wider waterfalls less expensive than before, since you only pay when data is actually found.

### Step 3: Pre-Filter Input Data

Credits wasted on unenrichable rows are the most common cost leak:

```typescript
// src/clay/cost-filter.ts
function estimateCreditCost(rows: any[], creditsPerRow: number): {
  filteredRows: any[];
  estimatedCredits: number;
  savings: number;
} {
  const personalDomains = new Set([
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com',
  ]);

  const filtered = rows.filter(row => {
    if (!row.domain?.includes('.')) return false;
    if (personalDomains.has(row.domain)) return false;
    if (!row.first_name || !row.last_name) return false;
    return true;
  });

  // Deduplicate
  const seen = new Set<string>();
  const deduped = filtered.filter(row => {
    const key = `${row.domain}:${row.first_name}:${row.last_name}`.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return {
    filteredRows: deduped,
    estimatedCredits: deduped.length * creditsPerRow,
    savings: (rows.length - deduped.length) * creditsPerRow,
  };
}

// Usage
const { filteredRows, estimatedCredits, savings } = estimateCreditCost(rawLeads, 6);
console.log(`Will process ${filteredRows.length} rows (${estimatedCredits} credits)`);
console.log(`Saved ${savings} credits by pre-filtering`);
```

### Step 4: Use Sampling Before Full Runs

Test enrichment quality on a small sample before committing credits to the full list:

```typescript
// src/clay/sampler.ts
function sampleForTest(rows: any[], sampleSize = 100): {
  sample: any[];
  remaining: any[];
  estimatedTotalCredits: number;
} {
  // Random sample for representative results
  const shuffled = [...rows].sort(() => Math.random() - 0.5);
  const sample = shuffled.slice(0, sampleSize);
  const remaining = shuffled.slice(sampleSize);

  return {
    sample,
    remaining,
    estimatedTotalCredits: rows.length * 6, // Estimate 6 credits/row average
  };
}

// Workflow:
// 1. Send sample (100 rows) to Clay test table
// 2. Check hit rate after enrichment completes
// 3. If hit rate > 60%, proceed with full list
// 4. If hit rate < 40%, clean input data first
```

### Step 5: Implement Credit Budget Alerts

```typescript
// src/clay/budget-monitor.ts
interface CreditBudget {
  monthlyLimit: number;      // From your plan
  dailyThreshold: number;    // Alert if exceeded
  perTableMax: number;       // Cap per table
}

const PLAN_BUDGETS: Record<string, CreditBudget> = {
  launch:     { monthlyLimit: 2_500, dailyThreshold: 125, perTableMax: 500 },
  growth:     { monthlyLimit: 6_000, dailyThreshold: 300, perTableMax: 1_500 },
  enterprise: { monthlyLimit: 50_000, dailyThreshold: 2_500, perTableMax: 10_000 },
};

class BudgetMonitor {
  private dailyUsage = 0;
  private monthlyUsage = 0;
  private tableUsage = new Map<string, number>();

  constructor(private budget: CreditBudget) {}

  recordUsage(tableId: string, credits: number) {
    this.dailyUsage += credits;
    this.monthlyUsage += credits;
    this.tableUsage.set(tableId, (this.tableUsage.get(tableId) || 0) + credits);

    // Check thresholds
    if (this.dailyUsage > this.budget.dailyThreshold) {
      console.warn(`ALERT: Daily credit usage (${this.dailyUsage}) exceeds threshold (${this.budget.dailyThreshold})`);
    }
    if (this.monthlyUsage > this.budget.monthlyLimit * 0.8) {
      console.warn(`ALERT: Monthly credits at ${((this.monthlyUsage / this.budget.monthlyLimit) * 100).toFixed(0)}%`);
    }
    if ((this.tableUsage.get(tableId) || 0) > this.budget.perTableMax) {
      console.error(`STOP: Table ${tableId} exceeded per-table cap (${this.budget.perTableMax} credits)`);
    }
  }
}
```

### Step 6: Credit-Per-Lead Cost Calculator

```typescript
function calculateCostPerLead(
  totalCredits: number,
  totalRows: number,
  rowsWithEmail: number,
  rowsPushedToCRM: number,
): void {
  console.log('=== Clay Cost Analysis ===');
  console.log(`Credits used: ${totalCredits}`);
  console.log(`Cost per row processed: ${(totalCredits / totalRows).toFixed(1)} credits`);
  console.log(`Cost per email found: ${(totalCredits / Math.max(rowsWithEmail, 1)).toFixed(1)} credits`);
  console.log(`Cost per CRM lead: ${(totalCredits / Math.max(rowsPushedToCRM, 1)).toFixed(1)} credits`);
  console.log(`Email find rate: ${((rowsWithEmail / totalRows) * 100).toFixed(1)}%`);
  console.log(`Qualification rate: ${((rowsPushedToCRM / totalRows) * 100).toFixed(1)}%`);
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Credits burning fast | Waterfall enriching all providers | Enable "stop on first result", reduce depth |
| Low hit rate (<30%) | Bad input data | Filter personal domains, validate before import |
| Unexpected charges | New column added with auto-run | Review all auto-run columns monthly |
| Credit rollover capped | Balance exceeds 2x monthly | Use credits before they cap out |

## Resources

- [Clay Pricing 2026](https://www.clay.com/pricing)
- [Clay University -- Actions & Data Credits](https://university.clay.com/docs/actions-data-credits)
- [Clay University -- Plans & Billing](https://university.clay.com/docs/plans-and-billing)

## Next Steps

For reference architecture patterns, see `clay-reference-architecture`.
