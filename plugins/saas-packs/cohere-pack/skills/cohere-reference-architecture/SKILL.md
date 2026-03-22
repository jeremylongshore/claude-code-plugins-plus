---
name: cohere-reference-architecture
description: |
  Implement Cohere reference architecture with best-practice project layout.
  Use when designing new Cohere integrations, reviewing project structure,
  or establishing architecture standards for Cohere applications.
  Trigger with phrases like "cohere architecture", "cohere best practices",
  "cohere project structure", "how to organize cohere", "cohere layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, cohere]
---

# Cohere Reference Architecture

## Overview
Production-ready architecture patterns for Cohere integrations.

## Prerequisites
- Understanding of layered architecture
- Cohere SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-cohere-project/
├── src/
│   ├── cohere/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── cohere/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── cohere/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── cohere/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── cohere/
│   └── integration/
│       └── cohere/
├── config/
│   ├── cohere.development.json
│   ├── cohere.staging.json
│   └── cohere.production.json
└── docs/
    └── cohere/
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
│          Cohere Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/cohere/client.ts
export class CohereService {
  private client: CohereClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: CohereConfig) {
    this.client = new CohereClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('cohere');
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
// src/cohere/errors.ts
export class CohereServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'CohereServiceError';
  }
}

export function wrapCohereError(error: unknown): CohereServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/cohere/health.ts
export async function checkCohereHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await cohereClient.ping();
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
│ Cohere    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Cohere    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/cohere.ts
export interface CohereConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadCohereConfig(): CohereConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./cohere.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Cohere operations.

### Step 4: Configure Health Checks
Add health check endpoint for Cohere connectivity.

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
| Type errors | Missing types | Add Cohere types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/cohere/{handlers} src/services/cohere src/api/cohere
touch src/cohere/{client,config,types,errors}.ts
touch src/services/cohere/{index,sync,cache}.ts
```

## Resources
- [Cohere SDK Documentation](https://docs.cohere.com/sdk)
- [Cohere Best Practices](https://docs.cohere.com/best-practices)

## Flagship Skills
For multi-environment setup, see `cohere-multi-env-setup`.