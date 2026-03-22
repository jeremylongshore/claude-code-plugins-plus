---
name: appfolio-cost-tuning
description: |
  Optimize AppFolio API costs through efficient usage patterns.
  Trigger: "appfolio cost".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio cost tuning | sed 's/\b\(.\)/\u\1/g'

## Overview
AppFolio Stack API pricing is partner-agreement based. Optimize by reducing unnecessary API calls.

## Cost Optimization
1. **Cache aggressively** — Property/unit data changes rarely (5-15 min TTL)
2. **Batch operations** — Fetch all leases once, filter locally
3. **Incremental sync** — Only fetch records modified since last sync
4. **Webhook-driven** — React to events instead of polling

## Usage Monitor
```typescript
class ApiUsageMonitor {
  private calls: Array<{ endpoint: string; timestamp: number }> = [];

  record(endpoint: string) { this.calls.push({ endpoint, timestamp: Date.now() }); }

  getHourlyReport() {
    const cutoff = Date.now() - 3600000;
    const recent = this.calls.filter(c => c.timestamp > cutoff);
    const byEndpoint: Record<string, number> = {};
    for (const c of recent) byEndpoint[c.endpoint] = (byEndpoint[c.endpoint] || 0) + 1;
    return { total: recent.length, byEndpoint };
  }
}
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
