---
name: granola-reference-architecture
description: |
  Implement Granola reference architecture with best-practice project layout.
  Use when designing new Granola integrations, reviewing project structure,
  or establishing architecture standards for Granola applications.
  Trigger with phrases like "granola architecture", "granola best practices",
  "granola project structure", "how to organize granola", "granola layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, granola]
---

# Granola Reference Architecture

## Overview
Production-ready architecture patterns for Granola integrations.

## Prerequisites
- Understanding of layered architecture
- Granola SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-granola-project/
├── src/
│   ├── granola/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── granola/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── granola/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── granola/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── granola/
│   └── integration/
│       └── granola/
├── config/
│   ├── granola.development.json
│   ├── granola.staging.json
│   └── granola.production.json
└── docs/
    └── granola/
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
│          Granola Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/granola/client.ts
export class GranolaService {
  private client: GranolaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: GranolaConfig) {
    this.client = new GranolaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('granola');
  }

  async get(id: string): Promise<Resource> {
    return this.cache.getOrFetch(id, () =>
      this.monitor.track('get', () => this.client.get(id))
    );
  }
}
```

### Step 2: Error Boundary
```typescript
// src/granola/errors.ts
export class GranolaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'GranolaServiceError';
  }
}

export function wrapGranolaError(error: unknown): GranolaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/granola/health.ts
export async function checkGranolaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await granolaClient.ping();
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
│ Granola    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Granola    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/granola.ts
export interface GranolaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadGranolaConfig(): GranolaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./granola.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Granola operations.

### Step 4: Configure Health Checks
Add health check endpoint for Granola connectivity.

## Output
- Structured project layout
- Client wrapper with caching
- Error boundary implemented
- Health checks configured

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Wrong layering | Separate concerns by layer |
| Config not loading | Wrong paths | Verify config file locations |
| Type errors | Missing types | Add Granola types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/granola/{handlers} src/services/granola src/api/granola
touch src/granola/{client,config,types,errors}.ts
touch src/services/granola/{index,sync,cache}.ts
```

## Resources
- [Granola SDK Documentation](https://docs.granola.com/sdk)
- [Granola Best Practices](https://docs.granola.com/best-practices)

## Flagship Skills
For multi-environment setup, see `granola-multi-env-setup`.