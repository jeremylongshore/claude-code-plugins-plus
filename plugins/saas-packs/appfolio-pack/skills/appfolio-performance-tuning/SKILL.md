---
name: appfolio-performance-tuning
description: |
  Optimize AppFolio API performance with caching and batch operations.
  Trigger: "appfolio performance".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio performance tuning | sed 's/\b\(.\)/\u\1/g'

## Performance Strategies
| Strategy | Savings | Implementation |
|----------|---------|---------------|
| Response caching | 60-80% fewer API calls | Cache properties/units (5 min TTL) |
| Parallel requests | 3-5x faster dashboard load | Promise.all for independent endpoints |
| Incremental sync | 70% less data transfer | Track last_modified timestamps |

## Parallel Dashboard Fetch
```typescript
async function loadDashboard() {
  const [properties, tenants, leases, units] = await Promise.all([
    client.http.get("/properties"),
    client.http.get("/tenants"),
    client.http.get("/leases"),
    client.http.get("/units"),
  ]);
  return { properties: properties.data, tenants: tenants.data, leases: leases.data, units: units.data };
}
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
