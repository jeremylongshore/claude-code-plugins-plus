---
name: quicknode-reference-architecture
description: |
  Implement QuickNode reference architecture with best-practice project layout.
  Use when designing new QuickNode integrations, reviewing project structure,
  or establishing architecture standards for QuickNode applications.
  Trigger with phrases like "quicknode architecture", "quicknode best practices",
  "quicknode project structure", "how to organize quicknode", "quicknode layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, quicknode]
---

# QuickNode Reference Architecture

## Overview
Production-ready architecture patterns for QuickNode integrations.

## Prerequisites
- Understanding of layered architecture
- QuickNode SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-quicknode-project/
├── src/
│   ├── quicknode/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── quicknode/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── quicknode/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── quicknode/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── quicknode/
│   └── integration/
│       └── quicknode/
├── config/
│   ├── quicknode.development.json
│   ├── quicknode.staging.json
│   └── quicknode.production.json
└── docs/
    └── quicknode/
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
│          QuickNode Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/quicknode/client.ts
export class QuickNodeService {
  private client: QuickNodeClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: QuickNodeConfig) {
    this.client = new QuickNodeClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('quicknode');
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
// src/quicknode/errors.ts
export class QuickNodeServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'QuickNodeServiceError';
  }
}

export function wrapQuickNodeError(error: unknown): QuickNodeServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/quicknode/health.ts
export async function checkQuickNodeHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await quicknodeClient.ping();
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
│ QuickNode    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ QuickNode    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/quicknode.ts
export interface QuickNodeConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadQuickNodeConfig(): QuickNodeConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./quicknode.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for QuickNode operations.

### Step 4: Configure Health Checks
Add health check endpoint for QuickNode connectivity.

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
| Type errors | Missing types | Add QuickNode types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/quicknode/{handlers} src/services/quicknode src/api/quicknode
touch src/quicknode/{client,config,types,errors}.ts
touch src/services/quicknode/{index,sync,cache}.ts
```

## Resources
- [QuickNode SDK Documentation](https://docs.quicknode.com/sdk)
- [QuickNode Best Practices](https://docs.quicknode.com/best-practices)

## Flagship Skills
For multi-environment setup, see `quicknode-multi-env-setup`.