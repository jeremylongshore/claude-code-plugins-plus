---
name: fireflies-reference-architecture
description: |
  Implement Fireflies.ai reference architecture with best-practice project layout.
  Use when designing new Fireflies.ai integrations, reviewing project structure,
  or establishing architecture standards for Fireflies.ai applications.
  Trigger with phrases like "fireflies architecture", "fireflies best practices",
  "fireflies project structure", "how to organize fireflies", "fireflies layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fireflies]
---

# Fireflies.ai Reference Architecture

## Overview
Production-ready architecture patterns for Fireflies.ai integrations.

## Prerequisites
- Understanding of layered architecture
- Fireflies.ai SDK knowledge
- TypeScript project setup
- Testing framework configured

## Project Structure

```
my-fireflies-project/
├── src/
│   ├── fireflies/
│   │   ├── client.ts           # Singleton client wrapper
│   │   ├── config.ts           # Environment configuration
│   │   ├── types.ts            # TypeScript types
│   │   ├── errors.ts           # Custom error classes
│   │   └── handlers/
│   │       ├── webhooks.ts     # Webhook handlers
│   │       └── events.ts       # Event processing
│   ├── services/
│   │   └── fireflies/
│   │       ├── index.ts        # Service facade
│   │       ├── sync.ts         # Data synchronization
│   │       └── cache.ts        # Caching layer
│   ├── api/
│   │   └── fireflies/
│   │       └── webhook.ts      # Webhook endpoint
│   └── jobs/
│       └── fireflies/
│           └── sync.ts         # Background sync job
├── tests/
│   ├── unit/
│   │   └── fireflies/
│   └── integration/
│       └── fireflies/
├── config/
│   ├── fireflies.development.json
│   ├── fireflies.staging.json
│   └── fireflies.production.json
└── docs/
    └── fireflies/
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
│          Fireflies.ai Layer        │
│   (Client, Types, Error Handling)        │
├─────────────────────────────────────────┤
│         Infrastructure Layer             │
│    (Cache, Queue, Monitoring)            │
└─────────────────────────────────────────┘
```

## Key Components

### Step 1: Client Wrapper
```typescript
// src/fireflies/client.ts
export class Fireflies.aiService {
  private client: Fireflies.aiClient;
  private cache: Cache;
  private monitor: Monitor;

  constructor(config: Fireflies.aiConfig) {
    this.client = new Fireflies.aiClient(config);
    this.cache = new Cache(config.cacheOptions);
    this.monitor = new Monitor('fireflies');
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
// src/fireflies/errors.ts
export class Fireflies.aiServiceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'Fireflies.aiServiceError';
  }
}

export function wrapFireflies.aiError(error: unknown): Fireflies.aiServiceError {
  // Transform SDK errors to application errors
}
```

### Step 3: Health Check
```typescript
// src/fireflies/health.ts
export async function checkFireflies.aiHealth(): Promise<HealthStatus> {
  try {
    const start = Date.now();
    await firefliesClient.ping();
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
│ Fireflies.ai    │
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Fireflies.ai    │
│   API       │
└─────────────┘
```

## Configuration Management

```typescript
// config/fireflies.ts
export interface Fireflies.aiConfig {
  apiKey: string;
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  retries: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
}

export function loadFireflies.aiConfig(): Fireflies.aiConfig {
  const env = process.env.NODE_ENV || 'development';
  return require(`./fireflies.${env}.json`);
}
```

## Instructions

### Step 1: Create Directory Structure
Set up the project layout following the reference structure above.

### Step 2: Implement Client Wrapper
Create the singleton client with caching and monitoring.

### Step 3: Add Error Handling
Implement custom error classes for Fireflies.ai operations.

### Step 4: Configure Health Checks
Add health check endpoint for Fireflies.ai connectivity.

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
| Type errors | Missing types | Add Fireflies.ai types |
| Test isolation | Shared state | Use dependency injection |

## Examples

### Quick Setup Script
```bash
# Create reference structure
mkdir -p src/fireflies/{handlers} src/services/fireflies src/api/fireflies
touch src/fireflies/{client,config,types,errors}.ts
touch src/services/fireflies/{index,sync,cache}.ts
```

## Resources
- [Fireflies.ai SDK Documentation](https://docs.fireflies.com/sdk)
- [Fireflies.ai Best Practices](https://docs.fireflies.com/best-practices)

## Flagship Skills
For multi-environment setup, see `fireflies-multi-env-setup`.