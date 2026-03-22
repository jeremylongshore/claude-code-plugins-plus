---
name: algolia-reference-architecture
description: |
  Implement Algolia reference architecture with best-practice project layout.
  Use when designing new Algolia integrations, reviewing project structure,
  or establishing architecture standards for Algolia applications.
  Trigger with phrases like "algolia architecture", "algolia best practices",
  "algolia project structure", "how to organize algolia", "algolia layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, algolia]
---

# Algolia Reference Architecture

## Overview
Production-ready architecture patterns for Algolia integrations.

## Prerequisites
- Understanding of layered architecture
- Algolia SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-algolia-project/
├── src/
│   ├── algolia/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── algolia/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── algolia/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── algolia/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── algolia/
│   └── integration/
│       └── algolia/
├── config/
│   ├── algolia.development.json
│   ├── algolia.staging.json
│   └── algolia.production.json
└── docs/
    └── algolia/
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
│          Algolia Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/algolia/client.ts
export class AlgoliaService {
  private client: AlgoliaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AlgoliaConfig) {
    this.client = new AlgoliaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('algolia');
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
// src/algolia/errors.ts
export class AlgoliaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AlgoliaServiceError';
  }
}

export function wrapAlgoliaError(error: unknown): AlgoliaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/algolia/health.ts
export async function checkAlgoliaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await algoliaClient.ping();
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
│ Algolia    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Algolia    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/algolia.ts
export interface AlgoliaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAlgoliaConfig(): AlgoliaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./algolia.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Algolia operations.

### Step 4: Configure Health Checks
Add health check endpoint for Algolia connectivity.

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
| Type errors | Missing types | Add Algolia types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/algolia/{handlers} src/services/algolia src/api/algolia
touch src/algolia/{client,config,types,errors}.ts
touch src/services/algolia/{index,sync,cache}.ts
```

## Resources
- [Algolia SDK Documentation](https://docs.algolia.com/sdk)
- [Algolia Best Practices](https://docs.algolia.com/best-practices)

## Flagship Skills
For multi-environment setup, see `algolia-multi-env-setup`.