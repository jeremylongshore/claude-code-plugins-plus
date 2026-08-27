---
name: glean-observability
description: 'Track: documents indexed per run (total + new + updated + deleted),
  indexing errors and retries, search API latency, zero-result query rate, stale content
  age distribution.

  Trigger: "glean observability", "observability".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.8.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- enterprise-search
- glean
compatibility: Designed for Claude Code
---
# Glean Observability

## Overview

Glean aggregates enterprise knowledge across dozens of connectors, making indexing health and search quality the two pillars of observability. Monitor connector sync status to catch stale content before users notice, track search latency to maintain sub-second responses, and measure zero-result rates to identify coverage gaps. Degraded indexing silently erodes search relevance, so proactive alerting is essential.

## Key Metrics

| Metric | Type | Target | Alert Threshold |
|--------|------|--------|-----------------|
| Search latency p95 | Histogram | < 400ms | > 1s |
| Zero-result query rate | Gauge | < 5% | > 10% |
| Documents indexed per run | Counter | Stable +/-5% | Drop > 20% |
| Connector sync errors | Counter | 0 | > 3 per hour |
| Stale content ratio | Gauge | < 10% | > 25% (>30 days old) |
| Indexing throughput | Gauge | > 1000 docs/min | < 500 docs/min |

## Instrumentation

```typescript
async function trackGleanSearch(query: string, client: GleanClient) {
  const start = Date.now();
  try {
    const results = await client.search({ query });
    const latency = Date.now() - start;
    metrics.histogram('glean.search.latency', latency);
    metrics.increment('glean.search.total');
    if (results.totalCount === 0) metrics.increment('glean.search.zero_results');
    return results;
  } catch (err) {
    metrics.increment('glean.search.errors', { error: err.code });
    throw err;
  }
}
```

## Health Check Dashboard

```typescript
async function gleanHealth(): Promise<Record<string, string>> {
  const connectors = await gleanAdmin.getConnectorStatus();
  const staleRatio = await gleanAdmin.getStaleContentRatio(30);
  const searchP95 = await metrics.query('glean.search.latency', 'p95', '5m');
  return {
    connectors: connectors.every(c => c.status === 'ok') ? 'healthy' : 'degraded',
    content_freshness: staleRatio < 0.1 ? 'healthy' : 'stale',
    search_latency: searchP95 < 400 ? 'healthy' : 'slow',
  };
}
```

## Alerting Rules

```typescript
const alerts = [
  { metric: 'glean.search.latency_p95', condition: '> 1000ms', window: '10m', severity: 'warning' },
  { metric: 'glean.search.zero_result_rate', condition: '> 0.10', window: '1h', severity: 'warning' },
  { metric: 'glean.indexing.sync_errors', condition: '> 3', window: '1h', severity: 'critical' },
  { metric: 'glean.indexing.doc_count_delta', condition: 'drop > 20%', window: '1d', severity: 'critical' },
];
```

## Structured Logging

```typescript
function logGleanEvent(event: string, data: Record<string, any>) {
  console.log(JSON.stringify({
    service: 'glean', event,
    connector: data.connector, doc_count: data.docCount,
    query: data.query ? data.query.substring(0, 100) : undefined,
    latency_ms: data.latency, result_count: data.resultCount,
    timestamp: new Date().toISOString(),
  }));
}
```

## Error Handling

| Signal | Meaning | Action |
|--------|---------|--------|
| Connector sync failure | Source API down or creds expired | Check connector config, rotate tokens |
| Zero-result spike | Missing content or bad query parsing | Audit indexed sources, check synonyms |
| Indexing doc count drop | Source deletion or API pagination bug | Compare source counts, review API logs |
| Search latency > 1s | Overloaded cluster or complex queries | Check Glean status page, review query patterns |

## Prerequisites

- A data-minimization policy for logs and traces, metric owners, alert routes, retention limits, and an approved restricted evidence destination.
- Synthetic probes for availability, freshness, and both authorized and denied access outcomes.
- Correlation IDs and configuration revisions that let responders connect signals without logging query text, titles, snippets, identities, or credentials.

## Instructions

1. Instrument aggregate request, error, latency, freshness, queue, and ACL-probe metrics at the connector and datasource boundary.
2. Redact event fields before export, bound payload capture, and validate that a failed redaction fails closed.
3. Alert on sustained failures, freshness regression, access-boundary difference, and evidence-pipeline failure with an owner and response runbook.
4. Test alerts with synthetic events, verify the destination/retention policy, and remove test data after the exercise.
5. Review dashboards after every connector or ACL change and retain only the minimum receipt needed for incident reconstruction.

## Output

Produce an observability receipt containing dashboard revision, metric/alert IDs, synthetic test results, owner, destination, retention, correlation ID, and remediation/rollback status. Raw source content and credentials are prohibited.

## Examples

`dashboard=search-r11; alert=freshness-lag; probe=pass; allow=pass; deny=pass; destination=restricted-ops; retention=14d; rollback=alert-r10` is a safe alert-test result.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)

## Next Steps

See `glean-incident-runbook`.
