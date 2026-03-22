---
name: finta-reference-architecture
description: |
  Implement Finta reference architecture with best-practice project layout.
  Use when designing new Finta integrations, reviewing project structure,
  or establishing architecture standards for Finta applications.
  Trigger with phrases like "finta architecture", "finta best practices",
  "finta project structure", "how to organize finta", "finta layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, finta]
---

# Finta Reference Architecture

## Overview
Production-ready architecture patterns for Finta integrations.

## Prerequisites
- Understanding of layered architecture
- Finta SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-finta-project/
├── src/
│   ├── finta/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── finta/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── finta/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── finta/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── finta/
│   └── integration/
│       └── finta/
├── config/
│   ├── finta.development.json
│   ├── finta.staging.json
│   └── finta.production.json
└── docs/
    └── finta/
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
│          Finta Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/finta/client.ts
export class FintaService {
  private client: FintaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: FintaConfig) {
    this.client = new FintaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('finta');
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
// src/finta/errors.ts
export class FintaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'FintaServiceError';
  }
}

export function wrapFintaError(error: unknown): FintaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/finta/health.ts
export async function checkFintaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await fintaClient.ping();
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
│ Finta    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Finta    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/finta.ts
export interface FintaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFintaConfig(): FintaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./finta.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Finta operations.

### Step 4: Configure Health Checks
Add health check endpoint for Finta connectivity.

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
| Type errors | Missing types | Add Finta types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/finta/{handlers} src/services/finta src/api/finta
touch src/finta/{client,config,types,errors}.ts
touch src/services/finta/{index,sync,cache}.ts
```

## Resources
- [Finta SDK Documentation](https://docs.finta.com/sdk)
- [Finta Best Practices](https://docs.finta.com/best-practices)

## Flagship Skills
For multi-environment setup, see `finta-multi-env-setup`.