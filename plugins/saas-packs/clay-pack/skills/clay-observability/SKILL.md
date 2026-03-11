---
name: clay-observability
description: |
  Set up comprehensive observability for Clay integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Clay operations, setting up dashboards,
  or configuring alerting for Clay integration health.
  Trigger with phrases like "clay monitoring", "clay metrics",
  "clay observability", "monitor clay", "clay alerts", "clay tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Observability

## Overview
Monitor Clay data enrichment pipeline health, credit consumption velocity, and enrichment success rates. Clay's credit-based pricing model means observability must track per-enrichment costs (email lookup: ~1 credit, company enrichment: ~5 credits, waterfall enrichment: variable).

## Prerequisites
- Clay Team or Enterprise plan
- API access for usage queries
- External metrics/alerting system

## Instructions

### Step 1: Track Credit Consumption in Real Time
```bash
set -euo pipefail
# Query current credit usage by table
curl "https://api.clay.com/v1/workspace/usage?group_by=table&period=today" \
  -H "Authorization: Bearer $CLAY_API_KEY" | \
  jq '.usage[] | {table_name, credits_used, rows_enriched, avg_credits_per_row: (.credits_used / (.rows_enriched + 0.01))}'
```

### Step 2: Monitor Enrichment Hit Rates
```typescript
// clay-enrichment-monitor.ts
async function monitorEnrichments() {
  const tables = await clayApi.listTables();
  for (const table of tables) {
    const stats = await clayApi.getTableStats(table.id);
    const hitRate = stats.rows_with_data / Math.max(stats.total_rows, 1) * 100;
    emitGauge('clay_enrichment_hit_rate_pct', hitRate, { table: table.name, enrichment: stats.enrichment_type });
    emitCounter('clay_credits_consumed', stats.credits_used, { table: table.name });

    if (hitRate < 30) {
      console.warn(`Low hit rate on ${table.name}: ${hitRate.toFixed(1)}% (check enrichment config)`);
    }
  }
}
```

### Step 3: Set Up Credit Burn Alerts
```yaml
groups:
  - name: clay
    rules:
      - alert: ClayCreditBurnHigh
        expr: rate(clay_credits_consumed[1h]) > 500  # HTTP 500 Internal Server Error
        annotations: { summary: "Clay burning >500 credits/hour (projected monthly: {{ $value * 720 }})" }  # 720: HTTP 500 Internal Server Error
      - alert: ClayLowHitRate
        expr: clay_enrichment_hit_rate_pct < 20
        for: 30m
        annotations: { summary: "Clay enrichment hit rate below 20% on {{ $labels.table }}" }
      - alert: ClayCreditBalance
        expr: clay_credits_remaining < 1000  # 1000: 1 second in ms
        annotations: { summary: "Clay credit balance below 1,000 -- refill needed" }
```

### Step 4: Log Enrichment Results for Audit
```json
{"ts":"2026-03-10T14:30:00Z","table":"outbound-leads","enrichment":"email_finder","rows_attempted":100,"rows_enriched":72,"credits_used":100,"hit_rate":72.0,"duration_ms":4500}  # 2026: 4500 = configured value
```

### Step 5: Build a Credit Efficiency Dashboard
Key panels: credit consumption by table (bar chart), enrichment hit rate by provider, daily/weekly credit burn trend, credits remaining gauge, and cost-per-enriched-row (credits used / rows with actual data returned). Tables with low hit rates and high credit burn are optimization targets.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Credits depleting fast | Waterfall enrichment trying all providers | Limit waterfall steps or set credit cap per row |
| Hit rate near 0% | Bad input data (invalid emails/domains) | Clean input data before enrichment |
| API timeout on enrichment | Provider rate limit | Reduce table auto-enrich concurrency |
| Usage API returning stale data | Caching lag | Wait 5 minutes for usage data to update |

## Examples

**Basic usage**: Apply clay observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack