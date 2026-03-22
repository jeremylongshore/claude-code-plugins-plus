---
name: oraclecloud-reference-architecture
description: |
  Implement Oracle Cloud reference architecture with best-practice project layout.
  Use when designing new Oracle Cloud integrations, reviewing project structure,
  or establishing architecture standards for Oracle Cloud applications.
  Trigger with phrases like "oraclecloud architecture", "oraclecloud best practices",
  "oraclecloud project structure", "how to organize oraclecloud", "oraclecloud layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, oraclecloud]
---

# Oracle Cloud Reference Architecture

## Overview
Production-ready architecture patterns for Oracle Cloud integrations.

## Prerequisites
- Understanding of layered architecture
- Oracle Cloud SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-oraclecloud-project/
├── src/
│   ├── oraclecloud/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── oraclecloud/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── oraclecloud/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── oraclecloud/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── oraclecloud/
│   └── integration/
│       └── oraclecloud/
├── config/
│   ├── oraclecloud.development.json
│   ├── oraclecloud.staging.json
│   └── oraclecloud.production.json
└── docs/
    └── oraclecloud/
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
│          Oracle Cloud Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/oraclecloud/client.ts
export class Oracle CloudService {
  private client: OracleCloudClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Oracle CloudConfig) {
    this.client = new OracleCloudClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('oraclecloud');
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
// src/oraclecloud/errors.ts
export class Oracle CloudServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Oracle CloudServiceError';
  }
}

export function wrapOracle CloudError(error: unknown): Oracle CloudServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/oraclecloud/health.ts
export async function checkOracle CloudHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await oraclecloudClient.ping();
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
│ Oracle Cloud    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Oracle Cloud    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/oraclecloud.ts
export interface Oracle CloudConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadOracle CloudConfig(): Oracle CloudConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./oraclecloud.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Oracle Cloud operations.

### Step 4: Configure Health Checks
Add health check endpoint for Oracle Cloud connectivity.

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
| Type errors | Missing types | Add Oracle Cloud types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/oraclecloud/{handlers} src/services/oraclecloud src/api/oraclecloud
touch src/oraclecloud/{client,config,types,errors}.ts
touch src/services/oraclecloud/{index,sync,cache}.ts
```

## Resources
- [Oracle Cloud SDK Documentation](https://docs.oraclecloud.com/sdk)
- [Oracle Cloud Best Practices](https://docs.oraclecloud.com/best-practices)

## Flagship Skills
For multi-environment setup, see `oraclecloud-multi-env-setup`.