---
name: databricks-reference-architecture
description: |
  Implement Databricks reference architecture with best-practice project layout.
  Use when designing new Databricks integrations, reviewing project structure,
  or establishing architecture standards for Databricks applications.
  Trigger with phrases like "databricks architecture", "databricks best practices",
  "databricks project structure", "how to organize databricks", "databricks layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, databricks]
---

# Databricks Reference Architecture

## Overview
Production-ready architecture patterns for Databricks integrations.

## Prerequisites
- Understanding of layered architecture
- Databricks SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-databricks-project/
├── src/
│   ├── databricks/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── databricks/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── databricks/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── databricks/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── databricks/
│   └── integration/
│       └── databricks/
├── config/
│   ├── databricks.development.json
│   ├── databricks.staging.json
│   └── databricks.production.json
└── docs/
    └── databricks/
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
│          Databricks Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/databricks/client.ts
export class DatabricksService {
  private client: DatabricksClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: DatabricksConfig) {
    this.client = new DatabricksClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('databricks');
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
// src/databricks/errors.ts
export class DatabricksServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'DatabricksServiceError';
  }
}

export function wrapDatabricksError(error: unknown): DatabricksServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/databricks/health.ts
export async function checkDatabricksHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await databricksClient.ping();
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
│ Databricks    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Databricks    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/databricks.ts
export interface DatabricksConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadDatabricksConfig(): DatabricksConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./databricks.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Databricks operations.

### Step 4: Configure Health Checks
Add health check endpoint for Databricks connectivity.

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
| Type errors | Missing types | Add Databricks types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/databricks/{handlers} src/services/databricks src/api/databricks
touch src/databricks/{client,config,types,errors}.ts
touch src/services/databricks/{index,sync,cache}.ts
```

## Resources
- [Databricks SDK Documentation](https://docs.databricks.com/sdk)
- [Databricks Best Practices](https://docs.databricks.com/best-practices)

## Flagship Skills
For multi-environment setup, see `databricks-multi-env-setup`.