---
name: palantir-reference-architecture
description: |
  Implement Palantir reference architecture with best-practice project layout.
  Use when designing new Palantir integrations, reviewing project structure,
  or establishing architecture standards for Palantir applications.
  Trigger with phrases like "palantir architecture", "palantir best practices",
  "palantir project structure", "how to organize palantir", "palantir layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, palantir]
---

# Palantir Reference Architecture

## Overview
Production-ready architecture patterns for Palantir integrations.

## Prerequisites
- Understanding of layered architecture
- Palantir SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-palantir-project/
├── src/
│   ├── palantir/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── palantir/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── palantir/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── palantir/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── palantir/
│   └── integration/
│       └── palantir/
├── config/
│   ├── palantir.development.json
│   ├── palantir.staging.json
│   └── palantir.production.json
└── docs/
    └── palantir/
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
│          Palantir Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/palantir/client.ts
export class PalantirService {
  private client: PalantirClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: PalantirConfig) {
    this.client = new PalantirClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('palantir');
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
// src/palantir/errors.ts
export class PalantirServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'PalantirServiceError';
  }
}

export function wrapPalantirError(error: unknown): PalantirServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/palantir/health.ts
export async function checkPalantirHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await palantirClient.ping();
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
│ Palantir    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Palantir    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/palantir.ts
export interface PalantirConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadPalantirConfig(): PalantirConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./palantir.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Palantir operations.

### Step 4: Configure Health Checks
Add health check endpoint for Palantir connectivity.

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
| Type errors | Missing types | Add Palantir types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/palantir/{handlers} src/services/palantir src/api/palantir
touch src/palantir/{client,config,types,errors}.ts
touch src/services/palantir/{index,sync,cache}.ts
```

## Resources
- [Palantir SDK Documentation](https://docs.palantir.com/sdk)
- [Palantir Best Practices](https://docs.palantir.com/best-practices)

## Flagship Skills
For multi-environment setup, see `palantir-multi-env-setup`.