---
name: figma-cost-tuning
description: |
  Optimize Figma API usage to minimize costs and stay within plan limits.
  Use when analyzing request volumes, reducing unnecessary API calls,
  or choosing the right Figma plan for your integration needs.
  Trigger with phrases like "figma cost", "figma pricing",
  "reduce figma API calls", "figma plan limits", "figma budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Cost Tuning

## Overview
Optimize Figma API usage costs. Figma's REST API rate limits are determined by plan tier and seat type. Reducing unnecessary requests keeps you within limits and avoids upgrading prematurely.

## Prerequisites
- Working Figma integration with request logging
- Understanding of your current API call volume
- Access to Figma admin settings (for plan details)

## Instructions

### Step 1: Understand Plan-Based Rate Limits
Figma rate limits vary by plan tier and seat type:

| Plan | Seat Types | Rate Limit Tier | Variables API |
|------|------------|----------------|---------------|
| Starter (Free) | Free | Lowest | No |
| Professional | Full, Viewer | Standard | No |
| Organization | Full, Collab, Viewer | Higher | No |
| Enterprise | Full, Collab, Viewer | Highest | Yes |

Key facts:
- Rate limits are per-user, per-minute
- View and Collab seats have lower limits than Full seats
- The Variables API (`/v1/files/:key/variables/*`) requires Enterprise
- Endpoint tiers (1/2/3) have different quotas within each plan

### Step 2: Track API Usage
```typescript
// Instrument all Figma API calls to track volume
class FigmaUsageTracker {
  private calls: Array<{ endpoint: string; timestamp: number; cached: boolean }> = [];

  record(endpoint: string, cached: boolean) {
    this.calls.push({ endpoint, timestamp: Date.now(), cached });
  }

  getReport(windowMs = 24 * 60 * 60 * 1000) {
    const cutoff = Date.now() - windowMs;
    const recent = this.calls.filter(c => c.timestamp > cutoff);

    // Group by endpoint
    const byEndpoint = new Map<string, { total: number; cached: number }>();
    for (const call of recent) {
      const key = call.endpoint.replace(/[a-zA-Z0-9]{20,}/, ':key');
      const entry = byEndpoint.get(key) || { total: 0, cached: 0 };
      entry.total++;
      if (call.cached) entry.cached++;
      byEndpoint.set(key, entry);
    }

    return {
      totalCalls: recent.length,
      cachedCalls: recent.filter(c => c.cached).length,
      cacheHitRate: recent.length > 0
        ? (recent.filter(c => c.cached).length / recent.length * 100).toFixed(1) + '%'
        : '0%',
      byEndpoint: Object.fromEntries(byEndpoint),
    };
  }
}

const tracker = new FigmaUsageTracker();
```

### Step 3: Reduce API Calls
```typescript
// 1. Use depth parameter to avoid fetching full file trees
// Saves bandwidth and processing time
const fileMeta = await figmaFetch(`/v1/files/${key}?depth=1`);

// 2. Batch node IDs into single requests
// Instead of 50 individual /nodes calls, make 1 call with 50 IDs
const ids = nodeIds.join(',');
await figmaFetch(`/v1/files/${key}/nodes?ids=${ids}`);

// 3. Cache with webhooks instead of polling
// Polling every 30s = 2,880 calls/day per file
// Webhooks = 0 polling calls (events push to you)

// 4. Cache image URLs (they're valid for 30 days)
// Re-rendering the same nodes wastes Tier 1 quota

// 5. Use GET /v1/files/:key?depth=1 to check lastModified
// before fetching the full file (skip if unchanged)
async function fetchFileIfChanged(
  fileKey: string,
  lastKnownVersion: string,
  token: string
) {
  const meta = await fetch(
    `https://api.figma.com/v1/files/${fileKey}?depth=1`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());

  if (meta.version === lastKnownVersion) {
    console.log('File unchanged, skipping full fetch');
    return null;
  }

  // File changed -- fetch the full version
  return fetch(
    `https://api.figma.com/v1/files/${fileKey}`,
    { headers: { 'X-Figma-Token': token } }
  ).then(r => r.json());
}
```

### Step 4: Cost-Saving Architecture
```
Polling Architecture (expensive):
  App → GET /v1/files/:key every 30s → 2,880 calls/day/file

Webhook Architecture (efficient):
  Figma → POST /webhooks/figma (only when file changes)
  App → GET /v1/files/:key (only after webhook) → ~10-50 calls/day/file

Savings: 95%+ fewer API calls
```

### Step 5: Usage Dashboard Query
```typescript
// Log API calls to a database for analysis
interface ApiCallLog {
  timestamp: Date;
  endpoint: string;
  fileKey: string;
  status: number;
  latencyMs: number;
  cached: boolean;
}

// Monthly usage summary
function getMonthlyReport(logs: ApiCallLog[]) {
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const monthLogs = logs.filter(l => l.timestamp >= monthStart);

  return {
    totalRequests: monthLogs.length,
    uniqueFiles: new Set(monthLogs.map(l => l.fileKey)).size,
    cacheHitRate: monthLogs.filter(l => l.cached).length / monthLogs.length,
    errorRate: monthLogs.filter(l => l.status >= 400).length / monthLogs.length,
    topEndpoints: Object.entries(
      monthLogs.reduce((acc, l) => {
        acc[l.endpoint] = (acc[l.endpoint] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    ).sort(([,a], [,b]) => b - a).slice(0, 5),
  };
}
```

## Output
- API usage tracked by endpoint and file
- Unnecessary calls eliminated with caching and webhooks
- Bandwidth reduced with `depth` parameter
- Monthly usage reports for capacity planning

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Hitting rate limits often | No caching or batching | Implement caching + batch requests |
| Variables API 403 | Not on Enterprise plan | Use styles API (free on all plans) |
| High bandwidth costs | Fetching full file trees | Use `depth=1` and `/nodes` endpoint |
| Polling waste | No webhooks configured | Set up FILE_UPDATE webhook |

## Resources
- [Figma Pricing Plans](https://www.figma.com/pricing/)
- [Figma Rate Limits](https://developers.figma.com/docs/rest-api/rate-limits/)
- [Figma Webhooks V2](https://developers.figma.com/docs/rest-api/webhooks/)

## Next Steps
For architecture patterns, see `figma-reference-architecture`.
