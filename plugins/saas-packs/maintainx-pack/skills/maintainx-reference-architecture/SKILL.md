---
name: maintainx-reference-architecture
description: |
  Implement MaintainX reference architecture with best-practice project layout.
  Use when designing new MaintainX integrations, reviewing project structure,
  or establishing architecture standards for MaintainX applications.
  Trigger with phrases like "maintainx architecture", "maintainx best practices",
  "maintainx project structure", "how to organize maintainx", "maintainx layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, maintainx]
---

# MaintainX Reference Architecture

## Overview
Production-ready architecture patterns for MaintainX integrations.

## Prerequisites
- Understanding of layered architecture
- MaintainX SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-maintainx-project/
├── src/
│   ├── maintainx/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── maintainx/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── maintainx/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── maintainx/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── maintainx/
│   └── integration/
│       └── maintainx/
├── config/
│   ├── maintainx.development.json
│   ├── maintainx.staging.json
│   └── maintainx.production.json
└── docs/
    └── maintainx/
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
│          MaintainX Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/maintainx/client.ts
export class MaintainXService {
  private client: MaintainXClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: MaintainXConfig) {
    this.client = new MaintainXClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('maintainx');
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
// src/maintainx/errors.ts
export class MaintainXServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'MaintainXServiceError';
  }
}

export function wrapMaintainXError(error: unknown): MaintainXServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/maintainx/health.ts
export async function checkMaintainXHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await maintainxClient.ping();
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
│ MaintainX    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ MaintainX    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/maintainx.ts
export interface MaintainXConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadMaintainXConfig(): MaintainXConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./maintainx.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for MaintainX operations.

### Step 4: Configure Health Checks
Add health check endpoint for MaintainX connectivity.

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
| Type errors | Missing types | Add MaintainX types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/maintainx/{handlers} src/services/maintainx src/api/maintainx
touch src/maintainx/{client,config,types,errors}.ts
touch src/services/maintainx/{index,sync,cache}.ts
```

## Resources
- [MaintainX SDK Documentation](https://docs.maintainx.com/sdk)
- [MaintainX Best Practices](https://docs.maintainx.com/best-practices)

## Flagship Skills
For multi-environment setup, see `maintainx-multi-env-setup`.