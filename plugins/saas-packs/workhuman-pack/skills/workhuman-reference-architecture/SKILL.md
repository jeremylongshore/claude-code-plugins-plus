---
name: workhuman-reference-architecture
description: |
  Implement Workhuman reference architecture with best-practice project layout.
  Use when designing new Workhuman integrations, reviewing project structure,
  or establishing architecture standards for Workhuman applications.
  Trigger with phrases like "workhuman architecture", "workhuman best practices",
  "workhuman project structure", "how to organize workhuman", "workhuman layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, workhuman]
---

# Workhuman Reference Architecture

## Overview
Production-ready architecture patterns for Workhuman integrations.

## Prerequisites
- Understanding of layered architecture
- Workhuman SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-workhuman-project/
├── src/
│   ├── workhuman/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── workhuman/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── workhuman/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── workhuman/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── workhuman/
│   └── integration/
│       └── workhuman/
├── config/
│   ├── workhuman.development.json
│   ├── workhuman.staging.json
│   └── workhuman.production.json
└── docs/
    └── workhuman/
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
│          Workhuman Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/workhuman/client.ts
export class WorkhumanService {
  private client: WorkhumanClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: WorkhumanConfig) {
    this.client = new WorkhumanClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('workhuman');
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
// src/workhuman/errors.ts
export class WorkhumanServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'WorkhumanServiceError';
  }
}

export function wrapWorkhumanError(error: unknown): WorkhumanServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/workhuman/health.ts
export async function checkWorkhumanHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await workhumanClient.ping();
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
│ Workhuman    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Workhuman    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/workhuman.ts
export interface WorkhumanConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadWorkhumanConfig(): WorkhumanConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./workhuman.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Workhuman operations.

### Step 4: Configure Health Checks
Add health check endpoint for Workhuman connectivity.

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
| Type errors | Missing types | Add Workhuman types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/workhuman/{handlers} src/services/workhuman src/api/workhuman
touch src/workhuman/{client,config,types,errors}.ts
touch src/services/workhuman/{index,sync,cache}.ts
```

## Resources
- [Workhuman SDK Documentation](https://docs.workhuman.com/sdk)
- [Workhuman Best Practices](https://docs.workhuman.com/best-practices)

## Flagship Skills
For multi-environment setup, see `workhuman-multi-env-setup`.