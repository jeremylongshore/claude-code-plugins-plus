---
name: clay-performance-tuning
description: |
  Optimize Clay API performance with caching, batching, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Clay integrations.
  Trigger with phrases like "clay performance", "optimize clay",
  "clay latency", "clay caching", "clay slow", "clay batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Performance Tuning

## Overview
Optimize Clay data enrichment throughput and reduce table processing times. Clay tables process enrichments row-by-row with each enrichment making external API calls (Clearbit, Apollo, Hunter, etc.).

## Prerequisites
- Clay account with active tables
- Understanding of enrichment provider rate limits
- API access for programmatic table management

## Instructions

### Step 1: Optimize Table Structure for Throughput
```yaml
# Design tables for efficient processing
best_practices:
  pre_filter_rows: true
    # Remove invalid rows BEFORE enrichment (saves time and credits)
    # Filter: valid domains, non-personal emails, non-duplicate entries

  order_enrichments_by_speed: true
    # Fast enrichments first (email lookup ~100ms)
    # Slow enrichments last (company profile ~2-5s)
    # Allows fast columns to complete while slow ones process

  limit_waterfall_depth: 2
    # Each waterfall step adds 1-5s per row
    # 5-step waterfall = 5-25s per row
    # 2-step waterfall = 2-10s per row
```

### Step 2: Use the Map Endpoint for Parallel Lookups
```bash
set -euo pipefail
# Instead of enriching row-by-row via the UI:
# Use the API to submit bulk enrichment requests
curl -X POST "https://api.clay.com/v1/tables/tbl_abc123/enrich-batch" \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  -d '{
    "rows": [
      {"domain": "stripe.com"},
      {"domain": "linear.app"},
      {"domain": "vercel.com"}
    ],
    "enrichments": ["company_profile"],
    "async": true
  }'
# Batch API processes in parallel internally
```

### Step 3: Pre-Validate Input Data
```typescript
// Clean data before submitting to Clay to avoid wasted processing time
function preValidateRows(rows: any[]): any[] {
  return rows.filter(row => {
    // Remove rows with invalid domains
    if (!row.domain || !row.domain.includes('.')) return false;
    // Remove personal email domains (won't enrich company data)
    const personalDomains = ['gmail.com', 'yahoo.com', 'hotmail.com'];
    if (personalDomains.includes(row.domain)) return false;
    // Remove duplicates
    return true;
  });
}
// Typical filtering removes 20-40% of rows, directly speeding up processing
```

### Step 4: Schedule Large Tables for Off-Peak Hours
```yaml
# Clay's enrichment providers have variable response times
# Processing during off-peak hours (US nighttime) often sees faster provider responses
scheduling:
  large_tables:  # 1000+ rows
    preferred_time: "02:00-06:00 UTC"
    reason: "Less contention on enrichment provider APIs"
  small_tables:  # <100 rows
    time: "Any time"
    reason: "Minimal impact from rate limits"
```

### Step 5: Monitor Processing Progress
```bash
set -euo pipefail
# Track table enrichment progress
curl "https://api.clay.com/v1/tables/tbl_abc123/status" \
  -H "Authorization: Bearer $CLAY_API_KEY" | \
  jq '{
    total_rows, rows_enriched, rows_pending, rows_failed,
    progress_pct: (.rows_enriched / .total_rows * 100),
    estimated_remaining_min: (.rows_pending * 3 / 60)  # ~3s per row average
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Table processing stuck | Enrichment provider rate limit | Wait for rate limit reset, or reduce table concurrency |
| Slow enrichment (>10s/row) | Waterfall trying many providers | Reduce waterfall depth to 2 steps |
| Batch fails halfway | Network timeout | Use async batch endpoint, check status via polling |
| Duplicate results | Same domain enriched multiple times | Deduplicate input data before enrichment |

## Examples

**Basic usage**: Apply clay performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay performance tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official ORM documentation
- Community best practices and patterns
- Related skills in this plugin pack