---
name: clickup-reference-architecture
description: |
  Implement ClickUp reference architecture with best-practice project layout.
  Use when designing new ClickUp integrations, reviewing project structure,
  or establishing architecture standards for ClickUp applications.
  Trigger with phrases like "clickup architecture", "clickup best practices",
  "clickup project structure", "how to organize clickup", "clickup layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickup]
---

# ClickUp Reference Architecture

## Overview
Production-ready architecture patterns for ClickUp integrations.

## Prerequisites
- Understanding of layered architecture
- ClickUp SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-clickup-project/
├── src/
│   ├── clickup/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── clickup/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── clickup/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── clickup/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── clickup/
│   └── integration/
│       └── clickup/
├── config/
│   ├── clickup.development.json
│   ├── clickup.staging.json
│   └── clickup.production.json
└── docs/
    └── clickup/
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
│          ClickUp Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/clickup/client.ts
export class ClickUpService {
  private client: ClickUpClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: ClickUpConfig) {
    this.client = new ClickUpClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('clickup');
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
// src/clickup/errors.ts
export class ClickUpServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'ClickUpServiceError';
  }
}

export function wrapClickUpError(error: unknown): ClickUpServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/clickup/health.ts
export async function checkClickUpHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await clickupClient.ping();
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
│ ClickUp    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ ClickUp    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/clickup.ts
export interface ClickUpConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadClickUpConfig(): ClickUpConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./clickup.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for ClickUp operations.

### Step 4: Configure Health Checks
Add health check endpoint for ClickUp connectivity.

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
| Type errors | Missing types | Add ClickUp types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/clickup/{handlers} src/services/clickup src/api/clickup
touch src/clickup/{client,config,types,errors}.ts
touch src/services/clickup/{index,sync,cache}.ts
```

## Resources
- [ClickUp SDK Documentation](https://docs.clickup.com/sdk)
- [ClickUp Best Practices](https://docs.clickup.com/best-practices)

## Flagship Skills
For multi-environment setup, see `clickup-multi-env-setup`.