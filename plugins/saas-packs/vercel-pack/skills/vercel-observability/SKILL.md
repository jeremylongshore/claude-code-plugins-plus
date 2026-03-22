---
name: vercel-observability
description: |
  Set up Vercel observability with runtime logs, analytics, log drains, and OpenTelemetry tracing.
  Use when implementing monitoring for Vercel deployments, setting up log drains,
  or configuring alerting for function errors and performance.
  Trigger with phrases like "vercel monitoring", "vercel metrics",
  "vercel observability", "vercel logs", "vercel alerts", "vercel tracing".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, monitoring, observability, logging]

---
# Vercel Observability

## Overview
Configure comprehensive observability for Vercel deployments using built-in analytics, runtime logs, log drains to external providers, OpenTelemetry integration, and custom instrumentation. Covers the full observability stack from function-level metrics to end-user experience monitoring.

## Prerequisites
- Vercel Pro or Enterprise plan (for log drains and extended retention)
- External logging provider (Datadog, Axiom, Sentry) — optional
- OpenTelemetry SDK — optional

## Instructions

### Step 1: Enable Vercel Analytics
In the Vercel dashboard:
1. Go to **Analytics** tab
2. Enable **Web Analytics** (Core Web Vitals, page views)
3. Enable **Speed Insights** (real user performance data)

```typescript
// For Next.js — add the analytics component
// src/app/layout.tsx
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/next';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
```

Install: `npm install @vercel/analytics @vercel/speed-insights`

### Step 2: Runtime Logs
```bash
# View runtime logs via CLI
vercel logs https://my-app.vercel.app --follow

# Filter by level
vercel logs https://my-app.vercel.app --level=error

# View logs via API
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v2/deployments/dpl_xxx/events?limit=50&direction=backward" \
  | jq '.[] | {timestamp: .created, level: .level, message: .text}'
```

Runtime logs include:
- Function invocation start/end with duration
- `console.log/warn/error` output from functions
- Edge Middleware execution logs
- HTTP request/response metadata

### Step 3: Structured Logging in Functions
```typescript
// lib/logger.ts — structured JSON logging
interface LogEntry {
  level: 'info' | 'warn' | 'error';
  message: string;
  requestId?: string;
  duration?: number;
  [key: string]: unknown;
}

export function log(entry: LogEntry): void {
  // Vercel captures console output as runtime logs
  const output = JSON.stringify({
    ...entry,
    timestamp: new Date().toISOString(),
    region: process.env.VERCEL_REGION,
    env: process.env.VERCEL_ENV,
  });

  switch (entry.level) {
    case 'error': console.error(output); break;
    case 'warn': console.warn(output); break;
    default: console.log(output);
  }
}

// Usage in API route:
export async function GET(request: Request) {
  const requestId = crypto.randomUUID();
  const start = Date.now();

  try {
    const data = await fetchData();
    log({ level: 'info', message: 'Fetched data', requestId, duration: Date.now() - start });
    return Response.json(data);
  } catch (error) {
    log({ level: 'error', message: 'Data fetch failed', requestId, error: String(error) });
    return Response.json({ error: 'Internal error', requestId }, { status: 500 });
  }
}
```

### Step 4: Log Drains (External Providers)
Configure log drains to send all Vercel logs to your logging provider:

In dashboard: **Settings > Log Drains > Add**

Supported providers:
| Provider | Type | Setup |
|----------|------|-------|
| Datadog | HTTP | API key + site URL |
| Axiom | HTTP | API token + dataset |
| Sentry | HTTP | DSN |
| Custom | HTTP/NDJSON | Any HTTPS endpoint |
| Grafana Loki | HTTP | Push URL + auth |

Log drain delivers:
- **Runtime logs**: function invocations, console output
- **Build logs**: build step output, warnings, errors
- **Static logs**: CDN access logs (edge)
- **Firewall logs**: WAF events

```bash
# Create a log drain via API
curl -X POST "https://api.vercel.com/v2/integrations/log-drains" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-datadog-drain",
    "type": "json",
    "url": "https://http-intake.logs.datadoghq.com/api/v2/logs",
    "headers": {"DD-API-KEY": "your-datadog-api-key"},
    "sources": ["lambda", "edge", "build", "static"]
  }'
```

### Step 5: OpenTelemetry Integration
```typescript
// instrumentation.ts (Next.js 13.4+)
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

export function register() {
  const sdk = new NodeSDK({
    traceExporter: new OTLPTraceExporter({
      url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
    }),
    instrumentations: [getNodeAutoInstrumentations()],
    serviceName: 'my-vercel-app',
  });
  sdk.start();
}
```

```javascript
// next.config.js
module.exports = {
  experimental: {
    instrumentationHook: true,
  },
};
```

### Step 6: Error Tracking with Sentry
```bash
npx @sentry/wizard@latest -i nextjs
```

```typescript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.VERCEL_ENV,
  release: process.env.VERCEL_GIT_COMMIT_SHA,
  tracesSampleRate: process.env.VERCEL_ENV === 'production' ? 0.1 : 1.0,
});
```

## Monitoring Dashboard Checklist

| Metric | Source | Alert Threshold |
|--------|--------|----------------|
| Error rate | Runtime logs | > 1% of requests |
| P95 function latency | Vercel Analytics | > 2s |
| Cold start frequency | Runtime logs | > 20% of invocations |
| Build success rate | Build logs | Any failure |
| Core Web Vitals (LCP) | Speed Insights | > 2.5s |
| Edge cache hit rate | Static logs | < 80% |

## Output
- Vercel Analytics and Speed Insights enabled
- Structured JSON logging in all functions
- Log drains configured to external provider
- Error tracking with Sentry or equivalent
- OpenTelemetry tracing for distributed systems

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Logs missing | Log retention expired (1hr free, 30d with Plus) | Enable log drains for persistence |
| Analytics not tracking | Missing `<Analytics />` component | Add to root layout |
| Log drain not receiving | Wrong URL or auth headers | Test the endpoint directly with curl |
| Sentry not capturing errors | DSN not set in production env | Add `NEXT_PUBLIC_SENTRY_DSN` to Production scope |
| OTEL traces missing | instrumentation.ts not loaded | Enable `instrumentationHook` in next.config.js |

## Resources
- [Vercel Observability](https://vercel.com/docs/observability)
- [Runtime Logs](https://vercel.com/docs/logs/runtime)
- [Vercel Analytics](https://vercel.com/docs/analytics)
- [Speed Insights](https://vercel.com/docs/speed-insights)
- [Log Drains](https://vercel.com/docs/observability/log-drains)
- [OpenTelemetry + Next.js](https://nextjs.org/docs/app/building-your-application/optimizing/open-telemetry)

## Next Steps
For incident response, see `vercel-incident-runbook`.
