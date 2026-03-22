---
name: miro-reference-architecture
description: |
  Implement Miro reference architecture with best-practice project layout.
  Use when designing new Miro integrations, reviewing project structure,
  or establishing architecture standards for Miro applications.
  Trigger with phrases like "miro architecture", "miro best practices",
  "miro project structure", "how to organize miro", "miro layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, miro]
---

# Miro Reference Architecture

## Overview
Production-ready architecture patterns for Miro integrations.

## Prerequisites
- Understanding of layered architecture
- Miro SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-miro-project/
├── src/
│   ├── miro/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── miro/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── miro/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── miro/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── miro/
│   └── integration/
│       └── miro/
├── config/
│   ├── miro.development.json
│   ├── miro.staging.json
│   └── miro.production.json
└── docs/
    └── miro/
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
│          Miro Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/miro/client.ts
export class MiroService {
  private client: MiroClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: MiroConfig) {
    this.client = new MiroClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('miro');
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
// src/miro/errors.ts
export class MiroServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'MiroServiceError';
  }
}

export function wrapMiroError(error: unknown): MiroServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/miro/health.ts
export async function checkMiroHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await miroClient.ping();
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
│ Miro    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Miro    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/miro.ts
export interface MiroConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadMiroConfig(): MiroConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./miro.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Miro operations.

### Step 4: Configure Health Checks
Add health check endpoint for Miro connectivity.

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
| Type errors | Missing types | Add Miro types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/miro/{handlers} src/services/miro src/api/miro
touch src/miro/{client,config,types,errors}.ts
touch src/services/miro/{index,sync,cache}.ts
```

## Resources
- [Miro SDK Documentation](https://docs.miro.com/sdk)
- [Miro Best Practices](https://docs.miro.com/best-practices)

## Flagship Skills
For multi-environment setup, see `miro-multi-env-setup`.