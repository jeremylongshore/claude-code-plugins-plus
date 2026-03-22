---
name: salesloft-reference-architecture
description: |
  Implement Salesloft reference architecture with best-practice project layout.
  Use when designing new Salesloft integrations, reviewing project structure,
  or establishing architecture standards for Salesloft applications.
  Trigger with phrases like "salesloft architecture", "salesloft best practices",
  "salesloft project structure", "how to organize salesloft", "salesloft layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesloft]
---

# Salesloft Reference Architecture

## Overview
Production-ready architecture patterns for Salesloft integrations.

## Prerequisites
- Understanding of layered architecture
- Salesloft SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-salesloft-project/
├── src/
│   ├── salesloft/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── salesloft/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── salesloft/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── salesloft/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── salesloft/
│   └── integration/
│       └── salesloft/
├── config/
│   ├── salesloft.development.json
│   ├── salesloft.staging.json
│   └── salesloft.production.json
└── docs/
    └── salesloft/
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
│          Salesloft Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/salesloft/client.ts
export class SalesloftService {
  private client: SalesloftClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: SalesloftConfig) {
    this.client = new SalesloftClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('salesloft');
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
// src/salesloft/errors.ts
export class SalesloftServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'SalesloftServiceError';
  }
}

export function wrapSalesloftError(error: unknown): SalesloftServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/salesloft/health.ts
export async function checkSalesloftHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await salesloftClient.ping();
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
│ Salesloft    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Salesloft    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/salesloft.ts
export interface SalesloftConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadSalesloftConfig(): SalesloftConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./salesloft.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Salesloft operations.

### Step 4: Configure Health Checks
Add health check endpoint for Salesloft connectivity.

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
| Type errors | Missing types | Add Salesloft types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/salesloft/{handlers} src/services/salesloft src/api/salesloft
touch src/salesloft/{client,config,types,errors}.ts
touch src/services/salesloft/{index,sync,cache}.ts
```

## Resources
- [Salesloft SDK Documentation](https://docs.salesloft.com/sdk)
- [Salesloft Best Practices](https://docs.salesloft.com/best-practices)

## Flagship Skills
For multi-environment setup, see `salesloft-multi-env-setup`.