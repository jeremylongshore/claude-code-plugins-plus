---
name: clay-cost-tuning
description: |
  Optimize Clay costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Clay billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "clay cost", "clay billing",
  "reduce clay costs", "clay pricing", "clay expensive", "clay budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Cost Tuning

## Overview
Reduce Clay data enrichment spending by optimizing credit usage per enrichment, limiting waterfall depth, and improving input data quality. Clay uses credit-based pricing where each enrichment provider costs different credits (email finder: ~1 credit, company enrichment: ~5 credits, waterfall enrichment: 3-15 credits depending on fallback depth).

## Prerequisites
- Clay account with visibility into credit consumption
- Understanding of which enrichment columns are in your tables
- Access to enrichment hit rate statistics

## Instructions

### Step 1: Audit Credit Consumption by Enrichment Type
```bash
set -euo pipefail
# Break down credits by enrichment provider/type
curl "https://api.clay.com/v1/workspace/usage?group_by=enrichment&period=last_30d" \
  -H "Authorization: Bearer $CLAY_API_KEY" | \
  jq '.usage[] | {enrichment: .enrichment_type, credits: .total_credits, rows: .rows_enriched, hit_rate_pct: (.rows_with_data / .rows_enriched * 100), cost_per_hit: (.total_credits / (.rows_with_data + 0.01))}' | \
  jq -s 'sort_by(-.credits)'
```

### Step 2: Limit Waterfall Enrichment Depth
```yaml
# Instead of running all 5 email finder providers (15 credits/row):
waterfall_before:
  - provider: clearbit     # 3 credits
  - provider: hunter       # 3 credits
  - provider: apollo       # 3 credits
  - provider: rocketreach  # 3 credits
  - provider: snov         # 3 credits
  # Total: 15 credits/row if none find email

# Cap at 2 providers (6 credits max):
waterfall_after:
  - provider: apollo       # 3 credits (highest hit rate first)
  - provider: hunter       # 3 credits
  # Total: 6 credits/row max, 3 if first provider hits
```

### Step 3: Clean Input Data Before Enrichment
```typescript
// Pre-validate data to avoid wasting credits on unenrichable rows
function shouldEnrich(row: any): boolean {
  // Skip rows with invalid domains
  if (row.domain && !row.domain.includes('.')) return false;
  // Skip personal email domains
  const personalDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'];
  if (personalDomains.includes(row.domain)) return false;
  // Skip already enriched rows
  if (row.email && row.email.includes('@')) return false;
  return true;
}
// Apply filter before running enrichment: 30-50% credit savings typical
```

### Step 4: Use Sampling for Large Tables
```yaml
# Instead of enriching 10,000 rows at once:
# 1. Enrich a 500-row sample first
# 2. Check hit rate and data quality
# 3. If hit rate >60%, proceed with full table
# 4. If hit rate <40%, clean input data first

sample_workflow:
  step1: "Import 500-row sample into test table"  # HTTP 500 Internal Server Error
  step2: "Run enrichments, check hit rate"
  step3: "If good, import full list into production table"
  step4: "Set max_rows limit as safety cap"
```

### Step 5: Set Table-Level Credit Caps
```bash
set -euo pipefail
# Configure maximum credits per table to prevent runaway costs
curl -X PATCH "https://api.clay.com/v1/tables/tbl_abc123" \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  -d '{"max_rows": 1000, "auto_enrich": false}'  # 1000: 1 second in ms
# Disable auto_enrich and trigger manually after data review
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Credits burning fast | Waterfall enriching every row | Limit waterfall to 2-3 providers max |
| Low hit rate (<30%) | Bad input data (personal emails, typos) | Clean data before enrichment |
| Table over-enriching | auto_enrich on with new rows streaming in | Disable auto_enrich, use manual triggers |
| Unexpected charge | New enrichment column added without cap | Always set credit limits per table |

## Examples

**Basic usage**: Apply clay cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay cost tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack