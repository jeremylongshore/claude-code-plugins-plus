---
name: flexport-reference-architecture
description: |
  Implement Flexport reference architecture for supply chain integrations
  with best-practice project layout, service boundaries, and data flow.
  Trigger: "flexport architecture", "flexport project structure", "flexport system design".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Reference Architecture

## Overview

Production reference architecture for Flexport logistics integrations. Three core services: Ingest (webhooks + polling), Core (business logic), and Expose (API + dashboard).

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Your Application                   │
├──────────────┬──────────────────┬─────────────────────┤
│  Ingest      │  Core            │  Expose             │
│              │                  │                     │
│  Webhook     │  Shipment        │  REST API           │
│  Receiver    │  Service         │  (your clients)     │
│              │                  │                     │
│  Scheduled   │  Product         │  Dashboard          │
│  Sync        │  Service         │  (Next.js/Astro)    │
│              │                  │                     │
│  Event       │  Invoice         │  Notifications      │
│  Queue       │  Service         │  (email/slack)      │
├──────────────┴──────────────────┴─────────────────────┤
│  Infrastructure: Cache (Redis) │ DB (Postgres) │ Queue │
├───────────────────────────────────────────────────────┤
│  Flexport API v2 (https://api.flexport.com)           │
└───────────────────────────────────────────────────────┘
```

## Project Layout

```
flexport-integration/
├── src/
│   ├── flexport/
│   │   ├── client.ts           # Singleton API client
│   │   ├── types.ts            # Zod schemas for API responses
│   │   └── webhooks.ts         # Webhook signature + routing
│   ├── services/
│   │   ├── shipment.service.ts # Shipment CRUD + tracking
│   │   ├── product.service.ts  # Product catalog sync
│   │   ├── invoice.service.ts  # Commercial + freight invoices
│   │   └── booking.service.ts  # Booking creation + amendments
│   ├── jobs/
│   │   ├── sync-shipments.ts   # Scheduled full sync (hourly)
│   │   └── cache-warmup.ts     # Pre-populate caches on deploy
│   ├── api/
│   │   ├── routes.ts           # Express/Fastify routes
│   │   └── middleware.ts       # Auth, logging, error handling
│   └── config/
│       ├── flexport.ts         # API config per environment
│       └── cache.ts            # TTL settings per data type
├── tests/
│   ├── unit/                   # Mocked API tests
│   └── integration/            # Live API tests (CI only)
├── .env.example
└── docker-compose.yml          # Redis + Postgres for local dev
```

## Data Flow

```
Flexport API ──webhook──> Ingest ──queue──> Core ──cache──> Expose
                                    │                │
                                    └── DB (Postgres) ┘
```

1. **Ingest**: Webhook receiver validates signatures, enqueues events
2. **Core**: Services process events, sync with Flexport API, update DB
3. **Expose**: API/dashboard reads from DB + cache, never directly from Flexport
4. **Scheduled jobs**: Hourly full sync catches any missed webhooks

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | PostgreSQL | Structured logistics data, JSONB for flexible fields |
| Cache | Redis with 5min TTL | Shipment data changes infrequently |
| Queue | BullMQ | Retry, dead letter, rate limiting built in |
| API client | Custom fetch wrapper | No official SDK, typed with Zod |
| Webhook processing | Async via queue | Fast 200 response, process later |

## Resources

- [Flexport Developer Portal](https://developers.flexport.com/)
- [Flexport API Reference](https://apidocs.flexport.com/)

## Next Steps

For multi-environment setup, see `flexport-multi-env-setup`.
