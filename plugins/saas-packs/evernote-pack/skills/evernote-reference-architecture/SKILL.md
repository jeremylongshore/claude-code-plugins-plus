---
name: evernote-reference-architecture
description: |
  Reference architecture for Evernote integrations.
  Use when designing system architecture, planning integrations,
  or building scalable Evernote applications.
  Trigger with phrases like "evernote architecture", "design evernote system",
  "evernote integration pattern", "evernote scale".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Reference Architecture

## Overview
Production-ready architecture patterns for building scalable, maintainable Evernote integrations. Covers service layer design, caching strategy, sync architecture, and deployment topology.

## Prerequisites
- Understanding of microservices or modular monolith architecture
- Cloud platform familiarity (AWS, GCP, or Azure)
- Knowledge of message queues and caching

## Instructions

### Architecture Layers

```
Client Layer    [Web App / Mobile / CLI]
                        |
API Layer       [Express/Fastify REST API]
                        |
Service Layer   [NoteService | SearchService | SyncService]
                        |
Integration     [EvernoteClient (rate-limited, instrumented)]
                        |
Infrastructure  [Redis Cache | PostgreSQL | Message Queue]
```

### Service Layer Design

Separate concerns into focused services:
- **NoteService**: CRUD operations, ENML formatting, tag management
- **SearchService**: Query building, pagination, result enrichment
- **SyncService**: Webhook handling, incremental sync, conflict resolution
- **AuthService**: OAuth flow, token storage, refresh logic

```javascript
// services/index.js - Service registry
class ServiceRegistry {
  constructor(noteStore, cache, db) {
    this.notes = new NoteService(noteStore);
    this.search = new SearchService(noteStore, cache);
    this.sync = new SyncService(noteStore, db);
  }
}
```

### Caching Strategy

Cache at two levels: in-memory LRU for hot data (note metadata, user info) and Redis for shared state (notebook lists, tag lists, sync checkpoints). Invalidate on webhook notification.

### Sync Architecture

Use webhooks as the primary change notification channel. Fall back to polling when webhooks are unavailable. Process changes through a message queue for reliability and retry. Store sync state (USN) in the database for crash recovery.

```
Evernote Webhook → API Gateway → Message Queue → Sync Worker → Database
                                                      ↓
                                              Evernote API (fetch changes)
```

### Database Schema

Store mirrored Evernote data locally for fast reads. Key tables: `users` (token, expiration), `notebooks`, `notes` (content, metadata), `tags`, `resources` (metadata, file path), `sync_state` (user_id, last_usn).

For the complete architecture diagrams, service implementations, database schema, and scaling guidelines, see [Implementation Guide](references/implementation-guide.md).

## Output
- Layered architecture with clear separation of concerns
- Service registry pattern for dependency management
- Two-level caching strategy (in-memory + Redis)
- Webhook-first sync architecture with polling fallback
- Database schema for local data mirroring
- Message queue integration for reliable event processing

## Error Handling
| Failure Mode | Impact | Mitigation |
|-------------|--------|------------|
| Evernote API outage | All sync stops | Circuit breaker, serve cached data |
| Redis down | Increased API call rate | Fall through to direct API, in-memory fallback |
| Database failure | Cannot persist sync state | Queue events, replay after recovery |
| Message queue failure | Webhook events lost | Polling fallback, periodic full sync |

## Resources
- [Twelve-Factor App](https://12factor.net/)
- [Evernote API Reference](https://dev.evernote.com/doc/reference/)
- [Evernote Synchronization](https://dev.evernote.com/doc/articles/synchronization.php)
- [Redis Documentation](https://redis.io/documentation)

## Next Steps
For multi-environment setup, see `evernote-multi-env-setup`.

## Examples

**Note-taking SaaS**: Build a web app where users connect their Evernote account via OAuth, sync notes to a local database, provide full-text search via PostgreSQL, and push changes back to Evernote.

**Team dashboard**: Aggregate notes from multiple Evernote Business users into a shared dashboard. Use the sync architecture to keep data fresh. Cache notebook/tag lookups for sub-100ms response times.
