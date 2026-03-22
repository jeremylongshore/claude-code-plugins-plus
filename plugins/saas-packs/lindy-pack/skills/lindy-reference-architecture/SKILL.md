---
name: lindy-reference-architecture
description: |
  Implement Lindy reference architecture with best-practice project layout.
  Use when designing new Lindy integrations, reviewing project structure,
  or establishing architecture standards for Lindy applications.
  Trigger with phrases like "lindy architecture", "lindy best practices",
  "lindy project structure", "how to organize lindy", "lindy layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lindy]
---

# Lindy Reference Architecture

## Overview
Production-ready architecture patterns for Lindy integrations.

## Prerequisites
- Understanding of layered architecture
- Lindy SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-lindy-project/
├── src/
│   ├── lindy/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── lindy/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── lindy/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── lindy/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── lindy/
│   └── integration/
│       └── lindy/
├── config/
│   ├── lindy.development.json
│   ├── lindy.staging.json
│   └── lindy.production.json
└── docs/
    └── lindy/
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
│          Lindy Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/lindy/client.ts
export class LindyService {
  private client: LindyClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: LindyConfig) {
    this.client = new LindyClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('lindy');
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
// src/lindy/errors.ts
export class LindyServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'LindyServiceError';
  }
}

export function wrapLindyError(error: unknown): LindyServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/lindy/health.ts
export async function checkLindyHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await lindyClient.ping();
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
│ Lindy    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Lindy    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/lindy.ts
export interface LindyConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadLindyConfig(): LindyConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./lindy.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Lindy operations.

### Step 4: Configure Health Checks
Add health check endpoint for Lindy connectivity.

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
| Type errors | Missing types | Add Lindy types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/lindy/{handlers} src/services/lindy src/api/lindy
touch src/lindy/{client,config,types,errors}.ts
touch src/services/lindy/{index,sync,cache}.ts
```

## Resources
- [Lindy SDK Documentation](https://docs.lindy.com/sdk)
- [Lindy Best Practices](https://docs.lindy.com/best-practices)

## Flagship Skills
For multi-environment setup, see `lindy-multi-env-setup`.