---
name: anima-reference-architecture
description: |
  Implement Anima reference architecture with best-practice project layout.
  Use when designing new Anima integrations, reviewing project structure,
  or establishing architecture standards for Anima applications.
  Trigger with phrases like "anima architecture", "anima best practices",
  "anima project structure", "how to organize anima", "anima layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anima]
---

# Anima Reference Architecture

## Overview
Production-ready architecture patterns for Anima integrations.

## Prerequisites
- Understanding of layered architecture
- Anima SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-anima-project/
├── src/
│   ├── anima/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── anima/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── anima/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── anima/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── anima/
│   └── integration/
│       └── anima/
├── config/
│   ├── anima.development.json
│   ├── anima.staging.json
│   └── anima.production.json
└── docs/
    └── anima/
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
│          Anima Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/anima/client.ts
export class AnimaService {
  private client: AnimaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: AnimaConfig) {
    this.client = new AnimaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('anima');
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
// src/anima/errors.ts
export class AnimaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'AnimaServiceError';
  }
}

export function wrapAnimaError(error: unknown): AnimaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/anima/health.ts
export async function checkAnimaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await animaClient.ping();
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
│ Anima    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Anima    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/anima.ts
export interface AnimaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadAnimaConfig(): AnimaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./anima.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Anima operations.

### Step 4: Configure Health Checks
Add health check endpoint for Anima connectivity.

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
| Type errors | Missing types | Add Anima types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/anima/{handlers} src/services/anima src/api/anima
touch src/anima/{client,config,types,errors}.ts
touch src/services/anima/{index,sync,cache}.ts
```

## Resources
- [Anima SDK Documentation](https://docs.anima.com/sdk)
- [Anima Best Practices](https://docs.anima.com/best-practices)

## Flagship Skills
For multi-environment setup, see `anima-multi-env-setup`.