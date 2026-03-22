---
name: fondo-reference-architecture
description: |
  Implement Fondo reference architecture with best-practice project layout.
  Use when designing new Fondo integrations, reviewing project structure,
  or establishing architecture standards for Fondo applications.
  Trigger with phrases like "fondo architecture", "fondo best practices",
  "fondo project structure", "how to organize fondo", "fondo layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fondo]
---

# Fondo Reference Architecture

## Overview
Production-ready architecture patterns for Fondo integrations.

## Prerequisites
- Understanding of layered architecture
- Fondo SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-fondo-project/
├── src/
│   ├── fondo/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── fondo/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── fondo/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── fondo/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── fondo/
│   └── integration/
│       └── fondo/
├── config/
│   ├── fondo.development.json
│   ├── fondo.staging.json
│   └── fondo.production.json
└── docs/
    └── fondo/
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
│          Fondo Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/fondo/client.ts
export class FondoService {
  private client: FondoClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: FondoConfig) {
    this.client = new FondoClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('fondo');
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
// src/fondo/errors.ts
export class FondoServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'FondoServiceError';
  }
}

export function wrapFondoError(error: unknown): FondoServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/fondo/health.ts
export async function checkFondoHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await fondoClient.ping();
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
│ Fondo    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Fondo    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/fondo.ts
export interface FondoConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFondoConfig(): FondoConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./fondo.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Fondo operations.

### Step 4: Configure Health Checks
Add health check endpoint for Fondo connectivity.

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
| Type errors | Missing types | Add Fondo types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/fondo/{handlers} src/services/fondo src/api/fondo
touch src/fondo/{client,config,types,errors}.ts
touch src/services/fondo/{index,sync,cache}.ts
```

## Resources
- [Fondo SDK Documentation](https://docs.fondo.com/sdk)
- [Fondo Best Practices](https://docs.fondo.com/best-practices)

## Flagship Skills
For multi-environment setup, see `fondo-multi-env-setup`.