---
name: brightdata-reference-architecture
description: |
  Implement Bright Data reference architecture with best-practice project layout.
  Use when designing new Bright Data integrations, reviewing project structure,
  or establishing architecture standards for Bright Data applications.
  Trigger with phrases like "brightdata architecture", "brightdata best practices",
  "brightdata project structure", "how to organize brightdata", "brightdata layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, brightdata]
---

# Bright Data Reference Architecture

## Overview
Production-ready architecture patterns for Bright Data integrations.

## Prerequisites
- Understanding of layered architecture
- Bright Data SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-brightdata-project/
├── src/
│   ├── brightdata/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── brightdata/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── brightdata/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── brightdata/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── brightdata/
│   └── integration/
│       └── brightdata/
├── config/
│   ├── brightdata.development.json
│   ├── brightdata.staging.json
│   └── brightdata.production.json
└── docs/
    └── brightdata/
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
│          Bright Data Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/brightdata/client.ts
export class Bright DataService {
  private client: BrightDataClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Bright DataConfig) {
    this.client = new BrightDataClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('brightdata');
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
// src/brightdata/errors.ts
export class Bright DataServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Bright DataServiceError';
  }
}

export function wrapBright DataError(error: unknown): Bright DataServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/brightdata/health.ts
export async function checkBright DataHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await brightdataClient.ping();
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
│ Bright Data    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Bright Data    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/brightdata.ts
export interface Bright DataConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadBright DataConfig(): Bright DataConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./brightdata.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Bright Data operations.

### Step 4: Configure Health Checks
Add health check endpoint for Bright Data connectivity.

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
| Type errors | Missing types | Add Bright Data types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/brightdata/{handlers} src/services/brightdata src/api/brightdata
touch src/brightdata/{client,config,types,errors}.ts
touch src/services/brightdata/{index,sync,cache}.ts
```

## Resources
- [Bright Data SDK Documentation](https://docs.brightdata.com/sdk)
- [Bright Data Best Practices](https://docs.brightdata.com/best-practices)

## Flagship Skills
For multi-environment setup, see `brightdata-multi-env-setup`.