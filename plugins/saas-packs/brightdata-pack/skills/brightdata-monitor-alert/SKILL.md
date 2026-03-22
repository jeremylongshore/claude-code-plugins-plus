---
name: brightdata-monitor-alert
description: |
  Execute Bright Data primary workflow: Monitor & Alert.
  Use when setting up error tracking and alerting for production apps,
  configuring performance monitoring thresholds, or building custom dashboards from infrastructure metrics.
  Trigger with phrases like "brightdata monitor",
  "configure monitoring with brightdata".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, brightdata]
---

# Bright Data Monitor & Alert

## Overview
Set up monitoring, configure alerts, and track system health metrics.
This is the primary workflow — know when things break before users tell you.


## Prerequisites
- Completed `brightdata-install-auth` setup

- Understanding of Bright Data core concepts

- Valid API credentials configured

## Instructions

### Step 1: Configure Monitoring
```typescript
// Initialize SDK in your application
const monitor = client.init({
  dsn: process.env.MONITOR_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,   // 10% of transactions
  profilesSampleRate: 0.01, // 1% of transactions
});

```

### Step 2: Set Alert Rules
```typescript
const alert = await client.alerts.create({
  name: 'Error Spike',
  conditions: [
    { type: 'event_frequency', value: 100, interval: '5m' },
  ],
  actions: [
    { type: 'slack', channel: '#oncall' },
    { type: 'pagerduty', severity: 'warning' },
  ],
  project: projectId,
});
console.log(`Alert rule created: ${alert.id}`);

```

### Step 3: Query Events
```typescript
const events = await client.events.list({
  project: projectId,
  query: 'is:unresolved level:error',
  sort: 'last_seen',
  limit: 20,
});
console.log(`${events.total} unresolved errors:`);
events.data.forEach(e => console.log(`  [${e.count}x] ${e.title}`));

```

## Output
- Completed Monitor & Alert execution

- Expected results from Bright Data API

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| DSN Invalid | Monitoring DSN is malformed or project has been deleted | Copy DSN from project settings. Verify project exists and is active. |
| Quota Exceeded | Monthly event quota exhausted — events being dropped | Increase sample rate filtering. Upgrade plan. Set rate limits on noisy events. |

## Examples

### Complete Workflow
```typescript
const client = new InfraClient({ apiKey: process.env.API_KEY });

async function setupMonitoring(projectId: string) {
  // Create alert for error spikes
  await client.alerts.create({
    project: projectId,
    name: 'P0 Error Spike',
    conditions: [{ type: 'event_frequency', value: 50, interval: '5m' }],
    actions: [{ type: 'slack', channel: '#oncall' }],
  });
  // Create alert for latency degradation
  await client.alerts.create({
    project: projectId,
    name: 'Latency P95 > 2s',
    conditions: [{ type: 'metric', metric: 'transaction.duration', threshold: 2000, percentile: 95 }],
    actions: [{ type: 'pagerduty', severity: 'critical' }],
  });
}

```

### Common Variations
- **Error tracking**: Capture and group exceptions with stack traces
- **Performance monitoring**: Track transaction latency, throughput, and Apdex
- **Infrastructure metrics**: CPU, memory, disk, network per host/container


## Resources
- [Bright Data Documentation](https://docs.brightdata.com)
- [Bright Data API Reference](https://docs.brightdata.com/api)

## Next Steps
For secondary workflow, see `brightdata-resource-management`.