# Klaviyo Reference Architecture — Layout & Layering

The full project structure, layer contract, and end-to-end data flow for a
production Klaviyo integration. Read this alongside
[implementation.md](implementation.md), which fills each layer with working code.

## Project Structure

```
src/
├── klaviyo/                     # SDK layer (thin wrappers)
│   ├── session.ts               # ApiKeySession singleton
│   ├── api.ts                   # Lazy API client getters
│   ├── types.ts                 # Shared Klaviyo types
│   └── errors.ts                # Error parsing/classification
├── services/                    # Business logic layer
│   ├── profile-sync.ts          # Bidirectional profile sync
│   ├── event-tracker.ts         # Server-side event tracking
│   ├── campaign-manager.ts      # Campaign create/send
│   ├── list-manager.ts          # List/subscription management
│   └── segment-query.ts         # Segment membership queries
├── webhooks/                    # Inbound webhook handlers
│   ├── router.ts                # Topic-based event routing
│   ├── verify.ts                # HMAC-SHA256 signature verification
│   └── handlers/
│       ├── profile-events.ts    # profile.created, profile.updated
│       ├── list-events.ts       # list.member.added/removed
│       └── campaign-events.ts   # campaign.sent, delivered
├── jobs/                        # Background jobs
│   ├── profile-sync-job.ts      # Scheduled bidirectional sync
│   ├── list-cleanup-job.ts      # Unengaged profile suppression
│   └── metrics-export-job.ts    # Export Klaviyo metrics to BI
├── middleware/
│   └── klaviyo-rate-limiter.ts  # Request queue + retry logic
├── config/
│   └── klaviyo.ts               # Environment-specific config
└── health/
    └── klaviyo.ts               # Health check endpoint
```

## Layer Architecture

```
┌──────────────────────────────────────────────┐
│              API / Webhook Layer              │
│    Express routes, webhook handlers           │
├──────────────────────────────────────────────┤
│              Service Layer                    │
│    profile-sync, event-tracker, campaigns     │
│    Business logic, orchestration, validation  │
├──────────────────────────────────────────────┤
│              Klaviyo SDK Layer                │
│    ApiKeySession, ProfilesApi, EventsApi      │
│    Error parsing, retry logic                 │
├──────────────────────────────────────────────┤
│              Infrastructure Layer             │
│    Cache (Redis), Queue (BullMQ),            │
│    Database (Prisma), Monitoring (OTel)       │
└──────────────────────────────────────────────┘
```

**Rules:**

- API layer calls Service layer only
- Service layer calls SDK layer and Infrastructure
- SDK layer never calls upward
- Webhooks are treated as API endpoints

## Data Flow Diagram

```
Your App                          Klaviyo
─────────                         ───────

User signs up ──→ ProfileSyncService.syncToKlaviyo()
                        │
                        ▼
                  POST /api/profiles/  ──→  Profile created
                                              │
                                              ▼
                                        Welcome Flow triggered
                                              │
                                              ▼
User purchases ──→ EventTracker.trackPurchase()
                        │
                        ▼
                  POST /api/events/  ──→  "Placed Order" event
                                              │
                                              ▼
                                        Post-purchase Flow
                                              │
                                              ▼
Profile updated ◀── Webhook ◀──────── profile.updated event
       │
       ▼
WebhookRouter.routeEvent()
       │
       ▼
Update local DB
```
