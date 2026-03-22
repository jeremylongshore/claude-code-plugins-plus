---
name: documenso-reference-architecture
description: |
  Implement Documenso reference architecture with best-practice project layout.
  Use when designing new Documenso integrations, reviewing project structure,
  or establishing architecture standards for document signing applications.
  Trigger with phrases like "documenso architecture", "documenso best practices",
  "documenso project structure", "how to organize documenso".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, documenso-reference]

---
# Documenso Reference Architecture

## Overview

Production-ready architecture for Documenso document signing integrations. Covers project layout, layered service architecture, webhook processing, and data flow.

## Prerequisites

- Understanding of layered architecture principles
- Documenso SDK knowledge (see `documenso-sdk-patterns`)
- TypeScript project with Node.js 18+

## Recommended Project Structure

```
my-signing-app/
├── src/
│   ├── documenso/
│   │   ├── client.ts              # Singleton SDK client
│   │   ├── errors.ts              # Custom error classes
│   │   ├── retry.ts               # Retry/backoff logic
│   │   └── types.ts               # Shared types
│   ├── services/
│   │   ├── document-service.ts    # Document CRUD operations
│   │   ├── template-service.ts    # Template-based workflows
│   │   └── signing-service.ts     # Orchestrates signing flows
│   ├── webhooks/
│   │   ├── handler.ts             # Express webhook router
│   │   ├── verify.ts              # Secret verification
│   │   └── processors/
│   │       ├── document-completed.ts
│   │       ├── document-signed.ts
│   │       └── document-rejected.ts
│   ├── api/
│   │   ├── health.ts              # Health check endpoint
│   │   └── routes.ts              # API routes
│   └── config/
│       └── index.ts               # Environment configuration
├── scripts/
│   ├── verify-connection.ts       # Quick health check
│   ├── create-test-doc.ts         # Test document generator
│   └── cleanup-test-docs.ts       # Test data cleanup
├── tests/
│   ├── unit/
│   │   └── document-service.test.ts
│   ├── integration/
│   │   └── document-lifecycle.test.ts
│   └── mocks/
│       └── documenso.ts           # Mock client factory
├── .env.development
├── .env.production
├── docker-compose.yml             # Self-hosted Documenso (dev)
└── package.json
```

## Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  API / Controllers                                       │
│  Routes, request validation, response formatting         │
├─────────────────────────────────────────────────────────┤
│  Service Layer                                           │
│  Business logic, orchestration, authorization            │
│  (document-service, template-service, signing-service)   │
├─────────────────────────────────────────────────────────┤
│  Documenso Client Layer                                  │
│  SDK wrapper, retry, error handling, caching             │
│  (client.ts, retry.ts, errors.ts)                       │
├─────────────────────────────────────────────────────────┤
│  External Services                                       │
│  Documenso API, S3/GCS storage, email, database         │
└─────────────────────────────────────────────────────────┘
```

**Rules:**
- Controllers never call Documenso directly -- always go through services
- Services never import `@documenso/sdk-typescript` directly -- use the client wrapper
- Webhook processors are isolated -- one file per event type
- Error handling happens at the client layer, not in controllers

## Data Flow

```
User Request
     │
     ▼
┌──────────┐   POST /api/sign
│   API    │──────────────────────────────┐
│  Router  │                              │
└──────────┘                              ▼
                                   ┌──────────────┐
                                   │   Signing    │
                                   │   Service    │
                                   └──────┬───────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             ┌──────────┐         ┌──────────┐          ┌──────────┐
             │ Template │         │ Document │          │   Your   │
             │ Service  │         │ Service  │          │    DB    │
             └────┬─────┘         └────┬─────┘          └──────────┘
                  │                    │
                  └────────┬───────────┘
                           ▼
                    ┌──────────────┐
                    │  Documenso   │
                    │  Client      │──→ Documenso API
                    │  (singleton) │
                    └──────────────┘

Webhook Flow:
Documenso API ──POST──→ /webhooks/documenso
                             │
                        ┌────▼────┐
                        │ Verify  │──→ Check X-Documenso-Secret
                        │ Secret  │
                        └────┬────┘
                             │
                        ┌────▼────┐
                        │ Router  │──→ Route by event type
                        └────┬────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        completed.ts    signed.ts     rejected.ts
        (archive PDF)  (update DB)  (alert sender)
```

## Setup Script

```bash
#!/bin/bash
set -euo pipefail

mkdir -p src/{documenso,services,webhooks/processors,api,config}
mkdir -p scripts tests/{unit,integration,mocks}

# Create .env.example
cat > .env.example << 'EOF'
DOCUMENSO_API_KEY=
DOCUMENSO_BASE_URL=https://app.documenso.com/api/v2
DOCUMENSO_WEBHOOK_SECRET=
LOG_LEVEL=info
NODE_ENV=development
EOF

echo "Project scaffolded. Copy .env.example to .env and fill in values."
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Singleton client | Avoids re-initialization overhead per request |
| Service layer | Separates business logic from API details |
| One processor per webhook event | Isolates side effects, easy to test |
| Mock client for tests | Fast unit tests without API calls |
| Template-first approach | Fewer API calls, consistent field placement |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Services import client, never the reverse |
| Config not loading | Wrong env file | Verify `NODE_ENV` matches config loader |
| Webhook processor crash | Unhandled error in processor | Wrap each processor in try/catch |
| Test isolation | Shared client state | Call `resetClient()` in `beforeEach` |

## Resources

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Documenso SDK](https://github.com/documenso/sdk-typescript)
- [12-Factor App](https://12factor.net/)

## Next Steps

For multi-environment setup, see `documenso-multi-env-setup`.
