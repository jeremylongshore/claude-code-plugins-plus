---
name: replit-reference-architecture
description: |
  Implement Replit reference architecture with best-practice project layout.
  Use when designing new Replit integrations, reviewing project structure,
  or establishing architecture standards for Replit applications.
  Trigger with phrases like "replit architecture", "replit best practices",
  "replit project structure", "how to organize replit", "replit layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, replit]
---

# Replit Reference Architecture

## Overview
Production-ready architecture patterns for Replit integrations.

## Prerequisites
- Understanding of layered architecture
- Replit SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-replit-project/
├── src/
│   ├── replit/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── replit/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── replit/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── replit/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── replit/
│   └── integration/
│       └── replit/
├── config/
│   ├── replit.development.json
│   ├── replit.staging.json
│   └── replit.production.json
└── docs/
    └── replit/
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
│          Replit Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/replit/client.ts
export class ReplitService {
  private client: ReplitClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ReplitConfig) {
    this.client = new ReplitClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('replit');
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
// src/replit/errors.ts
export class ReplitServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ReplitServiceError';
  }
}

export function wrapReplitError(error: unknown): ReplitServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/replit/health.ts
export async function checkReplitHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await replitClient.ping();
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
│ Replit    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Replit    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/replit.ts
export interface ReplitConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadReplitConfig(): ReplitConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./replit.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Replit operations.

### Step 4: Configure Health Checks
Add health check endpoint for Replit connectivity.

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
| Type errors | Missing types | Add Replit types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/replit/{handlers} src/services/replit src/api/replit
touch src/replit/{client,config,types,errors}.ts
touch src/services/replit/{index,sync,cache}.ts
```

## Resources
- [Replit SDK Documentation](https://docs.replit.com/sdk)
- [Replit Best Practices](https://docs.replit.com/best-practices)

## Flagship Skills
For multi-environment setup, see `replit-multi-env-setup`.