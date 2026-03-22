---
name: fathom-reference-architecture
description: |
  Implement Fathom reference architecture with best-practice project layout.
  Use when designing new Fathom integrations, reviewing project structure,
  or establishing architecture standards for Fathom applications.
  Trigger with phrases like "fathom architecture", "fathom best practices",
  "fathom project structure", "how to organize fathom", "fathom layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fathom]
---

# Fathom Reference Architecture

## Overview
Production-ready architecture patterns for Fathom integrations.

## Prerequisites
- Understanding of layered architecture
- Fathom SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-fathom-project/
├── src/
│   ├── fathom/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── fathom/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── fathom/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── fathom/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── fathom/
│   └── integration/
│       └── fathom/
├── config/
│   ├── fathom.development.json
│   ├── fathom.staging.json
│   └── fathom.production.json
└── docs/
    └── fathom/
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
│          Fathom Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/fathom/client.ts
export class FathomService {
  private client: FathomClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: FathomConfig) {
    this.client = new FathomClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('fathom');
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
// src/fathom/errors.ts
export class FathomServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'FathomServiceError';
  }
}

export function wrapFathomError(error: unknown): FathomServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/fathom/health.ts
export async function checkFathomHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await fathomClient.ping();
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
│ Fathom    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Fathom    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/fathom.ts
export interface FathomConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFathomConfig(): FathomConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./fathom.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Fathom operations.

### Step 4: Configure Health Checks
Add health check endpoint for Fathom connectivity.

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
| Type errors | Missing types | Add Fathom types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/fathom/{handlers} src/services/fathom src/api/fathom
touch src/fathom/{client,config,types,errors}.ts
touch src/services/fathom/{index,sync,cache}.ts
```

## Resources
- [Fathom SDK Documentation](https://docs.fathom.com/sdk)
- [Fathom Best Practices](https://docs.fathom.com/best-practices)

## Flagship Skills
For multi-environment setup, see `fathom-multi-env-setup`.