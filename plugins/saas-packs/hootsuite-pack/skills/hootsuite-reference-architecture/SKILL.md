---
name: hootsuite-reference-architecture
description: |
  Implement Hootsuite reference architecture with best-practice project layout.
  Use when designing new Hootsuite integrations, reviewing project structure,
  or establishing architecture standards for Hootsuite applications.
  Trigger with phrases like "hootsuite architecture", "hootsuite best practices",
  "hootsuite project structure", "how to organize hootsuite", "hootsuite layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hootsuite]
---

# Hootsuite Reference Architecture

## Overview
Production-ready architecture patterns for Hootsuite integrations.

## Prerequisites
- Understanding of layered architecture
- Hootsuite SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-hootsuite-project/
├── src/
│   ├── hootsuite/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── hootsuite/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── hootsuite/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── hootsuite/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── hootsuite/
│   └── integration/
│       └── hootsuite/
├── config/
│   ├── hootsuite.development.json
│   ├── hootsuite.staging.json
│   └── hootsuite.production.json
└── docs/
    └── hootsuite/
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
│          Hootsuite Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/hootsuite/client.ts
export class HootsuiteService {
  private client: HootsuiteClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: HootsuiteConfig) {
    this.client = new HootsuiteClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('hootsuite');
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
// src/hootsuite/errors.ts
export class HootsuiteServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'HootsuiteServiceError';
  }
}

export function wrapHootsuiteError(error: unknown): HootsuiteServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/hootsuite/health.ts
export async function checkHootsuiteHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await hootsuiteClient.ping();
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
│ Hootsuite    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Hootsuite    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/hootsuite.ts
export interface HootsuiteConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadHootsuiteConfig(): HootsuiteConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./hootsuite.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Hootsuite operations.

### Step 4: Configure Health Checks
Add health check endpoint for Hootsuite connectivity.

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
| Type errors | Missing types | Add Hootsuite types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/hootsuite/{handlers} src/services/hootsuite src/api/hootsuite
touch src/hootsuite/{client,config,types,errors}.ts
touch src/services/hootsuite/{index,sync,cache}.ts
```

## Resources
- [Hootsuite SDK Documentation](https://docs.hootsuite.com/sdk)
- [Hootsuite Best Practices](https://docs.hootsuite.com/best-practices)

## Flagship Skills
For multi-environment setup, see `hootsuite-multi-env-setup`.