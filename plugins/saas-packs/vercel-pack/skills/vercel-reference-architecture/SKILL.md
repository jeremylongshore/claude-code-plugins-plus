---
name: vercel-reference-architecture
description: |
  Implement Vercel reference architecture with best-practice project layout.
  Use when designing new Vercel integrations, reviewing project structure,
  or establishing architecture standards for Vercel applications.
  Trigger with phrases like "vercel architecture", "vercel best practices",
  "vercel project structure", "how to organize vercel", "vercel layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Reference Architecture

## Overview
Production-ready architecture patterns for Vercel integrations.

## Prerequisites
- Understanding of layered architecture
- Vercel SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-vercel-project/
├── src/
│   ├── vercel/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── vercel/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── vercel/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── vercel/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── vercel/
│   └── integration/
│       └── vercel/
├── config/
│   ├── vercel.development.json
│   ├── vercel.staging.json
│   └── vercel.production.json
└── docs/
    └── vercel/
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
│          Vercel Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/vercel/client.ts
export class VercelService {
  private client: VercelClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: VercelConfig) {
    this.client = new VercelClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('vercel');
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
// src/vercel/errors.ts
export class VercelServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'VercelServiceError';
  }
}

export function wrapVercelError(error: unknown): VercelServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/vercel/health.ts
export async function checkVercelHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await vercelClient.ping();
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
│ Vercel    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Vercel    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/vercel.ts
export interface VercelConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadVercelConfig(): VercelConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./vercel.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Vercel operations.

### Step 4: Configure Health Checks
Add health check endpoint for Vercel connectivity.

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
| Type errors | Missing types | Add Vercel types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/vercel/{handlers} src/services/vercel src/api/vercel
touch src/vercel/{client,config,types,errors}.ts
touch src/services/vercel/{index,sync,cache}.ts
```

## Resources
- [Vercel SDK Documentation](https://vercel.com/docs/sdk)
- [Vercel Best Practices](https://vercel.com/docs/best-practices)

## Flagship Skills
For multi-environment setup, see `vercel-multi-env-setup`.