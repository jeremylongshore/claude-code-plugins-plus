---
name: canva-reference-architecture
description: |
  Implement Canva reference architecture with best-practice project layout.
  Use when designing new Canva integrations, reviewing project structure,
  or establishing architecture standards for Canva applications.
  Trigger with phrases like "canva architecture", "canva best practices",
  "canva project structure", "how to organize canva", "canva layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, canva]
---

# Canva Reference Architecture

## Overview
Production-ready architecture patterns for Canva integrations.

## Prerequisites
- Understanding of layered architecture
- Canva SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-canva-project/
├── src/
│   ├── canva/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── canva/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── canva/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── canva/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── canva/
│   └── integration/
│       └── canva/
├── config/
│   ├── canva.development.json
│   ├── canva.staging.json
│   └── canva.production.json
└── docs/
    └── canva/
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
│          Canva Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/canva/client.ts
export class CanvaService {
  private client: CanvaClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: CanvaConfig) {
    this.client = new CanvaClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('canva');
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
// src/canva/errors.ts
export class CanvaServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'CanvaServiceError';
  }
}

export function wrapCanvaError(error: unknown): CanvaServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/canva/health.ts
export async function checkCanvaHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await canvaClient.ping();
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
│ Canva    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Canva    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/canva.ts
export interface CanvaConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadCanvaConfig(): CanvaConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./canva.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Canva operations.

### Step 4: Configure Health Checks
Add health check endpoint for Canva connectivity.

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
| Type errors | Missing types | Add Canva types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/canva/{handlers} src/services/canva src/api/canva
touch src/canva/{client,config,types,errors}.ts
touch src/services/canva/{index,sync,cache}.ts
```

## Resources
- [Canva SDK Documentation](https://docs.canva.com/sdk)
- [Canva Best Practices](https://docs.canva.com/best-practices)

## Flagship Skills
For multi-environment setup, see `canva-multi-env-setup`.