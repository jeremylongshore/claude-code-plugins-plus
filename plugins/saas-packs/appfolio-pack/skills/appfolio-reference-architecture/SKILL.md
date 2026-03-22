---
name: appfolio-reference-architecture
description: |
  Implement AppFolio reference architecture with best-practice project layout.
  Use when designing new AppFolio integrations, reviewing project structure,
  or establishing architecture standards for AppFolio applications.
  Trigger with phrases like "appfolio architecture", "appfolio best practices",
  "appfolio project structure", "how to organize appfolio", "appfolio layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, appfolio]
---

# AppFolio Reference Architecture

## Overview
Production-ready architecture patterns for AppFolio integrations.

## Prerequisites
- Understanding of layered architecture
- AppFolio SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-appfolio-project/
├── src/
│   ├── appfolio/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── appfolio/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── appfolio/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── appfolio/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── appfolio/
│   └── integration/
│       └── appfolio/
├── config/
│   ├── appfolio.development.json
│   ├── appfolio.staging.json
│   └── appfolio.production.json
└── docs/
    └── appfolio/
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
│          AppFolio Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/appfolio/client.ts
export class AppFolioService {
  private client: AppFolioClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AppFolioConfig) {
    this.client = new AppFolioClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('appfolio');
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
// src/appfolio/errors.ts
export class AppFolioServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AppFolioServiceError';
  }
}

export function wrapAppFolioError(error: unknown): AppFolioServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/appfolio/health.ts
export async function checkAppFolioHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await appfolioClient.ping();
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
│ AppFolio    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ AppFolio    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/appfolio.ts
export interface AppFolioConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAppFolioConfig(): AppFolioConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./appfolio.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for AppFolio operations.

### Step 4: Configure Health Checks
Add health check endpoint for AppFolio connectivity.

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
| Type errors | Missing types | Add AppFolio types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/appfolio/{handlers} src/services/appfolio src/api/appfolio
touch src/appfolio/{client,config,types,errors}.ts
touch src/services/appfolio/{index,sync,cache}.ts
```

## Resources
- [AppFolio SDK Documentation](https://docs.appfolio.com/sdk)
- [AppFolio Best Practices](https://docs.appfolio.com/best-practices)

## Flagship Skills
For multi-environment setup, see `appfolio-multi-env-setup`.