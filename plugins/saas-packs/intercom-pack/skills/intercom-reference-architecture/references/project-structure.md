# Intercom Reference Architecture — Full Project Structure

The complete directory layout for a production Intercom integration built on the
layered architecture. Directories map one-to-one onto the layers described in
`SKILL.md` and detailed in [implementation.md](implementation.md).

```
my-intercom-app/
├── src/
│   ├── intercom/
│   │   ├── client.ts              # Singleton IntercomClient wrapper
│   │   ├── types.ts               # Extended Intercom types
│   │   └── errors.ts              # Custom error classes
│   ├── services/
│   │   ├── contacts.service.ts    # Contact CRUD + search + merge
│   │   ├── conversations.service.ts  # Conversation lifecycle
│   │   ├── articles.service.ts    # Help Center article management
│   │   └── events.service.ts      # Data event tracking
│   ├── webhooks/
│   │   ├── router.ts              # Topic-based event routing
│   │   ├── signature.ts           # X-Hub-Signature verification
│   │   └── handlers/
│   │       ├── conversation.handler.ts
│   │       └── contact.handler.ts
│   ├── sync/
│   │   ├── contact-sync.ts        # CRM <-> Intercom contact sync
│   │   └── company-sync.ts        # Company data sync
│   ├── api/
│   │   ├── health.ts              # Health check endpoint
│   │   └── webhooks.ts            # Webhook endpoint
│   └── cache/
│       └── intercom-cache.ts      # LRU + Redis caching layer
├── tests/
│   ├── unit/
│   │   ├── contacts.test.ts
│   │   └── webhooks.test.ts
│   └── integration/
│       └── intercom.integration.test.ts
├── config/
│   ├── development.json
│   ├── staging.json
│   └── production.json
└── package.json
```

## Directory responsibilities

| Directory      | Layer            | Responsibility                                            |
|----------------|------------------|-----------------------------------------------------------|
| `src/intercom/`| Client           | SDK wrapper, typed errors, extended types                 |
| `src/services/`| Service          | Business logic, orchestration across Intercom resources   |
| `src/webhooks/`| API / Webhook    | Signature verification, topic routing, event handlers     |
| `src/sync/`    | Service          | Bidirectional CRM ↔ Intercom reconciliation               |
| `src/api/`     | API / Webhook    | HTTP endpoints (health, webhook receiver)                 |
| `src/cache/`   | Infrastructure   | LRU + Redis caching, webhook-driven invalidation          |
| `config/`      | Infrastructure   | Per-environment configuration                             |
