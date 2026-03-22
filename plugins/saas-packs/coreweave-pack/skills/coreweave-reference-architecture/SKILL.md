---
name: coreweave-reference-architecture
description: |
  Implement CoreWeave reference architecture with best-practice project layout.
  Use when designing new CoreWeave integrations, reviewing project structure,
  or establishing architecture standards for CoreWeave applications.
  Trigger with phrases like "coreweave architecture", "coreweave best practices",
  "coreweave project structure", "how to organize coreweave", "coreweave layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, coreweave]
---

# CoreWeave Reference Architecture

## Overview
Production-ready architecture patterns for CoreWeave integrations.

## Prerequisites
- Understanding of layered architecture
- CoreWeave SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-coreweave-project/
├── src/
│   ├── coreweave/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── coreweave/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── coreweave/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── coreweave/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── coreweave/
│   └── integration/
│       └── coreweave/
├── config/
│   ├── coreweave.development.json
│   ├── coreweave.staging.json
│   └── coreweave.production.json
└── docs/
    └── coreweave/
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
│          CoreWeave Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/coreweave/client.ts
export class CoreWeaveService {
  private client: CoreWeaveClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: CoreWeaveConfig) {
    this.client = new CoreWeaveClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('coreweave');
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
// src/coreweave/errors.ts
export class CoreWeaveServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'CoreWeaveServiceError';
  }
}

export function wrapCoreWeaveError(error: unknown): CoreWeaveServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/coreweave/health.ts
export async function checkCoreWeaveHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await coreweaveClient.ping();
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
│ CoreWeave    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ CoreWeave    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/coreweave.ts
export interface CoreWeaveConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadCoreWeaveConfig(): CoreWeaveConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./coreweave.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for CoreWeave operations.

### Step 4: Configure Health Checks
Add health check endpoint for CoreWeave connectivity.

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
| Type errors | Missing types | Add CoreWeave types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/coreweave/{handlers} src/services/coreweave src/api/coreweave
touch src/coreweave/{client,config,types,errors}.ts
touch src/services/coreweave/{index,sync,cache}.ts
```

## Resources
- [CoreWeave SDK Documentation](https://docs.coreweave.com/sdk)
- [CoreWeave Best Practices](https://docs.coreweave.com/best-practices)

## Flagship Skills
For multi-environment setup, see `coreweave-multi-env-setup`.