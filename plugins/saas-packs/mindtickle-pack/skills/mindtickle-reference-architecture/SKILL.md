---
name: mindtickle-reference-architecture
description: |
  Implement Mindtickle reference architecture with best-practice project layout.
  Use when designing new Mindtickle integrations, reviewing project structure,
  or establishing architecture standards for Mindtickle applications.
  Trigger with phrases like "mindtickle architecture", "mindtickle best practices",
  "mindtickle project structure", "how to organize mindtickle", "mindtickle layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mindtickle]
---

# Mindtickle Reference Architecture

## Overview
Production-ready architecture patterns for Mindtickle integrations.

## Prerequisites
- Understanding of layered architecture
- Mindtickle SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-mindtickle-project/
├── src/
│   ├── mindtickle/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── mindtickle/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── mindtickle/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── mindtickle/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── mindtickle/
│   └── integration/
│       └── mindtickle/
├── config/
│   ├── mindtickle.development.json
│   ├── mindtickle.staging.json
│   └── mindtickle.production.json
└── docs/
    └── mindtickle/
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
│          Mindtickle Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/mindtickle/client.ts
export class MindtickleService {
  private client: MindtickleClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: MindtickleConfig) {
    this.client = new MindtickleClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('mindtickle');
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
// src/mindtickle/errors.ts
export class MindtickleServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'MindtickleServiceError';
  }
}

export function wrapMindtickleError(error: unknown): MindtickleServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/mindtickle/health.ts
export async function checkMindtickleHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await mindtickleClient.ping();
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
│ Mindtickle    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Mindtickle    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/mindtickle.ts
export interface MindtickleConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadMindtickleConfig(): MindtickleConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./mindtickle.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Mindtickle operations.

### Step 4: Configure Health Checks
Add health check endpoint for Mindtickle connectivity.

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
| Type errors | Missing types | Add Mindtickle types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/mindtickle/{handlers} src/services/mindtickle src/api/mindtickle
touch src/mindtickle/{client,config,types,errors}.ts
touch src/services/mindtickle/{index,sync,cache}.ts
```

## Resources
- [Mindtickle SDK Documentation](https://docs.mindtickle.com/sdk)
- [Mindtickle Best Practices](https://docs.mindtickle.com/best-practices)

## Flagship Skills
For multi-environment setup, see `mindtickle-multi-env-setup`.