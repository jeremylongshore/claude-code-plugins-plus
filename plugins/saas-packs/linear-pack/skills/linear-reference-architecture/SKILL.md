---
name: linear-reference-architecture
description: |
  Implement Linear reference architecture with best-practice project layout.
  Use when designing new Linear integrations, reviewing project structure,
  or establishing architecture standards for Linear applications.
  Trigger with phrases like "linear architecture", "linear best practices",
  "linear project structure", "how to organize linear", "linear layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linear]
---

# Linear Reference Architecture

## Overview
Production-ready architecture patterns for Linear integrations.

## Prerequisites
- Understanding of layered architecture
- Linear SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-linear-project/
├── src/
│   ├── linear/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── linear/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── linear/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── linear/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── linear/
│   └── integration/
│       └── linear/
├── config/
│   ├── linear.development.json
│   ├── linear.staging.json
│   └── linear.production.json
└── docs/
    └── linear/
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
│          Linear Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/linear/client.ts
export class LinearService {
  private client: LinearClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: LinearConfig) {
    this.client = new LinearClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('linear');
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
// src/linear/errors.ts
export class LinearServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'LinearServiceError';
  }
}

export function wrapLinearError(error: unknown): LinearServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/linear/health.ts
export async function checkLinearHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await linearClient.ping();
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
│ Linear    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Linear    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/linear.ts
export interface LinearConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadLinearConfig(): LinearConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./linear.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Linear operations.

### Step 4: Configure Health Checks
Add health check endpoint for Linear connectivity.

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
| Type errors | Missing types | Add Linear types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/linear/{handlers} src/services/linear src/api/linear
touch src/linear/{client,config,types,errors}.ts
touch src/services/linear/{index,sync,cache}.ts
```

## Resources
- [Linear SDK Documentation](https://docs.linear.com/sdk)
- [Linear Best Practices](https://docs.linear.com/best-practices)

## Flagship Skills
For multi-environment setup, see `linear-multi-env-setup`.