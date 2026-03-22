---
name: flyio-reference-architecture
description: |
  Implement Fly.io reference architecture with best-practice project layout.
  Use when designing new Fly.io integrations, reviewing project structure,
  or establishing architecture standards for Fly.io applications.
  Trigger with phrases like "flyio architecture", "flyio best practices",
  "flyio project structure", "how to organize flyio", "flyio layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flyio]
---

# Fly.io Reference Architecture

## Overview
Production-ready architecture patterns for Fly.io integrations.

## Prerequisites
- Understanding of layered architecture
- Fly.io SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-flyio-project/
├── src/
│   ├── flyio/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── flyio/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── flyio/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── flyio/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── flyio/
│   └── integration/
│       └── flyio/
├── config/
│   ├── flyio.development.json
│   ├── flyio.staging.json
│   └── flyio.production.json
└── docs/
    └── flyio/
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
│          Fly.io Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/flyio/client.ts
export class Fly.ioService {
  private client: Fly.ioClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Fly.ioConfig) {
    this.client = new Fly.ioClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('flyio');
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
// src/flyio/errors.ts
export class Fly.ioServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Fly.ioServiceError';
  }
}

export function wrapFly.ioError(error: unknown): Fly.ioServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/flyio/health.ts
export async function checkFly.ioHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await flyioClient.ping();
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
│ Fly.io    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Fly.io    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/flyio.ts
export interface Fly.ioConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFly.ioConfig(): Fly.ioConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./flyio.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Fly.io operations.

### Step 4: Configure Health Checks
Add health check endpoint for Fly.io connectivity.

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
| Type errors | Missing types | Add Fly.io types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/flyio/{handlers} src/services/flyio src/api/flyio
touch src/flyio/{client,config,types,errors}.ts
touch src/services/flyio/{index,sync,cache}.ts
```

## Resources
- [Fly.io SDK Documentation](https://docs.flyio.com/sdk)
- [Fly.io Best Practices](https://docs.flyio.com/best-practices)

## Flagship Skills
For multi-environment setup, see `flyio-multi-env-setup`.