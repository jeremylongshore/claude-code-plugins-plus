---
name: stackblitz-reference-architecture
description: |
  Implement StackBlitz reference architecture with best-practice project layout.
  Use when designing new StackBlitz integrations, reviewing project structure,
  or establishing architecture standards for StackBlitz applications.
  Trigger with phrases like "stackblitz architecture", "stackblitz best practices",
  "stackblitz project structure", "how to organize stackblitz", "stackblitz layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, stackblitz]
---

# StackBlitz Reference Architecture

## Overview
Production-ready architecture patterns for StackBlitz integrations.

## Prerequisites
- Understanding of layered architecture
- StackBlitz SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-stackblitz-project/
├── src/
│   ├── stackblitz/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── stackblitz/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── stackblitz/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── stackblitz/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── stackblitz/
│   └── integration/
│       └── stackblitz/
├── config/
│   ├── stackblitz.development.json
│   ├── stackblitz.staging.json
│   └── stackblitz.production.json
└── docs/
    └── stackblitz/
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
│          StackBlitz Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/stackblitz/client.ts
export class StackBlitzService {
  private client: StackBlitzClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: StackBlitzConfig) {
    this.client = new StackBlitzClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('stackblitz');
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
// src/stackblitz/errors.ts
export class StackBlitzServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'StackBlitzServiceError';
  }
}

export function wrapStackBlitzError(error: unknown): StackBlitzServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/stackblitz/health.ts
export async function checkStackBlitzHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await stackblitzClient.ping();
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
│ StackBlitz    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ StackBlitz    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/stackblitz.ts
export interface StackBlitzConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadStackBlitzConfig(): StackBlitzConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./stackblitz.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for StackBlitz operations.

### Step 4: Configure Health Checks
Add health check endpoint for StackBlitz connectivity.

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
| Type errors | Missing types | Add StackBlitz types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/stackblitz/{handlers} src/services/stackblitz src/api/stackblitz
touch src/stackblitz/{client,config,types,errors}.ts
touch src/services/stackblitz/{index,sync,cache}.ts
```

## Resources
- [StackBlitz SDK Documentation](https://docs.stackblitz.com/sdk)
- [StackBlitz Best Practices](https://docs.stackblitz.com/best-practices)

## Flagship Skills
For multi-environment setup, see `stackblitz-multi-env-setup`.