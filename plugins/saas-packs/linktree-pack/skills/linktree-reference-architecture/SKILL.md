---
name: linktree-reference-architecture
description: |
  Implement Linktree reference architecture with best-practice project layout.
  Use when designing new Linktree integrations, reviewing project structure,
  or establishing architecture standards for Linktree applications.
  Trigger with phrases like "linktree architecture", "linktree best practices",
  "linktree project structure", "how to organize linktree", "linktree layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linktree]
---

# Linktree Reference Architecture

## Overview
Production-ready architecture patterns for Linktree integrations.

## Prerequisites
- Understanding of layered architecture
- Linktree SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-linktree-project/
├── src/
│   ├── linktree/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── linktree/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── linktree/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── linktree/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── linktree/
│   └── integration/
│       └── linktree/
├── config/
│   ├── linktree.development.json
│   ├── linktree.staging.json
│   └── linktree.production.json
└── docs/
    └── linktree/
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
│          Linktree Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/linktree/client.ts
export class LinktreeService {
  private client: LinktreeClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: LinktreeConfig) {
    this.client = new LinktreeClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('linktree');
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
// src/linktree/errors.ts
export class LinktreeServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'LinktreeServiceError';
  }
}

export function wrapLinktreeError(error: unknown): LinktreeServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/linktree/health.ts
export async function checkLinktreeHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await linktreeClient.ping();
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
│ Linktree    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Linktree    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/linktree.ts
export interface LinktreeConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadLinktreeConfig(): LinktreeConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./linktree.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Linktree operations.

### Step 4: Configure Health Checks
Add health check endpoint for Linktree connectivity.

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
| Type errors | Missing types | Add Linktree types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/linktree/{handlers} src/services/linktree src/api/linktree
touch src/linktree/{client,config,types,errors}.ts
touch src/services/linktree/{index,sync,cache}.ts
```

## Resources
- [Linktree SDK Documentation](https://docs.linktree.com/sdk)
- [Linktree Best Practices](https://docs.linktree.com/best-practices)

## Flagship Skills
For multi-environment setup, see `linktree-multi-env-setup`.