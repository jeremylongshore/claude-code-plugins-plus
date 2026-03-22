---
name: clari-reference-architecture
description: |
  Implement Clari reference architecture with best-practice project layout.
  Use when designing new Clari integrations, reviewing project structure,
  or establishing architecture standards for Clari applications.
  Trigger with phrases like "clari architecture", "clari best practices",
  "clari project structure", "how to organize clari", "clari layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clari]
---

# Clari Reference Architecture

## Overview
Production-ready architecture patterns for Clari integrations.

## Prerequisites
- Understanding of layered architecture
- Clari SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-clari-project/
├── src/
│   ├── clari/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── clari/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── clari/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── clari/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── clari/
│   └── integration/
│       └── clari/
├── config/
│   ├── clari.development.json
│   ├── clari.staging.json
│   └── clari.production.json
└── docs/
    └── clari/
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
│          Clari Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/clari/client.ts
export class ClariService {
  private client: ClariClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ClariConfig) {
    this.client = new ClariClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('clari');
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
// src/clari/errors.ts
export class ClariServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ClariServiceError';
  }
}

export function wrapClariError(error: unknown): ClariServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/clari/health.ts
export async function checkClariHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await clariClient.ping();
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
│ Clari    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Clari    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/clari.ts
export interface ClariConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadClariConfig(): ClariConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./clari.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Clari operations.

### Step 4: Configure Health Checks
Add health check endpoint for Clari connectivity.

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
| Type errors | Missing types | Add Clari types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/clari/{handlers} src/services/clari src/api/clari
touch src/clari/{client,config,types,errors}.ts
touch src/services/clari/{index,sync,cache}.ts
```

## Resources
- [Clari SDK Documentation](https://docs.clari.com/sdk)
- [Clari Best Practices](https://docs.clari.com/best-practices)

## Flagship Skills
For multi-environment setup, see `clari-multi-env-setup`.