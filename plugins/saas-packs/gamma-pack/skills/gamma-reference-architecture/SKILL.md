---
name: gamma-reference-architecture
description: |
  Implement Gamma reference architecture with best-practice project layout.
  Use when designing new Gamma integrations, reviewing project structure,
  or establishing architecture standards for Gamma applications.
  Trigger with phrases like "gamma architecture", "gamma best practices",
  "gamma project structure", "how to organize gamma", "gamma layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, gamma]
---

# Gamma Reference Architecture

## Overview
Production-ready architecture patterns for Gamma integrations.

## Prerequisites
- Understanding of layered architecture
- Gamma SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-gamma-project/
├── src/
│   ├── gamma/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── gamma/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── gamma/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── gamma/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── gamma/
│   └── integration/
│       └── gamma/
├── config/
│   ├── gamma.development.json
│   ├── gamma.staging.json
│   └── gamma.production.json
└── docs/
    └── gamma/
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
│          Gamma Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/gamma/client.ts
export class GammaService {
  private client: GammaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: GammaConfig) {
    this.client = new GammaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('gamma');
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
// src/gamma/errors.ts
export class GammaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'GammaServiceError';
  }
}

export function wrapGammaError(error: unknown): GammaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/gamma/health.ts
export async function checkGammaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await gammaClient.ping();
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
│ Gamma    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Gamma    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/gamma.ts
export interface GammaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadGammaConfig(): GammaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./gamma.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Gamma operations.

### Step 4: Configure Health Checks
Add health check endpoint for Gamma connectivity.

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
| Type errors | Missing types | Add Gamma types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/gamma/{handlers} src/services/gamma src/api/gamma
touch src/gamma/{client,config,types,errors}.ts
touch src/services/gamma/{index,sync,cache}.ts
```

## Resources
- [Gamma SDK Documentation](https://docs.gamma.com/sdk)
- [Gamma Best Practices](https://docs.gamma.com/best-practices)

## Flagship Skills
For multi-environment setup, see `gamma-multi-env-setup`.