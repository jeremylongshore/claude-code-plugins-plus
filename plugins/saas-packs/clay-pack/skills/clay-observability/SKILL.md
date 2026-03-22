---
name: clay-observability
description: |
  Monitor Clay enrichment pipeline health, credit consumption, and data quality metrics.
  Use when setting up dashboards for Clay operations, configuring alerts for credit burn,
  or tracking enrichment success rates.
  Trigger with phrases like "clay monitoring", "clay metrics", "clay observability",
  "monitor clay", "clay alerts", "clay dashboard", "clay credit tracking".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, monitoring, observability, dashboard]

---
# Clay Observability

## Overview

Monitor Clay data enrichment pipeline health across four dimensions: credit consumption velocity, enrichment success rates (hit rates), data quality scores, and CRM sync reliability. Clay's credit-based pricing model makes observability essential for cost control.

## Prerequisites

- Clay account with table access
- Metrics infrastructure (Prometheus/Grafana, Datadog, or custom)
- Webhook receiver that logs enrichment results
- Understanding of your enrichment column configuration

## Instructions

### Step 1: Instrument Your Clay Webhook Handler

```typescript
// src/clay/metrics.ts — collect metrics from enriched data flowing back from Clay
interface ClayMetrics {
  enrichmentsReceived: number;
  enrichmentsWithEmail: number;
  enrichmentsWithCompany: number;
  enrichmentsWithPhone: number;
  estimatedCreditsUsed: number;
  averageICPScore: number;
  leadsTier: { A: number; B: number; C: number; D: number };
}

class ClayMetricsCollector {
  private metrics: ClayMetrics = {
    enrichmentsReceived: 0,
    enrichmentsWithEmail: 0,
    enrichmentsWithCompany: 0,
    enrichmentsWithPhone: 0,
    estimatedCreditsUsed: 0,
    averageICPScore: 0,
    leadsTier: { A: 0, B: 0, C: 0, D: 0 },
  };
  private scoreSum = 0;

  record(lead: Record<string, any>, creditsPerRow: number = 6) {
    this.metrics.enrichmentsReceived++;
    if (lead.work_email) this.metrics.enrichmentsWithEmail++;
    if (lead.company_name) this.metrics.enrichmentsWithCompany++;
    if (lead.phone_number) this.metrics.enrichmentsWithPhone++;
    this.metrics.estimatedCreditsUsed += creditsPerRow;

    const score = lead.icp_score || 0;
    this.scoreSum += score;
    this.metrics.averageICPScore = this.scoreSum / this.metrics.enrichmentsReceived;

    if (score >= 80) this.metrics.leadsTier.A++;
    else if (score >= 60) this.metrics.leadsTier.B++;
    else if (score >= 40) this.metrics.leadsTier.C++;
    else this.metrics.leadsTier.D++;
  }

  getReport(): string {
    const m = this.metrics;
    const emailRate = m.enrichmentsReceived > 0
      ? ((m.enrichmentsWithEmail / m.enrichmentsReceived) * 100).toFixed(1)
      : '0';
    const companyRate = m.enrichmentsReceived > 0
      ? ((m.enrichmentsWithCompany / m.enrichmentsReceived) * 100).toFixed(1)
      : '0';

    return [
      `=== Clay Enrichment Report ===`,
      `Total processed: ${m.enrichmentsReceived}`,
      `Email find rate: ${emailRate}%`,
      `Company match rate: ${companyRate}%`,
      `Avg ICP score: ${m.averageICPScore.toFixed(1)}`,
      `Lead distribution: A=${m.leadsTier.A} B=${m.leadsTier.B} C=${m.leadsTier.C} D=${m.leadsTier.D}`,
      `Estimated credits used: ${m.estimatedCreditsUsed}`,
      `Cost per email found: ${(m.estimatedCreditsUsed / Math.max(m.enrichmentsWithEmail, 1)).toFixed(1)} credits`,
    ].join('\n');
  }
}
```

### Step 2: Set Up Prometheus Metrics (Optional)

