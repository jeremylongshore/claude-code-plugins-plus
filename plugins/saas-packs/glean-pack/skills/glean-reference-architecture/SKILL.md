---
name: glean-reference-architecture
description: |
  Implement Glean reference architecture with best-practice project layout.
  Use when designing new Glean integrations, reviewing project structure,
  or establishing architecture standards for Glean applications.
  Trigger with phrases like "glean architecture", "glean best practices",
  "glean project structure", "how to organize glean", "glean layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, glean]
---

# Glean Reference Architecture

## Overview
Production-ready architecture patterns for Glean integrations.

## Prerequisites
- Understanding of layered architecture
- Glean SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-glean-project/
├── src/
│   ├── glean/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── glean/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── glean/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── glean/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── glean/
│   └── integration/
│       └── glean/
├── config/
│   ├── glean.development.json
│   ├── glean.staging.json
│   └── glean.production.json
└── docs/
    └── glean/
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
│          Glean Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/glean/client.ts
export class GleanService {
  private client: GleanClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: GleanConfig) {
    this.client = new GleanClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('glean');
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
// src/glean/errors.ts
export class GleanServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'GleanServiceError';
  }
}

export function wrapGleanError(error: unknown): GleanServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/glean/health.ts
export async function checkGleanHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await gleanClient.ping();
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
│ Glean    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Glean    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/glean.ts
export interface GleanConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadGleanConfig(): GleanConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./glean.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Glean operations.

### Step 4: Configure Health Checks
Add health check endpoint for Glean connectivity.

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
| Type errors | Missing types | Add Glean types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/glean/{handlers} src/services/glean src/api/glean
touch src/glean/{client,config,types,errors}.ts
touch src/services/glean/{index,sync,cache}.ts
```

## Resources
- [Glean SDK Documentation](https://docs.glean.com/sdk)
- [Glean Best Practices](https://docs.glean.com/best-practices)

## Flagship Skills
For multi-environment setup, see `glean-multi-env-setup`.