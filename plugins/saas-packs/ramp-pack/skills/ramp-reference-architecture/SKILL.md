---
name: ramp-reference-architecture
description: |
  Implement Ramp reference architecture with best-practice project layout.
  Use when designing new Ramp integrations, reviewing project structure,
  or establishing architecture standards for Ramp applications.
  Trigger with phrases like "ramp architecture", "ramp best practices",
  "ramp project structure", "how to organize ramp", "ramp layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, ramp]
---

# Ramp Reference Architecture

## Overview
Production-ready architecture patterns for Ramp integrations.

## Prerequisites
- Understanding of layered architecture
- Ramp SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-ramp-project/
├── src/
│   ├── ramp/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── ramp/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── ramp/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── ramp/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── ramp/
│   └── integration/
│       └── ramp/
├── config/
│   ├── ramp.development.json
│   ├── ramp.staging.json
│   └── ramp.production.json
└── docs/
    └── ramp/
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
│          Ramp Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/ramp/client.ts
export class RampService {
  private client: RampClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: RampConfig) {
    this.client = new RampClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('ramp');
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
// src/ramp/errors.ts
export class RampServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'RampServiceError';
  }
}

export function wrapRampError(error: unknown): RampServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/ramp/health.ts
export async function checkRampHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await rampClient.ping();
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
│ Ramp    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Ramp    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/ramp.ts
export interface RampConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadRampConfig(): RampConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./ramp.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Ramp operations.

### Step 4: Configure Health Checks
Add health check endpoint for Ramp connectivity.

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
| Type errors | Missing types | Add Ramp types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/ramp/{handlers} src/services/ramp src/api/ramp
touch src/ramp/{client,config,types,errors}.ts
touch src/services/ramp/{index,sync,cache}.ts
```

## Resources
- [Ramp SDK Documentation](https://docs.ramp.com/sdk)
- [Ramp Best Practices](https://docs.ramp.com/best-practices)

## Flagship Skills
For multi-environment setup, see `ramp-multi-env-setup`.