```typescript
// src/clay/prometheus-metrics.ts
import { Counter, Gauge, Histogram } from 'prom-client';

// Counters
const clayEnrichmentsTotal = new Counter({
  name: 'clay_enrichments_total',
  help: 'Total enrichments received from Clay',
  labelNames: ['table', 'status'],
});

const clayCreditsUsed = new Counter({
  name: 'clay_credits_used_total',
  help: 'Estimated Clay credits consumed',
  labelNames: ['table', 'enrichment_type'],
});

// Gauges
const clayHitRate = new Gauge({
  name: 'clay_enrichment_hit_rate',
  help: 'Enrichment hit rate percentage',
  labelNames: ['table', 'field'],
});

const clayCreditBalance = new Gauge({
  name: 'clay_credit_balance',
  help: 'Remaining Clay credits',
});

const clayICPScore = new Histogram({
  name: 'clay_icp_score',
  help: 'Distribution of ICP scores',
  buckets: [20, 40, 60, 80, 100],
  labelNames: ['table'],
});

// Record enrichment
function recordEnrichment(table: string, lead: Record<string, any>) {
  clayEnrichmentsTotal.inc({ table, status: lead.work_email ? 'enriched' : 'empty' });
  clayCreditsUsed.inc({ table, enrichment_type: 'waterfall' }, 6);
  clayICPScore.observe({ table }, lead.icp_score || 0);
}
```

### Step 3: Configure Alerting Rules

```yaml
# prometheus/clay-alerts.yml
groups:
  - name: clay-enrichment
    rules:
      - alert: ClayCreditBurnHigh
        expr: rate(clay_credits_used_total[1h]) > 200
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Clay credit burn rate > 200/hour. Monthly projection: {{ $value | humanize }} credits"

      - alert: ClayLowEmailHitRate
        expr: clay_enrichment_hit_rate{field="email"} < 40
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Email find rate below 40% on table {{ $labels.table }}. Check input data quality."

      - alert: ClayCreditBalanceLow
        expr: clay_credit_balance < 500
        labels:
          severity: critical
        annotations:
          summary: "Clay credit balance below 500. Enrichments will stop when credits run out."

      - alert: ClayWebhookFailureRate
        expr: rate(clay_enrichments_total{status="error"}[15m]) > 0.1
        labels:
          severity: warning
        annotations:
          summary: "Clay webhook callback failure rate > 10%"
```

### Step 4: Build a Dashboard

Key panels for a Clay observability dashboard:

```yaml
dashboard_panels:
  row_1:
    - name: "Credit Balance"
      type: gauge
      metric: clay_credit_balance
      thresholds: [500, 1000, 5000]

    - name: "Credits Used Today"
      type: stat
      metric: increase(clay_credits_used_total[24h])

    - name: "Email Hit Rate"
      type: gauge
      metric: clay_enrichment_hit_rate{field="email"}
      thresholds: [40, 60, 80]

  row_2:
    - name: "Credit Burn Rate (hourly)"
      type: timeseries
      metric: rate(clay_credits_used_total[1h])

    - name: "ICP Score Distribution"
      type: histogram
      metric: clay_icp_score

  row_3:
    - name: "Lead Tier Breakdown"
      type: piechart
      metric: clay_enrichments_total by (tier)

    - name: "Cost per Enriched Lead"
      type: stat
      metric: clay_credits_used_total / clay_enrichments_total{status="enriched"}
```

### Step 5: Daily Summary Report

```typescript
// src/clay/daily-report.ts — generate daily enrichment summary
function generateDailyReport(collector: ClayMetricsCollector): void {
  console.log(collector.getReport());

  // Post to Slack
  if (process.env.SLACK_WEBHOOK_URL) {
    fetch(process.env.SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: `*Daily Clay Enrichment Report*\n\`\`\`\n${collector.getReport()}\n\`\`\``,
      }),
    }).catch(console.error);
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Credits depleting fast | High waterfall depth or uncapped tables | Add credit burn alert, reduce waterfall |
| Hit rate near 0% | Invalid input data (personal domains, typos) | Add data quality monitoring, pre-filter |
| Missing metrics | Webhook handler not instrumented | Add metrics collection to callback handler |
| Dashboard shows stale data | Metrics not being pushed | Verify Prometheus scrape config |

## Resources

- [Prometheus Client Libraries](https://prometheus.io/docs/instrumenting/clientlibs/)
- [Grafana Dashboard Examples](https://grafana.com/grafana/dashboards/)
- [Clay University -- Actions & Data Credits](https://university.clay.com/docs/actions-data-credits)

## Next Steps

For incident response, see `clay-incident-runbook`.
