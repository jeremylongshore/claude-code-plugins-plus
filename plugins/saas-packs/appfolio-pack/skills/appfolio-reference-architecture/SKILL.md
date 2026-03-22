---
name: appfolio-reference-architecture
description: |
  Reference architecture for AppFolio property management integration.
  Trigger: "appfolio architecture".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio reference architecture | sed 's/\b\(.\)/\u\1/g'

## Architecture
```
┌──────────────────────────────────────────────┐
│             Your Application                   │
│                                                │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐ │
│  │Dashboard │  │ Sync     │  │ Webhook     │ │
│  │(React)   │  │ Service  │  │ Handler     │ │
│  └────┬─────┘  └────┬─────┘  └──────┬──────┘ │
│       │              │               │         │
│  ┌────▼──────────────▼───────────────▼──────┐ │
│  │         AppFolio API Client               │ │
│  │  (Basic Auth, Retry, Cache, Rate Limit)   │ │
│  └────────────────────┬─────────────────────┘ │
└───────────────────────┼───────────────────────┘
                        │
              ┌─────────▼──────────┐
              │ AppFolio Stack API  │
              │ /properties         │
              │ /tenants            │
              │ /leases             │
              │ /units              │
              │ /bills              │
              └────────────────────┘
```

## Project Structure
```
appfolio-integration/
├── src/
│   ├── appfolio/
│   │   ├── client.ts          # Typed REST client with Basic Auth
│   │   ├── cache.ts           # Response cache with TTL
│   │   └── types.ts           # Property, Tenant, Lease, Unit types
│   ├── dashboard/
│   │   ├── portfolio.ts       # Portfolio summary
│   │   └── vacancy.ts         # Vacancy tracking
│   ├── sync/
│   │   └── incremental.ts     # Incremental data sync
│   ├── webhooks/
│   │   └── handler.ts         # Webhook endpoint
│   └── server.ts
├── tests/
│   ├── mocks/                 # Mock API responses
│   └── unit/
└── package.json
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
