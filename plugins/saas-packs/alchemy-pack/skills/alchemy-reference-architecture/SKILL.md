---
name: alchemy-reference-architecture
description: |
  Implement Alchemy reference architecture with best-practice project layout.
  Use when designing new Alchemy integrations, reviewing project structure,
  or establishing architecture standards for Alchemy applications.
  Trigger with phrases like "alchemy architecture", "alchemy best practices",
  "alchemy project structure", "how to organize alchemy", "alchemy layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, alchemy]
---

# Alchemy Reference Architecture

## Overview
Production-ready architecture patterns for Alchemy integrations.

## Prerequisites
- Understanding of layered architecture
- Alchemy SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-alchemy-project/
├── src/
│   ├── alchemy/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── alchemy/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── alchemy/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── alchemy/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── alchemy/
│   └── integration/
│       └── alchemy/
├── config/
│   ├── alchemy.development.json
│   ├── alchemy.staging.json
│   └── alchemy.production.json
└── docs/
    └── alchemy/
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
│          Alchemy Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/alchemy/client.ts
export class AlchemyService {
  private client: AlchemyClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AlchemyConfig) {
    this.client = new AlchemyClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('alchemy');
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
// src/alchemy/errors.ts
export class AlchemyServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AlchemyServiceError';
  }
}

export function wrapAlchemyError(error: unknown): AlchemyServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/alchemy/health.ts
export async function checkAlchemyHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await alchemyClient.ping();
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
│ Alchemy    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Alchemy    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/alchemy.ts
export interface AlchemyConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAlchemyConfig(): AlchemyConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./alchemy.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Alchemy operations.

### Step 4: Configure Health Checks
Add health check endpoint for Alchemy connectivity.

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
| Type errors | Missing types | Add Alchemy types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/alchemy/{handlers} src/services/alchemy src/api/alchemy
touch src/alchemy/{client,config,types,errors}.ts
touch src/services/alchemy/{index,sync,cache}.ts
```

## Resources
- [Alchemy SDK Documentation](https://docs.alchemy.com/sdk)
- [Alchemy Best Practices](https://docs.alchemy.com/best-practices)

## Flagship Skills
For multi-environment setup, see `alchemy-multi-env-setup`.