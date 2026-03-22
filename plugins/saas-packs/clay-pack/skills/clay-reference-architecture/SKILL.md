---
name: clay-reference-architecture
description: |
  Implement Clay reference architecture with best-practice project layout.
  Use when designing new Clay integrations, reviewing project structure,
  or establishing architecture standards for Clay applications.
  Trigger with phrases like "clay architecture", "clay best practices",
  "clay project structure", "how to organize clay", "clay layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clay]
---

# Clay Reference Architecture

## Overview
Production-ready architecture patterns for Clay integrations.

## Prerequisites
- Understanding of layered architecture
- Clay SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-clay-project/
├── src/
│   ├── clay/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── clay/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── clay/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── clay/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── clay/
│   └── integration/
│       └── clay/
├── config/
│   ├── clay.development.json
│   ├── clay.staging.json
│   └── clay.production.json
└── docs/
    └── clay/
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
│          Clay Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/clay/client.ts
export class ClayService {
  private client: ClayClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ClayConfig) {
    this.client = new ClayClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('clay');
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
// src/clay/errors.ts
export class ClayServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ClayServiceError';
  }
}

export function wrapClayError(error: unknown): ClayServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/clay/health.ts
export async function checkClayHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await clayClient.ping();
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
│ Clay    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Clay    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/clay.ts
export interface ClayConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadClayConfig(): ClayConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./clay.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Clay operations.

### Step 4: Configure Health Checks
Add health check endpoint for Clay connectivity.

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
| Type errors | Missing types | Add Clay types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/clay/{handlers} src/services/clay src/api/clay
touch src/clay/{client,config,types,errors}.ts
touch src/services/clay/{index,sync,cache}.ts
```

## Resources
- [Clay SDK Documentation](https://docs.clay.com/sdk)
- [Clay Best Practices](https://docs.clay.com/best-practices)

## Flagship Skills
For multi-environment setup, see `clay-multi-env-setup`.