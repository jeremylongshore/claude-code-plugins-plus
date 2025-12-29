---
name: supabase-reference-architecture
description: |
  Supabase reference architecture and best-practice layout.
  Use when designing Supabase integration architecture or reviewing patterns.
  Trigger with phrases like "supabase architecture", "supabase best practices",
  "supabase project structure", "how to organize supabase".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Reference Architecture

## Overview
Production-ready architecture patterns for Supabase integrations.

## Prerequisites
- supabase-install-auth completed
- Understanding of layered architecture
- TypeScript/Node.js project setup
- Basic understanding of design patterns

## Instructions

### Step 1: Project Structure

Organize your Supabase integration using a layered architecture that separates concerns and promotes maintainability. The following structure provides clear boundaries between client configuration, business logic, and API handlers.

```
my-supabase-project/
├── src/
│   ├── supabase/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── supabase/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── supabase/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── supabase/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── supabase/
│   └── integration/
│       └── supabase/
├── config/
│   ├── supabase.development.json
│   ├── supabase.staging.json
│   └── supabase.production.json
└── docs/
    └── supabase/
        ├── SETUP.md
        └── RUNBOOK.md
```

## Layer Architecture

```
┌─────────────────────────────────────────┐
│             API Layer                    │
│   (Controllers, Routes, Webhooks)        │
├─────────────────────────────────────────┤
│           Service Layer                  │
│  (Business Logic, Orchestration)         │
├─────────────────────────────────────────┤
│          Supabase Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### 1. Client Wrapper
```typescript
// src/supabase/client.ts
export class SupabaseService {
  private client: SupabaseClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: SupabaseConfig) {
    this.client = new SupabaseClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('supabase');
  }

  async get(id: string): Promise<Resource> {
    return this.cache.getOrFetch(id, () =>
      this.monitor.track('get', () => this.client.get(id))
    );
  }
}
```

### 2. Error Boundary
```typescript
// src/supabase/errors.ts
export class SupabaseServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'SupabaseServiceError';
  }
}

export function wrapSupabaseError(error: unknown): SupabaseServiceError {
  // Transform SDK errors to application errors
}
```

### 3. Health Check
```typescript
// src/supabase/health.ts
export async function checkSupabaseHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await supabaseClient.ping();
    return {
      status: 'healthy',
      latencyMs: Date.now() - start,
    };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
}
```

## Data Flow Diagram

```
User Request
     │
     ▼
┌─────────────┐
│   API       │
│   Gateway   │
└──────┬──────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│   Service   │───▶│   Cache     │
│   Layer     │    │   (Redis)   │
└──────┬──────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│ Supabase    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Supabase    │
│   API       │
└─────────────┘
```

### Step 2: Configuration Management

```typescript
// config/supabase.ts
export interface SupabaseConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadSupabaseConfig(): SupabaseConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./supabase.${env}.json`);
}
```

## Output
- Clean separation of concerns across layers
- Reusable client wrapper with caching/monitoring
- Consistent error handling patterns
- Health check endpoint for Supabase connectivity

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Circular dependency | Service importing client incorrectly | Use dependency injection |
| Config not found | Missing environment config file | Create config for environment |
| Type mismatch | SDK types don't match app types | Create adapter layer |
| Health check false positive | Stale cache | Disable cache for health checks |

## Examples

### Dependency Injection Pattern
```typescript
// src/container.ts
import { Container } from 'inversify';
import { SupabaseService } from './supabase/client';

const container = new Container();
container.bind(SupabaseService).toSelf().inSingletonScope();

export { container };
```

## Resources
- [Supabase Best Practices](https://supabase.com/docs/best-practices)
- [Architecture Examples](https://supabase.com/docs/examples)
- [TypeScript SDK Reference](https://supabase.com/docs/sdk/typescript)

## Flagship Skills
For multi-environment setup, see `supabase-multi-env-setup`.