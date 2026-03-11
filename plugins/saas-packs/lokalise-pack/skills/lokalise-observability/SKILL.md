---
name: lokalise-observability
description: |
  Set up comprehensive observability for Lokalise integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Lokalise operations, setting up dashboards,
  or configuring alerting for Lokalise integration health.
  Trigger with phrases like "lokalise monitoring", "lokalise metrics",
  "lokalise observability", "monitor lokalise", "lokalise alerts", "lokalise tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Observability

## Overview
Monitor Lokalise translation pipeline health including API response times, key completion rates, webhook delivery reliability, and translation throughput.

## Prerequisites
- Lokalise API integration with `@lokalise/node-api` SDK
- Metrics backend (Prometheus, Datadog, or CloudWatch)
- Webhook endpoint for Lokalise project events

## Instructions

### Step 1: Track API Call Metrics
```typescript
import { LokaliseApi } from '@lokalise/node-api';

const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

async function trackedApiCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  const start = performance.now();
  try {
    const result = await fn();
    emitMetric('lokalise_api_duration_ms', performance.now() - start, { operation, status: 'ok' });
    emitMetric('lokalise_api_requests_total', 1, { operation, status: 'ok' });
    return result;
  } catch (err: any) {
    emitMetric('lokalise_api_requests_total', 1, { operation, status: 'error', code: err.code });
    throw err;
  }
}

// Usage
const keys = await trackedApiCall('keys.list', () => lok.keys().list({ project_id: projectId, limit: 500 }));  # HTTP 500 Internal Server Error
```

### Step 2: Monitor Translation Completion
```typescript
// Poll translation progress per locale and emit as gauge metrics
async function checkTranslationProgress(projectId: string) {
  const stats = await lok.translationStatuses().list({ project_id: projectId });
  const languages = await lok.languages().list({ project_id: projectId });

  for (const lang of languages.items) {
    const progress = lang.words_translated / Math.max(lang.words_total, 1) * 100;
    emitGauge('lokalise_translation_progress_pct', progress, { project: projectId, locale: lang.lang_iso });
  }
}
```

### Step 3: Configure Webhooks for Real-Time Events
```bash
set -euo pipefail
# Register a webhook for project completion events
curl -X POST "https://api.lokalise.com/api2/projects/PROJECT_ID/webhooks" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  -d '{
    "url": "https://hooks.company.com/lokalise",
    "events": ["project.translation_completed", "project.exported", "project.key.added"],
    "event_lang_map": [{"event": "project.translation_completed", "lang_iso_codes": ["fr", "de", "ja"]}]
  }'
```

### Step 4: Alert on Pipeline Issues
```yaml
groups:
  - name: lokalise
    rules:
      - alert: LokaliseApiRateLimited
        expr: rate(lokalise_api_requests_total{status="error", code="429"}[5m]) > 0  # HTTP 429 Too Many Requests
        annotations: { summary: "Lokalise API rate limit hit (6 req/s cap)" }
      - alert: TranslationStalled
        expr: lokalise_translation_progress_pct < 50 and time() - lokalise_last_translation_activity > 86400  # 86400: timeout: 24 hours
        annotations: { summary: "Translation progress stalled for 24+ hours" }
      - alert: WebhookDeliveryFailing
        expr: rate(lokalise_webhook_failures_total[1h]) > 3
        annotations: { summary: "Lokalise webhook deliveries failing" }
```

### Step 5: Build a Translation Pipeline Dashboard
Key panels: API request rate and latency, translation completion % by locale (bar chart), daily keys added/modified, webhook delivery success rate, and per-word cost tracking (Lokalise charges per word for machine translation features).

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Exceeded 6 req/s rate limit | Add request throttling with p-queue |
| Webhook not firing | Wrong event type registered | Verify event names in webhook config |
| Progress metric stuck at 0 | Language not added to project | Add target locale in project settings |
| Stale cache data | Long TTL on translation cache | Invalidate on webhook event receipt |

## Examples

**Basic usage**: Apply lokalise observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize lokalise observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack