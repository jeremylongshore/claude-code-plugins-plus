---
name: clickhouse-reference-architecture
description: |
  Implement ClickHouse reference architecture with best-practice project layout.
  Use when designing new ClickHouse integrations, reviewing project structure,
  or establishing architecture standards for ClickHouse applications.
  Trigger with phrases like "clickhouse architecture", "clickhouse best practices",
  "clickhouse project structure", "how to organize clickhouse", "clickhouse layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickhouse]
---

# ClickHouse Reference Architecture

## Overview
Production-ready architecture patterns for ClickHouse integrations.

## Prerequisites
- Understanding of layered architecture
- ClickHouse SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-clickhouse-project/
├── src/
│   ├── clickhouse/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── clickhouse/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── clickhouse/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── clickhouse/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── clickhouse/
│   └── integration/
│       └── clickhouse/
├── config/
│   ├── clickhouse.development.json
│   ├── clickhouse.staging.json
│   └── clickhouse.production.json
└── docs/
    └── clickhouse/
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
│          ClickHouse Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/clickhouse/client.ts
export class ClickHouseService {
  private client: ClickHouseClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ClickHouseConfig) {
    this.client = new ClickHouseClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('clickhouse');
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
// src/clickhouse/errors.ts
export class ClickHouseServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ClickHouseServiceError';
  }
}

export function wrapClickHouseError(error: unknown): ClickHouseServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/clickhouse/health.ts
export async function checkClickHouseHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await clickhouseClient.ping();
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
│ ClickHouse    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ ClickHouse    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/clickhouse.ts
export interface ClickHouseConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadClickHouseConfig(): ClickHouseConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./clickhouse.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for ClickHouse operations.

### Step 4: Configure Health Checks
Add health check endpoint for ClickHouse connectivity.

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
| Type errors | Missing types | Add ClickHouse types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/clickhouse/{handlers} src/services/clickhouse src/api/clickhouse
touch src/clickhouse/{client,config,types,errors}.ts
touch src/services/clickhouse/{index,sync,cache}.ts
```

## Resources
- [ClickHouse SDK Documentation](https://docs.clickhouse.com/sdk)
- [ClickHouse Best Practices](https://docs.clickhouse.com/best-practices)

## Flagship Skills
For multi-environment setup, see `clickhouse-multi-env-setup`.